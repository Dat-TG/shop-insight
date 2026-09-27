---
name: pr-review
description: Review a ShopInsight pull request, or a branch before its PR, against the project's own rules — CLAUDE.md hard rules, SYSTEM_DESIGN DDL, keys and gold columns, the br-slice API and screen contract, PLAN.md ownership — and draft a short, verified review for the human reviewer to post.
when_to_use: Reviewing, re-reviewing or checking any PR or branch here — "review PR 10", "look at Khang's PR", "Tin pushed again", "is PR 9 ready to merge", the Wednesday teammate review. Use instead of the generic /code-review in this repo. Not for writing or fixing code, or answering comments on your own PR.
argument-hint: "[PR number | PR URL | branch]"
allowed-tools: Bash(python3 .claude/skills/pr-review/scripts/pr_context.py *) Bash(gh pr view *) Bash(gh pr list *)
---

# Reviewing a ShopInsight pull request

`main` is protected, so every change reaches it through a PR. In a team that meets twice
all semester, the PR review is the only quality gate. PLAN.md prices it at part of a
15-minute Wednesday slot: review one teammate's PR, leave at least one comment. So the
product is **a short, verified draft**, and the review itself should take minutes, not
a quarter of an hour. Claude drafts; the reviewer checks and posts; the author fixes.
Never edit the author's files.

