# AI usage — Group 15

The course rewards work the team can explain and defend. This file records where
AI assistance was used, so that anyone reading the repo or the report can tell
which parts were generated, which were verified, and how.

The rule the team follows: **AI may draft and may measure; a human decides.**
Nothing in this file was accepted because a model said it. Every load-bearing
number below was produced by running a command against the real dataset or the
real toolchain, and the command is named so it can be re-run.

## Session 1 — 14 September 2026 (W38)

**Tool:** Claude Code (Opus 5).
**Scope:** repository survey, and rewriting `SYSTEM_DESIGN.md` + `PLAN.md` for the
warehouse-layer design change. No application code was written in this session.

### What the AI produced

| Artefact | Status |
|---|---|
| `SYSTEM_DESIGN.md` — new section 5 (dimensional model), revised sections 1, 3, 4, 6, 8, 10, 11, 12 | AI-drafted, human review pending |
| `PLAN.md` — revised budget, week table, gate analysis, technical-traps list | AI-drafted, human review pending |
| `CLAUDE.md` — two corrections | AI-drafted, human-approved in advance |
| Two revision documents in the team Drive folder | AI-drafted, human review pending |

### How it was checked

The design work ran as a 26-agent review: four independent audits of the existing
documents, five parallel model designs (one per fact and dimension group), three
adversarial verifiers per design instructed to refute rather than approve, and two
independent schedule re-plans built from opposite priorities (protect the gates
vs protect the hour band). The two schedulers converged on the same conclusion
from different directions, which is why the slack figure is stated with
confidence.

The agents did not reason about the dataset in the abstract — they ran commands
against `data/raw/2019-Nov.csv` (9.0 GB, 67,501,979 rows). Findings that came out
of actual measurement rather than inference:

| Claim | How it was measured |
|---|---|
| `category_code` is empty in 32.4% of rows (21,898,171 / 67,501,979) | full scan of the raw CSV |
| Only 12,659 of 127,693 sampled products are ever purchased | scan of purchase rows in the 7% user bucket |
| The raw file holds 3,696,117 users; the 7% sample holds 258,088 | distinct-count on `user_id` |
| SCD2 range join produces 305,663,175 intermediate rows, 25% of it in product `1005115` | per-product event × version arithmetic on measured cardinalities |
| PySpark 3.5.9 segfaults on Python 3.14; 4.1.3 does not | both sdists downloaded and imported against `/usr/bin/python3`; cloudpickle round-trip tested |

The PySpark finding was re-verified by hand against the PyPI metadata before it
was written into the documents, because the whole W38 install step depends on it.

### What the AI got wrong, and was corrected on

- The first `fact_session_funnel` draft carried 8 foreign keys and 10 check
  constraints. That fails CLAUDE.md's "four students must understand any file in
  ten minutes" rule, and it was cut to the columns the two BRs actually read.
- The first `fact_inventory_daily` draft used the full 127,693-product universe,
  producing 19.15M rows — four times the event fact and past the 5-million-row
  cap. The SKU universe was narrowed to products with at least one purchase.
- A verifier caught that the proposed `dim_user` change-detection predicate was
  copy-pasted from `dim_product` and was not null-safe, which would have produced
  four identical versions for 88% of users.

### Judgement that stayed with the team

Four decisions were put to a human and answered by a human, not inferred: where
the design documents live, where the holiday calendar file lives, whether the
flat Postgres benchmark table survives alongside the star, and whether
`CLAUDE.md` could be edited. The schedule choice — protect the 2–4 h band and let
the gates flex, rather than the reverse — was also a human call between two
fully-worked alternatives.

## Standing conventions

- AI-generated SQL and Spark code is not committed until it has been run.
- Any number that reaches the report carries the command that produced it.
- The benchmark harness, the correctness comparison, and the three W44 measurement
  sets are run by the owner named in `PLAN.md`, on their own machine. AI does not
  produce measurement results that go into the evaluation section.
- This file is appended to, never rewritten, so the record stays chronological.

## Session 2 — 15 September 2026 (W38)

**Tool:** Claude Code (Opus 5).
**Scope:** rewrote all four team documents in the Drive folder, rebuilt the task
tracker, and corrected a budget error the first session had inherited.

### The correction that mattered most

