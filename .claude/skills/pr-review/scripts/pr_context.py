#!/usr/bin/env python3
"""Put one pull request (or branch) on disk for review, and print what a reviewer needs first.

    python3 .claude/skills/pr-review/scripts/pr_context.py 10 --out <dir>
    python3 .claude/skills/pr-review/scripts/pr_context.py https://github.com/Dat-TG/shop-insight/pull/10
    python3 .claude/skills/pr-review/scripts/pr_context.py w39-khang-warehouse
    python3 .claude/skills/pr-review/scripts/pr_context.py            # current branch against origin/main
    python3 .claude/skills/pr-review/scripts/pr_context.py my-branch --base pr/9   # stacked on another PR

Why a script instead of three gh commands. Each of these was measured on this repo
on 26 Sep 2026:
  - `gh pr diff` refuses any PR over 20,000 diff lines (HTTP 406). PR #9 is 95,475.
  - `gh pr view --json files` stops at 100 files. PR #9 changes 227.
  - `gh pr checkout` switches YOUR working tree to the author's branch.
So the PR head is fetched as a ref (refs/remotes/pr/<N>, readable as `pr/<N>`) and
exported with `git archive` into <out>/tree. Your branch, working tree and data/
are never touched.

It writes into --out, which must be outside the repo:
  tree/                   the PR head, every tracked file, paths as in the repo
  diff.patch              merge-base..head, hand-written files only (no vendored or
                          generated files), so agents without Bash can read it
  diff-since-review.patch only when a review exists and commits landed after it
  thread.md               description, comments, reviews and inline comments, in full
  context.json            everything below, machine-readable

It does NOT post, approve, comment, check out, or run the PR's code. Every signal
it prints is a prompt to go and read the file, never a finding on its own.
Standard library only, so it runs under any python3 without the .venv.
"""

import argparse
import datetime
import io
import json
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
TODAY = datetime.date.today()
LIST_CAP = 12              # paths printed per bucket before "... and N more"
LARGE_FILE_BYTES = 500_000

# First match wins. The bucket names are the first column of the routing table in
# SKILL.md, so a new bucket here needs a row there.
BUCKETS = [
    ("vendored",   r"^(\.agents/|node_modules/|vendor/|third_party/)|/node_modules/"),
    ("generated",  r"(^|/)(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|poetry\.lock|uv\.lock)$"
                   r"|\.min\.(js|css)$|\.map$|\.pyc$|(^|/)(dist|build|__pycache__)/"),
    ("data",       r"^data/(?!.*\.gitkeep$)|\.(parquet|zip|gz|duckdb|db)$"),
    ("styles",     r"\.(css|scss|sass|less)$"),
    ("assets",     r"\.(svg|png|jpe?g|gif|ico|webp|woff2?|ttf|eot)$"),
    ("claude",     r"^\.claude/"),
    ("tests",      r"^(tests|checks)/|(^|/)test_[^/]*\.py$|_test\.py$"),
    ("spark",      r"^(processing|ingestion)/.*\.py$"),
    ("sql",        r"\.sql$"),
    ("cql",        r"\.cql$"),
    ("api",        r"^serving/"),
    ("fixtures",   r"^web/fixtures/"),
    ("web",        r"^web/"),
    ("docs",       r"\.md$|^docs/"),
    ("seed",       r"^seed/"),
    ("config",     r"^(requirements\.txt|docker-compose\.ya?ml|\.env\.example|\.gitignore|conf/)"),
]
NOT_HAND_WRITTEN = {"vendored", "generated"}
# Never read line by line. The signals still scan every one of their added lines for
# secrets, and a vendored tree still gets a one-line decision (SKILL.md section 3).
SKIPPED = NOT_HAND_WRITTEN | {"styles", "assets"}

# Conservative on purpose: each pattern is a credential format, not a word like "password",
# so a hit is worth stopping for. docker-compose's local defaults never match.
SECRETS = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----|\bAKIA[0-9A-Z]{16}\b|\bgh[pousr]_[A-Za-z0-9]{36,}"
    r"|\bxox[abprs]-[A-Za-z0-9-]{10,}|\bsk-ant-[A-Za-z0-9_-]{20,}|\bsk-[A-Za-z0-9]{32,}\b|\bAIza[0-9A-Za-z_-]{35}\b")