**Keep it fast.** Everything happens in this conversation: no subagents (each one
re-reads the design docs, and four of them tripled a review's cost in testing), no
Spark jobs, no package installs, no builds. When a check would take minutes, do not
run it. Put it under "Could not check" and ask the author for the output. Run it only
if the reviewer asks ("chạy thử", "run it").

## 0. The standard: what blocks a merge

Approve once the PR moves the project forward and breaks nothing that counts, even if it
is not how you would have written it. CLAUDE.md rule 7 decides what counts: 8 working BRs
> clean code > performance. Only four kinds of finding block, each named by its tag:

| Tag | Means | Example |
|---|---|---|
| `breaks-the-demo` | crashes, will not start, wrong rows on a screen, a screen or endpoint that cannot be shown | `writeStream` with no checkpoint; a Cassandra query missing a partition-key column |
| `wrong-numbers` | it runs, but a number it produces or states is wrong | partitions on the wrong month; a row count that measures differently |
| `hard-rule` | breaks a CLAUDE.md hard rule or a project invariant | new technology, second silver writer, random sampling, unpinned dependency |
| `repo` | damage that cannot be undone after merge | files under `data/`, vendored third-party trees, secrets. Force-push is refused, so merged history is permanent |

Everything else is non-blocking: `style`, `nit`, and questions. A design change the
author made on purpose goes to the team (section 3, drift).

## 1. Put the PR on disk

```bash
python3 .claude/skills/pr-review/scripts/pr_context.py <PR number | PR URL | branch> --out <scratchpad>/pr-<N>
```

It runs in seconds. It fetches the PR head as `pr/<N>` and exports it to `<out>/tree`,
never touching your branch, working tree or `data/`. It prints:

- the metadata, the description's language, and who you are on GitHub;
- the latest review and the commits since it, and the branch age;
- the changed files sorted into buckets, with a **reading plan**;
- mechanical **signals**: syntax errors, the hook's Spark trap regexes, unpinned or
  banned requirements, new npm packages, new top-level directories, files under
  `data/`, and credentials in any added line.

A signal is a reason to read a file, never a finding by itself. It replaces
`gh pr diff`, which refuses PRs over 20,000 lines, and `gh pr checkout`, which moves
your tree.

Read files **only** from `<out>/tree`: your working tree is not the PR. With no
argument it reviews the current branch. On `main` it lists the open PRs. A branch
stacked on another PR takes `--base pr/<M>`.

## 2. Read the thread, then decide what to read

Open `<out>/thread.md`.

- **Claims.** Each claim in the description ("executed cleanly", a row count) needs
  evidence: the diff, `docs/evidence/`, or pasted output. If it has none, ask for it.
- **Already said.** Never re-raise a point someone made. Check whether it was addressed.
- **Still open.** Questions the author put to the team are part of the thread. Answer
  the ones the reviewer can answer, and list the rest under *Needs a team decision*.
- **Re-review.** If commits landed after the last review, the script wrote
  `<out>/diff-since-review.patch`. Review that delta and its callers, not the whole PR.
  Add no new nits. List each earlier point as addressed or not addressed.
- **Your own code.** If you wrote it in this session, say so and ask for `/pr-review`
  in a new session: models go easy on code they just wrote.

**Reading plan.** Read in full: hand-written code, DDL, config, and contract docs.
Check, don't read:

- fixtures: compare the field names the script prints with SYSTEM_DESIGN 6 and 7;
- placeholder stubs: only the route and the owner;
- a mirror file such as `web/src/types/api.ts`: its names against the original.

Skip: generated files, lockfiles, stylesheets and images. A vendored tree (`.agents/`,
`node_modules/`) is never read but always decided in one line. It almost never belongs,
and that is often the most important finding (`repo`). Skip by file type, never because
the PR is long. List what you skipped under "What I checked".

For each bucket the PR touches, open its section in
[layer-checks.md](references/layer-checks.md). For Spark files, use the trap list in
`.claude/agents/spark-reviewer.md` as your checklist, applied here and not as an agent.

## 3. PR-level checks

1. **Scope.** Does the diff do what the description says, and nothing unrelated?
   PLAN.md wants small PRs merged within the week, so a bundled PR gets a non-blocking
   "split next time".
2. **Ownership.** Each BR belongs to its owner (br-slice section 0). Work on someone
   else's BR is a question to that owner.
3. **Schedule.** Check PLAN.md's week table before calling anything premature. Stubs
   and fixtures for all eight BRs are the scheduled API contract, not horizontal work.
4. **Drift.** Name every place the PR contradicts CLAUDE.md, SYSTEM_DESIGN.md, PLAN.md
   or a `.claude/` skill, with file and section.
   - If the code is wrong, it is a finding.
   - If the change is deliberate, it is a team decision: the doc changes in the same
     PR, or the code goes back.
   - A PR description that says something the code does not do is drift too.
   - So is a number a doc still states: SYSTEM_DESIGN's counts came from an earlier
     sample, so a new measurement means the doc needs updating.
5. **Numbers.** Check a claimed number only when one cheap query settles it (DuckDB
   over the Parquet tiers, as in `.claude/agents/data-fact-checker.md`). Print the
   command and MATCH / MISMATCH. A number about an output the PR creates is not
   measurable here without running its job, so ask the author for the command and the
   output. Never estimate.
6. **Run evidence.** Every new script shows its OK line and row count in the PR.
   AI-drafted Spark and SQL are not committed until they have been run (AI_USAGE).
7. **Teammate's machine.** Something in the repo creates everything the PR needs:
   tables, keyspace, services (`docker-compose.yml`), packages, and settings
   (`.env.example`, with the credentials docker-compose really sets). If it works only
   on the author's laptop, it is `breaks-the-demo`.

## 4. Verify, then cut

A wrong comment costs the author an evening and the reviewer's credibility, and review
models lean towards seeing bugs. Restate each finding as one claim about behaviour,
then check it:

- **Point at it.** Quote the line from the tree. An omission names the function where
  the call belongs. No line means a question or nothing.
- **Handled elsewhere?** Check the caller, the helper, and the description.
- **Does the rule say that?** Open the cited doc section; do not quote from memory.

**Never report**, even when true:

- problems in lines or files the PR did not touch (at most two, in the notes);
- a compile error or missing import you only suspect. One that is really there is
  `breaks-the-demo`;
- security hardening for a local demo with no login. A committed secret is still `repo`;
- new technologies, abstractions, or performance tuning before the W41 benchmarks.
  Hard rules 1, 3 and 4 bind reviewers too;
- type hints, docstrings, logging, unit tests, or try/except the project does not ask
  for;
- UI polish (W45), naming taste, or anything already raised in the thread.

## 5. Draft

Write in **the description's language** (the script prints it), in the reviewer's first
person ("mình" in Vietnamese). Keep code, paths and tags as they are. Name the problem
and its consequence, never the person: one item per problem, one sentence of
consequence, one of fix. If the author could not tell what to change, cut the item.

```markdown
**Verdict: Request changes** — <what the PR achieves, and what must change before merge>

### Earlier points (re-review only)
- <point: addressed (commit) / not addressed>

### Must fix before merge
1. **`path:line`** · `tag` — <what is wrong → which screen, number or gate it breaks>. <The fix>.
   <PRs only: https://github.com/<owner>/<repo>/blob/<full head sha>/<path>#L<a>-L<b>, printed by the script>

### Needs a team decision
- <the deviation, the doc and section, who decides>

### Questions
- <what the code cannot tell you, addressed to whoever can answer>

### Optional
- nit: <at most three>

### What I checked
- <what was read, the commands and their results, what was skipped and why>
```

Vietnamese headings: **Kết luận: Cần sửa / Duyệt / Góp ý**, *Các điểm trước*, *Phải sửa
trước khi merge*, *Cần nhóm quyết*, *Câu hỏi*, *Không bắt buộc*, *Mình đã kiểm*. Omit
empty sections.

**Verdict:**
- *Request changes* if anything blocks.
- *Comment* if the rest waits only on the team.
- *Approve* otherwise.

The reviewer picks the real verdict when posting. The team's rule is at least one
comment, but never invent a problem to meet it. A verified confirmation counts, for
example "the null-safe SCD2 compare is right". That is also the only praise worth
writing.

Save the draft to `<out>/review.md`, print it, then add a short block that is **not**
part of the review:

```
Not for posting:
- Suggested verdict and why
- Could not check: <what, and what output to ask the author for>
- Checkpoint line: Reviewed #<N> (<author>): <x> must-fix, <y> team decisions
```

## 6. Posting: only when asked

Post only when the reviewer asks in this conversation. First show the exact text and
command, and wait for a yes:

```bash
gh pr review <N> --comment --body-file <out>/review.md   # or --request-changes / --approve, the reviewer's choice
```

Never approve, request changes or merge on your own, and never push to the author's
branch.
