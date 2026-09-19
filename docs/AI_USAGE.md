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

## Session 4 — 17 September 2026 (W38)

**Tool:** Claude Code (Opus 5).
**Scope:** Dat's two remaining W38 tasks: the unattended Spark setup (PR #3), and
`ingestion/load_bronze.py` with a correction of the sample numbers across the documents
(PR #4). This is the first application code in the repo. All of it was run on Dat's
machine (WSL2, Ubuntu 26.04, 20 cores, 15 GB) before it was committed.

### What the AI produced

| Artefact | Status |
|---|---|
| `docs/SETUP_SPARK.md` — install from zero, the pin and memory traps, troubleshooting for Linux and WSL | AI-drafted. Steps 2–4 and 8 were run on this machine; step 1 (a fresh WSL distro) and step 7 (the Kaggle download) were written, not executed. Human review pending: Dat's from-zero recording is the real test |
| `requirements.txt` (`pyspark==4.1.3`, `py4j==0.10.9.9`), `conf/spark-defaults.conf` | Run and verified |
| `processing/schema.py`, `processing/kata.py` | Run and verified; reviewed by the `spark-reviewer` agent, findings applied |
| `ingestion/load_bronze.py` | Run and verified, before and after applying the `spark-reviewer` findings |
| Corrections in `README.md`, `SYSTEM_DESIGN.md` (3.1, 8, 10, 11, 11.1), `CLAUDE.md`, `PLAN.md`, the `spark-job` and `streaming-job` skills, the `spark-reviewer` agent, the `check_python.py` hook | AI-drafted. The sample-number fix follows an option Dat chose in advance |

### How it was checked

Dat ran `sudo apt install -y openjdk-21-jdk-headless python3.14-venv unzip`; the AI did
the rest.

- `pip install -r requirements.txt` into a fresh `.venv`.
- `python processing/kata.py` printed 6.0 GiB, UTC, events from 00:00:00 to 03:52:45,
  view 97,489 · cart 1,089 · remove_from_cart 0 · purchase 1,422, and `KATA OK`.
- Two negative tests:
  - A copy of the kata with no `conf/` printed 1.0 GiB, Asia/Bangkok and 07:00:00, then
    `KATA MISMATCH`, exit 1.
  - A copy with a wrong `RAW_TIMESTAMP_FORMAT` failed with
    `Malformed records ... FAILFAST`.
- `python ingestion/load_bronze.py` was run twice. Both runs printed the same numbers and
  `BRONZE OK`. `.gitkeep` was deleted by the overwrite and restored by the script, and
  `git status --short data/` stayed empty. A third run, after the review fixes, printed
  the same numbers.
- Two more negative tests, on a scratch copy with a 1,000,000-byte CSV:
  - The script refused to start ("a partial download") and left `.gitkeep` alone.
  - With the size guard patched out, FAILFAST aborted the write on the cut-off last line,
    and `.gitkeep` was still restored.

| Claim | How it was measured |
|---|---|
| Spark's 7% sample is 4,767,012 rows / 258,390 users / 129,899 products / 30 dates | `python ingestion/load_bronze.py` (Spark 4.1.3). Independently, a Python copy of Spark's Murmur3 `hashLong` (seed 42) over the full CSV gave the same numbers; that copy was self-tested against Spark's `hash(1)` = -559580957 and `hash(1L)` = -1712319331 |
| Read as INT, the same rule gives 4,713,498 rows / 259,109 users, and only 18,150 users are shared with the BIGINT sample | Same Python pass, with `hashInt` |
| 2019-Nov.csv has no `remove_from_cart` events: view 63,556,110 · cart 3,028,930 · purchase 916,939 | Same Python pass, counting column 2 |
| First 100,000 rows: view 97,489 · cart 1,089 · purchase 1,422, from 00:00:00 to 03:52:45 UTC | `head -100001 data/raw/2019-Nov.csv \| tail -n +2 \| cut -d, -f2 \| sort \| uniq -c`, and the same with `-f1` plus `sort \| sed -n '1p;$p'` |
| This machine's Spark session time zone is Asia/Bangkok unless `conf/` pins UTC | The kata copy without `conf/` |
| `builder.config("spark.driver.memory", "6g")`: first session 6.0 GiB; `getOrCreate()` with a session running 1.0 GiB plus a WARN; new session after `stop()` 1.0 GiB while `getConf()` says `6g` | A three-case script reading `Runtime.maxMemory()` through py4j, run with `SPARK_CONF_DIR` pointing at an empty directory |
| Ubuntu 26.04 lacks `python3.14-venv` by default | `python3 -c "import ensurepip"` raised `ModuleNotFoundError` before the apt install |
| pyspark 4.1.3 is published only as a 434 MiB source package; the install took 4 min 18 s; py4j resolves to 0.10.9.9 | PyPI JSON API; `time pip install pyspark==4.1.3`; `pip freeze` |
| `load_bronze.py` takes 25 s on 20 cores and writes 97 files (112 MB) | Script output; `find data/bronze -name '*.parquet' \| wc -l`; `du -sh data/bronze` |
| JDK, venv and pip cache together take about 1.7 GB | `du -sh` on the three directories |

### What the AI got wrong, and was corrected on

- **The sample numbers from Session 1 (4,694,166 / 258,088 / 127,693) are not what Spark's
  `hash()` produces.**
  - No machine had a JDK before today, so Spark never produced those numbers.
  - The headline numbers are now replaced everywhere.
  - The counts derived from the old sample are flagged in SYSTEM_DESIGN 3.1, README and
    PLAN as "re-measure in W39". They are not recomputed. That covers the star row
    counts, SCD2 versions, 12,659 purchased SKUs and the range-join size.
  - The older rows of this file are left as written, as the append-only rule requires.
- **The documents said `builder.config("spark.driver.memory")` is always "silently
  ignored", and so did the W38 task text.**
  - Measured: it works when that builder starts the JVM. It is ignored once a JVM is
    running, and silently only after a `stop()`.
  - The rule (memory only in `conf/`) is unchanged; the reason is corrected in seven
    places.
- **The documents listed four event types.** The November file has three.
- **The first `kata.py` printed heap and time zone but never failed on them.** Also,
  Spark's CSV reader parses only the columns a query uses, so its FAILFAST never touched
  the timestamp format.
  - `spark-reviewer` caught both.
  - The reviewer's proposed fix, `spark.sql.csv.parser.columnPruning.enabled=false`, was
    tested and did not make FAILFAST check unused columns on Spark 4.1.3.
  - The kata now reads `event_time` itself and checks the time range.
- **The first conf comment expected "about 5.3 GiB".** JDK 21 (G1) reports the full
  6.0 GiB. Also found by the reviewer.
- **A schema comment called missing categories "empty".** Spark reads them as NULL, and
  the silver rules must test for NULL. Also found by the reviewer.
- **The first `load_bronze.py` had three gaps, all found by `spark-reviewer`.**
  - It passed any row count from 4.4 to 5.0 million, so the known-wrong samples (4,713,498
    and 4,694,166) would also have printed `BRONZE OK`. It now requires the exact numbers.
  - It restored `.gitkeep` only after a successful write; the restore is now in `finally`.
  - It deleted bronze before noticing a truncated CSV; it now checks the file size first.
- **The W38 task text said Spark 4.x requires JDK 21.** It requires 17 or newer; the
  team pins 21. The README had also said `spark-defaults.conf` is not a repo file; it now
  is.

### Judgement that stayed with the team

Dat decided three things:
- how to handle the wrong sample numbers: replace the headline numbers and add a note,
  without recomputing derived counts;
- that `SETUP_SPARK.md` is written in English;
- the approved plan: two PRs, `conf/` committed, `SPARK_CONF_DIR` set inside every
  script.

The recording, the group posts and the merges are Dat's.

Made by AI, flagged for review:
- The three-line start (`sys.path` plus `SPARK_CONF_DIR`) as the convention for every
  script.
- The two extra kata checks: the heap/time-zone lines and the time-range line.
- FAILFAST on the raw CSV.
- The bronze check requires the exact numbers. This is stricter than the task's
  "4.4–5.0 million rows".
- No repartition before the bronze write (rule 3).
- Restoring `.gitkeep` after an overwrite.
- Relying on `limit()` returning the file's first 100,000 rows. It does here, but Spark
  does not promise it; a troubleshooting row covers a mismatch.

Carried forward:
- Required approvals on `main` are still 0.
- Whether BR9 was ever promised to the lecturer is still open.
- `SETUP_SPARK.md` steps 1 and 7 still need a first real run by a teammate.

## Session 5 — 17 September 2026 (W38)

**Tool:** Claude Code (Opus 5).
**Scope:** a Vietnamese walkthrough of the Spark setup, after PRs #3 and #4 were merged.
No application code changed.

### What the AI produced

| Artefact | Status |
|---|---|
| `docs/SPARK_GUIDE_VI.md` — Vietnamese guide for Spark beginners, in seven parts: Spark concepts, install steps, reading the `kata.py` output, reading the `load_bronze.py` output, a walkthrough of every new file, what changed in W38, and troubleshooting | AI-drafted, human review pending |
| Links to it from `docs/SETUP_SPARK.md`, `README.md`, `CLAUDE.md`; `PLAN.md` now names the guide instead of the clip | AI-drafted, following Dat's decision |

### How it was checked

The guide adds no new claims beyond Session 4, with one exception: the worked `hash()`
example in part 5. That example was produced by Spark on this machine.

| Claim | How it was measured |
|---|---|
| `user_id` 512927188: `hash` as BIGINT = -713643297, `pmod` = 3 (kept); as INT, `pmod` = 57 (dropped). 520088904: 24 (INT 22). 530496790: 92 (INT 59) | `SELECT hash(CAST(<id> AS BIGINT)), pmod(...), hash(CAST(<id> AS INT)), pmod(...)` in PySpark 4.1.3; 512927188 was taken from `data/bronze` |
| An `event_date=` directory holds 2 Parquet files, and the files do not contain `event_date`: it comes from the directory name | `ls data/bronze/event_date=2019-11-01`; `spark.read.parquet(<one file>).columns` lists 9 columns, `spark.read.parquet("data/bronze").columns` lists 10 |

Every command and output shown in the guide was copied from Session 4's runs, not retyped.

### What the AI got wrong, and was corrected on

- Session 4 said the from-zero screen recording would be the real test of
  `SETUP_SPARK.md`. Dat dropped the clip. The Vietnamese guide replaces it, so steps 1
  (WSL install) and 7 (Kaggle download) still await their first real run, which will now
  be by a teammate following the guide.

### Judgement that stayed with the team

Dat decided: no clip, and a Vietnamese guide that explains each file and each step.

Made by AI, flagged for review: the guide is a **second file** next to the English
`SETUP_SPARK.md`, not a replacement. Both headers ask that a changed command be changed in
both. If the team would rather keep one file, the English one can go.

## Session 6 — 19 September 2026 (W38)

**Tool:** Claude Code (Opus 5).
**Scope:** Dat's last W38 task: `processing/batch_silver.py` (bronze -> silver), planned
first in plan mode, then written, run and reviewed. Also the documents that had to move
with it: a seventh cleaning rule and 31 silver date directories. Everything was run on
Dat's machine (WSL2, 20 cores) before it was committed.

### What the AI produced

| Artefact | Status |
|---|---|
| `processing/batch_silver.py` — `clean()` (the seven rules, also importable by the W40 stream), `write_silver()`, a `report()` that checks exact numbers, `SILVER OK` | Run and verified four times; reviewed by the `spark-reviewer` agent (0 findings), and its one consistency note applied |
| `SYSTEM_DESIGN.md` §3.1 (the 38-hour purchase gap), §4 (rule 7, 31 dates, measured row counts), §5.5 (31 `fact_event` partitions), §8 steps 2 and 7 (seven rules, import `clean()`) | AI-drafted, following Dat's two decisions below; human review pending |
| `README.md` (status, layout marks, silver check), `CLAUDE.md` (status, next task), the `spark-job`, `streaming-job` and `br-slice` skills, the `spark-reviewer` agent, `.claude/README.md` | AI-drafted, human review pending |
| `docs/SPARK_GUIDE_VI.md` — how to run and read `batch_silver.py` (part 4), a walkthrough of the file (part 5), three measured facts (part 6) | AI-drafted, human review pending |

### How it was checked

- `python processing/batch_silver.py` ran four times, each ending in `SILVER OK` with the
  same numbers. `.gitkeep` was restored every time, and `git status --short data/` stayed
  empty.
- `find data/silver -name '*.parquet' | wc -l` gave 93. `ls data/silver` showed 31
  `event_date=` directories. `du -sh data/silver` gave 136 MB.
- Before any code existed, the expected numbers were measured with read-only Spark
  aggregates over `data/bronze`.

| Claim | How it was measured |
|---|---|
| Silver is 4,754,015 rows: bronze 4,767,012, minus 12,996 with `price <= 0`, 0 with a null `user_id` and 1 with a null `user_session` | `count_if` over `data/bronze` for each rule; `batch_silver.py` output |
| 21,898,171 of 67,501,979 raw rows have an empty `category_code` (32.4%) | `tail -n +2 data/raw/2019-Nov.csv \| awk -F, '$5==""{n++} END{print n}'`. `grep -c '"'` on the file gives 0, so no field is quoted and a plain comma split is exact |
| After the UTC+7 shift, silver has 31 dates (2019-11-01 .. 2019-12-01), 25,859 rows on 2019-12-01, and events from 2019-11-01 07:00:02 to 2019-12-01 06:59:49 | `from_utc_timestamp` + `to_date` aggregate over bronze; `batch_silver.py` output |
| `from_utc_timestamp(t, "Asia/Ho_Chi_Minh")` equals `"+07:00"` on every row | Count of mismatches over bronze: 0 |
| On Spark 4.1.3, `split(...).getItem(2)` on a two-level code raises `INVALID_ARRAY_INDEX` (ANSI mode), while `get(arr, 2)` returns NULL | A three-row DataFrame probe |
| The only four-level code is `electronics.audio.music_tools.piano` (4,628 rows) | `groupBy("category_code")` over bronze, filtered to four levels |
| 258,330 users, 128,972 products, `unknown` counts l1 1,534,249 · l2 1,534,249 · l3 3,428,388 · brand 634,202 | `batch_silver.py` output. The null-session row is `electronics.smartphone`, checked with a `select` on bronze; that is why l3 is one lower than measured before rule 7 |
| Partition pruning works on both columns | `.explain()` of `event_type = 'purchase' AND event_date = '2019-11-29'` shows both in `PartitionFilters` and no `DataFilters`; 2,252 rows |
| `clean()` runs on a streaming DataFrame | `readStream.format("json").schema(EVENT_SCHEMA)` over five hand-written rows, a `memory` sink, `availableNow`. The `price = 0` and null-session rows were dropped, 20:00 UTC became 1 Dec 03:00, and nulls became `unknown` |
| The UTC guard fires, and without it a UTC+7 session files the events of 10:00-17:00 UTC under the next day | `clean()` with the session set to `Asia/Ho_Chi_Minh` raised `RuntimeError`. Four timestamps (09:59, 10:01, 16:59, 17:01 UTC) were dated in both sessions: only 10:01 and 16:59 moved |
| `batch_silver.py` takes 15-16 s on 20 cores | Script output |
| The raw file has no purchase from 2019-11-14 18:09:37 to 2019-11-16 08:32:34 UTC, and 0 on 15 Nov UTC; views and carts continue | `awk -F, '$2=="purchase" ...'` over the full CSV for the last purchase before and the first after; `grep -c "^2019-11-15[^,]*,purchase," data/raw/2019-Nov.csv` gave 0. Found because a deliberately broken silver run (UTC dates) had 89 date/type directories, not 90 |
| In silver, 15 Nov (Vietnam date) has 170 purchases and 35,812 carts | `groupBy("event_date").pivot("event_type").count()` on silver, 13-17 Nov |

### What the AI got wrong, and was corrected on

- **The first `EXPECTED` had `category_l3 'unknown'` = 3,428,389.** It was measured before
  rule 7 existed. The plan flagged it as ±1; the first run printed 3,428,388. It was
  pinned only after the dropped row was shown to be a two-level code.
- **The first null check in `report()` mixed `&` and `|` into an expression that did not
  test what its comment said.** It was rewritten as "any column except
  `category_code`" before the first run.
- **The docstring said every printed number must match, but the `event_time` range was
  printed and never checked.** Found by `spark-reviewer`; it is now in the gate.
- **The first comment on the UTC guard said a wrong session "misfiles half" the
  events.** Measured, it is the events of 10:00-17:00 UTC, 7 hours of 24; the comment
  and the guide were corrected.
- **The null-session row's time was reported as "2019-11-30 00:25:56 UTC"** in the
  question put to Dat and in the plan. It is 2019-11-29 17:25:56 UTC (30 Nov 00:25 in
  Vietnam). The value had been read through `.collect()`, which gives a Python
  `datetime` in the laptop's time zone, not UTC. It surfaced when a UTC-vs-Vietnam date
  count came out 917,163 instead of the 917,164 measured before rule 7. The decision is
  unaffected; `SYSTEM_DESIGN.md` §4 was corrected. Show timestamps with `.show()` or
  `date_format`, as `kata.py` does, never through a Python `datetime`.
- **Two numbers in the task text were corrected, not AI errors.** The task text cited
  21,898,175 empty categories; the raw file has 21,898,171, as PLAN.md already said. Its
  done condition, "max event_date matches the last day of the month in Vietnam time",
  reads as 30 Nov, but correct code gives 2019-12-01. Both were put to Dat before any
  code was written.

### Judgement that stayed with the team

Dat decided three things:
- keep the 25,859 events of 1 Dec, so silver has 31 date directories and the done check
  is `max(event_date) = 2019-12-01`;
- add rule 7, drop a null `user_session`, rather than leaving it to `batch_warehouse.py`
  and BR5;
- the approved plan: `clean()` shared with the stream, and the document updates.

Commit, PR and merge are Dat's.

Made by AI, flagged for review:
- `repartition("event_date", "event_type")` before the write, one file per directory.
  It is argued as determinism (93 files on every machine), not speed, but it is the
  closest thing to tuning before W41 (rule 3).
- Keeping the raw `category_code` column in silver, null included.
- The UTC check inside `clean()`, which raises instead of warning.
- The W40 stream importing `clean()` from `batch_silver.py`, rather than from a separate
  module.

Open:
- Rules 4 and 5 treat only NULL as missing. If `replayer.py` (W40, Tin) writes
  `"category_code": ""` or `"brand": ""` instead of null or leaving the key out, the stream
  gets `""`, not `unknown` (raised by `spark-reviewer`).
- `SYSTEM_DESIGN.md` 5.5 now says 31 `fact_event` partitions; the Postgres loader must
  create 2019-12-01 too.

Carried forward:
- Required approvals on `main` are still 0.
- Whether BR9 was ever promised to the lecturer is still open.
- `SETUP_SPARK.md` steps 1 and 7 still need a first real run by a teammate.