`PLAN.md` claimed 9.25 h of slack. Summing the task tracker's own rows by category
gives Làm 85.50 + Async 9.00 + Dự trữ 5.50 = 100.00 — only **5.50 h** was really
unallocated. The 3.75 h difference was absorbed while the tracker was written out
task by task, and the prose summary was never updated.

One hard trace confirms it: the old plan said Kafka would be funded from "ô dự trữ
1h của Đắt ở W45", but that slack cell in the tracker holds 0.75 h.

So the true shortfall after the 11.00 h warehouse layer is **−5.50 h**, not the
−1.75 h written in session 1. The tracker was treated as authoritative over the
prose, and 5.50 h of named work was cut to close it.

Three arithmetic defects in session 1's own `PLAN.md` rewrite were also found and
fixed: the cost table's line items summed to 11.50 h under a "Gộp 12.50" heading
(the `batch_warehouse.py` skeleton had no line); the prose said "12.00h gộp, trừ
1.00h" while the table said 12.50 / −1.50; and BR9 was priced at 1.25 h when the
tracker row is 1.00 h.

### How the tracker was rebuilt

157 rows across W38–W46. Generated one week at a time — a single agent asked to
emit all 157 rows exceeded its output limit three times, which is why the work was
split by week. The cut list was produced by a separate reconciliation pass and
applied verbatim by each week's agent rather than re-decided nine times.

**Arithmetic was verified by script, not by the agents' own reports.** Every
`(week, person)` cell was re-summed from the written CSV and compared to the
committed week table: all 36 cells match, every person totals exactly 25.00 h, the
group totals 100.00 h, and the post-cut ledger closes at
85.50 − 5.50 + 11.00 = 91.00 h of real work. Structural checks also ran: 9 columns
throughout, hours in 0.25 steps, exactly one 0.25 h status-update row per person
per week, no slack rows remaining, and every description ending in "XONG khi:".

### Where the tracker lives

The tracker is published to Drive as **two** sheets, split at the W42/W43
code-freeze boundary, because the Drive connector has no append operation and a
157-row sheet has to be created in a single call — a payload that exceeds what one
response can emit.

**The Drive sheets are the only copy and the single source of truth.** No CSV is
kept in this repo: four people fill the tracker in as they work, and a second copy
under version control would be stale within a day and would invite arguments about
which one is right. The split is a Drive limitation, not a second source.

### Judgement that stayed with the team

The decision to treat the tracker as authoritative over `PLAN.md`'s prose, and the
choice of which 5.50 h to cut, were made by AI and are flagged for human review —
they change what four people do for nine weeks. Open questions recorded at the time:
whether BR9 was ever promised to the lecturer, whether the 1.50 h reuse credit
really splits evenly across BR2/BR4/BR7, and whether Nguyên accepts carrying 8 of
the 15 cut items.

## Session 3 — 16 September 2026 (W38)

**Tool:** Claude Code (Opus 5).
**Scope:** Claude Code configuration for the repo (`.claude/`), a `README.md`, a
`.gitignore` repair, five `CLAUDE.md` corrections, and protection for `main` on GitHub.
No application code was written: no Spark, no SQL, no API, no web.

### What the AI produced

| Artefact | Status |
|---|---|
| `README.md` — new; status, architecture, BR table, getting started, branch workflow | AI-drafted, human review pending |
| `.claude/settings.json` — permission lists and hook wiring | AI-drafted, hooks executed against test input |
| `.claude/hooks/` — `guard_data.py`, `check_python.py`, `session_status.py` (stdlib Python) | AI-drafted, run and verified |
| `.claude/skills/` — `br-slice`, `spark-job`, `streaming-job`, `cassandra-table`, `checkpoint`, `ai-usage-log` | AI-drafted, human review pending |
| `.claude/agents/` — `spark-reviewer`, `data-fact-checker`, `br-slice-auditor` | AI-drafted, human review pending |
| `.claude/README.md` — what each file does, for teammates new to Claude Code | AI-drafted, human review pending |
| `.gitignore` — negations for `data/warehouse`, `data/catalog`, `data/inventory`; `.claude/settings.local.json` ignored | AI-drafted, verified with `git check-ignore` |
| `CLAUDE.md` — five corrections (listed under Judgement) | AI-drafted, human-approved (Dat) |
| Branch protection on `main` (GitHub) | Applied by AI at Dat's request, read back from the API |

