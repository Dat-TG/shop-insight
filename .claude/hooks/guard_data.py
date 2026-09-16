#!/usr/bin/env python3
"""PreToolUse hook (matcher: Bash). Blocks four shapes of command.

Why these four:

  1. rm, or find with -delete / -exec rm, on anything under data/ -
     data/raw/2019-Nov.csv is a 9.0 GB Kaggle download each of the four students
     fetched by hand, and rebuilding the bronze and silver tiers takes 15-25
     minutes (SYSTEM_DESIGN section 11). Nothing under data/ is in git, so there
     is nothing to restore from.
  2. git add / git commit naming a path under data/ - data/ is gitignored on
     purpose: no data moves between machines, every person regenerates the same
     bytes locally with pmod(hash(user_id), 100) < 7. A .gitkeep is exempt: the
     directory skeleton is tracked (.gitignore negates data/*/.gitkeep), only
     what lands inside it is not.
  3. git push --force / -f - the repo is the only handover channel between four
     people who almost never meet, so rewriting pushed history is expensive.
  4. git commit while on main, or a git push that lands on main - main is
     protected on GitHub (pull request required, admins included), so a direct
     push is rejected anyway. Stopping it here gives the reason before a local
     commit on main has to be untangled. Work on a branch and open a PR.

Everything else exits silently. The hook fails OPEN: any unexpected error exits
0 and prints nothing, so a bug in this file can never stop the team working.

Matching is done on parsed tokens, never on substrings, so an ordinary command
that merely mentions data - python processing/batch_silver.py, ls data/bronze,
python ingestion/load_bronze.py --data-dir data/bronze - is never touched. The
tokenizer respects quotes, so echo "some text" is one harmless echo even when
the quoted text looks like a command. The body of a heredoc is text, not
commands, so it is skipped: writing a file whose content mentions a trap
command is never blocked.

What it does NOT see, because reading it would mean parsing the shell properly
and this file has to stay readable in ten minutes: a command hidden in a string
another program runs (bash -c "..."), a path arriving on a pipe (xargs), and
deletions by tools other than rm and find (shutil.rmtree in a python -c). Treat
it as a guard against the slip, not against someone who means it.
"""

import json
import os
import re
import shlex
import subprocess
import sys

PROJECT_DIR = os.environ.get("CLAUDE_PROJECT_DIR") or os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

# Tokens that end one command and start the next. Newlines are NOT in this list:
# shlex treats them as whitespace and never emits one as a token, so segments()
# splits the command line by line before tokenizing.
SEPARATORS = (";", "|", "||", "&", "&&")

# Prefixes that just wrap the real command, or open a shell construct in front of
# it - `for d in bronze silver; do rm -rf data/$d; done` puts `do` first.
WRAPPERS = ("sudo", "nohup", "time", "command", "do", "then", "else", "(", "{", "!")

# A heredoc opener: <<WORD, <<-WORD, <<'WORD' or <<"WORD" (not the <<< here-string).
HEREDOC = re.compile(r"(?<!<)<<(?!<)(-?)\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\2")

# The branch GitHub protects (branch protection rule on Dat-TG/shop-insight).
PROTECTED_BRANCH = "main"

# git push options that take a separate value, so the value is not mistaken for
# the remote or a refspec.
PUSH_OPTS_WITH_VALUE = ("--repo", "-o", "--push-option", "--receive-pack", "--exec")

# git's own options that consume the next token, so it is not the subcommand.
GIT_OPTS_WITH_VALUE = ("-C", "-c", "--git-dir", "--work-tree", "--namespace")

# add/commit options whose value is a message, never a path we should judge:
# git commit -m "data/bronze loaded" is fine.
COMMIT_OPTS_WITH_VALUE = ("-m", "--message", "-F", "--file", "-C", "--reuse-message")

DENY_RM = (
    "Blocked by .claude/hooks/guard_data.py: this command deletes files under data/. "
    "data/raw/2019-Nov.csv is a 9.0 GB Kaggle download each person fetched by hand, and "
    "bronze/silver take 15-25 minutes to rebuild (SYSTEM_DESIGN section 11). "
    "Nothing under data/ is recoverable from git - the whole tree is gitignored. "
    "If a tier really must be rebuilt, delete just that one tier by hand in your own "
    "terminal, then re-run the load order in SYSTEM_DESIGN section 11."
)