BANNED_PACKAGES = re.compile(
    r"^(apache-airflow|airflow|dbt(-core)?|apache-flink|pyflink|redis|pyiceberg|delta-spark|deltalake)\b", re.I)
VIETNAMESE = re.compile(r"[ăâđêôơưàáạảãầấậẩẫằắặẳẵèéẹẻẽềếệểễìíịỉĩòóọỏõồốộổỗờớợởỡùúụủũừứựửữỳýỵỷỹ]", re.I)
PYSPARK_IMPORT = re.compile(r"^\s*(from|import)\s+pyspark\b", re.M)


def is_vietnamese(text):
    """True when enough words carry Vietnamese diacritics. One accented name ("Tín") is not a language."""
    words = re.findall(r"\w+", text)
    marked = sum(1 for w in words if VIETNAMESE.search(w))
    return marked >= max(5, len(words) // 20)


def run(*args, check=True):
    """Run a command in the repo and return stdout as text; None if it failed and check is False."""
    result = subprocess.run(args, cwd=REPO, capture_output=True, text=True)
    if result.returncode != 0:
        if check:
            sys.exit("pr_context: `%s` failed: %s" % (" ".join(args), result.stderr.strip()))
        return None
    return result.stdout


def gh_json(*args):
    """Parsed JSON from a read-only gh call, or None when gh is missing, logged out or offline."""
    if shutil.which("gh") is None:
        return None
    out = run("gh", *args, check=False)
    try:
        return json.loads(out) if out else None
    except json.JSONDecodeError:
        return None


def bucket_of(path):
    for name, pattern in BUCKETS:
        if re.search(pattern, path):
            return name
    return "other"


def resolve(target, base_override=None):
    """Turn the argument into (pr_number or None, head ref, base ref, gh metadata or None).

    base_override is for a branch stacked on another unmerged branch: without it, the
    diff against main would include all of the other branch's work too."""
    number = None
    if target:
        match = re.fullmatch(r"#?(\d+)|.*/pull/(\d+)(/.*)?", target.strip())
        if match:
            number = int(match.group(1) or match.group(2))
    fields = ("number,title,body,author,state,isDraft,url,baseRefName,headRefName,headRefOid,"
              "createdAt,updatedAt,reviewDecision,reviews,comments,commits")
    if number is None:
        branch = target or run("git", "rev-parse", "--abbrev-ref", "HEAD").strip()
        if branch in ("main", "origin/main", "HEAD"):
            open_prs = gh_json("pr", "list", "--state", "open", "--json", "number,title,author,headRefName")
            listing = "\n".join("  #%d %s (%s, %s)" % (p["number"], p["title"], p["author"]["login"], p["headRefName"])
                                for p in open_prs or [])
            sys.exit("pr_context: name a PR number, PR URL or branch - you are on main.\nOpen PRs:\n"
                     + (listing or "  (none, or gh is unavailable)"))
        meta = gh_json("pr", "view", branch.removeprefix("origin/"), "--json", fields)
        if meta is None:  # a branch with no PR yet: review it against main, description from its commits
            head = branch if run("git", "rev-parse", "--verify", "--quiet", branch, check=False) else "origin/" + branch
            run("git", "fetch", "--quiet", "origin", "main", check=False)
            return None, head, base_override or "origin/main", None
        number = meta["number"]
    else:
        meta = gh_json("pr", "view", str(number), "--json", fields)
    base = (meta or {}).get("baseRefName") or "main"
    fetched = run("git", "fetch", "--quiet", "origin",
                  "+pull/%d/head:refs/remotes/pr/%d" % (number, number), base, check=False)
    if fetched is None and not run("git", "rev-parse", "--verify", "--quiet", "pr/%d" % number, check=False):
        sys.exit("pr_context: could not fetch pull/%d/head from origin, and no local pr/%d ref exists." % (number, number))
    return number, "pr/%d" % number, base_override or "origin/" + base, meta


def changed_files(merge_base, head, tree):
    status = {}
    for line in run("git", "diff", "--name-status", "-M", merge_base, head).splitlines():
        parts = line.split("\t")
        status[parts[-1]] = parts[0][0]  # A, M, D, R (rename keeps only the new path)
    files = []
    for line in run("git", "diff", "--numstat", "-M", merge_base, head).splitlines():
        added, deleted, path = line.split("\t", 2)
        if " => " in path:  # rename shown as dir/{old => new}.py
            path = re.sub(r"\{[^}]* => ([^}]*)\}", r"\1", path).replace("//", "/")
            path = path.split(" => ")[-1]
        bucket = bucket_of(path)
        source = tree / path
        if (bucket in ("tests", "api", "other") and path.endswith(".py") and source.exists()
                and PYSPARK_IMPORT.search(source.read_text(encoding="utf-8", errors="replace"))):
            bucket = "spark"  # e.g. checks/scd2_integrity.py: runs Spark, so the Spark trap list applies
        files.append({
            "path": path,
            "status": status.get(path, "M"),
            "added": int(added) if added != "-" else 0,
            "deleted": int(deleted) if deleted != "-" else 0,
            "binary": added == "-",
            "bucket": bucket,
        })
    return files


def review_history(meta, head_sha, reviewer):
    """The last review overall, the invoking user's own last review, and what landed since each."""
    history = {"reviewer": reviewer, "latest": None, "yours": None}
    for review in (meta or {}).get("reviews") or []:
        sha = (review.get("commit") or {}).get("oid")
        if not sha:
            continue
        entry = {"author": review["author"]["login"], "state": review["state"],
                 "commit": sha, "at": review.get("submittedAt")}
        reachable = run("git", "merge-base", "--is-ancestor", sha, head_sha, check=False) is not None
        entry["reachable"] = reachable
        entry["commits_since"] = int(run("git", "rev-list", "--count", "%s..%s" % (sha, head_sha)).strip()) if reachable else None
        history["latest"] = entry  # gh lists reviews oldest first
        if entry["author"] == reviewer:
            history["yours"] = entry
    return history


def export_tree(head, out):
    """Every tracked file at the PR head, extracted into out/tree. No .git, no data/."""
    tree = out / "tree"
    if tree.exists():
        shutil.rmtree(tree)
    tree.mkdir(parents=True)
    archive = subprocess.run(["git", "archive", head], cwd=REPO, capture_output=True, check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(tree, filter="data")
    return tree


def load_trap_check():
    """The same 14 regex checks the PostToolUse hook runs, imported rather than copied."""
    sys.path.insert(0, str(REPO / ".claude" / "hooks"))
    try:
        from check_python import find_warnings
        return find_warnings
    except Exception:
        return None


def signals(files, tree, merge_base, head):
    """Cheap mechanical prompts for the reviewer. Each one still has to be confirmed by reading."""
    found = []
    find_warnings = load_trap_check()
    for f in files:
        path, bucket = f["path"], f["bucket"]
        if f["status"] == "D":
            continue
        if bucket == "data":
            found.append("%s: file under data/ or a data file in git - data/ is gitignored on purpose; nothing but .gitkeep is tracked" % path)
        size = int(run("git", "cat-file", "-s", "%s:%s" % (head, path)).strip())
        if size > LARGE_FILE_BYTES and bucket not in NOT_HAND_WRITTEN:
            found.append("%s: %d KB added - generated output or data rather than source?" % (path, size // 1000))
        if path.endswith(".py") and bucket not in NOT_HAND_WRITTEN:
            source = (tree / path).read_text(encoding="utf-8", errors="replace")
            try:
                compile(source, path, "exec")
            except SyntaxError as error:
                found.append("%s:%s: SyntaxError: %s - the file cannot run" % (path, error.lineno, error.msg))
                continue
            if bucket == "spark" and find_warnings:  # the hook's regexes were written for PySpark only
                for warning in find_warnings(path, source):
                    found.append("%s: trap check: %s" % (path, warning))
            if VIETNAMESE.search("".join(l for l in source.splitlines(True) if "#" in l or '"""' in l)):
                found.append("%s: Vietnamese text in a comment or docstring - CLAUDE.md wants English in code" % path)
    path, line_no = None, 0
    for line in run("git", "diff", "-U0", merge_base, head).splitlines():
        if line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else None
        elif line.startswith("@@"):
            line_no = int(re.search(r"\+(\d+)", line).group(1))
        elif line.startswith("+") and path:
            if SECRETS.search(line):
                found.append("%s:%d: looks like a credential - `repo`, blocking; it must be rotated, not just deleted" % (path, line_no))
            line_no += 1
    for f in files:
        if re.search(r"(^|/)\.env(\.[^/]*)?$", f["path"]) and not f["path"].endswith(".env.example") and f["status"] != "D":
            found.append("%s: an env file is committed - only .env.example belongs in git" % f["path"])
    existing = set(run("git", "ls-tree", "--name-only", merge_base).split())
    new_dirs = sorted({f["path"].split("/")[0] + "/" for f in files
                       if "/" in f["path"] and f["path"].split("/")[0] not in existing})
    if new_dirs:
        found.append("new top-level directories: %s - compare with SYSTEM_DESIGN section 10's layout" % ", ".join(new_dirs))
    requirements = next((f for f in files if f["path"] == "requirements.txt"), None)
    if requirements:
        for line in run("git", "diff", merge_base, head, "--", "requirements.txt").splitlines():
            if not line.startswith("+") or line.startswith("+++"):
                continue
            spec = line[1:].split("#")[0].strip()
            if not spec or spec.startswith("-"):
                continue
            if "==" not in spec:
                found.append("requirements.txt: `%s` is not pinned with == (CLAUDE.md: pinned exactly, not minimums)" % spec)
            if BANNED_PACKAGES.match(spec):
                found.append("requirements.txt: `%s` is a technology CLAUDE.md hard rule 1 bans" % spec)
            if re.match(r"pyspark\s*==\s*3\.", spec, re.I):
                found.append("requirements.txt: `%s` - PySpark 3.5.x segfaults on Python 3.14 (SYSTEM_DESIGN 11.1)" % spec)
    package = next((f for f in files if f["path"] == "web/package.json"), None)
    if package:
        def deps(ref):
            text = run("git", "show", "%s:web/package.json" % ref, check=False)
            data = json.loads(text) if text else {}
            return {**data.get("dependencies", {}), **data.get("devDependencies", {})}
        before, after = deps(merge_base), deps(head)
        added = ["%s@%s" % (name, after[name]) for name in sorted(after) if name not in before]
        if added:
            found.append("web/package.json: %d new npm packages - %s" % (len(added), ", ".join(added)))
    return found


def fixture_fields(files, tree):
    """Per fixture file: the keys of its data rows and of any meta object. Values are not the point."""
    def walk(node, rows, meta):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "meta" and isinstance(value, dict):
                    meta.update(k for k in value if not k.startswith("_"))
                walk(value, rows, meta)
        elif isinstance(node, list):
            for item in node:
                if isinstance(item, dict):
                    rows.update(k for k in item if not k.startswith("_"))
                walk(item, rows, meta)
    result = {}
    for f in files:
        if f["bucket"] != "fixtures" or not f["path"].endswith(".json") or f["status"] == "D":
            continue
        rows, meta = set(), set()
        try:
            walk(json.loads((tree / f["path"]).read_text(encoding="utf-8")), rows, meta)
        except (OSError, json.JSONDecodeError) as error:
            result[f["path"]] = "unreadable: %s" % error
            continue
        result[f["path"]] = "rows: %s | meta: %s" % (", ".join(sorted(rows)) or "-", ", ".join(sorted(meta)) or "-")
    return result


def write_thread(meta, number, out):
    """The whole conversation, so nobody re-raises a point that was already answered."""
    lines = ["# #%d %s" % (number, meta["title"]), "",
             "author %s, opened %s, %s" % (meta["author"]["login"], meta["createdAt"][:10], meta["state"].lower()),
             "", "## Description", "", (meta.get("body") or "(empty)").replace("\r\n", "\n"), ""]
    for c in meta.get("comments") or []:
        lines += ["## Comment by %s, %s" % (c["author"]["login"], c["createdAt"][:16]), "",
                  c["body"].replace("\r\n", "\n"), ""]
    for r in meta.get("reviews") or []:
        lines += ["## Review by %s, %s, %s at %s" % (r["author"]["login"], r["state"], (r.get("submittedAt") or "")[:16],
                                                  ((r.get("commit") or {}).get("oid") or "")[:7]), "",
                  (r.get("body") or "(no body)").replace("\r\n", "\n"), ""]
    inline = gh_json("api", "repos/{owner}/{repo}/pulls/%d/comments" % number, "--paginate") or []
    for c in inline:
        lines += ["## Inline by %s on %s:%s, %s" % (c["user"]["login"], c["path"], c.get("line") or c.get("original_line"),
                                                c["created_at"][:16]), "", c["body"].replace("\r\n", "\n"), ""]
    (out / "thread.md").write_text("\n".join(lines), encoding="utf-8")
    return len(inline)


def days_since(iso):
    return (TODAY - datetime.date.fromisoformat(iso[:10])).days


def ago(iso):
    days = days_since(iso)
    return "today" if days == 0 else "1 day ago" if days == 1 else "%d days ago" % days


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("target", nargs="?", help="PR number, PR URL or branch; default: the current branch")
    parser.add_argument("--out", help="output directory OUTSIDE the repo; default: a new temp directory")
    parser.add_argument("--base", help="diff against this ref instead of the PR base or origin/main (stacked branches)")
    args = parser.parse_args()

    out = Path(args.out).resolve() if args.out else Path(tempfile.mkdtemp(prefix="pr-review-"))
    if out == REPO or REPO in out.parents:
        sys.exit("pr_context: --out must be outside the repo (use your session scratchpad or /tmp): %s" % out)
    out.mkdir(parents=True, exist_ok=True)

    stacked = re.fullmatch(r"pr/(\d+)", args.base or "")
    if stacked:  # a base that is another PR: make sure its head is here
        run("git", "fetch", "--quiet", "origin", "+pull/%s/head:refs/remotes/pr/%s" % (stacked[1], stacked[1]), check=False)
    number, head, base, meta = resolve(args.target, args.base)
    head_sha = run("git", "rev-parse", head).strip()
    merge_base = run("git", "merge-base", base, head).strip()
    if meta and meta.get("headRefOid") and meta["headRefOid"] != head_sha:
        print("WARNING: fetched head %s differs from GitHub's %s - re-run to refresh." % (head_sha[:7], meta["headRefOid"][:7]))

    tree = export_tree(head, out)
    files = changed_files(merge_base, head, tree)
    hand = [f for f in files if f["bucket"] not in NOT_HAND_WRITTEN]
    hand_paths = [f["path"] for f in files if f["bucket"] not in SKIPPED]
    patch = run("git", "diff", "-M", merge_base, head, "--", *hand_paths) if hand_paths else ""
    (out / "diff.patch").write_text(patch, encoding="utf-8")

    reviewer = (gh_json("api", "user") or {}).get("login")
    history = review_history(meta, head_sha, reviewer) if meta else {"reviewer": reviewer, "latest": None, "yours": None}
    since = history["yours"] or history["latest"]
    if since and since["reachable"] and since["commits_since"]:
        delta = run("git", "diff", "-M", since["commit"], head, "--", *hand_paths) if hand_paths else ""
        (out / "diff-since-review.patch").write_text(delta, encoding="utf-8")

    commits = run("git", "log", "--reverse", "--date=short", "--format=%h %ad %an: %s", "%s..%s" % (merge_base, head)).splitlines()
    first_commit_day = run("git", "log", "--reverse", "--format=%ad", "--date=short", "%s..%s" % (merge_base, head)).split()
    inline_count = write_thread(meta, number, out) if meta else 0
    found = signals(files, tree, merge_base, head)

    # ---- the report ----
    text = (meta or {}).get("title", "") + "\n" + ((meta or {}).get("body") or "")
    if not meta:
        text += "\n".join(commits)
    language = "vi" if is_vietnamese(text) else "en"
    if meta:
        print("# PR #%d - %s" % (number, meta["title"]))
        print("%s | author %s | %s%s | base %s | head %s @ %s" % (
            meta["url"], meta["author"]["login"], meta["state"].lower(), ", DRAFT" if meta.get("isDraft") else "",
            base, meta["headRefName"], head_sha[:7]))
        print("opened %s (%s), %d commits, %d comments, %d reviews, %d inline comments" % (
            meta["createdAt"][:10], ago(meta["createdAt"]), len(commits), len(meta.get("comments") or []),
            len(meta.get("reviews") or []), inline_count))
    else:
        print("# Branch %s (no PR found - description comes from the commit messages)" % head)
        print("base %s | head %s | %d commits" % (base, head_sha[:7], len(commits)))
    if first_commit_day and days_since(first_commit_day[0]) > 7:
        print("branch age: first commit %s, %d days ago - PLAN.md: no branch lives longer than seven days"
              % (first_commit_day[0], days_since(first_commit_day[0])))
    print("language of the description: %s" % {"vi": "Vietnamese", "en": "English"}[language])
    print("you are: %s" % (reviewer or "unknown (gh unavailable)"))
    for label, entry in (("latest review", history["latest"]), ("your last review", history["yours"])):
        if entry:
            after = ("%d commits since: %s..%s" % (entry["commits_since"], entry["commit"][:7], head_sha[:7])
                     if entry["reachable"] else "its commit is no longer on the branch (force-pushed) - review everything")
            print("%s: %s %s at %s on %s - %s" % (label, entry["author"], entry["state"], entry["commit"][:7],
                                                (entry["at"] or "")[:10], after))
    if meta and not history["latest"]:
        print("no reviews yet")

    print("\n## Commits")
    for line in commits[-15:]:
        print("  " + line)
    if len(commits) > 15:
        print("  ... %d earlier" % (len(commits) - 15))

    print("\n## Files: %d changed, +%d -%d; hand-written: %d files, +%d -%d" % (
        len(files), sum(f["added"] for f in files), sum(f["deleted"] for f in files),
        len(hand), sum(f["added"] for f in hand), sum(f["deleted"] for f in hand)))
    order = [name for name, _ in BUCKETS] + ["other"]
    for name in order:
        group = [f for f in files if f["bucket"] == name]
        if not group:
            continue
        print("\n### %s: %d files, +%d -%d" % (name, len(group), sum(f["added"] for f in group), sum(f["deleted"] for f in group)))
        if name in NOT_HAND_WRITTEN:
            dirs = {}
            for f in group:
                key = "/".join(f["path"].split("/")[:3]) if f["path"].count("/") >= 2 else f["path"]
                dirs[key] = dirs.get(key, 0) + 1
            for key, count in sorted(dirs.items(), key=lambda kv: -kv[1])[:LIST_CAP]:
                print("  %4d files  %s" % (count, key))
            continue
        for f in sorted(group, key=lambda f: -(f["added"] + f["deleted"]))[:LIST_CAP]:
            print("  %s %-60s +%d -%d" % (f["status"], f["path"], f["added"], f["deleted"]))
        if len(group) > LIST_CAP:
            print("  ... and %d more" % (len(group) - LIST_CAP))

    read = [f for f in files if f["bucket"] not in SKIPPED | {"data", "fixtures", "tests"}]
    skipped = [f for f in files if f["bucket"] in SKIPPED]
    print("\n## Reading plan")
    print("  read in full:  %d files, +%d -%d" % (len(read), sum(f["added"] for f in read), sum(f["deleted"] for f in read)))
    fixtures = fixture_fields(files, tree)
    tests = [f["path"] for f in files if f["bucket"] == "tests"]
    if fixtures or tests:
        print("  check, don't read: %s" % "; ".join(filter(None, [
            "%d fixtures - compare the fields below with the contract" % len(fixtures) if fixtures else "",
            "%d tests - run them" % len(tests) if tests else ""])))
    for path, fields in fixtures.items():
        print("    %s  %s" % (path.removeprefix("web/fixtures/"), fields))
    if skipped:
        counts = {}
        for f in skipped:
            counts[f["bucket"]] = counts.get(f["bucket"], 0) + 1
        print("  skipped:       %d files, +%d (%s) - never read; only the signals below cover them" % (
            len(skipped), sum(f["added"] for f in skipped), ", ".join("%s %d" % kv for kv in counts.items())))

    print("\n## Signals (mechanical - read the file before believing any of them)")
    for line in found or ["none"]:
        print("  - " + line)

    print("\n## On disk")
    print("  PR head tree:   %s   (read files here; never from your working tree)" % tree)
    print("  full diff:      %s   or: git diff %s %s" % (out / "diff.patch", merge_base[:10], head))
    if (out / "diff-since-review.patch").exists():
        print("  since review:   %s   or: git diff %s %s" % (out / "diff-since-review.patch", since["commit"][:10], head))
    if meta:
        print("  thread:         %s" % (out / "thread.md"))
        print("  permalink base: https://github.com/%s/blob/%s/<path>#L<a>-L<b>" % (
            meta["url"].split("github.com/")[1].split("/pull/")[0], head_sha))

    (out / "context.json").write_text(json.dumps({
        "number": number, "head": head, "head_sha": head_sha, "base": base, "merge_base": merge_base,
        "language": language, "reviewer": reviewer, "history": history, "commits": commits,
        "files": files, "signals": found, "tree": str(tree), "meta": meta,
    }, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