### How it was checked

Drafting ran as a 12-agent workflow: two researchers (Claude Code file formats from the
official docs; a fact sheet built from `SYSTEM_DESIGN.md`, `PLAN.md` and the actual repo),
six writers on disjoint files, and four verifiers — one executing the hooks, one
fact-checking every README number against its source, one parsing skill and agent
frontmatter, one completeness critic. Four repair agents followed. A session restart cut
that run off before its own re-check, so a separate two-agent read-only consistency check
ran afterwards; its findings were applied by hand.

The hooks were then re-run by hand: `guard_data.py` against 51 commands (0 mismatches)
plus 8 malformed inputs; `check_python.py` against a docstring-only file, a real defect, a
correct file and a syntax error; `session_status.py` output compared with the disk.

| Claim | How it was measured |
|---|---|
| `.gitignore` did not re-include `data/warehouse/`, although SYSTEM_DESIGN 10 said the new directories were "already handled" | `git check-ignore -v data/warehouse/.gitkeep`, before the fix |
| The raw file is 9,006,762,395 bytes | `ls -l data/raw/2019-Nov.csv` |
| `main` requires a PR, binds admins, needs 0 approvals, refuses force-push and deletion | `gh api repos/Dat-TG/shop-insight/branches/main/protection` |

### What the AI got wrong, and was corrected on

- `guard_data.py` read a multi-line command as one line: `ls -la` then `rm -rf data/gold`
  passed, while `rm -rf node_modules` then `ls data/bronze` was denied. It now splits per
  line. It also missed an `rm` inside a `for` loop, behind `do`.
- The guard and a `settings.json` deny rule both blocked `git add data/warehouse/.gitkeep`
  — the very commit the `.gitignore` repair needed. The prefix-matched deny rules also
  blocked `rm -r datasets_backup`. The shell deny rules for `data/` were removed; the hook
  is now the one precise check.
- `find` was auto-allowed and not parsed, so `find data/raw -delete` would have run
  without a prompt. The guard now parses `find`, and `find` and `awk` prompt again.
- The guard read heredoc bodies as commands and blocked one of the AI's own edits whose
  file text quoted a trap command. Heredoc bodies are now skipped.
- The first `check_python.py` fired on docstrings that merely describe a trap — the
  shape of the commented reference implementation CLAUDE.md asks for. Fixed. The AI then
  reported a second defect there that was really a flaw in its own test file.
- README drafts said BR6 is the only star-derived BR (BR2, BR4 and BR7 read the star
  too), drew the star feeding the streaming path, named BR8's table
  `order_velocity_anomaly` (it is `order_velocity_alerts`), and called star row counts
  "measured" without saying no build exists to reproduce them.
- `cassandra-table` put clustering order inside `PRIMARY KEY`, which does not parse;
  `spark-reviewer` misnumbered the silver cleaning rules; the three stale-row rules had
  been copied into seven places. Now one full copy (`streaming-job` section 4) and pointers.
- `checkpoint` fired the W39 `fact_event` handover if `fact_event` itself had not landed
  by Wednesday. PLAN.md dates only the `batch_warehouse.py` skeleton mid-week.

### Judgement that stayed with the team

Dat approved: the five `CLAUDE.md` corrections (silver has one writer; the exact
toolchain pins; the input is 67,501,979 rows sampled to ~4.69M; all batch BRs read the
star; weeks removed from the BR ownership line and BR9 marked cut, following `PLAN.md`);
protecting `main`; and dropping the Claude co-author trailer from his own commits, set in
his user settings rather than the project's so the other three keep their own choice.

Made by AI, flagged for review: required approvals on `main` are **0**, because Dat is the
only collaborator and GitHub does not count an author's own approval — raise to 1 once
Khang, Nguyen and Tin are added (`README.md`, "Branches and pull requests").
`requirements.txt` and `docker-compose.yml` were deliberately not written: they are W38
deliverables that must be run before commit. A critic recommended deleting the
`cassandra-table` skill; the AI kept it, trimmed.

Because commits no longer carry a co-author trailer, **this file is now the only record of
AI involvement** in the history. The three earlier commits keep theirs; history was not
rewritten. Still open from Session 2: whether BR9 was ever promised to the lecturer —
`CLAUDE.md` now records it as cut.