DENY_GIT_DATA = (
    "Blocked by .claude/hooks/guard_data.py: this command stages or commits a path under "
    "data/. CLAUDE.md: 'data/ is gitignored, so no data ever moves between machines' - each "
    "person regenerates the same bytes locally with pmod(hash(user_id), 100) < 7. "
    "Commit the script that produces the file, not the file. If the artefact is authored "
    "rather than derived (the holiday calendar is the one example), it belongs in seed/, "
    "which sits outside data/ and is tracked."
)

DENY_FORCE_PUSH = (
    "Blocked by .claude/hooks/guard_data.py: force push. Four people hand work over through "
    "this repo and almost never meet, so rewriting history the others have already pulled "
    "costs someone a rescue session. Pull and merge, or push a new branch and open a PR."
)

DENY_MAIN = (
    "Blocked by .claude/hooks/guard_data.py: this commits on, or pushes to, main. main is "
    "protected on GitHub - every change goes through a pull request, admins included - so a "
    "direct push is rejected. Create a branch first (git switch -c <short-name>), commit "
    "there, push it, and open a PR."
)


def current_branch(directory):
    """Name of the checked-out branch, or None if it cannot be read quickly."""
    try:
        result = subprocess.run(
            ["git", "-C", directory, "symbolic-ref", "--short", "-q", "HEAD"],
            capture_output=True, text=True, timeout=1)
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() or None


# Set when an earlier command on the same line changes branch, as in
# `git switch -c feat && git commit -m x`: that commit lands on feat, not main.
switched_to = None


def branch_for(directory):
    return switched_to or current_branch(directory)


def new_branch(rest):
    """Branch that `git switch/checkout <rest>` leaves checked out, if clear."""
    if "--" in rest:
        return None  # checking out files; the branch does not change
    for index, token in enumerate(rest):
        if token in ("-c", "-C", "-b", "-B", "--create", "--force-create"):
            return rest[index + 1] if index + 1 < len(rest) else None
    positional = [token for token in rest if not token.startswith("-")]
    return positional[0] if positional else None


def push_lands_on_main(rest, directory):
    """True when `git push <rest>` would update the protected branch."""
    positional = []
    skip_next = False
    for token in rest:
        if skip_next:
            skip_next = False
        elif token in PUSH_OPTS_WITH_VALUE:
            skip_next = True
        elif token in ("--all", "--mirror"):
            return True  # both include main
        elif not token.startswith("-"):
            positional.append(token)
    refspecs = positional[1:]  # positional[0] is the remote
    if not refspecs:
        # A bare `git push` or `git push origin` pushes the current branch.
        return branch_for(directory) == PROTECTED_BRANCH
    for refspec in refspecs:
        target = refspec.lstrip("+").split(":")[-1]
        if target == "HEAD":
            target = branch_for(directory) or ""
        if target.removeprefix("refs/heads/") == PROTECTED_BRANCH:
            return True
    return False


def tokenize(command):
    """Split the command line into tokens, respecting quotes.

    punctuation_chars=True makes ; | & their own tokens, so `ls data && rm -rf
    data/gold` is seen as two commands while `echo "rm -rf data/gold"` stays one
    harmless echo.
    """
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        lexer.commenters = ""
        return list(lexer)
    except ValueError:
        # Unbalanced quote: the command is probably broken anyway. Split bluntly
        # so a destructive one is still seen; the worst case is a cautious deny.
        for character in (";", "|", "&"):
            command = command.replace(character, " %s " % character)
        return command.split()


def segments(command):
    """Group tokens into one list per command.

    Split line by line first, then on ; | & inside each line. A newline ends a
    command in the shell, but shlex counts it as whitespace and drops it, so
    without this pass a two-line command collapses into one. Both halves of that
    are wrong: `rm -rf node_modules` then `ls data/bronze` would read the ls path
    as an argument of the rm and deny a safe command, while `ls -la` then
    `rm -rf data/gold` would look like one harmless ls and slip through.

    A line ending in a backslash is joined to the next one, the way the shell
    joins it. Heredoc bodies are skipped up to their terminator line: they are
    file content, and docs in this repo quote trap commands on purpose.
    """
    found = []
    pending = []  # (strip_tabs, terminator) for heredocs whose body comes next
    for line in command.replace("\\\n", " ").split("\n"):
        if pending:
            strip_tabs, terminator = pending[0]
            if (line.lstrip("\t") if strip_tabs else line) == terminator:
                pending.pop(0)
            continue
        pending = [(dash == "-", word) for dash, _, word in HEREDOC.findall(line)]
        current = []
        for token in tokenize(line):
            if token in SEPARATORS:
                found.append(current)
                current = []
            else:
                current.append(token)
        found.append(current)
    return found


def is_data_path(token):
    """True when the token names data/ itself or something inside it."""
    if token.startswith("-"):
        return False
    path = os.path.expanduser(token.strip())
    if os.path.isabs(path):
        try:
            path = os.path.relpath(path, PROJECT_DIR)
        except ValueError:
            return False
    parts = [part for part in path.split("/") if part not in ("", ".")]
    return bool(parts) and parts[0] == "data"


def check_git(args, directory):
    index = 0
    while index < len(args) and args[index].startswith("-"):
        if args[index] == "-C" and index + 1 < len(args):
            directory = os.path.join(directory, args[index + 1])
        index += 2 if args[index] in GIT_OPTS_WITH_VALUE else 1
    if index >= len(args):
        return None
    subcommand, rest = args[index], args[index + 1:]

    if subcommand in ("add", "commit"):
        skip_next = False
        for token in rest:
            if skip_next:
                skip_next = False
                continue
            if token in COMMIT_OPTS_WITH_VALUE:
                skip_next = True
                continue
            if token.startswith("-") or " " in token:
                continue  # a flag, or a message that happens to mention data/
            if os.path.basename(token) == ".gitkeep":
                # Skeleton, not data. .gitignore negates data/*/.gitkeep on
                # purpose: the empty directory tree is tracked so a fresh clone
                # has somewhere to write, only its contents are not.
                continue
            if is_data_path(token):
                return DENY_GIT_DATA

    if subcommand in ("switch", "checkout"):
        global switched_to
        switched_to = new_branch(rest) or switched_to
        return None

    if subcommand == "commit" and branch_for(directory) == PROTECTED_BRANCH:
        return DENY_MAIN

    if subcommand == "push":
        for token in rest:
            if token == "-f" or token.startswith("--force"):
                return DENY_FORCE_PUSH
        if push_lands_on_main(rest, directory):
            return DENY_MAIN

    return None


def check_segment(tokens, directory):
    while tokens and os.path.basename(tokens[0]) in WRAPPERS:
        tokens = tokens[1:]
    if not tokens:
        return None

    program = os.path.basename(tokens[0])
    if program == "rm":
        for token in tokens[1:]:
            if is_data_path(token):
                return DENY_RM
    if program == "git":
        return check_git(tokens[1:], directory)
    # find is the other everyday way to delete: "find data/raw -delete" or
    # "find data -exec rm {} +". Deny when it searches under data/ AND deletes.
    if program == "find":
        deletes = "-delete" in tokens or any(
            token in ("-exec", "-execdir", "-ok", "-okdir")
            and index + 1 < len(tokens)
            and os.path.basename(tokens[index + 1]) == "rm"
            for index, token in enumerate(tokens))
        if deletes and any(is_data_path(token) for token in tokens[1:]):
            return DENY_RM
    return None


def main():
    payload = json.loads(sys.stdin.read())
    if payload.get("tool_name") != "Bash":
        return
    command = payload.get("tool_input", {}).get("command", "")
    if not isinstance(command, str):
        return
    directory = payload.get("cwd")
    if not isinstance(directory, str) or not os.path.isdir(directory):
        directory = PROJECT_DIR
    for tokens in segments(command):
        reason = check_segment(tokens, directory)
        if reason:
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }}))
            return


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # fail open: never block the team because this hook has a bug
    sys.exit(0)
