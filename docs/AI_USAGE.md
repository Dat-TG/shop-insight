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

## Session 7 — 20 September 2026 (W38)

**Tool:** Claude Code (Opus 5).
**Scope:** The last unbuilt W38 deliverable: Cassandra and Postgres in Docker, plus the
Docker install written into the setup guides so the other three do not need to be
messaged individually. No BR code and no Spark code; the one new Python file only reads.

### What the AI produced

| Artefact | Status |
|---|---|
| `docker-compose.yml` — `cassandra:4.1.12` + `postgres:16.15`, pinned to the patch, healthchecks, named volumes, heap and memory settings | Run and verified: pulled, started, restarted, torn down and brought back |
| `.env.example` — ports, database, user, password, keyspace. Decides the values `README.md` called "undecided until docker-compose.yml lands" | Run and verified: `docker compose config` resolves with no `.env` present |
| `serving/check_infra.py` — both drivers connect, prints `INFRA OK`. Carries `read_env()` for W39 | Run and verified, pass and fail paths both exercised |
| `requirements.txt` — 6 pins added, taken from `pip freeze` after a real install, not guessed | Run and verified |
| `docs/SETUP_SPARK.md` — new step 9 (Docker), old 9→10 and 10→11, 16 new troubleshooting rows, header budget, three stale W40/W41 dates | AI-drafted, human review pending |
| `docs/SPARK_GUIDE_VI.md` — new Phần 4, old 4-8→5-9 with TOC anchors rewritten, three file entries in Phần 6, four measured facts in Phần 7, 16 error rows in Phần 8 | AI-drafted, human review pending |
| `README.md`, `SYSTEM_DESIGN.md` (10, 11, 11.1), `CLAUDE.md`, `.claude/hooks/session_status.py`, `.claude/skills/cassandra-table/SKILL.md` — statements this work made false | AI-drafted, human review pending |

### How it was checked

Every command below was run on Dat's machine (WSL2 Ubuntu 26.04, 20 cores, 15 GiB).

```bash
docker compose config                      # resolves with no .env present
docker compose pull                        # both pinned tags exist in the registry
docker compose up -d --wait                # both Healthy
docker compose logs cassandra | grep -iE "JVM Arguments|Heap size|in pairs|G1"
docker compose exec cassandra nodetool info | grep -i "Heap Memory"
docker compose exec postgres psql -U shopinsight -d shopinsight \
  -c "SHOW shared_buffers; SHOW maintenance_work_mem; SELECT current_database(), current_user;"
pip install -r requirements.txt && pip freeze | grep -iE '^(cassandra-driver|psycopg2-binary|click|Deprecated|geomet|wrapt)=='
python serving/check_infra.py              # INFRA OK, exit 0; run twice, identical
docker compose stop cassandra && python serving/check_infra.py   # exit 1, Postgres still reported
docker compose down && docker compose up -d --wait               # volumes survived
docker compose stop && python processing/kata.py                 # KATA OK with Docker down
echo '{}' | python3 .claude/hooks/session_status.py | grep -i docker
```

| Claim | How it was measured |
|---|---|
| Both drivers have Python 3.14 wheels, so no compiler is needed | PyPI JSON API for `cassandra-driver==3.30.1` and `psycopg2-binary==2.9.13`: both publish `cp314 manylinux_2_17_x86_64`. Then confirmed by a real `pip install` |
| `cassandra:4.1.12` starts with a 2 GB heap | `docker compose logs cassandra` shows `-Xms2G -Xmx2G -Xmn256M` and `Heap size: 1.975GiB/1.975GiB`; `nodetool info` reports `143.12 / 2022.44` MB |
| `cassandra:4.1.12` runs CMS, not G1 | `-XX:+UseConcMarkSweepGC` is in the logged JVM arguments, and `-XX:+UseG1GC` is commented out in `/etc/cassandra/jvm11-server.options` |
| `MAX_HEAP_SIZE` alone would stop the container | Lines 148-153 of `/etc/cassandra/cassandra-env.sh` inside the image: the `elif` branch prints `please set or unset MAX_HEAP_SIZE and HEAP_NEWSIZE in pairs when using CMS GC` and `exit 1` |
| `postgres:16` needs no extension for the W39 GIN index | `SELECT count(*) FROM pg_opclass c JOIN pg_am a ON a.oid = c.opcmethod WHERE a.amname = 'gin' AND c.opcname = 'jsonb_path_ops'` returns 1 on a stock container |
| 75 s cold start, 19 s warm | `time docker compose up -d --wait`, first run and after a `down`/`up` |
| ~1.2 GB of images | `docker system df` → `Images 1.146GB` |
| Renumbering `SETUP_SPARK.md` breaks no cross-reference | `grep -rniE "SETUP_SPARK(\.md)? (step\|section) *[0-9]+"` across the repo: every hit names steps 3, 6, 7 or 8. Nothing referenced sections 9, 10 or 11 |
| The 9 VI table-of-contents anchors still resolve | A script that regenerates each anchor from the `## Phần` headings and compares; 9/9 match |

### What the AI got wrong, and was corrected on

- **The draft asserted Cassandra 4.1 runs G1GC and therefore ignores `HEAP_NEWSIZE`.**
  Both halves are wrong for `cassandra:4.1.12`: the image selects CMS, and under CMS
  `HEAP_NEWSIZE` becomes `-Xmn256M` and is honoured. The comment in `docker-compose.yml`
  was rewritten from what the container actually logged, and the real rule — the container
  exits 1 unless **both** variables are set — became a troubleshooting row in both guides
  and a clause in `SYSTEM_DESIGN.md` 11.1. The draft had this flagged as unverified with
  the command to settle it, which is why it was caught before the commit rather than by
  a teammate in W40.
- **A `**Check:**` line said `docker compose ps` shows both containers `exited`.** It does
  not: plain `ps` lists only running containers and prints an empty table. Corrected to
  `docker compose ps -a` in both guides, with the reason in parentheses.
- **The draft planned to put the Docker section at the end, as asked.** Grepping first
  showed nothing in the repo references `SETUP_SPARK.md` sections 9, 10 or 11 by number,
  so the renumber cost two heading lines. Put back to Dat, who chose step 9 — which also
  keeps the Docker error rows in the single troubleshooting section instead of two
  sections before the thing they troubleshoot.
- **The expected-output block in the docstring did not match the real output.** It was
  regenerated from an actual run rather than hand-edited, so the block a teammate compares
  against is the one the script prints.
- **`click==8.5.0` was left as a placeholder in the draft**, because no plan can know it.
  All six pins were taken from `pip freeze` after installing.

### Judgement that stayed with the team

Dat decided four things, before implementation:
- pin the image tags to the patch (`4.1.12`, `16.15`) rather than the floating `4.1` / `16`
  the task named, and record both in `SYSTEM_DESIGN.md` 11.1;
- set Postgres memory now as a config of record rather than leaving defaults until W41,
  so the W41 DuckDB comparison is not run against a 128 MB `shared_buffers`;
- mirror the whole thing into `docs/SPARK_GUIDE_VI.md` rather than the English file only;
- fix the `README.md` and `SYSTEM_DESIGN.md` statements this work makes false, in the
  same PR.

And, once the grep evidence existed, that Docker becomes step 9 with the old 9 and 10
renumbered.

Made by AI, flagged for review:
- **2 GB for Cassandra's heap and 512MB/256MB for Postgres.** Modest and documented as
  config of record, but they are still numbers chosen without a benchmark (rule 3). The
  argument is that they are what lets both containers and a 6 GB Spark driver share one
  laptop, not that they are fast.
- **`shm_size: 256mb` on Postgres.** Prevents `could not resize shared memory segment` in
  parallel workers and large index builds — Tin's W39 and W41 territory. It is a judgement
  call, not a measurement.
- **Publishing both ports on `127.0.0.1` only.** Deliberate, because neither store has
  authentication. It means a Windows GUI client must use `localhost` and not the WSL IP;
  there is a troubleshooting row for that.
- **`read_env()` living in `serving/check_infra.py`** rather than in a config module, with
  a written trigger to move it to `serving/config.py` when a caller outside `serving/`
  needs it in W42.
- **`shopinsight` as database, role and keyspace name, password `local_dev_only`.** The
  keyspace name must survive CQL without quoting, which rules out `shop-insight`.

Open:
- The Cassandra keyspace is named in `.env.example` but nothing creates it.
  `serving/apply_schema.py` is still Nguyen's W38 deliverable; `check_infra.py` reports the
  keyspace as `absent` without failing, so it keeps passing either way.
- `cassandra-driver` 3.30.1 printed no `local_dc` warning on `Cluster.connect()` here, so
  no execution profile was set. W40's `foreachBatch` code may still need
  `DCAwareRoundRobinPolicy(local_dc="datacenter1")`; the check prints `datacenter1` so the
  value is already on screen.
- ARM laptops are unverified: nobody on the team has one, and `docker manifest inspect`
  was not run for these two tags.

Carried forward:
- Required approvals on `main` are still 0.
- Whether BR9 was ever promised to the lecturer is still open.
- `SETUP_SPARK.md` steps 1 and 7 still need a first real run by a teammate — and now
  step 9 does too. Every number in step 9 comes from Dat's machine only.

## Session 8 — 27 September 2026 (W39)

**Tool:** Claude Code (Opus 5.5).
**Scope:** Review of Tín's PR #9 (branch `w39-warehouse-star`, head `ec2abb9`: the W38 app
skeleton, the API contract frozen in `1d93340` with its 8 fixtures, the W39 Postgres DDL and
three small dims), and the fixes Dat applied on that branch before merging. Planned in plan
mode, then done in the working tree in three passes: API and contract, warehouse, docs. The
AI committed nothing. The changes were staged for Dat, who reviews them, then commits,
pushes and merges.

### What the AI produced

| Artefact | Status |
|---|---|
| `serving/api/routers/br1.py`, `br3.py`, `br5.py`, `br7.py`, `br8.py` — `warehouse="fixture"` became `"Fixture"`, the enum value. `QueryMeta` rejects the lowercase one, so all five returned 500. Their docstrings drop the delivery weeks (PLAN.md owns the schedule) and say Now/Next like BR2, BR4 and BR6 | Run and verified: all 8 endpoints return 200 |
| `serving/api/routers/br2.py`, `br4.py`, `br6.py` — back on contract §4, §6 and §8 (parameters and row fields). `meta` is `Fixture`/0 instead of a hard-coded `Postgres` footer. The Postgres SQL is gone, and each docstring names its §2 store as the next step | Run and verified |
| `web/fixtures/br2-funnel-daily.json`, `br4-rfm-segments.json`, `br6-stockout-risk.json` — restored from `1d93340` | Run and verified: `git diff 1d93340 -- web/fixtures` is empty |
| `tests/test_fixtures.py` — each fixture's engine from §2, the exact field set per BR, a scan of every router's `warehouse="..."` literal | Run and verified, including a negative control |
| `requirements.txt` — the web block's comment corrected; the 15 dependencies of fastapi and uvicorn pinned | Run and verified: clean install |
| `warehouse/ddl.sql` — rebuilt from SYSTEM_DESIGN 5.4/5.5 verbatim inside `BEGIN; … COMMIT;`, no `IF NOT EXISTS`. The fact partitions are added and marked `-- not in 5.5`; the `dim_event_type` INSERT moved to the loader | Run and verified on scratch databases |
| `processing/batch_warehouse.py` moved to `serving/load_star_postgres.py` and edited: it connects through `read_env()` (the old default password was `shopinsight`, not `local_dev_only`), takes `--database`, and adds `day_name`, the 5.4 `dim_event_type` rows, `dim_warehouse` codes and types, and new checks. It prints `POSTGRES STAR OK` | Run and verified on scratch databases, twice |
| `seed/holidays_2019.csv` — reduced to SYSTEM_DESIGN 3.2's three rows | Run and verified through the loader |
| `docs/evidence/explain_fact_event_partition.sql` — new header and queries. `explain_output_w39.txt` is regenerated by `psql -a`, not hand-edited | Run and verified |
| `README.md` (status, Getting started, layout marks), `SYSTEM_DESIGN.md` §10 and §11, `docs/API_CONTRACT.md` §1.2, §11 and §12, this entry | AI-drafted, human review pending |
| A new PR description and a message to Tín, both drafted outside the repo | AI-drafted; Dat posts them |

### How it was checked

Every command ran on Dat's machine (WSL2). The Postgres checks used throwaway `scratch_`
databases only, never `shopinsight`, and all of them were dropped at the end.

```bash
pip install -r requirements.txt && pip check                 # No broken requirements found
diff <(pip freeze | sort -f) <(grep -E '^[A-Za-z]' requirements.txt | sed 's/\[standard\]//' | sort -f)   # empty
python tests/test_fixtures.py                                # All 8 fixture bundles passed validation, exit 0
uvicorn serving.api.main:app --port 8000                     # then curl all 8 endpoints and /openapi.json
cd web && npm ci && npm run build                            # tsc -b passes; vite: ✓ built in 438ms
docker exec -i shopinsight-postgres psql -X -q -v ON_ERROR_STOP=1 -U shopinsight -d scratch_ddl < warehouse/ddl.sql
python serving/load_star_postgres.py --database scratch_ddl  # run twice
docker exec -i shopinsight-postgres psql -X -a -v ON_ERROR_STOP=1 -U shopinsight -d scratch_ddl \
  < docs/evidence/explain_fact_event_partition.sql > docs/evidence/explain_output_w39.txt
```

| Claim | How it was measured |
|---|---|
| The lowercase value is what broke the five stubs | `QueryMeta(ms=0.0, warehouse='fixture', partitions=0, rows=0)` raises `ValidationError: Input should be 'Cassandra', 'Parquet', 'Postgres', 'DuckDB' or 'Fixture'`. `serving/api/models.py` is unchanged since `ec2abb9` |
| The test now fails on the drift PR #9 had | Negative control: `ec2abb9`'s fixtures and routers copied into a `mktemp -d` directory, `FIXTURES_DIR` and `ROUTERS_DIR` pointed at it, then `validate_all()`. It gives 31 errors: 6 `meta.warehouse` `'Postgres'`; 17 fields not in the contract (3 BR2, 8 BR4, 6 BR6); 8 router literals (5 `'fixture'`, 3 `'Postgres'`). A BR4 row with `rfm_cell` deleted gives 1 error |
| All 8 endpoints return 200 with `Fixture`/0 | curl: rows br2 3, br4 8, br6 6, the other five 0; `rows == len(data)` everywhere; no traceback in the uvicorn log |
| The query parameters match §4, §6 and §8 | `/openapi.json`: br2 `start_date, end_date, category_l1`; br4 `snapshot_date, segment, r_score, f_score, m_score`; br6 `warehouse_id, max_days`. `r_score=6`, `warehouse_id=0` and `max_days=0` each give 422 |
| The web pins are the whole dependency set | A clean venv with only `fastapi==0.115.12` and `uvicorn[standard]==0.34.3` froze to exactly the pinned set plus `click==8.5.0`, which was already pinned |
| `ddl.sql` is the design | `diff -B` against the 5.4/5.5 SQL blocks gives six hunks: header and BEGIN, the INSERT replaced by one comment, three partition blocks, COMMIT. A catalog query (columns, constraints, indexes, partition keys of every non-partition table) prints identical output for a database built from the design text and one built from `ddl.sql`: `CATALOG IDENTICAL`, 150 records (100 columns, 24 constraints, 23 indexes, 3 partitioned tables). Against the old `ddl.sql` the diff is 234 lines |
| Re-applying fails loudly | A second apply prints `ERROR: relation "dim_date" already exists` and exits 3; the catalog is unchanged |
| Every date has its partition | 31 rows, one per date from 2019-11-01 to 2019-12-01, inserted into `fact_event` and rolled back: `0\|31\|31` (none in DEFAULT) |
| A Dec-01 row in DEFAULT would block the Dec-01 partition | A rolled-back probe: `ERROR 23514: updated partition constraint for default partition ... would be violated by some row` |
| The loader works and is idempotent | Two runs on `scratch_ddl` give identical output: `dim_date` 92, holidays 3, `dim_event_type` 5, `dim_warehouse` 5, GIN `jsonb_path_ops`, partitions 32/5/32, `POSTGRES STAR OK`. On the old schema it exits 1 without the OK line |
| `dim_event_type` matches 5.4 | `SELECT * FROM dim_event_type ORDER BY event_type_key` prints the same on the design database (its INSERT) and on the loader's |
| Partition pruning and index choice | `explain_output_w39.txt`, PostgreSQL 16.15. The `fact_event` plans scan only `_20191129` and `_20191201`, and `fact_session_funnel` only `_20191111` to `_20191117`. There is one `Bitmap Index Scan on ix_dim_product_attrs`, and `fact_inventory_daily` scans only `wh1`. The tables are empty, so this proves plan shape, not speed |
| `npx tsc --noEmit` checks nothing in `web/` | `npx tsc --noEmit --listFilesOnly` lists 0 files. `npx tsc -p tsconfig.app.json --noEmit --listFilesOnly` lists 13 under `src/`, and `npx tsc -b` exits 0 |

### What the AI got wrong, and was corrected on

- **The plan's `requirements.txt` comment said every web package ships cp314 or pure-Python
  wheels.** The clean install showed `watchfiles` 1.3.0 installs as `cp310-abi3`. The
  comment now says "cp314, abi3 (watchfiles) or pure-Python wheels".
- **The first evidence SQL echoed its own expected strings.** `psql -a` prints comments, so
  `Bitmap Index Scan on ix_dim_product_attrs` counted 2, and `fact_event_default` appeared
  even though no plan scanned it. A grep on the output would have passed on a comment alone.
  Two `Expected:` comments were reworded and the output was regenerated with the same
  command. The one remaining `_default` match is the echoed comment, not a plan line.
- **The plan expected the catalog query to print 150 lines; it prints 156.** The count is
  150 records. `pg_get_constraintdef` prints `ck_fsf_stage`'s `CASE` over seven lines, which
  adds six continuation lines. The expectation was wrong, not the DDL.
- **The docs plan changed `batch_warehouse.py`'s Getting started comment to "silver -> star
  Parquet".** SYSTEM_DESIGN 5.6 step 6 and 8 step 3 say that script also loads Postgres, so
  the comment stayed as it was in both files. The conflict is recorded as open below.
- **The docs draft explained why `tsc --noEmit` checks nothing in both `README.md` and
  `docs/API_CONTRACT.md` §12.** It was cut to one copy, in the README.
- **A review of the fixes caught four more.** The PR description said all three routers were
  reverted to `1d93340`, but only `br2.py` was: `br4.py` and `br6.py` were parameterless
  placeholders there and had to be rewritten to §6 and §8. It said the Vite chunk-size
  warning predates the PR, but the whole `web/` app arrives in this PR's `62c182a`. The five
  placeholder routers still gave delivery weeks, and `br7.py`'s W39 was wrong (PLAN.md has
  BR7 in W40). The DDL creates partitions that SYSTEM_DESIGN 5.5 leaves to the loader, and
  that was not recorded as open. All four are fixed; the last is under Open.

### Judgement that stayed with the team

Dat decided:
- to fix PR #9 on its own branch rather than post review comments;
- to keep `.agents/` as Tín committed it;
- to move `processing/batch_warehouse.py` to `serving/load_star_postgres.py` (SYSTEM_DESIGN
  10), leaving the old name for his Spark skeleton;
- to revert BR2, BR4 and BR6 to the contract frozen in `1d93340` rather than extend it;
- to merge with a merge commit, as for #7 and #8;
- to rewrite the PR description.

Made by AI, in the plan Dat approved, flagged for review:
- **Fixtures carry the production engine while the routers serving them say `"Fixture"`.**
  So the fixture's `meta` and the live footer differ until each router reads its store.
- **Dropping BR4's `limit` parameter**, which §6 does not have.
- **Warehouse codes and types** (`HAN-01` … `HPH-01`; central, regional,
  fulfilment_partner). They are invented; no source defines them.
- **Warehouse 5 active.** Khang's `gen_inventory.py` sends a fifth of purchases there
  (`1 + pmod(xxhash64(user_id), 5)`). This was read from `origin/w39-khang-warehouse` at the
  local ref `7ebabc1` without a fetch, so the remote may have moved.
- **The DDL has no `IF NOT EXISTS` and runs as one transaction.** Applied over an old schema
  it exits 3 instead of skipping; anyone who applied the old file must reset first.
- **The loader's `--database` flag**, needed because `read_env()` ignores shell variables and
  verification had to hit scratch databases.
- **The holiday file reduced to SYSTEM_DESIGN 3.2's three rows.** Among the rows removed,
  `All Saints Day` marked 1 Nov as a holiday.

Open:
- SYSTEM_DESIGN 5.5 types `fact_event.user_session` as `uuid` but
  `fact_session_funnel.user_session` as `text`.
- `funnel_daily` has no session count for contract §4 (Dat, BR2).
- `rfm_cell` is in the BR4 response but is not an `rfm_segments` gold column (Khang).
- `.claude/skills/br-slice/SKILL.md` §3 still describes the envelope from before the contract.
- Who loads Postgres: SYSTEM_DESIGN 5.6 step 6 and 8 step 3 say `batch_warehouse.py`; 10 says
  `load_star_postgres.py` reads the Parquet star. Section 11 now lists both scripts. To be
  reconciled in Dat's Spark skeleton PR.
- Against a schema built from the old DDL, the loader ends in a raw psycopg2 traceback
  (exit 1, no OK line) instead of a message pointing at the reset.
- The loader's missing-seed hint still says `git add seed/holidays_2019.csv`, which does not
  help a teammate who lacks the file.
- The move was a plain `mv` followed by edits, not a pure rename commit. Staged, git records
  it as `rename processing/batch_warehouse.py => serving/load_star_postgres.py (59%)`, above
  the 50% default, so `git log --follow` crosses it.
- `CLAUDE.md` "Current status" still says there is no BR code; this PR did not touch it.
  `README.md`'s note that only Dat-TG is a collaborator is stale.
- SYSTEM_DESIGN 5.5 says the loader creates the fact partitions; `warehouse/ddl.sql` creates
  them (31 days + DEFAULT for `fact_event` and `fact_session_funnel`, `wh1..wh5`). Move that
  into 5.5 and drop the `-- not in 5.5` markers in the Spark skeleton PR. Until then, a
  loader that follows 5.5 with a plain `CREATE TABLE … PARTITION OF` fails:
  `ERROR: relation "fact_event_20191101" already exists` (checked on a scratch database).

Carried forward:
- Required approvals on `main` are still 0.
- Whether BR9 was ever promised to the lecturer is still open.
- `SETUP_SPARK.md` steps 1, 7 and 9 still need a first real run by a teammate.
- `serving/apply_schema.py` is still unwritten, so nothing creates the Cassandra keyspace.
- Session 6's open item, that the Postgres loader must create 2019-12-01, is closed:
  `ddl.sql` now creates `fact_event_20191201` and `fact_session_funnel_20191201`.

## Session 9 — 27 September 2026 (W39)

**Tool:** Claude Code (Opus 5.5).
**Scope:** Dat's W39 PR A (branch `w39-warehouse-skeleton`). It adds the `processing/batch_warehouse.py`
skeleton, puts two streaming rules in `processing/schema.py`, makes the six build steps contiguous in README and
SYSTEM_DESIGN 11, and closes the two Session 8 open items assigned to "Dat's Spark skeleton PR". Planned in plan
mode after a read-only survey of the code, the docs and the local data, then done in the working tree. The AI
committed nothing. The changes are staged for Dat, who re-runs the checks, then commits, pushes and merges.
`fact_event` is PR B, after PR #11.

### What the AI produced

| Artefact | Status |
|---|---|
| `processing/batch_warehouse.py` — new. The SYSTEM_DESIGN 5.6 order with one stub per table (each returns None; the two SCD2 steps return `(dim, events)` so the surrogate keys ride on the event rows). `write_dim`/`write_fact` skip None, refuse any path not directly under `data/warehouse/`, and return the table read back. `read_silver` + `check_silver_types` use `EVENT_SCHEMA` as a type yardstick and check the row count before anything is overwritten. `load_postgres` is a stub. Prints `WAREHOUSE OK` only at 9 of 9 tables, otherwise `WAREHOUSE PARTIAL: n of 9 tables built` | Run and verified |
| `processing/schema.py` — two rules for the W40 streaming job in the docstring (never write silver; shift to UTC+7 and recompute `event_date` through `clean()`). Code unchanged | Run and verified (imported by the skeleton) |
| `README.md` — block (c) lists the six steps in order, with `load_star_postgres.py` marked optional until step 6 calls it; (e) is the app only; Status, layout marks, the star-count paragraph, the approvals note | AI-drafted, human review pending |
| `SYSTEM_DESIGN.md` — 5.5 (`ddl.sql` creates the fact partitions), 5.6 step 6 and 8 step 3 (the load goes through `serving/load_star_postgres.py`), 10 (layout: `dim_product.py`, `dim_user.py`, `checks/`, two docs), 11 (the same run order as README) | AI-drafted, human review pending |
| `warehouse/ddl.sql` — comments only: the header, the `fact_event` partition comment copied from 5.5, and a new `fact_inventory_daily` comment. The three `-- not in 5.5` markers are gone | Checked by diff (below). Not re-applied to a database, since no statement changed |
| `serving/load_star_postgres.py` — docstring only: step 6 calls loading functions added here; the small-dim rows stay here and are imported | AI-drafted, Tín's review pending |
| `CLAUDE.md` (Current status, Next task), `.claude/skills/spark-job/SKILL.md` (intro line), `.gitignore` (comment only), `docs/SPARK_GUIDE_VI.md` (schema.py section) | AI-drafted, human review pending |
| `.claude/hooks/session_status.py` — counts `dim_product.py`, `dim_user.py` and `checks/scd2_integrity.py`, the files section 10 now lists | Run and verified: prints `processing 5/9` and `checks/scd2_integrity.py present` |

### How it was checked

Every command ran on Dat's machine (WSL2, Python 3.14.4, Spark 4.1.3, Java 21). The one write went to
`data/warehouse/stg_rfm_snapshot/` and `data/warehouse/dim_user/`, which are gitignored and which `dim_user.py`
rewrites with the same content.

```bash
python -m py_compile processing/schema.py processing/batch_warehouse.py serving/load_star_postgres.py
python processing/batch_warehouse.py        # 9 x "not built yet", WAREHOUSE PARTIAL: 0 of 9 tables built, exit 0
ls -A data/warehouse                        # .gitkeep only, before the write test below
python tests/test_fixtures.py               # All 8 fixture bundles passed validation.
python checks/scd2_integrity.py data/warehouse/dim_user user_id   # SCD2 OK
python processing/dim_user.py                                     # DIM_USER OK
```

| Claim | How it was measured |
|---|---|
| The type guard catches a wrongly typed silver | `check_silver_types` on silver with `user_id` cast to int and `price` to double exits 1: `price: DoubleType() (expected DecimalType(10,2))`, `user_id: IntegerType() (expected LongType())` |
| `write_fact`/`write_dim` work with a real builder, no file edited | `write_fact(build_rfm_snapshot(read_silver(s)), STG_RFM_SNAPSHOT_DIR, "snapshot_date", "user_id")` then `write_dim(build_dim_user(r), DIM_USER_DIR)`, using Khang's merged functions: `stg_rfm_snapshot` 1,291,650 (258,330 users x 5) in 5 directories, `dim_user` 319,426, of which 258,330 current. `dim_user.py`'s own run prints the same 319,426 and `DIM_USER OK`. `.gitkeep` survives |
| `ddl.sql` is still 5.4/5.5 verbatim | The BEGIN..COMMIT body, without `PARTITION OF` statements, diffed line by line against the `sql` blocks of 5.4-5.5: the only hunk is the documented `dim_event_type` INSERT |
| `EVENT_SCHEMA` is declared once | `grep -rn "StructType(\|StructField(" --include=*.py processing ingestion serving checks` finds only `processing/schema.py` |
| The `.gitignore` half of task 4 was already done | `git log` shows the three negations and `.gitkeep` files arrived in `b43222e` (16 Sep). `git check-ignore -v` does not ignore `seed/holidays_2019.csv` or the three `.gitkeep`, and ignores `data/warehouse/fact_event/...parquet` through `data/*/*` |
| Silver facts that PR B depends on | Read-only PySpark over `data/silver` during planning: 4,754,015 rows; `distinct()` gives 4,746,703, so 7,312 exact duplicates; the busiest day is 2019-11-17 with 482,049 rows; 677,255 events (14.2%) have a price different from their product's last price that day |
| Teammates can approve PRs | `gh api repos/Dat-TG/shop-insight/collaborators`: Dat-TG admin; khangbuiquoc203, chuntinne05 and nguyennguyenthiquoc write |

A review workflow (a docs-consistency reader, each finding checked by a second agent told to refute it) and a
separate `spark-reviewer` pass ran before staging. What both found is in the last two bullets below.

### What the AI got wrong, and was corrected on

- **The plan's `write_fact` sorted by `sort_col` alone.** Spark sorts by the partition column before a
  partitioned write and does not keep an order that does not start with it. The code sorts by
  `(partition_col, sort_col)`.
- **The plan's negative-test command set an attribute that does not exist**, and it had the type check inline
  in `read_silver`, where it cannot be tested alone. It became `check_silver_types()`.
- **The planning subagent proposed `WAREHOUSE OK: 0 of 9 tables built`.** An OK line for an empty warehouse
  reads as done. It prints `WAREHOUSE PARTIAL` until all nine are built.
- **The docs review found six defects in the first draft, all fixed.** The README called step 5 "star Parquet"
  and dropped "until step 6 calls it", so it no longer matched SYSTEM_DESIGN 11. That is the wording Session 8
  rejected. `schema.py` said `funnel_daily` is built from silver; it is built from the star. The docstring of
  `load_star_postgres.py` still described the old plan. `ddl.sql` kept a comment 5.5 does not have. Section 10
  and the README layout lacked `dim_user.py`, `checks/` and `docs/BR_SCOPE.md`. The README approvals note was
  stale.
- **`spark-reviewer` found that the wiring comment would crash step 4.** It told owners to import
  `build_dim_product`/`build_dim_user` by name, but the stubs have those names, and a `def` after the import
  rebinds them, so the stub calls itself (TypeError at step 4, RecursionError at step 2) after earlier tables are
  overwritten. The comment now prescribes `import processing.dim_user as user_scd2` and qualified calls. It also
  noted that `fact_inventory_daily`'s docstring invited the banned range join; the docstring now names the
  equi-join route (one row per version per day, joined on `(product_id, snapshot_date)`).
- **The task list said the `.gitignore` negations were missing, and it set `fact_event` at 4,681,493 rows.**
  Both are from before W39: the negations exist since `b43222e`, and 4,681,493 is the old sample. `fact_event`
  is 1:1 with silver, so its target is 4,754,015.

### Judgement that stayed with the team

Dat decided:
- the skeleton ships with stubs only; Dat wires Khang's and Nguyen's functions in PR B, with them as reviewers;
- `event_type_key` comes from `DIM_EVENT_TYPE_ROWS`, imported from `serving/load_star_postgres.py`;
- README lists the six steps in order, plus `load_star_postgres.py` as an optional line after
  `batch_warehouse`.

Made by AI, flagged for review:
- **Who loads Postgres.** `batch_warehouse` step 6 calls loading functions Tín adds to
  `serving/load_star_postgres.py`, passing the tables read back from Parquet. It needs Tín's agreement; if he
  disagrees, 5.6, 8, 10, 11 and the loader docstring change together.
- `WAREHOUSE PARTIAL` exits 0, so the skeleton "runs without error" while tables are missing.
- The approvals note now says the teammates are collaborators. The setting itself is still 0; raising it is
  Dat's call.

Open:
- PLAN.md 212-213: the Wednesday handover trigger (skeleton not in by the W39 checkpoint, so `fact_event` goes
  to Khang) formally fired. Dat keeps `fact_event` and says so in the team post.
- For PR B and the PR #11 review: `dim_product` versions are one per product per day (the DDL's `valid_from
  date` + `UNIQUE (product_id, valid_from)` forces it), so a spot-check of `fact_event.price` against
  `dim_product.price` fails for 14.2% of events by design. `ddl.sql:161` says "AS OF event_time". PR #11's
  `product_sk` is IntegerType where the DDL has bigint.
- Old-sample numbers still in the docs: `fact_event` 4,681,493 (`ddl.sql:155`, SYSTEM_DESIGN 5.2 and 5.5,
  README), `fact_inventory_daily` 1,898,850 (`gen_inventory.py` expects 12,731 products, so 1,909,650), and
  1005115's 46,499 events (47,059 in silver). PR B fixes the first; the others belong to their owners.
- Carried from Session 8: `fact_event.user_session` uuid against `fact_session_funnel.user_session` text;
  `funnel_daily` has no session count for contract §4 (Dat, BR2); `rfm_cell` is in the BR4 response but not in
  `rfm_segments` (Khang); `.claude/skills/br-slice/SKILL.md` §3 describes the old envelope; the loader's raw
  traceback on an old schema and its missing-seed hint.
- Closed here: who loads Postgres (pending Tín, above), the 5.5 fact partitions, `CLAUDE.md` Current status,
  the README collaborator note.

## Session 10 — 28 September 2026 (W40)

**Tool:** Claude Code (Opus 5.5).
**Scope:** Dat's W39 PR B, `fact_event` (task 3), on branch `w39-fact-event` from main `b637b17`, after PR #11
and #12 merged. It wires steps 1 (`dim_event_type`), 2, 3 and 4 of `processing/batch_warehouse.py` to the owners'
modules and fills in `fact_event`. It also adds `check_fact_event()` and the standalone
`checks/fact_event_spot.py`. The Postgres step 6 is untouched. Planned in plan mode, from a read-only research workflow and
a read-only measurement of silver, then done in the working tree. The AI committed nothing. The changes are
staged for Dat, who re-runs the checks, then commits, pushes and opens the PR.

### What the AI produced

| Artefact | Status |
|---|---|
| `processing/batch_warehouse.py` — **step 1:** `build_dim_event_type` = `createDataFrame(DIM_EVENT_TYPE_ROWS)`, cast to the `ddl.sql` types, in its order. **Steps 2-4:** calls into `processing.dim_product as product_scd2` and `processing.dim_user as user_scd2`, `assign_versions` on full silver; the events drop the product's `version_no`. **Step 5:** `build_fact_event`, with `event_sk = date_key * 10^7 + row_number()` per `event_date`, a broadcast join to `dim_event_type` (-1 when unmatched), and casts to bigint. **Checks:** `check_fact_event()`, 20 counts plus 2 lines of information, folded into `checks_ok` with the call first. **Other:** a catalog guard before the first write; the docstrings | Run and verified |
| `checks/fact_event_spot.py` — new. For 5 pinned events it checks (a) fact price = own silver row = pin, (b) `product_sk` → a version of the same `product_id` in force on `event_date`, (c) that version's price = the end-of-day price = pin. Times go through `date_format` only | Run and verified, with negative tests |
| `warehouse/ddl.sql` — comments only: `Measured: 4,754,015 rows`; `product_sk`/`user_sk` "SCD2 version in force on event_date" (was "AS OF event_time"); the header says batch_warehouse "writes" the five `dim_event_type` rows | Checked by diff against SYSTEM_DESIGN 5.5. Not re-applied, since no statement changed |
| `SYSTEM_DESIGN.md` — 5.2 row count, 5.5 (the same three comment edits as `ddl.sql`), the old-sample paragraph (3.1, lines 90-94) now exempts `fact_event`, section 10 lists `checks/fact_event_spot.py` | AI-drafted, human review pending |
| `README.md` — Status date and rows, the star-count paragraph, `(not written yet)` removed for `apply_schema.py` and `gen_catalog.py`, step 5 comment, layout marks | AI-drafted, human review pending |
| `CLAUDE.md` (Current status, Next task), `.claude/agents/data-fact-checker.md` (the example row's number) | AI-drafted, human review pending |
| `.claude/hooks/session_status.py` — `SINGLE_FILES` counts `checks/fact_event_spot.py`, as section 10 now lists it | Run and verified: prints `checks/fact_event_spot.py present` |

### How it was checked

Every command ran on Dat's machine (WSL2, Python 3.14.4, Spark 4.1.3, Java 21). The writes went to
`data/catalog/` and `data/warehouse/` only, both gitignored.

```bash
python ingestion/gen_catalog.py      # products 128,972, distinct product_id 128,972, took 20 s, CATALOG OK
python processing/batch_warehouse.py # dim_event_type 5, dim_product 210,454, stg_rfm_snapshot 1,291,650 (5 dirs),
                                     # dim_user 319,426, fact_event 4,754,015 (31 dirs), 20 check lines at their
                                     # expect, most events in one day 482,049, price != version price 677,255 (14.2%),
                                     # took 71 s, WAREHOUSE PARTIAL: 5 of 9 tables built, exit 0
python checks/scd2_integrity.py data/warehouse/dim_product product_id   # all six counts 0, SCD2 OK
python checks/scd2_integrity.py data/warehouse/dim_user user_id         # all six counts 0, SCD2 OK
python checks/fact_event_spot.py     # 5 rows Y Y Y, FACT_EVENT SPOT OK, exit 0
python tests/test_fixtures.py        # All 8 fixture bundles passed validation.
```

| Claim | How it was measured |
|---|---|
| `event_sk` is the same on all four machines | Read-only PySpark over silver: 4,169 groups tie on `(event_date, event_time, user_session, product_id, event_type)`, and 0 of them differ in any other column. They are exactly the 4,169 exact-duplicate groups (7,312 extra rows, 11,481 rows in all). On the written fact, `event_sk ties that differ` = 0 |
| `max_by(price, event_time)` in `dim_product.py` breaks no tie today | 315 product-days share their last `event_time`, and 0 of them with different price, brand or category. Breaking ties low or high gives the same 210,454 versions and the same 677,255 |
| Silver numbers in the brief | 4,754,015 rows; 31 dates; busiest day 2019-11-17 with 482,049; view/cart/purchase 4,474,579 / 214,286 / 65,150; 258,330 users; 0 date mismatches, 0 `price <= 0`, 0 nulls |
| The five pins | Each `(product_id, event_time)` matches 1 silver row and 1 `(event_time, user_session, event_type)`. Rows 1-3 have 4/4/2 prices that day, rows 4-5 have one. Rows 4-5 were picked by a rule: among that date's single-price product-days whose product has more than one version, the one with the most events, and its first event |
| The numbers written into the docs | The `data-fact-checker` agent, read-only PySpark on `data/warehouse/`: `fact_event` 4,754,015 = silver, 31 directories, all nine types as `ddl.sql` says (`user_session` string); per key 4,474,579 / 214,286 / 65,150 / 0; `dim_product` 210,454 rows, 128,972 products, 30,654 with more than one version; `stg_rfm_snapshot` 1,291,650; `dim_user` 319,426, of which 258,330 current; 677,255 = 14.2%; max position 482,049 on 11-17; 0 duplicate `event_sk` |
| `check_fact_event` can fail | The real function, fed a mutated copy of the written fact. `user_sk` moved to version 1: `user_sk not in force 348,640`, returns False. One price + 0.01: `fact rows not in silver 1`, returns False |
| `fact_event_spot.py` can fail | A wrong pinned version price turns column c to N, `FACT_EVENT SPOT FAILED`, exit 1. A pin at a second with no event exits 1 with "0 silver rows, expected 1. Pin another event." |
| `batch_warehouse.py` imports with Docker down | `import processing.batch_warehouse` pulls in psycopg2 and cassandra-driver through `serving/load_star_postgres.py`, and does not connect |

Review before staging:
- **Planning:** a read-only workflow. Three agents made a docs edit map, a code trace and the measurements. A Plan agent wrote the draft, and two critics reviewed it (`spark-reviewer` and a spec skeptic).
- **After the first run:** a second workflow. `spark-reviewer`, an adversarial reviewer hunting for vacuous checks, and `data-fact-checker` ran, and each serious finding went to a verifier told to refute it.
- **After the fixes:** `spark-reviewer` re-read the changed checks.

### What the AI got wrong, and was corrected on

- **The first `check_fact_event` checked identity on the wrong object.** "Right product" and "right user" ran only
  on the `events` plan, recomputed from silver, not on the fact that was written. The docstring claimed that was
  the only way. The adversarial reviewer showed two mutated facts that pass every count: `user_sk` moved to
  version 1, and `product_sk` moved to another product whose version covers the whole month. The fix adds two checks
  on the files:
  - `user_sk not in force`;
  - `fact rows not in silver`: fact → natural keys through the three dimensions, then `exceptAll` against silver.
    With equal row counts, this is multiset equality.

  Both negative tests above now fail as they should.
- **`checks_ok = checks_ok and check(...)` would skip every later check once one failed**, and the comment told
  owners to copy it. It is now `check(...) and checks_ok`.
- **The spot script said "Pin another event" when the fault was in the fact.** If the pin is unique in silver but
  the fact has 0 or 2 rows for it, it now prints `FACT_EVENT SPOT FAILED` instead.
- **The design draft left pins 4-5 as placeholders.** Its reason was that the measurement subagent had not run:
  plan mode was on, and that subagent read plan mode as a ban on read-only Spark. The main session then ran the same
  script read-only, and the pins are measured values.
- **The draft said a `max_by` tie would still pass the fact-side check "within one run".** Both critics refuted
  that: `product_sk` is a global `row_number`, so a tie resolved differently between the dim write and the fact
  write shifts every later key. It is moot only because the tie count is 0 (above).
- **The `events` rows kept the product's `version_no`.** `spark-reviewer` noted that the first join to `dim_user`
  (W40) would then fail with AMBIGUOUS_REFERENCE. The events now drop it after `build_dim_product` has used it.
- **The docstring said `fact_event` is in `ddl.sql` order.** On disk `event_date` comes last, because it is the
  directory name. The docstring now says so.
- **The brief's line numbers had drifted.** 4,681,493 was at `ddl.sql:153` (not 155), and "AS OF event_time"
  at `ddl.sql:159-160` and SYSTEM_DESIGN 483-484 (not 161-162). Section 10 already listed `dim_product.py` and
  `dim_user.py`, which the old plan wanted to add.

### Judgement that stayed with the team

Dat decided:
- **How the stubs are wired:** import the modules under an alias, and call `assign_versions` on full silver;
- **Sources and scope:** `dim_event_type` from `DIM_EVENT_TYPE_ROWS`; Postgres step 6 stays Tín's stub;
- **fact_event's spec:** the `event_sk` formula and order, keeping the 7,312 duplicates, the check list, and the
  three conditions a/b/c for "the right price at event time";
- **The pins:** the three pinned events with their expected prices;
- **How the PR ends:** Dat keeps `fact_event`, and the PR stops at staging.

Made by AI, flagged for review:
- **Checks beyond the brief's list:**
  - `event_date values` = 31;
  - `date_key wrong`;
  - `event_sk ties that differ`;
  - `product_sk not in force`;
  - `user_sk not in force`;
  - `fact rows not in silver`.

  All six are 0 or 31 today, and each fails the build.
- **`events.drop("version_no")` inside Nguyen's step 2 wiring.** Khang and Nguyen review the wiring.
- **The rule that picked pins 4-5.**
- **The README Status date moved to 2026-09-28 / W40.**

Open:
- **For Nguyen (`dim_product.py`):**
  - `product_sk` is int (DDL bigint), and `version_no` is bigint (DDL integer);
  - `attributes` is a struct, not JSON text, so step 6 needs `to_json` for `jsonb`;
  - the `_SUCCESS` guard in `read_silver_events`;
  - `max_by` has no tie-break: 315 product-days tie on time today, harmlessly.
- **For Tín (step 6), and his confirmation of the Session 9 loader decision:**
  - `fact_event` reads back with `event_date` last;
  - `user_session` is string (DDL uuid);
  - timestamps are written as INT96 (`spark.sql.parquet.outputTimestampType`);
  - collecting `event_time` raw shifts it +7 h.
- **The team post:** Dat keeps `fact_event` (PLAN.md 212-213).
- **Old-sample numbers that belong to other owners, still in the docs:**
  - `dim_product` "127,693 → 244,025" (`ddl.sql:89`, SYSTEM_DESIGN 92/391/592, README:61), measured here as 128,972 → 210,454;
  - `fact_inventory_daily` 1,898,850;
  - 1005115's 46,499 events.
- **Stale since PR #11:** `docs/SETUP_SPARK.md:351` and `docs/SPARK_GUIDE_VI.md:465`, both saying "before that file exists". Also the
  `ai-usage-log` skill still says this file "holds two sessions".
- **`assign_versions` is computed about five times per run:** the count inside `build_dim_product`, the two writes and the
  checks. The run takes 71-74 s. Rule 3: no cache before the W41 numbers.
- **Carried from Session 8:**
  - `fact_event.user_session` uuid against `fact_session_funnel.user_session` text;
  - `funnel_daily` has no session count (Dat, BR2);
  - `rfm_cell` is not in `rfm_segments` (Khang);
  - `br-slice` §3 describes the old envelope;
  - the loader's raw traceback on an old schema and its missing-seed hint.

Closed here:
- `fact_event` 4,681,493;
- "AS OF event_time";
- Session 9's "spot-check fails for 14.2% by design", now definition (c) of the spot check.

## Session 11 — 28-29 September 2026 (W40)

**Tool:** Claude Code (Opus 5.5).
**Scope:** the Part 1 tracker sheet (W38–W42) was checked against the repo and edited in place. `PLAN.md` and
`README.md` were brought in line with it, and three Mermaid diagrams were added to `README.md`. No application code
was written. At Dat's request the AI committed the repo changes on branch `w40-plan-and-readme-diagrams` and opened the
PR. Dat reviews it and merges it.

### What the AI produced

| Artefact | Status |
|---|---|
| Part 1 tracker sheet — 89 cells in 54 rows (descriptions, gates, notes and 12 statuses). A new row 66 for Tín (W40, 0.50 h): step 6 of `batch_warehouse.py`, plus the flat silver table the benchmark needs. The hours column rewritten as numbers | Written in place through the Google Sheets connector, then read back and compared (below). Wording: human review pending |
| `PLAN.md` — two moves, and nobody's total changes. The replayer goes to Dat: the W40 streaming-foundation row goes from 1.00 to 1.25 h, paid by the W41 Spark-memory row (0.25 → 0 h, done since W38). Step 6 and the flat table become Tín's W40 row (0.50 h), paid by the W40 benchmark-harness row (1.00 → 0.50 h). The owner table, week table and totals line follow, with a new "Sửa ngày 28/9" paragraph | AI-drafted, approved by Dat. Tín's confirmation pending |
| `README.md` — the replayer's run line names Dat. Under Architecture, the ASCII drawing becomes a Mermaid flowchart, and a new "The star schema" subsection holds a Mermaid ER diagram. Under Getting started (d), a sequence diagram shows the stream's start order | AI-drafted, rendered and checked (below). Human review pending |
| `docs/AI_USAGE.md` — this session | AI-drafted |

### How it was checked

The tracker:
- **Audit.** A workflow compared every Part 1 row with the repo. 7 auditors and 7 adversarial verifiers, told to
  refute the findings, left 119 findings standing.
- **Edits.** 5 drafters wrote the cell edits, and 5 checkers plus 1 consistency critic reviewed them. A script applied
  them to a local copy and refused any replacement that did not match exactly once: 0 errors.
- **Writing.** The new row was inserted inside the sheet's Table, which then reaches row 100. Every untouched cell was
  sent as null, so it was not rewritten.
- **Reading back.** A full read of `A1:J` was compared cell by cell with the approved text: 0 mismatches in rows 2–100.
  The header was unchanged, and row 66 is formatted like row 65.
- **Hours and statuses.** Summed per person per week, the sheet's hours equal the `PLAN.md` week table: 64.50 h for
  W38–W42. Statuses: Chưa bắt đầu 60, Xong 35, Đang làm 4.

The week table in `PLAN.md`:

```bash
python3 -c "import re; r=[[float(x) for x in l.strip().strip('|').split('|')[-4:]] for l in open('PLAN.md') if re.match(r'\| W(3[89]|4[0-6]) \|', l)]; print([sum(c) for c in zip(*r)], [sum(h) for h in r], min(map(min, r)), max(map(max, r)))"
# [25.0, 25.0, 25.0, 25.0] [12.5, 15.0, 15.0, 11.75, 10.25, 8.75, 9.75, 8.75, 8.25] 2.0 4.0
```

The diagrams:
- **Which Mermaid GitHub runs.** GitHub's renderer script (`mermaidMarkdown-*.js` on
  `viewscreen.githubusercontent.com`) calls Mermaid 11.17.2. It sets `securityLevel: "antiscript"` and flowchart
  padding 48, and switches to the dark theme when the page is dark.
- **Rendering.** Each `mermaid` block was cut from `README.md` and rendered with `@mermaid-js/mermaid-cli@11`, which is
  the same 11.17.2, under those settings, light and dark. The images were then inspected. Widths: 874, 1,263 and
  1,140 px. The blocks also parse on Mermaid 10.9.8 and 12.0.0.
- **Content.** Every label was checked against SYSTEM_DESIGN sections 1, 4, 5.3–5.6, 6, 7 and 8, against
  `warehouse/ddl.sql`, and against `main()` in `processing/batch_warehouse.py`.

### What the AI got wrong, and was corrected on

- **The first route to the sheet wiped its formatting.** The AI rebuilt the sheet as an `.xlsx`, and Dat imported it
  with "Replace spreadsheet". The import wiped the Google Sheets Table formatting (header colour, stripes, dropdown
  chips), which an `.xlsx` cannot carry. Dat restored the sheet from Version history, and it matched the pre-edit
  export with 0 differences. He then connected the Google Sheets connector, and the edits were redone in place.
- **The first diagram drafts were 1,400–2,200 px wide.** GitHub would have shrunk their text, and Mermaid 11 broke
  long labels in mid-name. They are now 874–1,263 px. The architecture block sets `wrappingWidth: 260` so that no
  table name breaks.
- **The first star-schema layout drew a relation that does not exist.** The `dim_user` → `fact_event` edge ran behind
  `fact_inventory_daily`, so it read as a link between those two tables. Writing some relationships fact-first gives
  four rows and no crossing.
- **A "partition key" note was true for Postgres only.** It sat on `fact_inventory_daily.warehouse_id`, but the
  Parquet copy is partitioned by `snapshot_date` (SYSTEM_DESIGN 5.3; `write_fact` in `batch_warehouse.py`). Both
  columns are now labelled.
- **A fourth diagram, the build order inside `batch_warehouse.py`, rendered as a tangle.** It was dropped. The
  script's docstring and SYSTEM_DESIGN 5.6 already give the order.

### Judgement that stayed with the team

Dat decided:
- **The edits.** Apply every proposed tracker edit as drafted ("Áp luôn đề xuất"), including the hour moves above,
  and make `PLAN.md` and `README.md` follow them.
- **After the failed import.** Restore the sheet, then connect the Sheets connector.
- **The PR.** One PR carries `PLAN.md`, `README.md` and this entry.

Made by AI, flagged for review:
- **Tín's new W40 row was assigned without Tín.** He confirms it or hands it back.
- **Three rows marked Xong are back to Đang làm:**
  - Row 38: `docs/evidence/` holds no DESCRIBE evidence for the five Cassandra tables yet.
  - Rows 43 and 44: their Postgres half is done, but `build_dim_date()` and `build_dim_warehouse()` are still stubs.

  Nguyên and Tín review them.
- **Nguyên's row 58 now covers more for the same 0.75 h.** It adds the BRIN and partial-index plans, and it waits for
  row 66 (step 6).
- **The README diagrams.** Above all, the ASCII architecture drawing was replaced, and the `wrappingWidth` setting was
  added.
- **Hours now display as "0,25".** That comes from the sheet's vi_VN locale. Switching it to English (US) is Dat's call.

Open, written in the sheet as "CẦN CHỐT":
- **Keep or drop `fact_session_funnel`.** The row 28 flag fired. Dat decides in the Wednesday 30/9 post.
- **BR4's source.** Either `dim_user` where `is_current`, or `stg_rfm_snapshot` by snapshot date. Khang asked in PR #10
  on 26/9, and nobody has answered.
- **BR2.** Either change the gold column or change the contract (row 68).
- **BR8's drill-down to single orders.** Neither `order_velocity_alerts` nor API_CONTRACT section 10 carries the
  orders (row 80).
- **Khang's 0.50 h in W41.** It is free, because row 74 was done in W39.

Found in SYSTEM_DESIGN, not fixed here:
- **5.2's ASCII star links `fact_session_funnel` to `dim_product`.** `warehouse/ddl.sql` gives that table no
  `product_sk`, and the README diagram follows the DDL.
- **Section 8, step 5 says each replayer file holds "roughly 2,000 rows".** At `--speed 60`, a 5-second file holds 5
  minutes of events: 4,767,012 / 8,640 ≈ 552 rows on average.

## Session 12 — 29 September 2026 (W40)

**Tool:** Claude Code (Opus 5.5).
**Scope:** the W40 streaming foundation: the replayer, the source reader, and the streaming job with BR1 and three W41
stubs, plus the pattern doc and its Vietnamese twin. It also corrected existing text in eleven files. Dat asked for a
plan first, answered two design questions and approved the plan; the AI then wrote the code and ran it. At first
Docker Desktop was not running, so the Cassandra write path was run against a stand-in that records the CQL. Dat then
ran the test steps, started Docker and asked for a re-test before the commit. The AI re-ran everything
against the live Cassandra, which found two more defects (below), and then committed and opened the PR.

### What the AI produced

| Artefact | Status |
|---|---|
| `ingestion/replayer.py` — reads bronze in `event_time` order and writes one JSON file every 5 s. `--speed` and `--start` (UTC). Spark writes the JSON (`to_json`). Writes are atomic: a hidden `.tmp-` name, then a rename. File names are unique per run | Run and verified (below) |
| `processing/source.py` — `read_events()`: JSON, explicit `EVENT_SCHEMA`, `FAILFAST` | Run and verified |
| `processing/streaming_gold.py` — BR1 → `gmv_by_minute` (1-minute windows, update mode, one UNLOGGED batch per partition key), `TZ=UTC` in the first lines, `--fresh`, a READY line, a two-line log per micro-batch, shuffle partitions 4. `start_br3/5/8` are stubs whose docstrings carry each BR's traps | Run and verified, against a stand-in and then the live Cassandra 4.1.12 |
| `docs/STREAMING_PATTERN.md` (new) and `docs/SPARK_GUIDE_VI.md` Phần 10 (its Vietnamese twin) | AI-drafted, human review pending |
| The "foreachBatch is pickled" wording, corrected in 8 files: `requirements.txt` (comment only, pins unchanged), `SYSTEM_DESIGN.md` 11.1, `README.md`, `PLAN.md`, `docs/SETUP_SPARK.md`, `docs/SPARK_GUIDE_VI.md` bước 5, `.claude/skills/spark-job/SKILL.md`, `.claude/agents/spark-reviewer.md` | AI-drafted, human review pending |
| `SYSTEM_DESIGN.md` §8 step 5 (rows per file, the demo start, 15 Nov) and §11 step 3 (`--fresh`); `README.md` run lines and status tree; `CLAUDE.md` current status and next task; `.claude/skills/streaming-job/SKILL.md` (three new traps) | AI-drafted, human review pending |
| `docs/AI_USAGE.md` — this session | AI-drafted |

### How it was checked

Scratch scripts in the session's scratchpad, not committed. Each one sets `SPARK_CONF_DIR` like every repo script.

| Claim | How it was measured |
|---|---|
| The replayer sends every bronze row exactly once | `python ingestion/replayer.py --speed 100000` printed `6 files, 4,767,012 rows in 39 s` and `REPLAY OK` |
| The JSON hop loses nothing | `spark.read.schema(EVENT_SCHEMA).option("mode", "FAILFAST").json("data/stream_landing")` against bronze's nine columns: 4,767,012 rows on both sides, and `exceptAll` gives 0 in both directions |
| Rows per 5-minute file at `--speed 60` | Bronze grouped by `floor(unix_seconds(event_time) / 300)`: 8,607 of 8,640 slices are non-empty. Min 1, median 511, mean 553.9, p90 861, max 3,078. By UTC hour, from 66 per file (23:00) to 882 (15:00–16:00) |
| Which day to demo | Bronze grouped by `event_date`: 16 Nov has 453,734 rows; 17 Nov has 446,186 rows and 13,076 purchases; 15 Nov has 432,575 rows and 0 purchases |
| `collect()` shifts timestamps by the laptop's zone | On this laptop (+07), `spark.sql("select timestamp'2019-11-17 15:00:00'")` collects as `22:00:00`, and as `15:00:00` after `TZ=UTC` plus `time.tzset()` |
| `foreachBatch` is not pickled in classic mode | Read in pyspark 4.1.3: `pyspark/sql/utils.py:143`, `ForeachBatchFunction`, a py4j callback implementing `PythonForeachBatchFunction` |
| BR1 equals silver | `streaming_gold.main()` ran with `connect_cassandra` replaced by a session that records the CQL rendered by cassandra-driver's own encoder. Replay: 17 Nov, 08:00–08:30 UTC, `--speed 60`. The last value per `(event_date, category_l1, window_start)`, compared with the same minutes computed from `data/silver`: 316 of 316 identical, GMV 136,338.65, 435 orders |
| A restart resumes | The job was stopped with Ctrl-C and restarted without `--fresh`, and the replay continued from 08:30. Batch 7 followed batch 6 with no file re-read. 369 of 369 windows identical to silver, GMV 165,010.95, 505 orders |
| `window_start` is the Vietnam wall clock | In the recorded CQL, `1572591720000` = `2019-11-01T07:02:00Z` for 07:02 in Vietnam |
| The progress count is taken after cleaning | Six landed files, rows against rows passing `price > 0`, a present `user_id` and a present `user_session`: 1,804 → 1,791, 2,011 → 2,007, 1,878 → 1,871, 1,820 → 1,812, 2,097 → 2,087, 2,057 → 2,046. All six equal the progress lines |
| Shuffle partitions | Dry run at Spark's default 200: `triggerExecution` 3.5–4.8 s for 48–68 events, and batch 0's write took 6.7 s. At 4: 1.0–1.7 s for 1,812–2,087 events, and 4.8 s for the first batch after start |
| The project's trap hook | `.claude/hooks/check_python.py` on the three new files: no warning |
| Live Cassandra equals silver | Dat's own run (21:33, 71 files from 08:00 UTC on 17 Nov), then the AI's `--fresh` re-run of 08:00–08:35 UTC. Every `gmv_by_minute` row read back with cassandra-driver and compared with the same minutes from `data/silver`: 3,772 of 3,772 identical, 0 missing, 0 extra, GMV 1,794,180.25, 5,618 orders. The row count stayed 3,772 through the re-run: the upsert is idempotent |
| Live restart | Restart without `--fresh`, replay from 08:35 UTC: batch 8 followed batch 7, no file re-read, and the 3,772 rows were still identical |
| Live micro-batch time | 0.9–1.7 s per batch for 1,791–2,087 events, and 4.8–5.2 s for the first batch after start |
| `connect_cassandra()`'s three outcomes | With `read_env` patched: the right keyspace gives a session; `no_such_ks` exits with "Run python serving/apply_schema.py"; port 9999 exits with "Run docker compose up -d --wait" |

### What the AI got wrong, and was corrected on

- **The plan said "about 550 rows per file" as if that were typical.** 554 is the mean, but the hour decides:
  the first dry run, from 00:00 UTC, gave 32–61 rows per file. The docs now give the spread and a busy `--start`.
- **The first draft kept Spark's default 200 shuffle partitions.** Measured too slow: a batch took longer than the
  5 s trigger, and batch 1 had to take two files at once. The value is now 4, set after the numbers (hard rule 3).
- **The progress log first keyed on `batchId`.** The idle report before the first file carries id 0 with 0 rows, so
  it hid the real batch 0. It now keys on the report's timestamp and skips empty reports.
- **The leftover-files warning tested `any(CHECKPOINT_DIR.iterdir())`.** The tracked `.gitkeep` always satisfies that,
  so the warning could never fire. It now looks for directories only. Caught on review, before the first run.
- **The first log label said "events read".** Spark pushes `clean()`'s row filters into the JSON scan, so the count is
  taken after cleaning. It is relabelled "events after cleaning".
- **The first BR3 stub said to rank inside `write_batch` but did not say to leave update mode.** In update mode the
  micro-batch holds only the changed rows, so the top 20 would silently miss products. The stub and both docs now
  require append mode.
- **The first doc draft called 17 Nov "the busiest day" after measuring that one day only.** Ranking all days shows
  16 Nov has more events and 17 Nov the most purchases, and it turned up 15 Nov with none. The docs are reworded, and
  they now warn about 15 Nov.
- **The first doc draft said BR1's plain upsert "is right for two" of the other tables.** It is right for BR5 and
  BR8 and wrong for BR3.
- **An `rm` of the six test files in `data/stream_landing/` was blocked by `.claude/hooks/guard_data.py`.** It was
  not worked around. The next dry run cleared them through the approved `--fresh` flag.
- **Earlier sessions' text, corrected here:** "cloudpickle serialises every foreachBatch closure" (8 files, listed
  above) is false in classic `local[*]` mode. The pin is unchanged.
- **Found only by the live run: a warning in the log.** `load_balancing_policy` was passed straight to `Cluster()`,
  and cassandra-driver printed a DeprecationWarning at the top of the micro-batch log, which is the Gate 1a
  screenshot. It now goes through an execution profile, and no warning is printed.
- **Found only by the live run: the wrong fix for a missing keyspace.** `connect(keyspace)` raises
  `NoHostAvailable` for a missing keyspace, not `InvalidRequest`. The draft would have told the user to start Docker
  when the fix is `apply_schema.py`. It now connects first and checks `cluster.metadata.keyspaces`.
- **The Gate 1a checklist said the first `window_start` shows 15:xx.** That is true only for a short run: rows come
  newest first. It now says to compare with the "Vietnam" times in the replayer's log.

### Judgement that stayed with the team

Dat decided:
- **The plan, approved as written.** The replayer uses Spark plus `toLocalIterator`, with the `TZ` fix, `--fresh`,
  update mode for BR1 and the 5-second trigger.
- **The pattern doc.** English as the version of record, with a Vietnamese twin in `SPARK_GUIDE_VI.md` Phần 10.
- **Cassandra timestamps.** They hold the Vietnam wall clock, silver's convention, and the API appends `+07:00`.

Made by AI, flagged for review:
- **`spark.sql.shuffle.partitions = 4`.** It is frozen into every checkpoint, and it was measured on 20 cores only.
  The team's 4-core laptops are unmeasured, and the W41 benchmarks may revisit it.
- **BR1 aggregates every event, not only purchases.** A minute with views and no sale gets a `gmv 0` row. The API
  contract allows this.
- **`--fresh` deletes under `data/checkpoints/` and `data/stream_landing/`.** That is the guard hook's territory,
  kept to those two directories.
- **Output-mode advice.** Append for BR3 and BR5, update for BR8. The owners decide.
- **The corrected cloudpickle reason.** It was read from the pyspark source. The PySpark 3.5 segfault itself was not
  reproduced.

Dat also decided: re-test against the live Cassandra before the commit, then commit, push and open the PR.

Pending:
- **Gate 1a screenshots (Dat)**, and the group post (Dat).
- **The three teammates' confirmation** that the pattern doc is enough to write BR3, BR5 and BR8.

Carried forward from Session 11: the §8 step 5 "2,000 rows" is fixed here. Every other open item there is untouched.

## Session 13 — 30 September 2026 (W40)

**Tool:** Claude Code (Opus 5.5).
**Scope:** BR1 end to end: the `category_l1 = 'all'` total row in the stream, `GET /api/br1/realtime` on
Cassandra, the BR1 screen, and the docs that move with them. Dat asked for a plan first, answered two design
questions and approved it; the AI wrote the code and ran all of it against the live stack. Nothing is committed
yet: the work sits uncommitted on branch `w40-br1-slice`.

### What the AI produced

| Artefact | Status |
|---|---|
| `processing/streaming_gold.py` — `ALL_CATEGORIES`; in `start_br1`, `explode(array(category_l1, 'all'))` before the `groupBy`, so every window also gets an `all` total row; comments and docstring numbers updated | Run and verified (below) |
| `serving/api/cassandra.py` (new) — `session()`, cached, connected on the first request; the one session every Cassandra router imports | Run and verified |
| `serving/api/main.py` — an exception handler: `NoHostAvailable` / `OperationTimedOut` become HTTP 503 with the command to run | Run and verified |
| `serving/api/routers/br1.py` — replaces the placeholder: one prepared `SELECT ... LIMIT 120` on `(event_date, category_l1)`, rows trimmed to 120 minutes before the newest, `+07:00` appended, `meta` `Cassandra / 1 partition` | Run and verified |
| `web/src/pages/BR1Page.tsx` — date (default 2019-11-17) and category filters, four cards (GMV, orders, AOV over the last 60 min; vs previous 60 min), GMV line for 60 minutes with empty minutes drawn as 0, 10 s refresh, a table view, the QueryMeta footer; `web/src/index.css` — two small classes | Run and verified (headless screenshots) |
| `serving/api/models.py`, `web/src/types/api.ts` — the `category_l1` description mentions `"all"`; no field change | AI-drafted, human review pending |
| `docs/API_CONTRACT.md` §3 — the `all` partition, up to 120 rows, the default-date note, a measured example | AI-drafted, human review pending |
| `docs/STREAMING_PATTERN.md` and `docs/SPARK_GUIDE_VI.md` Phần 10 — Block 4 (the explode, BR1 only), the per-BR table, the Gate 1a checklist (the `all` SELECT, a third screenshot), `--fresh` after a code change, and the stale-tail warning with `TRUNCATE` | AI-drafted, human review pending |
| `SYSTEM_DESIGN.md` §6 (BR1 key reasoning) and §9 (sketch footer 120 rows); `CLAUDE.md` current status and next task | AI-drafted, human review pending |
| `docs/evidence/gate1a_br1_run.txt` (new) — text copy of the run below | Captured from the run |
| `docs/AI_USAGE.md` — this session | AI-drafted |

### How it was checked

Scratch scripts in the session's scratchpad, not committed. Stack: `docker compose up -d --wait`,
`check_infra.py` INFRA OK, `apply_schema.py` APPLY_SCHEMA OK, `streaming_gold.py --fresh`, then
`replayer.py --speed 60 --start "2019-11-17 08:00:00"`.

| Claim | How it was measured |
|---|---|
| `'all'` cannot collide with a real category | Spark over `data/silver`, `groupBy("category_l1").count()`: 14 values, 13 categories plus `unknown` (1,534,249 rows) |
| 2019-11-17 has the most purchases by Vietnam date | Same read, purchases by `event_date`: 17 Nov 11,736, 16 Nov 4,853, 18 Nov 3,115 |
| `all` = the sum of the 14 category rows = silver | For each closed minute of 17 Nov 15:00–16:40, all 15 partitions read with cassandra-driver, and silver aggregated by `date_trunc('minute', event_time)`: 100 of 100 minutes identical on both comparisons, GMV 443,809.62, 1,397 orders |
| The same holds across a crash | Ctrl-C during batch 69 (offsets written, commit not), restart without `--fresh`: batch 69 re-ran, and batch 70 caught up about 7 files (19,598 events), not the 73 in the landing directory. Minutes 20:20–21:10: 50 of 50 identical on both comparisons, GMV 256,441.32, 840 orders |
| Micro-batch time with the extra row | 0.7–1.7 s per batch for 1,700–3,011 events; each batch writes 12–15 partitions |
| The endpoint reads one partition, fast | `curl 'localhost:8000/api/br1/realtime?event_date=2019-11-17'`: `ms` 4.6–15.8, `partitions` 1, `rows` 115 (the replay at 16:54), then 120 |
| Its edge cases | `event_date=2019-13-40` gives 422; no `event_date` gives 200 and `data: []`. With `docker compose stop cassandra`: 503 on first connect, 503 with a cached session, and 200 again 12 s after `docker compose up -d --wait` |
| The screen moves | `chrome-headless-shell --screenshot` of `/br1`, two page loads at least 15 s apart: the window went from 17:50–18:49 to 18:20–19:19, GMV 321.1K to 348.8K. One page kept open 25 s of virtual time called the API 4 times (StrictMode's double first call in dev, then at 10 s and 20 s) |
| Build and contract | `npm run build`, `npx oxlint` exit 0, `python tests/test_fixtures.py` "All 8 fixture bundles passed validation" |
| Spark review | The `spark-reviewer` agent on the `streaming_gold.py` diff: no defect in the explode (watermark kept, state key schema unchanged, update mode sound). Three wording findings, all applied (below) |

### What the AI got wrong, and was corrected on

- **The planned API answered a Cassandra outage with 503 only at first connect.** `session()` is cached, so after one
  good request a stopped Cassandra raised `NoHostAvailable` from `execute()`: a bare HTTP 500 the screen cannot
  explain. Found by stopping the container. One exception handler in `serving/api/main.py` now covers connect,
  prepare and execute for every Cassandra router.
- **The "updated" indicator inherited the toolbar label style.** It read "UPDATED 5S AGO", then, in monospace,
  "5  s  ago". Seen in the screenshots; it is now a label plus plain text.
- **Three findings from the spark-reviewer, all applied.** `--fresh` was not listed as needed after pulling a change
  to a query's code. "The explode would double their counts" is wrong for BR3, where it would list every product
  twice instead. One comment line was ungrammatical.
- **The first evidence draft said the two screenshots were "about 30 s apart".** That was never measured. It now
  says "at least 15 s apart", which the command guarantees.
- **Found by the run, not fixed: stale tails from earlier replays.** `--fresh` keeps Cassandra rows by design. The
  #15 dry run had replayed 17 Nov up to 20:54, so while this replay was at 20:09, `electronics`' newest row was still
  20:54. A category's chart would stand still until the replay passed it. `all` was unaffected because it is new.
  The docs now say to `TRUNCATE shopinsight.gmv_by_minute` before a demo of a day already replayed. See the open
  question below.
- **Seen once, not diagnosed: a `StackOverflowError` in a Java regex on Ctrl-C.** It came from the stream thread
  while `query.stop()` cancelled a running micro-batch. The job still printed "stopped by Ctrl-C", the restart
  resumed, and the 50-minute check above matched. A second Ctrl-C, while the job was idle, printed nothing.

### Judgement that stayed with the team

Dat decided:
- **"vs previous period" means the last 60 minutes against the 60 before.** So the API returns up to 120 rows from
  one partition, and the text of API_CONTRACT §3 changes (not its fields or parameters).
- **The screen starts on 2019-11-17, and the API default stays as the contract says**: today in Vietnam time, an
  empty 200 on 2019 data.
- **The plan, approved as written.**

Made by AI, flagged for review:
- **The `all` row is made by exploding each event before the aggregation.** It was not a sum in `write_batch`,
  which update mode would make partial, and it was not a second query.
- **Where the shared pieces live.** `serving/api/cassandra.py` and the 503 handler in `main.py` are shared files
  that BR3, BR5, BR6 and BR8 will use.
- **Screen rules.** Empty minutes are drawn as 0. "vs previous" shows "—" until the response spans 110 minutes.
  The category list is hard-coded from the silver measurement above.
- **The `TRUNCATE` advice in the docs**, rather than making `--fresh` truncate the table.

Open questions for the team:
- **Should `--fresh` also empty the Cassandra tables** it feeds (at least `gmv_by_minute`)? This changes the
  behaviour documented for all four streaming BRs.
- **Is the Ctrl-C `StackOverflowError` worth chasing before W41**, or should it be a note in the pattern doc?
- **`web/fixtures/br1-gmv-by-minute.json` (Tin's) mixes four categories in one response.** The live endpoint never
  does. It was left unchanged.

Pending:
- **The Gate 1a screenshots, and the group post (Dat).** Now three shots: log, cqlsh, screen.
- **Review of the docs above, then the commit and the PR (Dat).**
- **Tell the team about the text change to API_CONTRACT §3**, in the PR body.

Carried forward from Session 12: the three teammates' confirmation that the pattern doc is enough to write BR3,
BR5 and BR8; the `spark.sql.shuffle.partitions = 4` measurement on a 4-core laptop.

## Session 14 — 30 September 2026 (W40)

**Tool:** Claude Code (Opus 5.5).
**Scope:** the two open questions from Session 13. Dat asked for a recommendation on each and accepted both:
`--fresh` now empties the four streaming tables, and Ctrl-C stops between micro-batches. The work is on
branch `w40-br1-slice`, still uncommitted.

### What the AI produced

| Artefact | Status |
|---|---|
| `processing/streaming_gold.py` — `STREAMING_TABLES`; `forget_earlier_runs(cassandra)` also runs `TRUNCATE` on the four tables (never `stockout_risk`); `signal.signal(SIGINT, default_int_handler)` after Spark starts; `stop_between_batches()` waits up to `STOP_WAIT_SECONDS` (10) for a running batch before `stop()`; new Ctrl-C messages; docstring | Run and verified (below) |
| `docs/STREAMING_PATTERN.md` and `docs/SPARK_GUIDE_VI.md` Phần 10 — what `--fresh` does and why, the manual `TRUNCATE` advice from Session 13 removed, Ctrl-C behaviour, Block 7, Gate 1a checklist | AI-drafted, human review pending |
| `SYSTEM_DESIGN.md` §11 and `README.md` run lines; `.claude/skills/streaming-job/SKILL.md` §4 (the `--fresh` reset is not BR5's forbidden delete) | AI-drafted, human review pending |
| `docs/AI_USAGE.md` — this session | AI-drafted |

### How it was checked

Scratch harnesses in the session's scratchpad, not committed. `ctrlc_trials.py` starts the job, starts the replayer
(17 Nov from 08:00 UTC, `--speed 60`) after the first READY, and sends SIGINT when a batch is running, meaning its
`offsets` file exists and its `commits` file does not, after a set delay.

| Claim | How it was measured |
|---|---|
| pyspark cancels jobs on Ctrl-C | Read in pyspark 4.1.3: `pyspark/core/context.py:406-415`, a SIGINT handler that calls `cancelAllJobs()` and then raises `KeyboardInterrupt`. The JVM itself ignores SIGINT (`java_gateway.py:97-98`) |
| The error before the fix | 7 trials on the old stop code, SIGINT 0–0.9 s into a batch: 1 `StackOverflowError` (0.5 s in, with a `SPARK_JOB_CANCELLED` line); 4 of 7 logs had ERROR or Exception lines (for example `TorrentBroadcast` when SIGINT came at 0 s) |
| The fix | 6 trials, SIGINT 0.3–0.6 s into a batch (5 of them caught it still running): 0 `StackOverflowError`, 0 cancelled jobs, 0 ERROR or Exception lines. Every batch committed before the stop (offsets = commits). The stop took 0.6–1.6 s, and 6.0 s once when a catch-up batch and the next one both ran. 2 more trials after the review fixes, 0.4 and 0.5 s into a running batch: the same result. 8 of 8 in total |
| A second Ctrl-C quits | `double_ctrlc.py`: two SIGINTs 0.1 s apart, 0.3 s into a batch. Exit after 0.2 s, a Python `KeyboardInterrupt` traceback, no Java error. The cut batch had offsets 31 and commit 30, so it re-runs on restart. `pgrep -af java` found no JVM besides Cassandra's |
| `--fresh` empties the tables | Trial 1 printed `--fresh: removed 1 checkpoint directories and 22 landed files, emptied gmv_by_minute, trending_products, abandoned_carts, order_velocity_alerts` |
| The numbers survive all of it | After the truncate, 6 interrupted restarts and the double Ctrl-C: 17 Nov 15:00–17:00, 120 of 120 minutes where `all` = the sum of the 14 categories = silver. GMV 533,156.27, 1,680 orders |
| `TRUNCATE` cost | About 0.8 s through cqlsh. `nodetool listsnapshots`: 6 `truncated-*` snapshots, 167.35 KiB in total (`auto_snapshot: true`) |
| Hook | `.claude/hooks/check_python.py` on the file: silent. `grep -i "delete[^;]*abandoned_carts"`: no match |
| Spark review | The `spark-reviewer` agent: nothing that breaks the demo or gives wrong numbers; 4 style findings (below) |

### What the AI got wrong, and was corrected on

- **Session 13's first answer to the stale tail was a manual `TRUNCATE` in the docs.** It depended on someone
  remembering, before the rehearsal and the talk. Dat accepted the recommendation to make `--fresh` do it, and the
  manual step is gone from both guides.
- **The first reproduction attempt showed nothing.** SIGINT at the very start of a batch comes before any Spark job
  runs, so there was nothing to cancel: 0 errors in 3 tries (only a `TorrentBroadcast` ERROR). Delaying it 0.3–0.9 s
  into the batch reproduced the `StackOverflowError`. The fix was judged against that timing, not the first one.
- **Four findings from the spark-reviewer, all applied in code.**
  - The query starts sat outside the `try`: a W41 `start_brN` that raises would skip the clean stop.
  - "Ctrl-C stops between two micro-batches" overstated it. The wait is bounded at 10 s, and "1–2 s per batch" was
    measured with BR1 alone.
  - The BR5 stub's "NEVER delete" did not say "inside `write_batch`", while the new comment relied on that.
  - The comment made the error sound constant; it now gives 1 of 7.
- **The reviewer also proposed matching `truncate` in `.claude/hooks/check_python.py`.** It was not applied: a
  hook is harness configuration, and that is Dat's call (below).

### Judgement that stayed with the team

Dat decided:
- **`--fresh` empties the four streaming tables** (not `stockout_risk`). This changes behaviour documented for BR3,
  BR5 and BR8, so the team should hear about it in the PR body.
- **Fix the Ctrl-C error, with a 30-minute budget.** It took one line to restore Python's Ctrl-C handler plus a wait
  before `stop()`, so the fallback (a note in the docs) was not needed.

Made by AI, flagged for review:
- **`STOP_WAIT_SECONDS = 10`, shared by all queries.** With four queries in one JVM a batch may outlast the 5 s
  trigger and the wait can run out. The cut batch then re-runs on restart. Re-measure in W41.
- **Restoring `signal.default_int_handler` overrides pyspark's handler.** A Ctrl-C no longer cancels a long Spark
  job at once; the wait covers that, and a second Ctrl-C quits immediately.

Open for Dat:
- **Should `.claude/hooks/check_python.py:141` also warn on `truncate ... abandoned_carts`?** A `TRUNCATE` inside
  `write_batch` would erase every day, not just today, and the hook would stay silent.

Pending, carried forward from Session 13: the Gate 1a screenshots and group post (Dat); review, commit and PR (Dat),
with the API_CONTRACT §3 text change and the `--fresh` change named in the PR body; the three teammates'
confirmation of the pattern doc; the 4-core measurement of `spark.sql.shuffle.partitions = 4`. Session 13's two open
questions about `--fresh` and the `StackOverflowError` are closed here. Its fixture question is unchanged.

## Session 15 — 30 September 2026 (W40)

**Tool:** Claude Code (Opus 5.5).
**Scope:** closes Session 14's open question. Dat asked for the hook to warn on a `TRUNCATE` of `abandoned_carts`
as well as a `DELETE`. Uncommitted, on branch `w40-br1-slice`.

### What the AI produced

| Artefact | Status |
|---|---|
| `.claude/hooks/check_python.py` — the `abandoned_carts` check now matches `(delete\|truncate)[^;\n]*abandoned_carts`; the message names the one legitimate reset (`--fresh`) | Run and verified |
| `.claude/README.md`, `.claude/skills/streaming-job/SKILL.md` §4, `docs/STREAMING_PATTERN.md`, `docs/SPARK_GUIDE_VI.md` — the one-line descriptions of that check | AI-drafted, human review pending |

### How it was checked

| Claim | How it was measured |
|---|---|
| It fires on the new case and still on the old | The hook fed a PostToolUse payload, with `CLAUDE_PROJECT_DIR` pointed at a scratch copy. It warns on `"TRUNCATE abandoned_carts"`, `"truncate table shopinsight.abandoned_carts"` and `"DELETE FROM abandoned_carts WHERE event_date = ?"` |
| It does not fire on correct code | Silent on a file that says "never truncate abandoned_carts" only in a docstring and a comment, and silent on the real `processing/streaming_gold.py` (the `--fresh` `TRUNCATE` names tables through `STREAMING_TABLES`) |
| No other file starts warning | `grep -rn -i -E "truncate[^;]*abandoned_carts" --include=*.py` over the repo, hooks excluded: no match |

### What the AI got wrong, and was corrected on

No defect was found in this change. What could have found one: the five payload tests above, including the real
job file that legitimately empties the table. When the edit was saved, the hook also ran on its own file and
printed four warnings: `spark.executor.memory`, silver, the Cassandra connector and banned imports. That comes
from the hook's own string literals, which contain the patterns. The hook's docstring already names this edge.
The warnings predate this change and do not involve the `abandoned_carts` check.

### Judgement that stayed with the team

Dat decided: extend the hook (Session 14's open question, now closed).

## Session 16 — 24 September – 1 October 2026 (W39–W40)

**Tool:** Claude Code (Opus 5.5).
**Scope:** Khang's own work, planned with GitHub spec-kit in a folder outside the repo, in
three parts:
- Bringing Khang's machine to the team baseline: WSL2 Ubuntu 26.04, Spark, and
  `load_bronze.py` and `batch_silver.py` at `BRONZE OK` and `SILVER OK`.
- The W38–W39 deliverables, merged as PR #10 (`8a3ce31`).
- The W40 work in this change set: report sections 1, 2, 3 and 4.1, and BR4 end to end.

The W40 part was drafted on 27 September and re-checked three times against `main`: on
28 September at `2d385bc`, after PRs #11, #12 and #13 merged; on 30 September at `873140f`,
after #14 and #15; and on 1 October at `3286057`, after #16. The AI ran no git command that
writes. Khang
reviews every change and runs every git command himself.

### What the AI produced

| Artefact | Status |
|---|---|
| `processing/dim_user.py` — weekly RFM snapshots (7, 14, 21, 28, 30 Nov) into `stg_rfm_snapshot`; `dim_user` SCD2 per SYSTEM_DESIGN 5.4 with `version_no`, `user_sk = user_id * 10 + version_no`, an exclusive `valid_to`, and a new segment valid from the day after its snapshot; `with_user_sk()`, which keys the events by an equi-join on (`user_id`, snapshot) | Run and verified; merged in PR #10 |
| `checks/scd2_integrity.py` — overlaps, gaps, empty ranges, keys without exactly one current row, `is_current` disagreeing with `valid_to`, nulls. Reusable for `dim_product` | Run and verified, including on a deliberately broken dimension; merged in PR #10 |
| `ingestion/gen_inventory.py` — daily stock for the 12,731 purchased SKUs × 5 warehouses × 30 days, as a running balance of real purchases | Run and verified; merged in PR #10 |
| `docs/BR_SCOPE.md` — the eight BRs and their done criteria | Human-reviewed; merged in PR #10 |
| `docs/REPORT.md` — sections 1, 2, 3 and 4.1 in Vietnamese, each ending in a table of the commands behind its numbers | AI-drafted, every command re-run on 27 Sep, sections 3.3 and 4.1 re-checked against `main` on 28 Sep, and sections 2.1, 3.1 and 3.2 corrected on 1 Oct; human review pending |
| `processing/batch_gold.py` — the BR4 part. It runs the tracker's one-current-row query on `dim_user`, stops without writing if the count is not 0, then projects `dim_user WHERE is_current` into `data/gold/rfm_segments/snapshot_date=2019-11-30/`. With no `dim_user` it exits and names `batch_warehouse.py`, which builds it | Run and verified |
| `serving/api/routers/br4.py` — DuckDB over the one partition directory; `rfm_cell` built from the three scores; `warehouse="Parquet"`; a malformed or missing date returns `data=[]` | Run and verified |
| `requirements.txt` — `duckdb==1.5.5` | Run and verified: clean install, `pip check` |
| `web/src/pages/BR4Page.tsx` and a heatmap block appended to `web/src/index.css` | Run and verified: `npm run build` (`tsc -b`) and `oxlint` pass with 0 warnings, and the page is served by Vite against the live API. Khang checked the screen in the browser on 28 Sep |
| `docs/BR_SCOPE.md` — BR4 row aligned with the team documents (source `dim_user` current rows) | Human review pending |
| `README.md` — the status lines this change makes false: the Status block (BR4 on real data, `batch_gold.py`), the step 6 comment under Getting started, and the layout marks for `batch_gold.py`, `web/` and `api/`. The same lines now also name BR1 on real data, which #16 made true without changing them. Also the `fact_inventory_daily` estimate under the star row counts: 1,909,650 on Spark's sample | AI-drafted, human review pending |
| `SYSTEM_DESIGN.md` 5.5 — `fact_inventory_daily` at 12,731 purchased SKUs and 1,909,650 rows (was 12,659 and 1,898,850, from the earlier sample), with the figures derived from them. 3.1 — the old-sample paragraph now exempts the inventory universe, as it exempts `fact_event` | Checked against `gen_inventory.py` and silver (below); human review pending |
| PR descriptions and notes to the team, drafted outside the repo | AI-drafted; Khang posts them |

### How it was checked

Every command ran on Khang's machine (WSL2, 12 cores, 15 GB). The second block is the
re-check on 28 September, in the order README's Getting started gives.

```bash
python processing/dim_user.py                                  # DIM_USER OK
python ingestion/gen_inventory.py                              # INVENTORY OK

python ingestion/gen_catalog.py                                # products 128,972, CATALOG OK
python processing/batch_warehouse.py                           # dim_user 319,426, all 20 checks at their expect,
                                                               # WAREHOUSE PARTIAL: 5 of 9 tables built
python checks/scd2_integrity.py data/warehouse/dim_user user_id  # SCD2 OK
python processing/batch_gold.py                                # twice: RFM_SEGMENTS OK, GOLD OK
python tests/test_fixtures.py                                  # All 8 fixture bundles passed validation
uvicorn serving.api.main:app --port 8000                       # then curl every example in the BR4 contract
cd web && npm ci && npm run build && npx oxlint src/pages/BR4Page.tsx   # tsc -b passes; 0 warnings, 0 errors
```

On 30 September at `873140f`, and again on 1 October at `3286057`, `pip install -r
requirements.txt` and `pip check`, `batch_gold.py`, `test_fixtures.py`, the BR4 curl checks,
the heatmap timing and the web build were run again. Every result matched, and the gold
checksum was unchanged.

The Vite chunk-size warning (676 kB) predates this change: a build of `main` alone at
`3286057` gives 667 kB and the same warning. BR4 adds about 8 kB and no dependency.

| Claim | How it was measured |
|---|---|
| `dim_user` is sound | `dim_user.py`: 1,291,650 snapshot rows, 319,426 versions, 258,330 current; 0 events without a `user_sk` or on the wrong version; `scd2_integrity.py` 0 on every check. The `dim_user` that `batch_warehouse.py` writes gives the same counts and `SCD2 OK` |
| Inventory is a running balance of real purchases | Stock equals yesterday plus received minus sold on every row (0 broken); units sold per product, warehouse and day equal the silver purchases; 10.6% of pairs below reorder on 30 Nov |
| The BR4 gold is deterministic | Two runs print identical lines and give the same checksum over all eight columns (`129134856866586`), both on the `dim_user` that `dim_user.py` wrote and on the one `batch_warehouse.py` wrote on 28 Sep |
| The BR4 gold refuses a bad input | A scratch `dim_user` with 3 extra current rows: the run prints 3, exits without writing, and a sentinel file in the output directory survives. With `data/warehouse/dim_user` moved away, it exits 1 and names `batch_warehouse.py` |
| The BR4 API follows contract section 6 | curl: cell (5,5) returns 2,228 rows, all `r=5, f=5`, sorted by monetary; `no_purchase` with `r_score=1` returns 0 rows; `2019-11-07` returns `partitions: 0`; `abc` returns 200 with no rows; `r_score=6` returns 422; an unknown segment returns 0 rows; never-purchased users carry null scores, never 0 |
| The heatmap meets the 2-second target | 20 loads of five parallel `r_score` calls from a Python client on the same machine, on 1 Oct: p50 216 ms, p95 292 ms. The 25 cell lists all match their heatmap counts, and together sum to 31,005 buyers |
| The report's numbers are current | Each command in the report's source tables was re-run on 27 Sep. Brand nulls were counted twice, by `awk` and by Spark, and both give 9,218,235 (13.7%). On 1 Oct DuckDB recounted the raw file and matched `awk` on every figure: 21,898,171 rows without `category_code`, 188,088 zero prices and none negative, 9,218,235 without `brand`, 916,939 purchases. The catalogue count, 128,972, is the `products` line of `gen_catalog.py` |
| The `unknown` category's weight | DuckDB over `data/silver`, purchases grouped by `category_l1`: `unknown` has 16,271 of 65,150 purchases (25.0%) and 2,024,608 of 19,785,531 in revenue (10.2%), second after electronics. The command is in the report's section 3 source table |
| SYSTEM_DESIGN 5.5's inventory figures | `gen_inventory.py` writes 12,731 products and 1,909,650 rows; silver has 128,972 products. So 128,972 × 5 × 30 = 19,345,800, and 116,241 of 128,972 products (90.1%) are never purchased |
| Inventory rows without a `product_sk` | DuckDB over `data/inventory` and the merged `dim_product`: 198,755 of 1,909,650 rows, for 6,910 products, fall before the product's first version. No product is missing from `dim_product` |

### What the AI got wrong, and was corrected on

- **It scored F by value thresholds instead of `ntile(5)`,** departing from the tracker
  without asking. Khang had it reverted. The underlying problem became a question for the
  team: one-time buyers are spread over F1–F4, and 468 of them are champions on 30 Nov.
- **The first `dim_user` used an inclusive `valid_to`.** It was changed to exclusive to match
  SYSTEM_DESIGN and `dim_product`.
- **A review found a look-ahead.** A new segment took effect on the snapshot day itself, so
  that day's earlier events carried a segment earned by a later purchase. Validity now starts
  the day after the snapshot.
- **The first `gen_inventory.py` drew each day's stock independently,** so stock could rise
  with no delivery. The first fix made it a running balance, but it dropped the tracker's
  "about 10% of SKUs below reorder_point" and added a seventh column. Khang asked whether
  the fix still followed the team, and it did not. The final version keeps the tracker's six
  columns and holds about 10% of product-warehouse pairs below reorder as pairs waiting for a
  supplier.
- **`BR_SCOPE.md` collected implementation notes and open questions in chat voice.** It was
  trimmed to the scope table, and the questions moved to the PR.
- **The first PR description spoke about Khang in the third person and ran long.** It was
  rewritten in his voice.
- **A report draft said the brief caps the dataset at 5 million rows.** That cap is the team's
  hard rule 5, not the brief. It was corrected before review.
- **This entry waited for review while PRs #12 to #16 merged.** It was numbered Session 9,
  then 11, then 13, and Dat's entries took each number. Its first draft also listed as open
  README items that #12 and #13 closed. It was renumbered each time, and its open items were
  re-checked against `main`.
- **Four statements went stale when #11, #12 and #13 merged, and the re-check caught them.**
  - `batch_gold.py` told a user with no `dim_user` to run `dim_user.py`. The run order now
    builds `dim_user` in `batch_warehouse.py`, so the message names that script.
  - The report's section 4.1 diagram named `dim_user.py` as its own step. It now names
    `batch_warehouse.py`, which imports both SCD2 modules.
  - Sections 2 and 4.1 said an event carries the product price and segment of its exact
    moment. A version holds at most one day, with the day's closing price, so the text now
    says the version in force on the event's day.
  - Section 3.3 said the catalogue script was still on a branch, and section 3's source table
    took the catalogue count from `batch_silver.py`. The count now comes from `gen_catalog.py`.
- **A review against the team's `pr-review` checklist on 1 October found three report
  sentences that the code or the data contradict.**
  - Section 3.1 said dropping the `unknown` category would cut the executive screen's revenue
    by about a third. That third is the share of events; measured on silver, `unknown` is
    25.0% of purchases and 10.2% of revenue.
  - Section 2.1 said the BR1 screen draws a separate line for `unknown`. The screen built in
    #16 draws one line, with `unknown` as a category in the filter and inside the `all` total.
  - Section 3.2 said all three retail events fall inside the data period. Cyber Monday,
    2 December, falls one day after it, inside `dim_date`'s October to December range.
- **The report outline put the three-level data model in section 5.** That left no place for
  the tracker's section 5, the application and its evidence. Khang moved the model into
  section 4, as his W45 tracker row says.

### Judgement that stayed with the team

Decisions put to Khang and answered by him:
- RFM snapshots are weekly, `dim_user` follows SYSTEM_DESIGN 5.4, and F uses `ntile(5)` as
  the tracker says.
- BR4 gold follows the team documents and projects the current `dim_user` rows into the
  30 Nov partition. This is despite the measured cost: 23,198 of 31,005 buyers then show the
  recency of an earlier snapshot. The heatmap is unaffected, with 0 cells or segments
  differing from the 30 Nov snapshot. This is Khang's answer to the tracker's open question
  on BR4's source (Session 11); the team can still choose `stg_rfm_snapshot` instead.
- The frozen API contract stays unchanged. The heatmap takes its 25 counts from five calls
  by `r_score`, not from a new aggregate endpoint.
- Khang creates `processing/batch_gold.py`, and Tin (BR6) and Nguyen (BR7) add their
  functions to it.
- The report is one Vietnamese file, `docs/REPORT.md`, with the tracker's six sections:
  section 4 holds the architecture, the technologies and the three-level data model,
  section 5 the application and its evidence, and section 6 the evaluation. The tracker's
  W44 row for Dat still calls the data model section 3.
- On 28 September Khang reversed his earlier call to leave README to Dat. README's Status
  block asks each change to fix the lines it makes false, so the BR4 change updates them.
- The `fact_inventory_daily` figures in SYSTEM_DESIGN 5.5, which Sessions 9 and 10 left to
  their owner, are fixed in the report change, and so is SYSTEM_DESIGN 3.1, which listed
  them among the old-sample counts. README repeats them, so its line is fixed in the BR4
  change, the only change that touches README. The brand-null share, the "two days" claim
  and BR9 stay with Dat.
- `dim_user`'s own checks join `checks_ok` in `batch_warehouse.py` in a separate small change
  after the two W40 changes, in Khang's free 0.50 h of W41. Khang says so on #13.

Made by AI, flagged for review:
- SYSTEM_DESIGN 5.5 called the unpurchased products "99.8% dead weight". It is 90%
  (116,241 of 128,972), and it was 90.1% on the earlier sample too.

Open:
- The segment table in `dim_user.py` differs from the BR4 fixture examples: the fixture has
  444 as loyal (champion here) and 111 as at_risk (hibernating here).
- SYSTEM_DESIGN 3.1 gives brand nulls as 14.9%, but the file shows 13.7%. It and README say
  the first 5M rows cover about two days, but row 5,000,000 is 2019-11-04 07:09:03 UTC,
  about three days (Dat).
- SYSTEM_DESIGN 2 still lists BR9 for Merchandising (Dat).
- `fact_inventory_daily` (W40): 198,755 inventory rows fall before their product's first
  `dim_product` version, so they find no `product_sk`. The `build_fact_inventory_daily`
  docstring asks for that case to be decided explicitly.
- `batch_warehouse.py` runs only `check_events` from `dim_user.py` (Khang, above).
- A cell-count endpoint for BR4 would cut the heatmap payload from 5.4 MB to 25 rows. The
  5.4 MB is the sum of `curl -w '%{size_download}'` over the five `r_score` calls, 5,423,848
  bytes on 1 Oct. It needs a contract change, agreed by all.
- The tracker's BR4 row says the gold groups by `rfm_cell` and `segment` with a customer
  count and summed monetary. SYSTEM_DESIGN 7 and API_CONTRACT 6 freeze eight per-customer
  columns, which the screen's customer list needs, and the code follows them (Dat, tracker).
- The tracker's W46 cross-check row gives 21,898,175 events without `category_code`. `awk`
  and DuckDB both count 21,898,171 (Dat, tracker).

Closed here:
- "`rfm_cell` is in the BR4 response but not in `rfm_segments` (Khang)", carried by
  Sessions 8, 9 and 10. The router builds it from the three scores, and the gold keeps the
  contract's eight columns.
- `fact_inventory_daily` 1,898,850 in SYSTEM_DESIGN 5.5 and README, left to its owner by
  Sessions 9 and 10.
- Session 11's question on Khang's free 0.50 h in W41 (above).

## Session 17 — 2 October 2026 (W40)

**Tool:** Claude Code (Opus 5.5).
**Scope:** Dat's review of PR #17 (Session 16's report sections 1, 2, 3 and 4.1 and the
SYSTEM_DESIGN inventory counts), before and after PR #18 merged, and the fixes the review
found, pushed to the PR branch `w40-khang-report` for Dat to review and merge. Then, at Dat's
request, the items Session 16 left to Dat, fixed in the same PR after `main` (#18) was merged
into the branch so that README is current. No application code changed: two Python files
change in a comment and a docstring only. Session 16 is not edited here: this file is
appended to, so its corrections are recorded below.

### What the AI produced

| Artefact | Status |
|---|---|
| The review draft for PR #17 | AI-drafted; not posted, at Dat's request |
| `docs/REPORT.md` 1.1 — the purchase peak is 16–17 Nov (UTC): 17 Nov has 185,195 purchases, about 5.8 times Black Friday's 32,107, which ranks third. Section 1's source table gains the command | Measured (below); human review pending (Dat) |
| `docs/REPORT.md` 2.4 — only customers with a purchase by the snapshot date get R, F and M scores; the others have none and are `no_purchase`. An event carries the segment of its week's snapshot (4.1 gives the 1–7 Nov case) | Checked against `dim_user.py` and API_CONTRACT 6; human review pending (Dat) |
| `docs/REPORT.md` 4.1 — the diagram: the holiday seed goes straight to `batch_warehouse.py`, and `gen_catalog.py` and `gen_inventory.py` sit under processing, reading silver. The text says `batch_warehouse.py` reads the three side sources. The SCD2 bullet separates the product's closing price from the customer's weekly segment | Checked against the scripts and SYSTEM_DESIGN 1; human review pending (Dat) |
| `SYSTEM_DESIGN.md` 5.5 — the inventory universe is the SKUs with a purchase in silver, not in the window: 42 of the 12,731 are bought only on 1 Dec (Vietnam time) | Measured (below); human review pending (Dat) |
| Session 16's items for Dat, plus SYSTEM_DESIGN 3.2 (left open by the first push) and PLAN.md's old-sample purchased-SKU count. Brand nulls 14.9% → 13.7% in SYSTEM_DESIGN 3.1, API_CONTRACT 5, `processing/schema.py` and SPARK_GUIDE_VI. The first 5M rows cover about three days, not two, in SYSTEM_DESIGN 3.1, README, `ingestion/load_bronze.py` and SPARK_GUIDE_VI. BR9 leaves SYSTEM_DESIGN 2. SYSTEM_DESIGN 3.2 no longer calls Black Friday the largest demand signal. PLAN.md's purchased-SKU count moves to 12,731 / 128,972 | Measured (the raw-file, peak and 12,731-SKU rows below); the two `.py` files change in a comment and a docstring only, and `python3 -m py_compile` passes; human review pending (Dat) |

### How it was checked

Every command ran on Dat's machine (WSL2): the first push against `main` at `f15bd40` and
the PR head `bc12fc0`, the second against the branch after `main` was merged in (`889a391`). No Spark job ran. After #18 merged, a Workflow of 17 agents (4 checkers, then one
skeptic per finding, told to refute it) re-read the PR against `main`: 8 findings survived and
5 were refuted. Every number below was then re-measured directly. A second Workflow of 12
agents (3 checkers on the fix diff, then one skeptic per finding) found 9 problems in the
fixes. 7 survived, two of them the same point. All are corrected below; the last, the
contradiction with SYSTEM_DESIGN 3.2, in the second push, with Session 16's items for Dat.
A third Workflow of 15 agents (3 checkers on the second push's diff, then one skeptic per
finding) found 12 problems; 7 survived, 5 of them distinct. Four are fixed. The fifth, the old
12.659 in SPARK_GUIDE_VI's dated W38 changelog (Phần 7), is left as history.

| Claim | How it was measured |
|---|---|
| Purchases per UTC day: 17 Nov 185,195, 16 Nov 68,247, 29 Nov 32,107 (third) | `awk -F, 'NR>1 && $2=="purchase" {d[substr($1,1,10)]++} END {for (k in d) print k, d[k]}' data/raw/2019-Nov.csv \| sort -k2 -n -r \| head -3`, the command added to the report |
| Per Vietnam date on silver, 29 Nov ranks fourth (2,252 purchases), after 17 Nov (11,736), 16 Nov (4,853) and 18 Nov (3,115) | DuckDB: `SELECT event_date, count(*) FROM read_parquet('data/silver/*/*/*.parquet', hive_partitioning = true) WHERE event_type = 'purchase' GROUP BY 1 ORDER BY 2 DESC LIMIT 4` |
| 12,731 SKUs are purchased in silver, 12,689 of them in 1–30 Nov; 42 only on 1 Dec | DuckDB: `min(event_date)` per purchased `product_id` over silver, counted all, `<= 2019-11-30` and `= 2019-12-01` |
| Only customers with a purchase by 30 Nov are scored: 31,005 of 258,330 `rfm_segments` rows have an `r_score`; the 227,325 others are all `no_purchase`, including 112 who bought only on 1 Dec (Vietnam time) | DuckDB over `data/gold/rfm_segments`, joined on `user_id` to each user's first purchase date in silver |
| BR4 gold against `stg_rfm_snapshot` at 30 Nov, buyers only: recency differs for 23,198, frequency and monetary for 590, segment for 0 | DuckDB join of `data/gold/rfm_segments` and `data/warehouse/stg_rfm_snapshot` on `user_id`, `snapshot_date = 2019-11-30` |
| Session 16's report figures hold on `main`: `unknown` is 25.0% of purchases and 10.2% of revenue, 31,005 buyers by 30 Nov, silver 4,754,015 / 258,330 / 128,972 | The DuckDB command in report section 3's source table, run verbatim (25.0%, 10.2%); DuckDB `SELECT count(*), count(DISTINCT user_id), count(DISTINCT product_id)` over silver; DuckDB distinct purchasing `user_id` with `event_date <= 2019-11-30` (31,005). `batch_gold.py`, whose `buyers` line the report cites, was read but not run |
| Session 16's raw-file figures for Dat: 21,898,171 rows without `category_code`, 9,218,235 without `brand`, row 5,000,000 at 2019-11-04 07:09:03 UTC | The `awk` commands in report section 3's source table |

### What the AI got wrong, and was corrected on

- **A rewrite of report 4.1 said `batch_warehouse.py` is the only reader of the three side
  sources.** `serving/load_star_postgres.py` also reads `seed/holidays_2019.csv`, so the
  sentence now says only that `batch_warehouse.py` reads them directly.
- **The first review draft listed three report numbers as unverifiable** because DuckDB was not
  installed. Once #18 brought it in, two of them were measured and both hold; only the 10.6%
  below reorder is left, because `data/inventory` is empty on this machine.
- **The first review draft asked whether #18 should merge before #17.** #18 merged first, so
  the question became a request to correct Session 16 instead. That correction is made here,
  not in Session 16, because this file is append-only.
- **The first draft carried a nit on report 2.1** ("cộng vào doanh thu của mọi ngành"). It was
  the weakest point, and it was dropped.
- **The first fix of report 2.4 tied the scores to having bought at all.** 112 customers bought
  only on 1 Dec (Vietnam time), after the last snapshot, and have no score. The sentences now
  count purchases up to the snapshot date.
- **The first fix of report 2.4 said every event carries the latest snapshot before its day.**
  Events of 1–7 Nov carry the 7 Nov snapshot, as the fixed 4.1 bullet says, so 2.4 now names
  the event's weekly snapshot and leaves the detail to 4.1.
- **This session's first draft overstated three things about Session 16.** It said all of
  #18's rows were "human review pending", when only two were. It listed Session 16's open items
  for Dat without the tracker's BR4 row. It cited `batch_gold.py` for 31,005, although no Spark
  job ran. All three are corrected above.

### Judgement that stayed with the team

Decisions put to Dat and answered by him:
- No review comment is posted. The fixes are pushed to `w40-khang-report`, and Dat reviews and
  merges them himself. An attempt to fix and merge in one step was refused by Claude Code's
  auto-mode classifier ("Merge Without Review"), and Dat chose this path after it.
- The items Session 16 left to Dat are fixed in this PR, not in a separate one.

Made by AI, flagged for review:
- The fix scope. Left out: the tracker's items (outside the repo), `gen_inventory.py`'s window
  (Khang), and BR9's other mentions in SYSTEM_DESIGN. Sections 1, 5.2, 5.4, 8, 9 and 13 still
  describe BR9 as a bonus screen, and 5.4 cites it for the GIN operator class, so removing them
  is a team decision.
- Session 16's 90% figure in SYSTEM_DESIGN 5.5 (116,241 of 128,972), carried forward. Its
  arithmetic was re-checked here; Dat's review of this push decides it.

Corrections to Session 16:
- Its scope line puts "BR4 end to end" in "this change set". BR4 merged separately as PR #18
  (`f15bd40`) on 2 October. The rows for `batch_gold.py`, `br4.py`, `requirements.txt`,
  `BR4Page.tsx` and `index.css`, the `BR_SCOPE.md` BR4 row and `README.md` landed there. The
  "human review pending" statuses on the `BR_SCOPE.md` and `README.md` rows were written before
  that merge; the other four rows were already run and verified.
- Its BR4 decision gives the cost of projecting the current `dim_user` rows as 23,198 buyers
  with an earlier recency. 590 buyers also show an earlier frequency and monetary, which the
  cell list displays (`BR4Page.tsx`) and sorts by (`br4.py`, `ORDER BY monetary DESC`). The
  choice between `dim_user` and `stg_rfm_snapshot` stays with Khang.

Open:
- The tracker: its BR4 row (Session 16), its W46 count of 21,898,175 rows without
  `category_code` (the file has 21,898,171), and its W44 row, which puts the three-level data
  model in section 3 when the report has it in section 4 (Dat, tracker).
- `gen_inventory.py` builds its SKU universe from all of silver. Limiting it to 1–30 Nov would
  give 12,689 SKUs and 1,903,350 rows, and would change its `EXPECTED_PRODUCTS` (Khang).
- The 10.6% of pairs below reorder on 30 Nov was not re-measured: `data/inventory` is empty on
  Dat's machine.

Closed here:
- Session 16's open items for Dat that live in the repo: the brand-null share, the "two days"
  claim, and BR9 in SYSTEM_DESIGN 2.
- SYSTEM_DESIGN 3.2's Black Friday claim, which this session's first push left open.
- PLAN.md's purchased-SKU count, 12,659 / 127,693 from the earlier sample, now 12,731 / 128,972.

## Session 18 — 3 October 2026 (W40)

**Tool:** Claude Code (Opus 5.5).
**Scope:** Dat's W40 task, `fact_session_funnel`, the accumulating snapshot. In
`processing/batch_warehouse.py`: the body of `build_fact_session_funnel(events)` (signature
kept), a new `check_fact_session_funnel()` folded into `checks_ok`, and the docstring. Plus
the doc lines the new table makes false. Planned in plan mode first, then built on branch
`w40-fact-session-funnel`. Postgres is not loaded here: that goes through Tin's step 6.

### What the AI produced

| Artefact | Status |
|---|---|
| `processing/batch_warehouse.py` — `build_fact_session_funnel()`: one `groupBy("user_session")`, `user_sk`/`user_id`/`event_date` from the first event (min of a struct), milestones, signed lags, counts, values, `funnel_stage` from the counts, `is_abandoned` | Run and verified (three full runs, below); human review pending (Dat) |
| `processing/batch_warehouse.py` — `check_fact_session_funnel()` (12 checked lines, 3 information lines) and its line in `main()` | Run and verified, including five mutations that make it fail; human review pending (Dat) |
| `processing/batch_warehouse.py` module docstring — the "Today it prints" block, pasted from the third run | Run output; human review pending (Dat) |
| `SYSTEM_DESIGN.md` 5.2 table, 5.5 DDL comment, section 8 and the old-sample paragraph; `warehouse/ddl.sql` (Tin's file, mirrors 5.5); `.claude/skills/spark-job/SKILL.md` — 954,686 → 970,797 | Measured (below); human review pending (Dat; Tin for `ddl.sql`) |
| `README.md` and `CLAUDE.md` status lines — 6 of 9 tables, `fact_session_funnel` no longer a stub; README date line | Checked against the run; human review pending (Dat) |
| `docs/REPORT.md` 4.1 — the full-recompute sentence Dat asked for, reworded to read naturally, with the milestone clause the reason needs | Human review pending (Khang, report owner) |
| Drafts, not posted: the PR description, a message to Tin, a note to Nguyen and Khang, the group post | AI-drafted; Dat sends them |

### How it was checked

Everything ran on Dat's machine (WSL2), branch `w40-fact-session-funnel` off `main` `9d964d0`.
Before any code was written, a read-only prototype ran the drafted body in memory. Two
independent rebuilds matched it row for row (`exceptAll` 0 both ways): Spark SQL with window
functions, and DuckDB over silver plus `dim_user`. Then `python processing/batch_warehouse.py`
ran three times (59, 58 and 59 s). Each run printed `WAREHOUSE PARTIAL: 6 of 9 tables built`
with every check line at its expect. The table's fingerprint was the same after every run:
`.venv/bin/python -c "import duckdb; print(duckdb.sql(\"select count(*), bit_xor(hash(t)) from read_parquet('data/warehouse/fact_session_funnel/**/*.parquet', hive_partitioning=true) t\").fetchone())"`
gave `(970797, 2197298498416271562)`. Three Workflows of 3 agents each did the work: one to
understand, one to review the plan (prototype, spark-reviewer, completeness critic) and one to
review the diff (spark-reviewer, data-fact-checker, docs sweep). `python tests/test_fixtures.py`
passes.

| Claim | How it was measured |
|---|---|
| 970,797 rows, one per distinct silver `user_session` (old sample: 954,686) | The check's first line; DuckDB `select count(distinct user_session) from read_parquet('data/silver/**/*.parquet', hive_partitioning=true)` |
| `funnel_stage` 1 / 2 / 3: 838,795 / 77,098 / 54,904, no stage 0; `is_abandoned` 77,098; negative lags 521 (view→cart) and 448 (cart→purchase) | The check's information lines; DuckDB `select funnel_stage, count(*) from read_parquet('data/warehouse/fact_session_funnel/**/*.parquet', hive_partitioning=true) group by 1` |
| Measure totals equal silver: view 4,474,579, cart 214,286, purchase 65,150 events; cart value 62,570,985.31, purchase value 19,785,531.43 | The check's five total lines, against `silver.agg(...)` in the same function |
| The check can fail. `funnel_stage = 1` → `ck_fsf_stage violated` 132,002. `coalesce(view_to_cart_sec, 0)` → `ck_fsf_lags violated` 848,073. `user_sk + 1` → `user_sk not in force` 970,797. `purchase_count = cart_count` → 214,286 against 65,150. `purchase_value = cart_value` → 62,570,985.31 against 19,785,531.43 | `bw.check_fact_session_funnel()` on mutated in-memory copies of the table read back from disk; nothing written. Each mutation fails exactly its own line |
| `is_abandoned` and BR5's 30-minute rule disagree on 498 sessions, 0.6% of the 77,098 abandoned ones. 1 has a cart in the last 30 minutes of data; 497 bought, but only more than 30 minutes after the first cart, or only before it | DuckDB over silver: per session the first cart and first purchase, and the purchases in `[first_cart_at, first_cart_at + 30 min]`; data ends at `max(event_time)` = 2019-12-01 06:59:49 |
| 31 `session_start_date` directories, matching `ddl.sql`'s 31 day partitions | `write_fact`'s own line |

### What the AI got wrong, and was corrected on

- **The first plan shared one `funnel_stage()` helper between the build and the check.** The
  `ck_fsf_stage` line would have compared an expression with itself and could never fail
  (spark-reviewer and the critic, plan review). The build now derives the stage from the counts
  and the check uses `ddl.sql`'s CASE on the timestamps; the `funnel_stage = 1` mutation shows
  it failing.
- **The first plan took `session_start_date` from `to_date(session_start_at)`,** so "session_start_date
  wrong" re-ran the build's own expression. The date now comes from silver's `event_date` on
  the first event, the date step 4 used to pick `user_sk`.
- **The first plan's `user_sk` check did not compare `user_id`,** so a `user_sk` belonging to
  another user would have passed. Added.
- **The first version of the check compared only the row count with silver.** A wrong measure,
  for example `purchase_count` counted from carts, printed every line at its expect
  (spark-reviewer, diff review). Five total lines against silver were added, and two mutations
  show them failing.
- **The first docstring said "one shuffle, no join".** That is true of the function's code, but
  `events` is a plan: writing the table re-runs steps 2-4, `with_user_sk`'s broadcast join
  included. Reworded.
- **The first docstring put BR5's difference at "a few hundred sessions, about 0.6%"** without
  saying 0.6% of what. Measured: 498, of the 77,098 abandoned sessions.
- **The first `REPORT.md` sentence** parsed "mỗi lần chạy bảng này" as one phrase and made
  Parquet the subject of "cập nhật". Reworded.
- **The first plan missed six stale status lines:** README.md's date line, :17, :164-165, :299
  and :391, and CLAUDE.md's second status paragraph (completeness critic).

### Judgement that stayed with the team

Given by Dat in the task: the grain, the columns, `session_sk = xxhash64(user_session)`,
`user_sk` from the session's first event with no join, the load through step 6, the check
counting `ck_fsf_stage` and `ck_fsf_lags`, and the report sentence.

Decisions put to Dat and answered by him (3 October, in plan mode):
- Lags are kept signed (521 + 448 negative), not clamped to 0.
- `is_abandoned` = a cart and no purchase in the session, not BR5's 30-minute rule.
- Tin fixes his own loader. This change does not touch `serving/load_star_postgres.py`.
- Every doc line the table makes false is fixed in the same change.

Made by AI, flagged for review:
- `purchase_at` is the **first** purchase (7,138 sessions buy more than once).
- `cart_value` sums cart prices and ignores `remove_from_cart` (0 rows in the source).
- The check's size: the task asked for the two CHECK counts. The other ten lines catch NOT
  NULL, the primary key, the date, `user_sk` and the measures, each shown able to fail.
- The `REPORT.md` wording (Khang owns the report) and the `ddl.sql` comment (Tin's file).

Open:
- Tin's `load_fact_session_funnel` on `origin/w40-tin-br6` (no PR yet). Its INSERT leaves out
  `last_event_at` and `purchase_value`, both NOT NULL. Its five timestamps are not cast to
  `timestamp_ntz`, so they would land 7 h late. Loading and checking this table in Postgres
  waits on it (Tin).
- BR2's `funnel_daily` needs `category_l1`, and this table has no product or category column
  (Dat, W41).
- The `is_abandoned` difference from BR5 goes to Nguyen (BR5) and Khang (correctness gate).
- Not caused by this change: `serving/load_star_postgres.py:4` says no Parquet star exists;
  CLAUDE.md says only BR1 serves real data (BR4 does too); SYSTEM_DESIGN 5.2 lists BR5 as served
  by this table.
- The group post of 970,797 (Dat).

Closed here:
- Session 11's "Keep or drop `fact_session_funnel`" (row 28): kept. Dat decided by assigning
  this build.

## Session 19 — 1-3 October 2026 (W40-W41)

**Tool:** Claude Code (Opus 5.5).
**Scope:** BR3 end to end: `start_br3` in the stream, `GET /api/br3/trending` on Cassandra, the BR3 screen, and
the docs that move with them. Khang asked for the W41 work to start early, chose how the API finds the newest
window, and checked the screen in the browser. The AI wrote the code and ran it against the live stack on Khang's
machine. On branch `w41-khang-br3`, merged with `main` after #17 and #18 (3 October). Merged with `main` again
after #22 (6 October, Dat): the README and AI_USAGE conflicts were resolved with AI help, and this session was
renumbered 18 → 19.

### What the AI produced

| Artefact | Status |
|---|---|
| `processing/streaming_gold.py` — `start_br3`: views and carts per product in 15-minute windows sliding every minute, `outputMode("append")`, top 20 ranked in `write_batch` (`row_number` by `view_count`, `cart_count`, `product_id`), each window deleted then inserted; `TRENDING_TOP`; the module docstring marks BR3 done | Run and verified (below) |
| `serving/api/routers/br3.py` — replaces the placeholder: without `window_start`, `SELECT DISTINCT window_start` and the largest key; then one partition read; `+07:00` appended; `meta` counts every partition key listed plus the one read | Run and verified |
| `web/src/pages/BR3Page.tsx` — top 20 table with up, down and NEW arrows against the window a minute earlier, a Live mode and a window picker, 10 s refresh, four KPI cells, the QueryMeta footer; `web/src/index.css` — a BR3 block and `datetime-local` in one shared selector | Run and verified (Khang, in the browser) |
| `docs/STREAMING_PATTERN.md` and `docs/SPARK_GUIDE_VI.md` Phần 10 — the BR3 row of the group-by table no longer groups by `brand` | Reviewed by Dat in #19, brand counts corrected |
| `README.md` status block, run line and layout marks; `CLAUDE.md` current status | Reviewed by Dat in #19 |
| `docs/evidence/gate1b_br3_run.txt` (new) — text copy of the run below | Captured from the run |
| `docs/AI_USAGE.md` — this session | AI-drafted |

### How it was checked

Scratch scripts in the session's scratchpad, not committed. Stack: `docker compose up -d --wait`, INFRA OK,
APPLY_SCHEMA OK, `streaming_gold.py --fresh`, then `replayer.py --speed 60 --start "2019-11-17 08:00:00"` for
413 s (81 files, 196,024 rows, 15:00-21:45 Vietnam time).

| Claim | How it was measured |
|---|---|
| Grouping by `brand` would list a product twice | DuckDB over `data/silver`: 612 of 128,972 products have more than one brand value: 573 a real brand on some events and `unknown` on others (product 4804718: `apple`, and 49 `unknown` events), 42 two real brands (16600184: `bugati` and `bugatti`), 3 both; 0 products have two `category_l1` |
| Ties at rank 20 need a rule | 17 Nov 15:00-21:00 Vietnam time, 360 windows: #20 and #21 tie on `view_count` in 212, and on `cart_count` too in 64 |
| A window has room for 20 | 43,134 full windows over the month: median 855 products, max 3,767; 193 (0.4%) have fewer than 20, mostly data gaps (5 Nov 07:53-08:07: 1 product) |
| The ranking logic, before Cassandra existed here | A real stream over 36 replayer-style files (17 Nov 15:00-18:00), `write_batch` against a fake table keeping the `(window_start, rank)` rules: each batch closed 5 windows; 155 complete windows, 3,100 of 3,100 rows identical to DuckDB over silver |
| The live table is right | All 394 windows written (14:46-21:19): one per minute, 20 rows each, ranks 1-20, no product twice. The 380 windows from 15:00: 7,600 of 7,600 rows identical to DuckDB over silver |
| The same holds across a crash | Ctrl-C after batch 11 (windows to 15:29), restart without `--fresh`: batch 12 wrote 15:30-15:34, batch 13 caught up 15 windows. No lost or repeated window; the 380 windows above span it |
| The delete must run on its own | A window at 2000-01-01: DELETE, then a batch of 3 INSERTs: 3 rows, twice. DELETE inside the insert batch: 0 rows |
| Micro-batch time with BR1 and BR3 in one JVM | 76 batches each: BR1 median 476 ms (p95 790), BR3 median 719 ms (p95 1,120, max 1,462); `write_batch` median 392 ms |
| The endpoint | 20 calls each: no `window_start` at 394 windows, `meta.ms` median 7.6, partitions 395; a given window 2.3 ms, 1 partition. Offset, no offset and UTC give the same window; `15:00:30` gives 200 `[]`; an empty table gives 200 `[]`, partitions 0. Two calls 12 s apart: window 14:59 then 15:09, top 3 reordered |
| Listing the keys as the table grows | A scratch table with the same schema, dropped afterwards, 15 runs each: 394 windows 7.5 ms, 1,440 13.8 ms, 43,200 346 ms |
| Build, contract and hook | `npm run build`, `npx oxlint` 0 warnings; `python tests/test_fixtures.py` all 8 bundles pass; `.claude/hooks/check_python.py` silent on both Python files, and it does warn on a probe file inserting into `trending_products` without a DELETE |
| Review | The `pr-review` checklist, `layer-checks.md` and the `spark-reviewer` trap list, read in this session. The pr-review skill advises a fresh session for code written in the same one |
| Session 17's open 10.6% (pairs below reorder on 30 Nov, report section 3) | DuckDB over `data/inventory` on Khang's machine: 6,738 of 63,655 pairs on 2019-11-30, 10.6%; 1,909,650 rows, 12,731 products |

### What the AI got wrong, and was corrected on

- **The offline harness first reported 51 views where silver had 54.** Its 36 files were written in the same
  second, the file source orders by modification time, and the stream read them out of order, so the watermark
  dropped events. Spacing the modification times 5 s apart, as the replayer does, gave 3,100 of 3,100. The job
  was not at fault.
- **The first hook check proved nothing.** A shell loop lost its variable and the probe file sat outside the
  project, which the hook skips. Re-run with the real paths and an in-project probe (deleted afterwards).
- **In Live mode the window picker showed the newest window**, so a 10 s refresh could overwrite a time being
  typed. Found in a review of the diff; the picker now stays empty in Live mode.
- **The first evidence draft said the first batch "of each run" was left out of the timings.** Only the very first
  one was.
- **612 was first described as products with a real brand and `unknown`.** It counts every product with more than
  one brand value: 573 of those, 42 with two real brands, 3 both. Found in Dat's review of #19; the code was right,
  the sentence in four places was not.

### Judgement that stayed with the team

Khang decided:
- **The newest window is found by listing the partition keys**, with the real partition count in the footer. No
  contract or schema change; the cost is measured above and is material for report 4.2.

Made by AI, flagged for review:
- **Ties go to `cart_count`, then the lower `product_id`.** API_CONTRACT §5 names only `view_count`.
- **Grouped by `product_id` alone**: `brand` is the real one when any event has it, `category_l1` through `max()`.
  Purchases are dropped before the aggregation.
- **The arrows come from a second call** for the window a minute earlier. The footer adds both calls, as BR4's
  heatmap footer adds its five.
- **The docs edits above**, including Dat's pattern docs and `CLAUDE.md`.

Closed in review (Dat, #19):
- **BR_SCOPE's "always 20 rows" for BR3.** 0.4% of the month's windows have fewer than 20 products and show fewer
  rows, so the criterion now reads "20 rows when the window has at least 20 products".
- **`STOP_WAIT_SECONDS = 10`** has room with BR1 and BR3 (max 1.46 s). It stays at 10 s; re-measure once BR5 and
  BR8 join (Nguyen, Tin).
- **Ties** need no contract change: API_CONTRACT §5 fixes only `view_count` and `rank ASC`.
- **The footer adding both calls** is fine, as BR4's does.
- **The newest window by listing the keys** is kept and written down as the one exception in
  `.claude/skills/br-slice/SKILL.md`.

Closed here: Session 17's 10.6% below reorder, measured above.

Pending: the group post with the Gate 1b screenshots, and the PR (Khang).

## Session 20 — 3 October 2026 (W41)

**Tool:** Claude Code (Opus 5.5).
**Scope:** the follow-up Khang promised on #13: `batch_warehouse.py` now runs the `dim_user` checks that only
`processing/dim_user.py` ran before. It uses Khang's 0.50 h of W41. Branch `w41-khang-dimuser-checks`.

### What the AI produced

| Artefact | Status |
|---|---|
| `processing/dim_user.py` — `EXPECTED_RANGES` (what each count must be, in one place), `dim_user_stats()` (the counts on `stg_rfm_snapshot` and `dim_user`), `expected_range()` and `all_as_expected()`; `main()` uses them instead of its own list | Run and verified (below) |
| `processing/batch_warehouse.py` — `check_dim_user()`: eleven lines in the style of `check_fact_event()`, folded into `checks_ok`; three lines in the docstring's sample output | Run and verified |
| `docs/AI_USAGE.md` — this session | AI-drafted |

### How it was checked

| Claim | How it was measured |
|---|---|
| The build passes with the new checks | `python processing/batch_warehouse.py` on Khang's machine, 123 s: each of the eleven new lines at its expected value (`stg_rfm_snapshot` 1,291,650; `dim_user versions` 319,426, within 258,330 to 1,291,650; `dim_user current` 258,330; the eight others 0), then `WAREHOUSE PARTIAL: 5 of 9 tables built` |
| The build still passes after main took #22 (`fact_session_funnel`) and #19 (BR3) | Dat merged `origin/main` into this branch on 6 October. The three conflicts in `batch_warehouse.py` (docstring, checks, `main()`) keep both sides, `check_dim_user()` after `check_fact_session_funnel()`; this session became 20. `python processing/batch_warehouse.py` on Dat's machine, 61 s: all three check blocks at their expected values, the eleven `dim_user` lines last, then `WAREHOUSE PARTIAL: 6 of 9 tables built` |
| `dim_user.py` run alone behaves as before | `python processing/dim_user.py`: the same counts and `DIM_USER OK`, 27 s |
| The check can fail | A scratch script called `check_dim_user()` on copies read back from disk and changed in memory only. One user given a second current version: current 258,331, overlaps 1, not_one_current 1. A non-buyer given a second, closed version: non-buyers not 1 version 1, empty_ranges 1. `stg_rfm_snapshot` one row short: 1,291,649. It returned False all three times and True on the intact tables. Nothing on disk changed |
| No clash with Tin's branch | `git diff origin/main origin/w40-tin-br6 -- processing/batch_warehouse.py`: its hunks start at lines 156, 181, 297 and 475; the checks block and the `checks_ok` lines in `main()` are untouched |
| Hook | `.claude/hooks/check_python.py` silent on both files |

### What the AI got wrong, and was corrected on

No defect was found in this change. What could have found one: the three corruptions above, each of which turns
a different count, and the standalone run of `dim_user.py`, whose pass rule now comes from the same table.

### Judgement that stayed with the team

Khang decided (30 September, on the tracker's question about his free 0.50 h in W41): spend it on these checks,
as said on #13.

Made by AI, flagged for review:
- **The expected values live in `dim_user.py`**, not in `batch_warehouse.py`, so the standalone script and the
  build read one list. `batch_warehouse.py` reaches them through the `user_scd2` alias, like its build steps.
- **The events are not counted twice.** `check_fact_event()` already runs `user_scd2.check_events()`.
- **`dim_user.py` run alone now prints its six SCD2 counts before the three event counts.** The counts and the
  pass rule are unchanged.

## Session 21 — 6-7 October 2026 (W41)

**Tool:** Claude Code (Opus 5.5).
**Scope:** BR2 end to end (tracker row 68), branch `w41-br2-slice`. `batch_gold.py` builds `funnel_daily` from
`fact_session_funnel`; `GET /api/br2/funnel` reads it with DuckDB; the BR2 screen shows real numbers and a
by-category table. Planning was a read-only workflow: three agents mapped the data, the code and the project's
rules, three Plan agents designed it from different angles, one merged them and two critics reviewed the merge.

### What the AI produced

| Artefact | Status |
|---|---|
| `processing/batch_gold.py` — `furthest_stage()`, `build_session_categories()`, `funnel_measures()`, `build_funnel_daily()`, `session_category_checks()`, `funnel_daily_stats()`, `run_funnel_daily()`; `main()` checks four `_SUCCESS` files and runs BR4 and BR2 independently | Run and verified (below) |
| `serving/api/routers/br2.py` — `_load_fixture()` replaced by `_partitions()` + `_read_funnel()` (DuckDB over the `event_date` directories in range); `warehouse="Parquet"`, `partitions` = directories read; docstring rewritten | Run and verified |
| `web/src/pages/BR2Page.tsx` — KPIs, bars and drop-off on `session_count`, rates guarded against 0, the 14 categories copied from `BR1Page.tsx`, dates up to 2019-12-01, a 15-call "Conversion by Category" table with its own footer, notes on the counting rule and 15 Nov; `web/src/index.css` — `.panel__note`, `.category-button`, the selected row | Built and driven in headless Chromium |
| `docs/API_CONTRACT.md` §4 — the three `*_events` gold columns, sources, definitions, empty cases, a measured example; response fields unchanged | AI-drafted, team sign-off pending |
| `web/fixtures/br2-funnel-daily.json` — the measured default response and metadata; `serving/api/models.py`, `web/src/types/api.ts` — comments only | AI-drafted |
| `SYSTEM_DESIGN.md` §3.1 (purchases without a cart, 1-7 Nov) and §7 (columns, the `'all'` row, BR1 vs BR2 per day); `CLAUDE.md` and `README.md` status; one phrase in `docs/STREAMING_PATTERN.md` and `docs/SPARK_GUIDE_VI.md` | AI-drafted |
| `docs/evidence/gate2a_br2_run.txt` (new) — text copy of the run below | Captured from the run |
| `docs/AI_USAGE.md` — this session | AI-drafted |

### How it was checked

| Claim | How it was measured |
|---|---|
| The gold job passes and agrees with its inputs | `python processing/batch_gold.py` on Dat's machine, 29 s: `RFM_SEGMENTS OK`; pre-write checks 0 events lost, 0 without a category, 0 sessions whose best category stage differs from `funnel_stage`; 465 rows, 31 partitions, 15 categories incl. `all`; `all` sessions 970,797 / 132,002 / 54,904 equal `fact_session_funnel`; `all` and category events both 4,474,579 / 214,286 / 65,150 equal `fact_event` per `event_type_key`; 0 rows where sessions rise; `FUNNEL_DAILY OK`, `GOLD OK` |
| Gold equals the star | One-off DuckDB recompute from `fact_session_funnel`, `fact_event`, `dim_product`: `EXCEPT` 0 rows both ways on 465 rows; `cr_*` equal the ratios on all 465 (NULL on the 50 with `carts = 0`) |
| No range join | `grep -nE "valid_from\|valid_to\|BETWEEN" processing/batch_gold.py serving/api/routers/br2.py`: no match |
| The API returns the gold, under 2 s | `uvicorn` + curl, slowest of 3 warm: defaults 16.36 ms, 30 partitions, sessions 966,143 / 131,498 / 54,676, rates 1.0 / 0.1361 / 0.0566; 15 Nov 1 partition; 11-01..12-01 31 partitions. Bad date, start > end, October, unknown category: 200 and `data []` |
| Contract and types | `python tests/test_fixtures.py`: all 8 bundles pass; `cd web && npx tsc -b && npm run build`: passes |
| The screen works | Built app driven over the Chrome DevTools Protocol (scratch script, not committed): the category select, both dates and a table row change the KPIs and the footer's partition count; stationery on 1 Nov shows "—", no NaN; 1-7 Nov still decreases |
| 8,845 purchases without a cart, 6,649 on 1-7 Nov, 695 sessions without a view | DuckDB on `fact_session_funnel`: `count_if(purchase_count>0 and cart_count=0)`, the same with `session_start_date <= '2019-11-07'`, `count_if(view_count=0)` |
| 117,396 sessions touch more than one category | DuckDB: `fact_event JOIN dim_product USING (product_sk)`, `group by user_session having count(distinct category_l1) > 1` |
| 7,433 sessions cross midnight; 17 Nov purchases 11,991 (BR2) vs 11,736 (BR1) | DuckDB on `fact_event` (`count(distinct event_date) > 1` per session) and `sum(purchase_count)` on `fact_session_funnel` vs `count(*)` of purchase events with `event_date = '2019-11-17'` |

### What the AI got wrong, and was corrected on

- **The chart had no bars.** The first headless screenshot showed axes only: Recharts' entry animation never ran
  under the headless clock, and nothing proved it would in a recording. Fixed with `isAnimationActive={false}`,
  as BR1's chart already does.
- **The plan made the category table optional.** A critic found that `br-slice-auditor` checks the screen
  against br-slice section 4, which lists the table, so an optional table could fail the gate. It became
  must-ship (Dat's decision below).
- **The plan's code comment named the tokens its own grep guard bans** (`valid_from`, `valid_to`, `BETWEEN`), so
  the guard could never pass. The comment says "a range join on the SCD2 validity dates" instead.
- **The first KPI label was "Sessions with a view".** 695 sessions reach the view step with no view event, so it
  is "Sessions".
- **The planned drop-off divided by zero.** Stationery on 1 Nov has 0 cart sessions; the column now shows "—".
- **The plan rewrote SYSTEM_DESIGN 8 step 4 and section 10 to "BR4 and BR2".** Those lines describe the design,
  and Tin's branch adds BR6 to `batch_gold.py` this week; they were left alone.
- **The data-measuring agent returned nothing.** Its numbers came from the code-map agent, and every number in
  the docs was measured again in this session before it went in.
- **The new status text gave `funnel_daily` only half its lineage.** CLAUDE.md said "from `fact_session_funnel`",
  and SYSTEM_DESIGN §7's older first line now contradicted the new paragraph under it; the category rows come
  through `fact_event` + `dim_product`. Found by the review workflow's contract reviewer. Fixed in CLAUDE.md,
  SYSTEM_DESIGN §5.2's "Serves" row and §7, README, `models.py`'s storage map, BR_SCOPE and the br-slice skill.
- **README declared BR7 live, but its run order never ran `processing/gold_br7.py`.** On this machine
  `data/gold/product_affinity` does not exist and `/api/br7/*` answers 500. Found by the same reviewer; the run
  order now has the step. BR7's gold itself was not built here.

### Judgement that stayed with the team

Dat decided (7 October, in this session):
- **D1.** `views`/`carts`/`purchases` become session counts, and gold gains `view_events`, `cart_events` and
  `purchase_events`; the response is unchanged. This answers tracker row 46's note, "đổi cột gold hay đổi hợp đồng".
- **D4.** The by-category table is built from 15 calls to the existing endpoint, as BR4 builds its heatmap. No
  contract change; it ships with the slice.

Needs all four before merge: the gold column names are frozen (API_CONTRACT §4, SYSTEM_DESIGN 7, PLAN.md), so D1
goes to the group in Dat's Wednesday checkpoint. Not yet agreed.

Made by AI, flagged for review:
- **Reaching a step is `funnel_stage` >= 1 / >= 2 / = 3**, as `models.py` already said, not a non-null milestone
  timestamp: with timestamps, 1-7 Nov shows more sessions at purchase than at cart.
- **`conversion_rate` is a session ratio**, recomputed from the summed counts; the W38 fixture used an event
  ratio. Event counts rise from cart to purchase on 1-7 Nov, which would break BR_SCOPE's "counts decrease".
- **A category row stages each session on that category's events alone.** Giving every touched category the
  session's own `funnel_stage` would count 63,351 purchases against 54,904 sessions that bought.
- **Bad input returns 200 and `data []`**, as BR4 does and contract §1.3 says, not BR1's 422.
- **The date inputs allow 2019-12-01**, the 31st partition; the defaults stay 11-01..11-30.
- **CLAUDE.md and README now say BR7 is live too.** `br7.py` reads Parquet and its screen fetches it (Nguyen to
  confirm).

Closed here: `funnel_daily` has no session count (Sessions 8, 9, 10: lines 728, 860, 997); BR2's gold column or
contract (Session 11, line 1098); `funnel_daily` needs `category_l1` (Session 18, line 1807).

Carried forward:
- `FunnelCategoryRow` in `models.py` and `api.ts` still has no route, fixture or contract section (Tin, 1d93340).
  The screen does not use it.
- SYSTEM_DESIGN 5.2's star still links `fact_session_funnel` to `dim_product` (Session 11, line 1103).
- Tin's `origin/w41-tin-merge-br6` rewrites `batch_gold.py`'s `main()` (argparse, "BATCH GOLD OK"): whoever merges
  second wires in the other's run function. His `br4.py` fallback labels fixture data `"Parquet"`, which the
  contract calls fabricated meta; raise it in his review.
- For Khang's report: the 1-7 Nov purchases without a cart, and BR2's 15 Nov (131 purchase sessions of 53,553).
- The Gate 2a screenshot of `/br2` with its footer goes to the group chat (Dat).

## Session 22 — 12 October 2026 (W42)

**Tool:** Claude Code (Opus 5.5).
**Scope:** Dat's review of Nguyen's PR #26 (BR5 end to end), then a run of BR5 on the PR head and small fixes on
`w41-nguyen` before the merge. No query, endpoint or screen logic was changed: Nguyen's code is as Nguyen pushed it.

### What the AI produced

| Artefact | Status |
|---|---|
| Review of #26 — read-only, against CLAUDE.md, SYSTEM_DESIGN 6.1, API_CONTRACT §7, `STREAMING_PATTERN.md` and the Spark trap list; no blocking finding. Not posted (Dat's decision below) | Human-approved |
| `=` — the empty file at the repo root that came in with 2e38359, removed | Run and verified (nothing reads it) |
| `processing/streaming_gold.py` — docstring status line: BR5 `done (W41)` | Comment only |
| `serving/api/routers/br5.py`, `web/src/pages/BR5Page.tsx` — "a few thousand rows at most" replaced with the measured partition sizes; final newline added | Comment only |
| `SYSTEM_DESIGN.md` §6.1 — the same claim replaced with the measured sizes | AI-drafted |
| `CLAUDE.md` and `README.md` status — BR5 live, `GET /api/br5/carts` reads Cassandra, Gate 2a open only for BR8 and BR6 | AI-drafted |
| `docs/evidence/gate2a_br5_run.txt` (new) — text copy of the run below | Captured from the run |
| `docs/AI_USAGE.md` — this session | AI-drafted |

### How it was checked

| Claim | How it was measured |
|---|---|
| BR5's stream runs and writes | Dat's machine, branch `w41-nguyen` at 2e38359: `python processing/streaming_gold.py --fresh` (`READY: 3 of 4 jobs`), then `python ingestion/replayer.py --speed 60 --start "2019-11-17 08:00:00"` for 78 files (15:00-21:30 Vietnam time, 187,468 rows). First carts in batch 9; 70 batches upserted 2,621 carts; no exception; Ctrl-C stopped cleanly |
| The stream's rows are right | Scratch script (not committed): `abandoned_carts` for 2019-11-17 read with cassandra-driver against DuckDB on silver over the same hours, sessions split at 30-minute gaps, cart and no purchase, last event + 30 min <= the final watermark 21:19:59, the latest split per session kept. 2,600 rows both sides, 2,600 identical in value, items, user and time, 0 only on one side; Σ`cart_value` 1,411,565.93 both |
| The API returns them sorted, with measured meta | `uvicorn` + curl: `?event_date=2019-11-17` 13.6 ms, 1 partition, 2,600 rows; no parameters 2 partitions (the `DISTINCT` listing + the day); `min_value=500` 721 rows, lowest 501.03; `2019-11-16` 200 with `data []`. Each sorted by `cart_value` descending, `meta.rows == len(data)` |
| The screen compiles | `cd web && npx tsc -p tsconfig.app.json --noEmit`: exit 0. Not rendered in a browser |
| Partition sizes in the comments and §6.1 | DuckDB on all of silver, the same 30-minute rule, grouped by the date of the last event: median 1,609; 17 Nov 8,774, of which 3,965 with the last event from 15:00; 15 Nov 18,303 or 18,304 between runs |
| `cart_value` means what the star means | `processing/batch_warehouse.py:348`: `fact_session_funnel.cart_value` is also `sum(price)` over cart events |

### What the AI got wrong, and was corrected on

- **The first measurement queries globbed `data/silver/*/*.parquet`.** Silver is partitioned by `event_date` and
  `event_type`, so they found no file. Rerun with `**/*.parquet` and `hive_partitioning=true`.
- **The busiest-day count was first reported as exactly 18,303.** A rerun gave 18,304: ties in `event_time` make
  the 30-minute split differ by one between runs. The docs say "about 18,300".
- **The replayer was stopped with SIGTERM, not Ctrl-C,** so `replayer.log` ends in a Java `Connection reset`
  trace. It is a stop artefact, not a fault; the evidence file says it was stopped after file 78.
- **The stop command's `pgrep -f` matched its own shell** and sent that shell SIGINT too. The stream got its
  SIGINT as well and stopped cleanly ("stopped; the checkpoints keep the progress", exit 0).

### Judgement that stayed with the team

Dat decided (12 October, in this session): no review comment on #26; fix what the review found, then merge.

Made by AI, flagged for review:
- **The fixes went onto Nguyen's branch** as a new commit (no force-push), and #26 is squash-merged, so the `=`
  file never enters `main`'s history. Nguyen keeps authorship of the BR5 code.
- **`cart_value` counts every cart event,** so one product added 32 times in 9 minutes makes the largest cart,
  53,157.63 with `item_count` 1. It matches `fact_session_funnel.cart_value`, and nothing was changed. Nguyen to
  say whether the BR5 list should keep it.
- **One row per (day, session) keeps only the latest abandoned split:** 21 of 2,621 upserts in the run
  overwrote an earlier one. That is the key SYSTEM_DESIGN 6.1 chose.

Carried forward:
- The Gate 2a screenshot of `/br5` with its footer goes to the group chat (Nguyen).
- The BR5 numbers above are gate evidence, not evaluation results: the ≥99% correctness comparison and Gate 2b
  timings stay with their owners in PLAN.md.
- Session 21's carried-forward list is unchanged; nothing in it was touched here.

## Session 23 — 13 October 2026 (W42)

**Tool:** Claude Code (Opus 5.5).
**Scope:** Dat's re-review of Tin's PR #23 (BR6 + BR8 + warehouse step 6) at 48b62de, then a fix for its two blocking
findings on `w41-tin-merge-br6`, local test steps for the whole PR, and the pre-merge status docs. Tin's BR6 and BR8
query, endpoint and screen code is as Tin pushed it; only the Postgres load of `fact_session_funnel` changed.

### What the AI produced

| Artefact | Status |
|---|---|
| Re-review of #23 — Khang's four points and the four must-fix items, the team decision, the questions and the nits from the 11 Oct review, each marked addressed or not; two new blocking findings in the `fact_session_funnel` load. Not posted (Dat's decision below) | Superseded by the fix |
| `serving/load_star_postgres.py` — `load_fact_session_funnel()` now inserts `last_event_at` and `purchase_value`; its docstring no longer calls `cart_value` nullable | Run and verified (14235bd) |
| `processing/batch_warehouse.py` — `load_postgres()` renders `fact_session_funnel`'s five timestamps with `date_format` before `toLocalIterator()`, as `fact_event`'s `event_time` already was | Run and verified (14235bd) |
| Local test steps for the whole PR: `gen_inventory.py`, `batch_warehouse.py` with Postgres up, Postgres row counts, `batch_gold.py --br6`, the BR6 and BR8 curls, the BR8 stream with the replayer, both screens | Run by Dat, reported OK |
| `CLAUDE.md` and `README.md` status — all nine tables and `WAREHOUSE OK`, step 6 loads Postgres, BR6 and BR8 live, next task Gate 2b, open items | AI-drafted |
| `docs/AI_USAGE.md` — this session | AI-drafted |

### How it was checked

| Claim | How it was measured |
|---|---|
| Step 6 stopped whenever Postgres was up | `warehouse/ddl.sql`: `fact_session_funnel.last_event_at` and `.purchase_value` are `NOT NULL` with no default; the loader listed 17 of the table's 19 columns. Read from the DDL, not reproduced on the old code |
| The old load shifted timestamps by 7 hours | `.venv/lib/python3.14/site-packages/pyspark/sql/types.py`: `TimestampType.fromInternal` calls `datetime.fromtimestamp` (local time); `date +%z` → `+0700`; `conf/spark-defaults.conf` → `spark.sql.session.timeZone UTC`. Reproduced: session -9223038402290496650 (`session_start_date` 2019-11-17) is collected as 2019-11-18 05:45:11 and rendered by the fix as 2019-11-17 22:45:11 |
| The fixed load is right | Scratch database `scratch_pr23` with `warehouse/ddl.sql` applied; scratch script (not committed) runs the real `load_postgres()` on `fact_session_funnel` for 2019-11-17, `read_env` patched to the scratch database. Postgres vs Parquet: 71,594 rows both; 31,938 starting at 17:00 or later both; 0 rows where `session_start_at::date <> session_start_date`; min start 2019-11-17 00:00:07, max `last_event_at` 2019-11-23 13:02:13 and Σ`purchase_value` 3,799,654.81 equal. Database dropped afterwards |
| The whole PR runs | Dat's machine, branch at 14235bd: the local test steps 1-7, reported "Run ok" by Dat. No log was captured in this session; that is what Tin's evidence files are for |
| `fact_inventory_daily` 1,909,650 and `BR6 OK` 63,655 in CLAUDE.md and README | The expected values printed in the test steps (12,731 purchased SKUs x 5 warehouses x 30 days; 12,731 x 5 for the last day), which Dat's run reported OK against. Not re-measured by AI |
| `dim_product` 210,454 and `dim_user` 319,426 (expected values in the test steps) | DuckDB `count(*)` over `data/warehouse/dim_product/*.parquet` and `data/warehouse/dim_user/*.parquet` on Dat's machine |
| The earlier points are addressed | `git diff ab616d3 pr/23` (1db318b, 48b62de); `git diff --quiet main pr/23 -- serving/api/routers/br4.py serving/api/cassandra.py serving/check_infra.py` → identical; `gh pr view 23` → MERGEABLE, CLEAN; `git merge-tree --write-tree main pr/23` → no conflict |

### What the AI got wrong, and was corrected on

- **The 11 Oct review told Tin to bring `serving/load_star_postgres.py` over from `w40-tin-br6` without checking its
  loaders against `warehouse/ddl.sql`.** That branch already left out `last_event_at` and `purchase_value`
  (`git show origin/w40-tin-br6:serving/load_star_postgres.py`, line 540), so following the advice carried the
  crash into #23. This re-review compared every loader's column list with the DDL and the Parquet builders.
- **The message of commit 14235bd says the full `batch_warehouse.py` run passes on Dat's machine.** It was written
  before Dat said which test "Run ok" covered. Dat then confirmed the full steps 1-7, so the claim stands, but it
  went into a pushed commit before it was confirmed.

### Judgement that stayed with the team

Dat decided (13 October, in this session): fix the two findings on Tin's branch instead of posting the review and
waiting; commit and push 14235bd to `w41-tin-merge-br6` (no force-push); update CLAUDE.md, README and this log
before the merge; leave the Gate 2a evidence files to Tin in a follow-up PR; then squash-merge #23.

Made by AI, flagged for review:
- **CLAUDE.md's next task is now Gate 2b** (W42 in PLAN.md), with Gate 2a counted as met in code and its BR6 and
  BR8 evidence still owed.
- **A squash merge keeps Tin as the author** of the BR6, BR8 and step 6 code on `main`; Dat's fix commit is folded in.

Carried forward:
- Tin: `docs/evidence/gate2a_br6_run.txt` and `gate2a_br8_run.txt`, laid out like `gate2a_br5_run.txt`. They should
  show the 1,909,650 and 63,655 above.
- Team: `docs/BR_SCOPE.md` says BR8's demo opens an alert to its list of orders; the screen expands an alert to its
  window totals, and `order_velocity_alerts` stores no orders. Tin proposes the wording, the team agrees.
- Session 22's carried-forward list is unchanged; nothing in it was touched here.

## Session 24 — 9 and 18 October 2026 (W41-W42)

**Tool:** Claude Code (Opus 5.5).
**Scope:** report section 4.2, Cassandra (tracker row 74): partition and clustering keys, keys designed backwards
from the screen's question, and the three tables that leave stale rows. Branch `w41-khang-report-4-2`. On 18
October, after #23 and #26 merged, `main` was merged into the branch (this entry was Session 22 until then; the
12 October session took that number) and the BR5 and BR6 bullets were checked against the code that landed.

### What the AI produced

| Artefact | Status |
|---|---|
| `docs/REPORT.md` 4.2 — keys on `gmv_by_minute` and `trending_products`, the contrast with the star, the cost of BR3's "newest window" in four measured sizes, the stale-row paragraph (`stockout_risk`, `trending_products`, `abandoned_carts`) | AI-drafted, numbers measured or quoted from `docs/evidence/` |
| `docs/REPORT.md` "Nguồn số liệu của mục 4" — one command per number | AI-drafted |
| `docs/REPORT.md` 4.2, 18 October — one sentence with BR5's measured cost of sorting in the API; the source table's BR5 and BR6 row points to the code instead of `SYSTEM_DESIGN.md` 6.1 | AI-drafted, number quoted from `docs/evidence/gate2a_br5_run.txt` |
| `docs/evidence/cassandra_describe_gmv_by_minute.png`, `docs/evidence/cassandra_describe_trending_products.png` | Taken by Khang with `cqlsh` |
| `docs/AI_USAGE.md` — this session | AI-drafted |

### How it was checked

| Claim | How it was measured |
|---|---|
| Every key in 4.2 | The same text in `serving/cassandra_schema.cql`, `SYSTEM_DESIGN.md` 6 and 6.1, and the two `DESCRIBE TABLE` screenshots (`trending_products` shows the default `rank ASC`) |
| BR3, newest window, at 19,669 windows | Khang's machine, 9 October, the table left by the replays of 1-3 October (17 Nov 14:46 to 1 Dec 06:34): `uvicorn` on a spare port, 15 calls to `GET /api/br3/trending`, median `meta.ms` 159.2, `partitions` 19,670, `rows` 20 |
| BR3, one window | 15 calls with `window_start=2019-11-17T21:19:00+07:00`: median 2.26 ms, 1 partition, 20 rows |
| BR1, 1 partition, 120 rows, 5.7 ms | Quoted from `docs/evidence/gate1a_br1_run.txt` (Dat's machine, Gate 1a); 4.2's source table says so |
| 394, 1,440 and 43,200 windows (a scratch table with the same schema); the delete inside a batch; 7,600 of 7,600 rows; no duplicates after a restart | Quoted from `docs/evidence/gate1b_br3_run.txt`, not re-measured |
| Which tables hold rows now | `SELECT count(*)`: `gmv_by_minute` 165,481, `trending_products` 393,121, `abandoned_carts`, `stockout_risk` and `order_velocity_alerts` 0. So BR5 and BR6 are described from the design, not measured |
| The BR5 and BR6 bullets match the code (18 October, `main` at 03394c9) | `serving/cassandra_schema.cql`: `abandoned_carts` `((event_date), user_session)`, `stockout_risk` `((warehouse_id), days_to_stockout, product_id)`; `run_br6` in `processing/batch_gold.py` runs `DELETE FROM stockout_risk WHERE warehouse_id = ?` per warehouse, then inserts; `start_br5` in `processing/streaming_gold.py` only inserts; `serving/api/routers/br5.py` sorts by `cart_value` descending. The text of both bullets stands |
| BR5, one day: 1 partition, 2,600 carts, 13.6 ms | Quoted from `docs/evidence/gate2a_br5_run.txt` (Dat's machine, Gate 2a, `?event_date=2019-11-17`), not re-measured |

### What the AI got wrong, and was corrected on

- It planned to quote 320 ms for the default BR3 call at about 19,670 windows: a single reading on 3 October,
  never committed. The median of 15 calls is 159 ms; 4.2 uses the median and gives the command.

### Judgement that stayed with the team

Khang decided: take the two `DESCRIBE TABLE` screenshots himself. The tracker points to Nguyen's W39 screenshots in
`docs/evidence/`, but `main` holds none.

Made by AI, flagged for review:
- **"Khoá phân vùng"**, not the tracker's "khoá phân mảnh": 4.1 and every screen footer already say "phân vùng".
- **BR5 and BR6 were written from `SYSTEM_DESIGN.md` 6.1 on 9 October,** when `start_br5` was a stub and BR6's
  writer was in Tin's #23. On 18 October both bullets were checked against the merged code and stand unchanged;
  BR5 now has one number, quoted from Gate 2a. Nguyen and Tin: say if the wording misdescribes your code.

Carried forward:
- Session 23's carried-forward list is unchanged; nothing in it was touched here.

## Session 25 — 18 October 2026 (W42)

**Tool:** Claude Code (Opus 5.5).
**Scope:** report section 4.3, Spark (tracker row 87): `local[*]`, batch against streaming, the five Structured
Streaming concepts the jobs use, writing Cassandra with `cassandra-driver` inside `foreachBatch`, the two memory
traps, and the null-safe version test of `dim_user`. Branch `w42-khang-report-4-3`, cut from
`w41-khang-report-4-2` because both sections edit `docs/REPORT.md`.

### What the AI produced

| Artefact | Status |
|---|---|
| `docs/REPORT.md` 4.3 — five code excerpts copied from the repo (`read_events`, BR3's `writeStream`, the head of BR3's `write_batch`, the two settings of `conf/spark-defaults.conf`, `cell_changed` in `dim_user.py`) | AI-drafted, numbers measured or quoted |
| `docs/REPORT.md` "Nguồn số liệu của mục 4" — seven rows for 4.3 | AI-drafted |
| `docs/evidence/dim_user_null_compare.txt` (new) — the null shares and the `!=` comparison below | Captured from the run |
| `docs/AI_USAGE.md` — this session | AI-drafted |

### How it was checked

| Claim | How it was measured |
|---|---|
| The five excerpts are verbatim | Scratch script (not committed): every line of each code block is a line of its file, and every block but the two-line config one is contiguous in it |
| `rfm_cell` NULL for 97.3% of users on 7 Nov, 88.0% on 30 Nov | DuckDB on `data/warehouse/stg_rfm_snapshot` on Khang's machine; the query is in the evidence file |
| With `!=`, 295,452 versions instead of 319,426, 5,529 current rows stale, all six SCD2 counts 0 | Scratch script (not committed) on Khang's machine: `version_no` recomputed from `stg_rfm_snapshot` with the repo's `eqNullSafe` line and with `!=`, then `build_dim_user()` and `scd2_violations()` imported from the repo. The `eqNullSafe` run gives back the 319,426 rows of `dim_user` on disk |
| 200 against 4 shuffle partitions | Quoted from the comment in `main()` of `processing/streaming_gold.py` (W40 dry run, Dat's machine), not re-measured |
| BR1 476 ms and BR3 719 ms per micro-batch; the restart after batch 11 | Quoted from `docs/evidence/gate1b_br3_run.txt`, not re-measured |
| The builder-config trap, 1.0 GiB heap with `getConf()` at `6g` | Quoted from `docs/SETUP_SPARK.md` section 6 (measured on PySpark 4.1.3), not re-measured |
| Every Spark script runs `local[*]` and sets `SPARK_CONF_DIR` first | `grep` over `processing/`, `ingestion/`, `checks/`: every file that builds a SparkSession sets `master("local[*]")`, and its `SPARK_CONF_DIR` line comes before its first `pyspark` import |

### What the AI got wrong, and was corrected on

- **The first draft said no later check could catch the `!=` mistake.** The integrity checks cannot, but comparing
  the current segment with the last snapshot in `stg_rfm_snapshot` does (that is how the 5,529 were counted). The
  sentence now says so.
- **The first draft's `getConf()` sentence left out that the new session is built with `6g`.** Added, as in
  `docs/SETUP_SPARK.md` section 6.

### Judgement that stayed with the team

Made by AI, flagged for review:
- **Three statements of tracker row 87 are not followed, because the code and the data say otherwise.**
  - 88% is the share of NULL `rfm_cell` at the last snapshot (30 Nov), not the first; the first, 7 Nov, is 97.3%.
  - With `<>` the version test loses versions, it does not add them. The tracker says a non-buyer would get a new
    version every snapshot. In this code a comparison with NULL is NULL and `sum()` skips it, so the first purchase
    (NULL to a value) opens no version. Counting NULL as a change would give 1,254,555 versions instead (DuckDB,
    same data, in the evidence file); 4.3 describes what Spark does with the code as written.
  - `builder.config("spark.driver.memory")` is not always ignored. It works when that builder starts the JVM, as
    `conf/spark-defaults.conf` and `docs/SETUP_SPARK.md` section 6 already say; 4.3 follows them.
- **The shuffle-partition paragraph is not in the tracker row.** It is the one Spark setting the team changed on a
  measurement; it can go if 4.3 must stay at two pages.
- **4.3 is about 2.5 pages with its five excerpts.**

Carried forward:
- Session 23's carried-forward list is unchanged; nothing in it was touched here.

## Session 26 — 21 October 2026 (W43)

**Tool:** Claude Code (Opus 5.5).
**Scope:** revision v3 of the indexing presentation (Canva `DAHYkUBuuhM`, 19 pages) against the reviewer's comments
of 21 October, plus one new measurement for page 17. No application code was written; the measurement script was run
and its source is appended to its evidence file.

### What the AI produced

| Artefact | Status |
|---|---|
| PR #31 (E1, `docs/evidence/presentation_parquet_run.txt`) merged with a merge commit | Done by the AI after Đắt approved the plan |
| `docs/evidence/presentation_csv_vs_parquet.txt` (E4) — revenue per category on the same 7% sample, DuckDB on a CSV export of bronze vs DuckDB on `data/silver` with hive partitioning | Run and verified on Đắt's machine |
| Canva `DAHYkUBuuhM` — slide text on 18 pages, speaker notes on 17, references with venues and docs URLs, title renamed to `Group15_Indexing_Presentation` | AI-edited; Đắt approved the 19 draft thumbnails before the commit |
| Figures F14 (p17), F7 (p10), F8 (p11), F2 (p5), F9 (p12) redrawn as SVG and rendered to PNG with headless Chromium and Arimo; each checked by a second, independent agent | AI-drawn; approved with the thumbnails |
| `docs/PRESENTATION_SLIDES.md` "Số được dùng" table — 19-page numbering, rows for "khớp 10%", "9 GB" and E4 | AI-drafted; local file, excluded by `.git/info/exclude` |
| `docs/AI_USAGE.md` — this session | AI-drafted |

### How it was checked

- Every review point was checked read-only before anything was edited: four agents (repo facts, technical claims
  with primary sources, Vietnamese wording, figures) and one adversarial agent over their combined output.
- The draft deck was scanned for leftover terms ("ngược từ câu hỏi", "quét dải", "index học được", "hash table",
  "9,009", …). Every "Nguồn:" footer matches a page 19 entry; page numbers run 1–19; notes exist on all 19 pages.

| Claim | How it was measured |
|---|---|
| CSV 177.0 ms → partitioned Parquet 9.0 ms; Parquet opens 31 of 93 files | `.venv/bin/python presentation_csv_vs_parquet.py` (source at the end of the evidence file): 1 warm-up + 5 timed runs each, median; `EXPLAIN ANALYZE` prints `Scanning Files: 31/93`; both sides return the same 14 groups and 65,150 orders |
| "khớp 10% dòng", "gần 2/3 số trang" (p8) | `docs/evidence/gin_vs_seqscan.txt`: 21,078 / 210,454 rows; Heap Blocks 7,646 vs seq-scan buffers 11,608 |
| Colour is synthetic | `ingestion/gen_catalog.py`, `COLORS` chosen by a hash of `product_id` |
| BR6 is batch but writes Cassandra | `run_br6` in `processing/batch_gold.py` |
| The total-revenue screen reads one partition | `serving/api/routers/br1.py` reads the `category_l1 = 'all'` partition |

### What the AI got wrong, and was corrected on

- While planning, it told Đắt the copy differed from the original deck "only on a few pages". It differs on almost
  every page (v2 restructured it). It re-asked with the facts, and Đắt changed the decision to re-recording the video.
- `update_fill` silently re-cropped images: F14 came out zoomed and cut at the edges, and the GIN figure and F5 (where
  only the alt text was changed) were zoomed slightly. This was caught on the thumbnails; the crops were reset, and
  F5's restored to its original values.
- The first E4 run printed an empty `File Filters` line. The extraction was fixed and the script re-run; the committed
  file is the second run (152.0 / 8.3 ms in the first run, 177.0 / 9.0 ms in the second).
- Canva captions were added at the default 16 px black and then reformatted to 24 px grey. The page 15 strip wrapped
  "xoá" onto a second line until the sentence was shortened and the box widened.
- Three review claims were refuted rather than applied: "5 màn hình thời gian thực" (BR6 is batch), "the total screen
  reads many partitions" (it reads `'all'`), and "Cassandra 5.0 replaced Summary/Index with BTI" (BTI is opt-in).

### Judgement that stayed with the team

Đắt decided:
- submit the copy's PDF on 23/10 and re-record the video from it;
- drop thousands separators in the speaker notes only; slides and the report keep rule 4;
- run the CSV vs Parquet measurement and no Cassandra measurement;
- approve the plan, then approve the commit after seeing the thumbnails.

Made by AI, flagged for review:
- the terminology choices (quét khoảng, khoá, bảng băm, join, máy, bỏ qua / xoá, English section names);
- the declined review items: no ShopInsight example on pages 7 and 10, keep the DELETE + INSERT example on page 9,
  keep "trả bằng" and M for LSM on page 15, no learned index on the RUM triangle, author-year references instead of
  IEEE numbering;
- the page 17 line carries two numbers, against the one-number rule, because it is a before/after pair;
- F7's right panel is now 3 × 2 boxes; F9 keeps the root label `silver/`.

Not done: the P3 items of the plan (F4b "key", F5 marker, taller F6 and F13, bullet unification) and the layout of
pages 9 and 16.

Carried forward:
- The original deck `DAHYFi9Mr50` shows `updated_at` 21/10 19:07, from another account. This session never opened an
  editing transaction on it. Its owner should check the version history.
- Owners write the "Bản video" narration for their pages (only 12–15 have one) and re-record from the locked PDF;
  Nguyên assembles; someone asks the lecturer about the deadline as a fallback.
- `docs/PRESENTATION_REVISION_PLAN.md` (local) has a v3 section (§9); the F7, F8, F14 rows of its §4 still describe v2.
- Session 24's carried-forward list is unchanged; nothing in it was touched here.

## Session 27 — 23 October to 3 November 2026 (W43-W45)

**Tool:** Claude Code (Opus 5.5).
**Scope:** two artefacts of the indexing presentation that were made in Claude Code sessions not logged at the time,
the "Áp dụng cho ShopInsight" figure F14 (23 October) and evidence E5 (26 October), brought to `main` through PR #32 on
3 November (sprint task T01). This entry was written on 3 November from the files themselves and the "Số được dùng"
table of `docs/PRESENTATION_SLIDES.md`, not from the two sessions' transcripts. No application code was written.

### What the AI produced

| Artefact | Status |
|---|---|
| `docs/figures/shopinsight_applied_map.html` — figure F14 of Canva `DAHYkUBuuhM` as HTML, rendered at 3x by headless Chromium to the PNG on the slide (the command is in the file's header) | AI-drawn on 23/10; it is the figure on the page 17 Đắt presented. Committed unchanged |
| `docs/figures/fonts/` — Arimo (Apache 2.0) from Google Fonts: `arimo.css` and 16 woff2 subsets, so the figure renders the same on a machine without Arimo | Downloaded on 23/10; committed unchanged |
| `docs/evidence/presentation_price_zonemap.txt` (E5) — the `price` min/max in the footer of each of the 93 silver row groups, and how many of them a `price > v` filter could skip | Run on Đắt's machine on 26/10; re-run on 3/11 (below) |
| `docs/AI_USAGE.md` — the merge of `main` into this branch, which renumbered the E4 session from 25 to 26; this session | AI-drafted |

### How it was checked

On 3/11, before the merge, three independent agents checked these three artefacts read-only. Each check ran before `data/silver` was rebuilt for task T02.

| Claim | How it was measured |
|---|---|
| E5 reproduces | The script in E5's SOURCE section, extracted verbatim and re-run with `.venv/bin/python` from the repo root: sections 1-3 (129 lines) are identical. Only the header date differs |
| A filter `price > 1000` can skip 0 of the 93 row groups, although only 4.97% of rows match | E5 section 2, and a separate DuckDB query: `parquet_metadata('data/silver/*/*/*.parquet')`, `path_in_schema = 'price'`, 0 row groups with max <= 1000, and 236,207 of 4,754,015 rows with `price > 1000` |
| The figure needs nothing from the network | Every `href`, `src` and `url()` in the HTML and `arimo.css` is relative and exists. A render inside `unshare -rn` (no network) is byte-identical to a normal one, and the browser requested only `file://` URLs |
| The bundled Arimo is what the figure renders with | Rendered again with `fonts/` deleted, it is a different PNG, and DejaVu Sans overflows 5 boxes. With `fonts/` present, CDP `CSS.getPlatformFontsForNode` puts every glyph on the web font, Vietnamese diacritics included |
| The conflict resolution drops nothing | The resolved file starts with `main`'s file byte for byte (`cmp`), followed by the branch's 74-line block with one changed line, the heading. Headings run 1 to 26 |

### What the AI got wrong, and was corrected on

- **Neither session was logged when it happened.** The figure and E5 stayed untracked on Đắt's machine for 11 and 8
  days, so the project deck (T06), which redraws the figure, depended on one laptop. This entry is the late log.
- **Session 26 (then numbered 25) took a number that `main` already had.** It was written on 21/10 without checking
  `main` for the next free number, and Khang's report 4.3 entry, merged first, had taken 25. The heading was
  renumbered and nothing else in the block changed. The merge commit says so, because the already-pushed `cf744d5`
  message still says "session 25".
- **E5 only reads the Parquet footers.** No Spark query filtering on price was timed. The file says this itself, and
  the slide table keeps it in the spoken line only, not as a measured skip.

### Judgement that stayed with the team

Đắt decided (sprint sheet, row T01, 2/11): bring E5 and `docs/figures/` to `main` inside PR #32 rather than a new PR,
and fix the duplicate session number while updating the branch. Then merge.

Made by AI, flagged for review:
- `main`'s Session 25 keeps its number because it reached `main` first; Đắt's E4 entry moved instead.
- The HTML still carries the indexing talk's labels ("Hình minh hoạ", the badges 02/03/04, "trang 16", "trang 17",
  "BRIN mới tạo, chưa đo"). They are part of F14 as presented. T06 removes them when it redraws the figure for the
  project deck.
- The Apache 2.0 licence is named in the HTML header but its text is not in the repo.

Carried forward:
- Session 26's carried-forward list is unchanged; nothing in it was touched here.

## Session 28 — 3 November 2026 (W45)

**Tool:** Claude Code (Opus 5.5).
**Scope:** sprint task T02. Rebuild Đắt's demo machine from the raw CSV, time each batch job, start the stream in the
README order, and check that all eight screens show real numbers. No application code was written or changed. The
timing script was run, and its source is appended to its evidence file.

### What the AI produced

| Artefact | Status |
|---|---|
| `docs/evidence/batch_timings.txt` — wall-clock time of the seven one-time batch jobs (`load_bronze.py` to `gold_br7.py`), run one after another on `main` @ `aa65472` with nothing else running. It includes each job's stdout and the script source | Run on Đắt's machine, 3/11 |
| The demo machine: Postgres and Cassandra up; `streaming_gold.py --fresh`, then after READY `replayer.py --speed 60 --start "2019-11-17 08:00:00"`; uvicorn on :8000; vite on :5173 | Run. The replayer and the streaming job were stopped once 17/11 (Vietnam time) had been replayed |
| `docs/AI_USAGE.md` — this session | AI-drafted |

### How it was checked

| Claim | How it was measured |
|---|---|
| The seven jobs take 426.5 s, of which `batch_warehouse.py`, with its Postgres load, takes 273.0 s | `batch_timings.txt` section 1: `date +%s.%N` before and after each job. It is one run, not a median |
| A re-run rebuilds the same data | `batch_timings.txt` section 2: every count each job prints equals the documented count. Silver has 4,754,015 rows in 31 dates and 93 directories. The facts have 4,754,015 / 970,797 / 1,909,650 rows. `dim_product` has 210,454 rows and `dim_user` 319,426, and every SCD2 check is 0 |
| Gold is current (BR2 and BR4 had been stale since 7/10, and BR7 was missing) | Section 2: `funnel_daily` 465 rows, `rfm_segments` 258,330, `stockout_risk` 63,655 (12,731 per warehouse), `product_affinity` 314 |
| All 8 screens show real numbers | Eight agents ran in parallel, one per screen. Each rendered it in headless Chromium over CDP, read the QueryMeta footer, and compared one number on screen with a direct `cqlsh` or DuckDB query taken at almost the same moment. All 8 matched, and the load footers ranged from 3.6 to 216 ms. Example: BR1 shows GMV 311.3K and 919 orders for 16:45-17:44 on 17/11, which is the sum of those minutes of `gmv_by_minute` (`category_l1 = 'all'`). BR2 shows 966,143 sessions, the sum of `funnel_daily` 'all' over 1-30 Nov |

### What the AI got wrong, and was corrected on

- **The first smoke test called each endpoint with no parameters.** BR1 and BR5 looked empty, BR7 returned 422 and BR4
  returned all 258,330 rows, but no screen sends a bare call like that. Each one sends a date (BR1, BR5, BR8), a product (BR7) or
  a segment and an R score (BR4). The verdict above comes from the rendered screens, not from that test.
- **The evidence header shows the raw CSV as "8.4G".** `du -h` counts in GiB. The file is 9,006,762,395 bytes, the 9.0 GB
  the docs give. The generated file was left as it ran, with this note as the explanation.
- **Stopping the replayer with `pkill -f 'ingestion/replayer.py'` also killed the shell running that command**, because
  the pattern was in the shell's own command line. The replayer did stop, and the streaming job was then stopped by PID.

### Judgement that stayed with the team

Đắt decided (sprint sheet, row T02, 2/11): re-run the whole chain once to time each job, and start the streaming job
before the replayer.

Made by AI, flagged for review:
- The replay starts at 17/11 08:00 UTC, the date the streaming screens open on. The streaming tables hold 17/11 from
  15:00 to about 00:50 Vietnam time. To demo again, run `streaming_gold.py --fresh` first.
- The timings are one run each, and the wall clock includes JVM start and stop. They answer "how long does the batch
  build take" and are not benchmark results. The benchmark with repeated runs is T12 and T14.
- Seen on the screens and left to their owners, since T02 changes no code:
  - **BR8:** `GET /api/br8/alerts` without `event_date` returns 500. `_latest_date()` returns the driver's
    `cassandra.util.Date`, which has no `isoformat()` (`serving/api/routers/br8.py` line 105); the screen always sends
    a date. The page logs React's "unique key" error, because the fragment in `rows.map` has no key. Its table and
    footer disappear during each 10 s refresh. Its subtitle says "rolling", but the windows are tumbling.
  - **BR3:** in Live mode the footer counts every window partition (126 at load, and growing), because the endpoint
    runs `SELECT DISTINCT window_start` to find the newest window. With a chosen window it reads 2.
  - **BR7:** there is no footer until an anchor product is clicked. **BR5:** the empty state has no footer.
  - **All screens:** at 1440 px the nav bar hides the BR8 tab. T08 regroups the nav.
  - Already in rows T09 and T10: BR6's cards count only the 100 rows read per warehouse; BR8 applies its severity filter
    after `LIMIT 500`; BR8's thresholds text; BR5's two Vietnamese strings; BR4's single snapshot.

Carried forward:
- The owner issues above, until T09 and T10 close them. Session 27's list is unchanged.

## Session 29 — 4 November 2026 (W45)

**Tool:** Claude Code (Opus 5.5).
**Scope:** sprint task T06: the skeleton of the project deck, the redrawn architecture figure, and the file the team
writes the deck's content in. No application code was written.

### What the AI produced

| Artefact | Status |
|---|---|
| Claude Slides deck "Group15_ShopInsight_Project": 26 pages in the report's 6 sections. Each page has its section, a working title, its speaker taken from row T20, and a dashed box naming its block in `docs/project_deck.md` and its sources. The agenda table and the BR pages' user group, path (batch or real time) and serving table are filled in; everything else is left to T20 | AI-built; Đắt reviews before the PDF goes to the team |
| `docs/figures/shopinsight_architecture.html` — F14 (`shopinsight_applied_map.html`) without the indexing talk's labels (02, 03, 04, "trang 16", "trang 17", "Hình minh hoạ") and without "đo trên 3 ngày dữ liệu; BRIN mới tạo, chưa đo". The PostgreSQL line now lists B+-tree, partial, BRIN and GIN, and its box is shorter. Rendered at 2x and placed on page 08 | AI-drawn; the render was viewed |
| `docs/project_deck.md` — one block per page (`## Trang NN · name · writer`) with empty fields for the title, up to 4 key points, the spoken lines and the syllable count, plus a source hint. It ends with "## Lỗi trình bày (không phải trang slide)" for T26 | AI-drafted |
| `docs/AI_USAGE.md` — this session | AI-drafted |

### How it was checked

| Claim | How it was measured |
|---|---|
| Deck and file agree page by page | A script compared `deck.json`'s order, each slide's speaker pill, its footer number and its title with the 26 `## Trang` headers of `project_deck.md`. All 26 match, and the per-person totals are Khang 7, Nguyên 8, Đắt 6, Tín 5 pages, as in row T20 |
| No indexing-talk label is left in the figure | `grep` finds "trang 16", "trang 17", "Hình minh hoạ" and "BRIN mới tạo" only in the header comment, which names what was removed |
| Postgres index types on the figure exist | `warehouse/ddl.sql`: GIN on `attributes jsonb_path_ops`, BRIN on `fact_event.event_time`, partial indexes (`WHERE is_current`, `WHERE event_type_key = 3`, ...) and B-tree |
| The BR pages' user groups, paths and tables | REPORT.md §1.2 (user groups) and the BR table in CLAUDE.md (layer and sink); table names from `serving/cassandra_schema.cql` and `data/gold/` |

### What the AI got wrong, and was corrected on

- **The figure first kept the PostgreSQL box at its old height.** With the BRIN line gone, the box had an empty
  third line. It was shortened from 122 to 88 px before the render that went onto the slide.
- Nothing else was found. The check that could have found a speaker or page-number mismatch between the deck and
  the file is the comparison above.

### Judgement that stayed with the team

Đắt decided (sprint sheet, rows T06 and T20, 2-3/11): the deck is Claude Slides; it follows the report's 6 sections;
the speaker split is the one in T20; `project_deck.md` holds the content.

Made by AI, flagged for review:
- **26 pages.** Section 4 has two data-model pages (concept and logic, then physical), not three. Section 5 has one
  page per BR, so each of the 8 gate2b screenshots gets a page. There are no section-divider pages.
- **Section 5 follows the owners' order** (BR1, BR2 · BR3, BR4 · BR5, BR7 · BR6, BR8), not the user-group order, so
  each person demos without a break.
- **Page 26 (references) is shown but not read.** It is listed under Nguyên with no spoken lines.
- **The cover's subtitle,** "Từ nhật ký hành vi mua sắm tới 8 màn hình trả lời dưới 2 giây", is a draft for Khang to
  keep or change. The members' full names and student IDs are a placeholder.
- **Typeface Be Vietnam Pro, for its Vietnamese diacritics;** the colours are the figure's navy and blue plus an orange
  speaker pill.

Carried forward:
- The PDF of the skeleton deck goes to the team Drive, exported from the deck by Đắt, and the post to the group is
  his. Session 28's list is unchanged.

## Session 30 — 5 November 2026 (W45)

**Tool:** Claude Code (Opus 5.5).
**Scope:** two changes Đắt asked for after seeing the T06 skeleton deck: fewer changes of speaker, so the video
needs fewer cuts, and a cover with the school's full name and logo. No application code was written.

### What the AI produced

| Artefact | Status |
|---|---|
| Claude Slides deck "Group15_ShopInsight_Project" — new page order and two pages that change speaker, with the speaker pills, footers, block numbers and agenda table updated to match | AI-edited after Đắt chose the option |
| The deck's cover — HCMUT logo (`Logo_BK_TPHCM.png` from Đắt's Drive, 320 × 320) with "Đại học Quốc gia Thành phố Hồ Chí Minh / Trường Đại học Bách khoa / Khoa Khoa học và Kỹ thuật Máy tính", on a white background that matches the logo's opaque white; title in the logo's navy, edge bar and rule in its blue | AI-edited |
| `docs/project_deck.md` — the blocks in the new order with their new numbers and writers; the assignment table now lists the eight speaking runs | AI-edited; block contents moved unchanged |
| `docs/AI_USAGE.md` — this session | AI-drafted |

### How it was checked

| Claim | How it was measured |
|---|---|
| Each person speaks in exactly 2 runs; 7 changes of speaker instead of 12 | A script reads `deck.json`'s order and the 26 `## Trang` headers: the runs are Khang › Nguyên › Đắt › Tín › Đắt › Nguyên › Khang › Tín |
| Deck and file still agree | The same script checks each edited slide's speaker pill, footer number and the block number in its text against the file's header: all 12 match. The other 14 slides kept their position, so their numbers did not change |
| The logo is the school's | The PNG was viewed: the "BK TP.HCM" mark in navy and blue on white |

### What the AI got wrong, and was corrected on

- **The first round of slide edits failed: the local copies of the slides were gone,** because `/tmp` was cleared
  overnight. Nothing was published. The 11 slides were read back from the deck (unchanged since 4/11), the edits
  were applied again, and only then published.

### Judgement that stayed with the team

Đắt chose, out of three options put to him: reorder and move two pages from Nguyên to Tín. Cassandra (page 12) moved
because both of Tín's BRs (BR6, BR8) write Cassandra. Kết luận (page 25) moved because it follows Tín's two evaluation
pages. The other options were reorder only (Nguyên would still speak in 4 runs) and Cassandra to Đắt.

Made by AI, flagged for review:
- **The faculty line** "Khoa Khoa học và Kỹ thuật Máy tính" is inferred from the course code CO5173; Đắt confirms
  or removes it.
- **Section 4 now shows Spark before Cassandra** (pipeline order), while report 4.2 is Cassandra and 4.3 is Spark.
- **Section 5 now starts with Tín (BR6, BR8),** so his Cassandra and alternatives pages lead straight into his demo.
- **Row T20 of the sprint sheet still lists the old split.** The sheet cannot be edited from here; Đắt updates it.

Carried forward:
- Session 29's list is unchanged.

## Session 31 — 6 November 2026 (W45)

**Tool:** Claude Code (Opus 5.5).
**Scope:** Khang's project-deck blocks (pages 01-04 and 20-22 of `docs/project_deck.md`, sprint row T20) and the
correctness check that page 22 cites (T19): a rebuild of the batch layers and one replay on Khang's machine, an
independent answer for each BR, and the SCD2 integrity of both dimensions.

### What the AI produced

| Artefact | Status |
|---|---|
| `checks/correctness_8br.py` (new) — DuckDB answer for each BR from silver (BR6: the inventory series), compared with the gold Parquet and Cassandra tables the screens read; matched / max(answer, stored) per BR, threshold 99% | Run and verified |
| `docs/evidence/correctness_8br.txt` (new) — the run, the eight scores, BR4's raw-value limitation, a run that is meant to fail, SCD2 for both dimensions | Captured from the run |
| `docs/project_deck.md` pages 01-04, 20-22 — title, up to four points, spoken lines and syllable count each; 549 syllables in total against the file's 540 | AI-drafted, Khang reviews |
| `docs/AI_USAGE.md` — this session | AI-drafted |

### How it was checked

| Claim | How it was measured |
|---|---|
| The system side is current | Khang's machine on `main` at 3e632d8. `batch_warehouse.py` wrote all nine Parquet tables with every check at its expected value (step 6 stopped on a Postgres without the star DDL; no BR reads Postgres); `batch_gold.py` printed GOLD OK and `gold_br7.py` BR7 OK; `streaming_gold.py --fresh` ran 4 of 4 jobs while the replayer sent 78 files, 187,468 rows, 17 Nov 15:00-21:30 Vietnam time, as in `gate2a_br5_run.txt`. bronze, silver, catalogue and inventory were reused: their scripts are unchanged since those files were written (`git log` per script) |
| All eight BRs match 100% | `python checks/correctness_8br.py` with the replay span and the final watermark 21:19:59 (BR3's last batch replaced the windows up to 21:00-21:04). BR2 465, BR4 258,330, BR6 63,655, BR7 314 rows over the whole month; BR1 4,563, BR3 7,580, BR5 2,600, BR8 5,815 over the replay |
| The answer does not reuse the system's code | The script imports nothing from `processing/`. BR6's units sold come from the inventory balance (stock yesterday + received - stock today), not from the warehouse hash; BR5's 2,600 equals the count Dat's Gate 2a run found |
| The check can fail | The same run with the watermark ten minutes early: BR3 97.36%, BR5 96.77%, exit 1 |
| SCD2 is intact | `checks/scd2_integrity.py` on `dim_product`: all six counts 0, SCD2 OK. `dim_user`: the same six counts, all 0, in `batch_warehouse.py`'s output |
| BR4's raw values | DuckDB, `rfm_segments` against `stg_rfm_snapshot` at 30 Nov: recency differs for 23,198 users, frequency or monetary for 590, any for 23,353; Session 17 found the same 23,198 and 590 |
| The deck blocks' numbers | Page 03 from REPORT §1 "Nguồn số liệu của mục 1"; page 04 from §1.2; page 20 from BR_SCOPE BR3 and the code (`F.window(..., "15 minutes", "1 minute")`, key `(window_start, rank)`); page 21 from BR_SCOPE BR4 and `BR4Page.tsx` (the heatmap is r_score by f_score); page 22 from the evidence file above. Syllables counted by a script over each spoken block |

### What the AI got wrong, and was corrected on

- **The first float comparison rounded to four significant digits,** while the docstring promised a 1e-4 relative
  tolerance. Three of BR6's 63,655 rows (days such as 5.6875, stored by Cassandra's 32-bit float as 5.68749) fell
  on either side of a rounding boundary. The comparison now uses `math.isclose(rel_tol=1e-4)`, as documented.
- **The first draft of the spoken lines ran to 583 syllables before page 22.** Pages 02-04, 20 and 21 were cut to
  bring the seven pages to 549.

### Judgement that stayed with the team

Made by AI, flagged for review:
- **The answer for BR3 and BR5 stops at the stream's final watermark,** because both write a window only once the
  watermark closes it. A replay that stops earlier or later needs that watermark passed again.
- **BR4 scores the heatmap fields (scores and segment), and reports the raw values beside them.** The raw values'
  90.96% is the `dim_user` projection Khang kept on #17 (18 Oct), not a fault of BR4's query; it belongs in
  report section 6's limitations.
- **The cover's title** is the draft Session 29 proposed for Khang; the GV line keeps the presentation deck's
  "PGS.TS.".

Carried forward:
- Session 30's list is unchanged.

## Session 32 — 8 November 2026 (W45)

**Tool:** Claude Code (Opus 5.5).
**Scope:** Dat's review of PR #36, Khang's correctness check (Session 31). At Dat's request the AI fixed the
review's two points on the PR branch, replayed 17 Nov again and re-ran the check on Dat's machine, for Dat to
merge. No BR code was changed.

### What the AI produced

| Artefact | Status |
|---|---|
| `checks/correctness_8br.py` — money compared exactly as a Decimal, not as a float under the 1e-4 tolerance; the score divides by rows, not distinct keys; the `differs` lines print plain values | Run and verified |
| `docs/evidence/correctness_8br.txt` — a reviewer re-run section below Khang's run | Captured from the run |
| `docs/AI_USAGE.md` — this session | AI-drafted |

### How it was checked

| Claim | How it was measured |
|---|---|
| Money was compared more loosely than the docstring said | DuckDB over silver: the busiest `'all'` minute of 17 Nov 15:00-21:30 Vietnam time is 11,782.53, so 1e-4 relative let it be 1.18 off. With that row's `gmv` raised by 1.00 in Cassandra, the check at the PR head still matched BR1 4,563 of 4,563; the fixed check matched 4,562 (99.98%). The value was put back and BR1 returned to 100% |
| A duplicated row was invisible | `score()` on one answer row against the same row stored twice: 100% before the fix, 50% after |
| The fix changes no number in Khang's run | Khang's replay repeated on Dat's machine (78 files, 187,468 rows, final watermark 21:19:59): the check before and after the fix print the same eight rows, all 100%, and BR4's raw values at 90.96% |
| The gold Parquet tables hold one row per key, so the row-based score changes nothing today | DuckDB: `funnel_daily` 465, `rfm_segments` 258,330, `product_affinity` 314 rows, each equal to its count of distinct keys |

### What the AI got wrong, and was corrected on

- **The replay script's summary printed the watermark 21:14:59,** the last one a log line showed (batch 77). The
  final batch 78 carried no new events and closed the BR3 windows up to 21:00-21:04, so the final watermark was
  21:19:59, as Khang recorded; the check was run with 21:19:59.

### Judgement that stayed with the team

- **Dat** asked for the fixes to go on Khang's branch and for the PR to be merged after the re-run.
- Khang's run stays the record for report section 6: the correctness comparison is run by its owner. The re-run on
  Dat's machine is a reviewer's reproduction. Whether Khang re-runs the fixed check on his machine before the
  report quotes it is Khang's call; on this data it printed the same numbers.

Carried forward:
- Session 31's list is unchanged.

## Session 33 — 8 November 2026 (W45)

**Tool:** Claude Code (Opus 5.5).
**Scope:** Dat's review of PR #39, Nguyen's T13 ground-truth check and T09 BR7 sort. At Dat's request the AI fixed
the review's points on the PR branch, re-ran the check on Dat's machine and merged the PR. The AI did not change
any BR code. The BR7 sort (lift first) is Nguyen's change, and the AI checked it.

### What the AI produced

| Artefact | Status |
|---|---|
| `checks/ground_truth.py` — BR8 takes a required `--replay-start` and `--replay-end` instead of counting every window since midnight; every line counts missing, extra and duplicated stored rows against the score; BR7 applies gold_br7's cut-offs and compares support; money compared exactly; MISS and INCOMPLETE when a BR cannot run; module docstring | Run and verified |
| `docs/evidence/ground_truth_run.txt` — header for Tin's run, then a reviewer re-run: before and after the fix on the same replay, wrong spans, one mutation at a time, Cassandra unreachable | Captured from the runs |
| `docs/AI_USAGE.md` — this session | AI-drafted |

### How it was checked

| Claim | How it was measured |
|---|---|
| The check at the PR head gives a false LOW for BR8 after `./run_demo.sh stream` | Cassandra holds the 15:00-21:30 Vietnam-time replay of PR #36's re-run (`order_velocity_alerts` 5,815 rows, 15:00-21:25). `python checks/ground_truth.py --replay-end "2019-11-17 21:30:00"` at c7e11be printed `LOW BR8 65.60% (5,649/8,611)`. On the same replay, correctness_8br.py scores BR8 100%. Silver holds 2,962 (window, user) purchase pairs before 15:00 that the stream never received |
| The fixed check passes on correct data | Same replay: `--replay-start "2019-11-17 15:00:00" --replay-end "2019-11-17 21:30:00"` printed BR4 31,005, BR6 63,655, BR7 314 and BR8 5,815 of 5,815, then GROUND TRUTH OK. It was run before and after merging origin/main 0511e42 into the branch |
| The fixed check fails on wrong data | A mutation harness fed the unchanged module mutated copies of the gold Parquet and of the Cassandra rows (`data/` and Cassandra only read): one value off, a missing row, an extra row, an exact or stale duplicate, a stream with a different threshold, a stream that died at 18:00. Every case moved matched/total. The one exception is a duplicated BR8 row, which the primary key makes impossible to store. Per-case figures are in the evidence file |
| BR7 now sorts as API_CONTRACT §9 says | `serving.api.routers.br7.get_affinity(1005115)` returned 10 rows with lift descending (top row: 1005230, co_count 3, lift 4.07) in 18.7 ms; an unknown id returns `[]`. `npx tsc -b --noEmit` in `web/` exited 0 |
| The numbers in Tin's run hold | DuckDB: `rfm_segments` has 31,005 buyers, `product_affinity` 314 rows, stockout_risk's last day 12,731 × 5 = 63,655 rows. Silver has 4,144 closed purchase pairs on 17 Nov up to 16:44:47, the count a replay from midnight gives |

### What the AI got wrong, and was corrected on

- **The AI's first fix kept two blind spots, and its own docstring hid them.** That docstring said every line counted a
  duplicated stored row, but BR4's `FULL JOIN ... count(*)` still scored `rfm_segments` 100% with every buyer row
  doubled (62,010/62,010). Its BR8 defaults also took the replay span from the table under test, so a stream that
  died mid-replay scored 100%. Three independent reviewer agents found the BR4 gap; mutation testing found the BR8
  one. Every such finding was upheld by two refuting agents. BR4 now counts each matched buyer once over the larger
  row count (every row doubled gives 50%), and the span flags are required.
- **The first fix said BR8 compares windows "closed by the watermark".** BR8 writes in update mode, so a stored row
  is final once all its window's events were replayed. The extra 10-minute cut dropped complete windows and kept one
  the watermark had not closed. The filter is now "the window lies inside the replay".
- **The PR's comment gave the wrong reason for BR7's DISTINCT.** It cited the 7,312 exact duplicates in silver, but
  only one of those is a purchase. The DISTINCT counts a repeat buy in one session once, as gold_br7 does.

### Judgement that stayed with the team

- **Dat** asked for the fixes to go on Nguyen's branch and for the PR to be merged after them.
- The review's other suggestion was to drop `ground_truth.py`, because `checks/correctness_8br.py` (#36) already
  covers these four BRs and more. Dat asked for it to be fixed, so it stays, and two checks now overlap:
  - `ground_truth.py` checks BR4's raw values as of each user's stored snapshot.
  - `correctness_8br.py` checks the scores and segment, and its "BR4 raw" line measures the values as of 30 Nov (90.96%).

  Which one T19 and report section 6 quote is the team's call.
- The re-run on Dat's machine is a reviewer's reproduction. T19 is Nguyen's: the owner runs the fixed check, with the
  span of the owner's replay.
- **Open:** the PR title promised a BR5 fix that is not in it. On main, BR5's screen still shows two Vietnamese
  strings, which T09 asks Nguyen to translate. Nguyen should also add a line here if the T13 commits were
  AI-assisted; this file does not say.

Carried forward:
- Session 31's list is unchanged.

## Session 34 — 10 November 2026 (W46)

**Tool:** Claude Code (Opus 5.5), one agent writing and an independent reviewer agent.
**Scope:** sprint task T03, done for Tín at Dat's request: finish PR #30 on Tín's branch `w41-benchmark-4-4` so that
main holds no benchmark or survey number without a real measurement behind it. No application code was changed.

### What the AI produced

| Artefact | Status |
|---|---|
| `benchmark/results/w41_benchmark_queries.md` — every p50/p95, every "10 lần đo" heading and the 10-run harness (which called the 10th run "p95") removed; each result block now points at `benchmark/run_benchmark.py` (T12). Versions match `requirements.txt`. The Cassandra "wrong key" config is the same question on `gmv_by_minute` with `ALLOW FILTERING`, not `bloom_demo`. Says plainly that no flat table exists | AI-drafted, reviewed by a second agent |
| `docs/EVALUATION_SURVEY.md` — the BR8 task expands one alert to its 5-minute window totals, as `BR8Page.tsx` shows; one check question added for that step | AI-drafted, reviewed |
| `benchmark/plot_benchmark.py` — the seven hardcoded numbers are gone; it reads the newest `summary_*.csv` (`system,query,variant,runs,p50_ms,p95_ms`) and builds the footnote from the `runs` column. matplotlib stays an optional, unpinned dependency | Run and verified on a fake CSV in a throwaway venv; nothing committed from that run |
| `benchmark/verify_duckdb_star.py` — `--warehouse-dir`, expected counts measured now, no emoji | Run and verified |
| `benchmark/results/w41_benchmark_environment.md` — the guessed CPU is replaced by "the env file of the run" | AI-drafted |

### How it was checked

| Claim | How it was measured |
|---|---|
| The star tables hold dim_date 92, dim_event_type 5, dim_warehouse 5, dim_product 210,454, dim_user 319,426, fact_event 4,754,015, fact_session_funnel 970,797, fact_inventory_daily 1,909,650 rows | `.venv/bin/python benchmark/verify_duckdb_star.py --warehouse-dir data/warehouse` printed `DUCKDB STAR OK` |
| No unmeasured timing is left on the branch | `git grep -nE 'p50 ≈|p95 ≈|10 lần|10 runs'` and a wider grep (times[9], 0.10, bloom_demo, Ryzen, 127,693, 244,025) found nothing |
| The plot script reads only the CSV | Run in a scratch venv with matplotlib against a fake 8-row summary; it exits 1 with a clear message when the CSV is missing or has other columns |

### What the AI got wrong, and was corrected on

- The script's old expected count for `dim_event_type` was 4. The build has 5 rows (DuckDB count), so the check had
  been failing silently on the real data. The new count is measured.
- The reviewer noted that `LIMIT 60` on the wrong-key query can stop after the first matching partition, which
  understates a full scan. T12 times the query without the LIMIT.

### Judgement that stayed with the team

- **Dat** asked for T03 to be done for Tín on Tín's own branch and merged when the review passed.
- The plot script is kept because the T03 row says to keep it. Whether to commit a chart is Dat's call once T14's
  real CSV exists.

## Session 35 — 10 November 2026 (W46)

**Tool:** Claude Code (Opus 5.5), one agent writing and two independent reviewer agents.
**Scope:** sprint task T12 (Dat's): the query benchmark harness. New files only under `benchmark/`; no application
code was changed. The official 3 + 20 run is T14's and is logged with it.

### What the AI produced

| Artefact | Status |
|---|---|
| `benchmark/queries.sql` — 21 named blocks: Postgres star (one-day count with and without partition pruning; one hour of `event_time` by Seq Scan, BRIN and a temporary B-tree; `attributes @>` with and without GIN; revenue by category over 1, 7 and 31 days), DuckDB on the Parquet star (hive pruning vs `date_key`, min/max on `event_time`, the struct filter on `attributes`, 1/7/31 days), Cassandra right vs wrong partition key on `gmv_by_minute` and `stockout_risk`. Each block carries `expect` lines that the runner checks against the plan or trace | Run (test sizes) and verified |
| `benchmark/run_benchmark.py` — plain functions; 3 untimed warm-up runs then 20 timed runs per variant, nearest-rank p50/p95; writes `raw_<ts>.csv`, `summary_<ts>.csv` (`system,query,variant,runs,p50_ms,p95_ms`, extra columns after), `env_<ts>.txt` and `plans_<ts>.txt`; drops the temporary B-tree in `finally` | Run (test sizes) and verified |
| `benchmark/README.md` — how to run, what each variant shows, the output format | AI-drafted |

### How it was checked

| Claim | How it was measured |
|---|---|
| Every forced variant really gets its plan | `run_benchmark.py --runs 2 --warmup 1 --out-dir <scratch>`: all 21 blocks printed `plan check: OK`. A reviewer reran `--runs 1 --warmup 1` and read every plan: pruning_on reads only `fact_event_20191129`, pruning_off opens all 32 partitions, brin is a Bitmap Index Scan on the per-day BRIN, btree an Index Scan with no Bitmap node, gin a Bitmap Index Scan on `ix_dim_product_attrs`, DuckDB hive_pruning `Scanning Files: 1/31` |
| Postgres and DuckDB answer the same question | The reviewer compared results: one hour 7,087 rows / 2,002,997.66 in both; `space_grey` 21,489 in both; one day 131,796 in both; the 7-day top 3 categories equal to the cent |
| The temporary index never survives | A timed `SELECT 1/0` inside the btree variant raised, and `pg_indexes` then held no `bench_fe_time_btree` |
| Nearest-rank percentile is right | Compared with `ceil(p*n/100)` for n = 1..2000 at p = 50, 95, 99 |

### What the AI got wrong, and was corrected on

- The task brief said `WHERE warehouse_id = 'wh1'`. `stockout_risk.warehouse_id` is an int (`serving/cassandra_schema.cql`),
  so the query uses `warehouse_id = 1`.
- The first test run failed its own BRIN check: the empty `fact_event_default` partition gets a Seq Scan. The
  `expect` line now forbids a Seq Scan on the day partitions only.
- `--runs 0` crashed with an IndexError (reviewer). It is now rejected by the argument parser.
- Limits found in review that the report must state rather than hide: pruning_off probes 31 partitions through an
  index and returns 0 rows from them, so its gap is not the whole value of pruning; `space_grey` matches about 10%
  of products, so GIN's gain is modest; `gmv_by_minute` holds one replayed day, so its wrong-key scan is small and
  the clear wrong-key contrast is `stockout_risk`; the btree setup's `ANALYZE fact_event` refreshes statistics for
  good.

### Judgement that stayed with the team

- **Dat** set the protocol in the sprint sheet (3 warm-up + 20 timed runs) and asked for the benchmark to run on his
  machine with nothing else on the CPU (T14).
- The choice of queries follows the T12 row; the extra Cassandra trace in the plans file goes beyond it, flagged for
  Dat's review.

## Session 36 — 10 November 2026 (W46)

**Tool:** Claude Code (Opus 5.5), one agent writing, one reviewer agent and one data-fact-checker agent.
**Scope:** sprint task T04, done for Khang at Dat's request: the report skeleton for sections 4.4-6, the BR8 wording
in three documents, BR7 in the section 4.1 diagram, and a measured Big Data subsection. Documents only.

### What the AI produced

| Artefact | Status |
|---|---|
| `docs/REPORT.md` — empty headings 4.4, 4.5, 5, 6.1-6.4 and Tài liệu tham khảo, each with the task and writer; §2.8 BR8 expands an alert to its 5-minute window totals; the §4.1 diagram and the line after it credit BR7 to `gold_br7.py`; new §3.5 "Đặc trưng Big Data" with its rows in §3's source table | AI-drafted, reviewed, numbers re-measured by a second agent |
| `docs/BR_SCOPE.md` line 16, `SYSTEM_DESIGN.md` §9 — BR8 opens an alert to its window totals, not to a list of orders | AI-drafted, checked against `web/src/pages/BR8Page.tsx` |
| `CLAUDE.md` — the open BR8 decision is recorded as closed | AI-drafted |

### How it was checked

| Claim | How it was measured |
|---|---|
| Raw file: 67,501,979 rows, 9,006,762,395 bytes (9.0 GB, 8.39 GiB; `du -h` prints GiB) | DuckDB `count(*)` over `read_csv('data/raw/2019-Nov.csv')`; `ls -l` |
| 32.44% of raw events lack `category_code` (21,898,171); 32.32% in bronze; 32.27% `unknown` in silver | DuckDB `count(*) FILTER (WHERE category_code IS NULL)` on raw and bronze; `category_l1 = 'unknown'` on silver |
| Bronze 4,767,012 rows (7.06% of raw), silver 4,754,015 | DuckDB over the Parquet directories |
| The demo replay sends about 481 events per wall-clock second | 187,468 rows in 78 files (`docs/evidence/correctness_8br.txt`, cross-checked with DuckDB over `data/stream_landing/*.json`), one file every 5 s (`ingestion/replayer.py`) |
| Nested JSON exists only in the catalogue | `DESCRIBE read_json('data/catalog/products.json')`: `attributes` is a STRUCT holding a STRUCT, a STRUCT and a VARCHAR[]; the replayer's lines are flat and leave out null fields |

### What the AI got wrong, and was corrected on

- The sprint sheet says "32.4%" with no population and "JSON lồng nhau" for the data in general. The 32.4% holds
  only for the full raw file, and nesting exists only in the generated catalogue. The report states each figure with
  its population and says where the JSON is nested. Dat's brief carried the sheet's wording.
- `.claude/skills/br-slice/SKILL.md` line 111 still says BR8 expands "to the underlying orders". It was outside the
  task's file list and is left as a follow-up.

### Judgement that stayed with the team

- **Dat** decided on 10 Nov, by asking for this task, that BR8's screen stays as built (window totals) and the
  documents follow it. That closes the decision CLAUDE.md had open.
- The Big Data text is a numbered §3.5 rather than an unheaded paragraph. That was the AI's choice, flagged for
  Khang, who owns the report.

## Session 37 — 10 November 2026 (W46)

**Tool:** Claude Code (Opus 5.5), one agent writing and one reviewer agent.
**Scope:** sprint task T07's leftovers, done for Tín at Dat's request: `run_demo.sh` could not start Spark on a
machine without `JAVA_HOME`, and its stream logs had no wall-clock time; plus a stale docstring and a stale DDL
comment. No Spark or API logic changed.

### What the AI produced

| Artefact | Status |
|---|---|
| `run_demo.sh` — `JAVA_HOME` kept if set, else derived from `java` on PATH, else macOS `java_home -v 21`, else a clear error; every line of `logs/stream_*.log` and `logs/replayer_*.log` stamped with local wall-clock time to the millisecond, through process substitution so `$!` stays the python PID; READY detection follows the stamp | Tested in isolation; the real `stream` run is T14's |
| `processing/batch_warehouse.py` — the module docstring describes today's nine tables, checks, step 6 and `WAREHOUSE OK` instead of "WAREHOUSE PARTIAL: 6 of 9" | AI-drafted, reviewed against the code |
| `warehouse/ddl.sql` and `SYSTEM_DESIGN.md` §5.4 — "128,972 products -> 210,454 versions", measured 10 Nov | Measured |

### How it was checked

| Claim | How it was measured |
|---|---|
| This machine has no `JAVA_HOME`, and the derived one is JDK 21 | `readlink -f /usr/bin/java` gives `/usr/lib/jvm/java-21-openjdk-amd64/bin/java`, whose `-version` is 21.0.12.1 |
| The stamper keeps the right PID and READY still works | A fake python printing to stdout and stderr: `$!` was the python PID, READY was seen after 2 s, `stop` killed python and nothing was left running; a fake that exits early hits the die branch |
| dim_product has 128,972 products in 210,454 versions | `count(*), count(DISTINCT product_id)` in DuckDB on `data/warehouse/dim_product` and in Postgres `dim_product`: both (210454, 128972) |
| `infra` still works | `./run_demo.sh infra` printed `INFRA OK`, `APPLY_SCHEMA OK` |

### What the AI got wrong, and was corrected on

- The first commit changed the count only in `ddl.sql`. `ddl.sql`'s header says its body is SYSTEM_DESIGN §5.4-5.5
  verbatim, so the reviewer flagged the drift; §5.4 now carries the same comment. README line 167 and
  SYSTEM_DESIGN line 92 still have the old count; T21 (Tín) owns them.
- Reviewer notes left as known limits: the stamper needs bash 5 (Ubuntu 26.04 has 5.3; stock macOS bash 3.2 would
  fail), and the stamp is local time while the replayer prints event times in UTC.

### Judgement that stayed with the team

- **Dat** asked for these fixes inside T07's scope during the code freeze; the timestamped log is in T07's own
  description ("log có giờ thực").

## Session 38 — 10 November 2026 (W46)

**Tool:** Claude Code (Opus 5.5), one agent writing and one reviewer agent.
**Scope:** sprint task T08, done for Khang at Dat's request: the navigation grouped by the four user groups, the
header text, and the unused `UnderDevelopment` component removed. Web only; no page component was edited.

### What the AI produced

| Artefact | Status |
|---|---|
| `web/src/App.tsx` + navbar styles — four labelled groups: Executives (BR1); Marketing (BR2, BR4, BR5); Merchandising (BR3, BR7); Operations & Risk (BR6, BR8); header "CO5173 · Group 15" | Built and looked at |
| `web/index.html` — title "ShopInsight · CO5173 · Group 15" | Built |
| `web/src/components/UnderDevelopment.tsx` — deleted, with the CSS only it used | Built; grep finds no reference |

### How it was checked

| Claim | How it was measured |
|---|---|
| It builds and the fixtures still validate | `npm run build` (tsc -b + vite build) passed; `npm run lint` printed nothing; `python tests/test_fixtures.py` printed "All 8 fixture bundles passed validation." |
| The groups render at every width | vite on a spare port, screenshots with Playwright's headless Chromium at 1440, 1366, 900 and 390 px wide; at 1440 all four groups fit on one row, where BR7 and BR8 had been cut off before |
| Nothing else still uses the removed names | `grep -rn 'UnderDevelopment\|under-dev\|Team 15'` outside node_modules, .git and dist: no match |

### What the AI got wrong, and was corrected on

No defect was found in review. What could have found one: the reviewer checked the group order against the T08
row, the active-tab state on each route, the 390 px layout, and that no `BR*Page.tsx` file changed. Left as a
known limit because of the code freeze: at phone width the active tab is not scrolled into view.

### Judgement that stayed with the team

- **Dat** set the four groups and their BRs in the T08 row.
- The 900 px media query no longer turns the header into a column, because the header now wraps by itself. That was
  the AI's choice, flagged for Khang.

## Session 39 — 10 November 2026 (W46)

**Tool:** Claude Code (Opus 5.5), one agent writing and two reviewer agents.
**Scope:** the code part of sprint tasks T09 and T10, done at Dat's request for Khang (BR4), Nguyen (BR5) and Tín
(BR6, BR8): six small fixes found by reading the code. No new endpoint or feature. The owners' hands-on checks of
their own screens are not part of this session.

### What the AI produced

| Artefact | Status |
|---|---|
| `web/src/pages/BR4Page.tsx` + `docs/BR_SCOPE.md` line 12 — the snapshot is picked from `STORED_SNAPSHOTS = ['2019-11-30']` (kept in step with `batch_gold.LAST_SNAPSHOT`) instead of a free date that gave an empty page | Built |
| `web/src/pages/BR5Page.tsx` — the three Vietnamese strings in English | Built |
| `serving/api/routers/br6.py` + CLAUDE.md — per warehouse, a second read `days_to_stockout >= 9999 LIMIT 5`, skipped when `max_days < 9999`, de-duplicated by `product_id`; the no-sales SKUs now reach the screen | Run live and verified |
| `BR6Page.tsx`, `BR8Page.tsx` — the table stays on screen during a refresh (BR5's pattern); a filter change clears both the rows and the error; BR8's expanded row keyed by `window_start-user_id` in a keyed Fragment | Built; not yet clicked through in a browser |
| `document.title` on the seven pages that had none, equal to each page's heading | Built |

### How it was checked

| Claim | How it was measured |
|---|---|
| The no-sales rows appear, and only when they should | uvicorn from the branch on a spare port. `GET /api/br6/stockout`: partitions 5, rows 525, 105 per warehouse of which 5 at 9999. `warehouse_id=1`: 105 rows, 5 at 9999. `max_days=7`: 500 rows, none at 9999. `max_days=9998.9`: none at 9999; `max_days=9999`: included. No duplicate (warehouse_id, product_id); days non-decreasing. A reviewer repeated these on its own port |
| Build and fixtures | `npm run build` passed; `python tests/test_fixtures.py` printed "All 8 fixture bundles passed validation." |
| Titles match headings | The reviewer read all seven: Real-time Operations, Conversion Funnel, Trending Products, RFM Segments, Abandoned Carts, Inventory Alerts, Risk Alerts |

### What the AI got wrong, and was corrected on

- The brief said `warehouse_id=wh1`; the API takes an int 1-5 (HTTP 422 otherwise). Tests used `warehouse_id=1`.
- After a failed request, changing a filter kept the old error banner and hid the first-load spinner (reviewer). A
  filter change now clears the error too, in BR6 and BR8. BR5 has the same gap and was left alone.
- Known limit, unchanged: the merged BR6 rows sort on the raw float, so two rows whose rounded days match can show
  out of `product_id` order.

### Judgement that stayed with the team

- **Dat** listed these fixes in the T09 and T10 rows and asked for them during the code freeze.
- One list option, not an endpoint that lists snapshots, was the AI's choice to respect the freeze; flagged for Khang.
- Still owed by people, not code: each owner clicks through their screens and posts "BRx: đạt n/n" (T09). Dat's BR1
  and BR2 are checked during T14.

## Session 40 — 10 November 2026 (W46)

**Tool:** Claude Code (Opus 5.5), in Dat's session on Dat's machine.
**Scope:** sprint task T14 (Dat's), the measurement session: the query benchmark, the 8 screens timed and
photographed, the correctness and integrity checks, Postgres against Parquet, streaming throughput and latency, plus
Dat's T09 self-check of BR1 and BR2 and T10's High-filter check. **Dat chose (10 Nov) that Claude types the commands
and Dat reviews the raw output before the PR is merged**, a departure from this file's standing rule that the owner
runs the measurements; the PR is held for that review. No application code was changed.

### What the AI produced

| Artefact | Status |
|---|---|
| `benchmark/results/{raw,summary,env,plans,stdout}_20261110_010557.*` — the official `run_benchmark.py` run: 21 variants, 3 warm-up + 20 timed each, 21 of 21 plan checks OK, at clean 02b22f1 | Run; awaiting Dat's review |
| `docs/evidence/gate2b_curl_raw.txt` — 8 endpoints, 3 warm-up + 20 timed calls, QueryMeta ms and curl round trip; BR4's five per-R-score calls the screen really makes, measured separately | Run; awaiting review |
| `docs/evidence/gate2b_br1.png` … `gate2b_br8.png` — each screen with its QueryMeta footer | Captured; tables cut to 15 rows in the image only |
| `docs/evidence/t14_checks.txt`, `ground_truth_run.txt` (appended) — correctness_8br, ground_truth, SCD2 on both dimensions, fact_event_spot | Run |
| `docs/evidence/pg_vs_parquet_counts.txt` — the 8 star tables, Postgres vs Parquet | Run |
| `docs/evidence/streaming_perf.txt` + `t14_logs/` — throughput and micro-batch latency from the timestamped logs of two replays | Run |
| `docs/evidence/t09_t10_live_checks.txt` — BR1 3/3, BR2 2/2, BR8's first High alert 81 s into the replay | Run |

### How it was checked

| Claim | How it was measured |
|---|---|
| Every screen answers under 2 s | `gate2b_curl_raw.txt`: the slowest call of all 160 is BR4's unfiltered endpoint, 1,067.7 ms; the screen's own BR4 calls max 57.5 ms |
| All 8 BRs match an independent answer at 100% | `correctness_8br.py --replay-start "2019-11-17 15:00:00" --replay-end "2019-11-17 21:30:00" --watermark "2019-11-17 21:19:59"` after each of two replays; `ground_truth.py` OK for BR4, BR6, BR7, BR8 |
| The replay sends what the 6 and 8 Nov runs sent | Replayer log: 78 files, 187,468 rows, stopped by SIGINT right after file 78, as the earlier runs record |
| The benchmark measured the intended plans | `plans_20261110_010557.txt`: `plan check: OK` 21 times |
| Streaming keeps up with the replay | `streaming_perf.txt` run 1: BR1 and BR5 483.0 events/s against an offered 480.7 rows/s; triggerExecution p95 800-1,252 ms |

### What the AI got wrong, and was corrected on

- The first draft of `gate2b_curl_raw.txt` said BR4's screen asks for "one cell's list". `BR4Page.tsx` loads the
  heatmap with five calls, one per R score. The note was rewritten, and those five calls were measured instead of
  described.
- The first screenshots were full-page images up to 26,546 px tall, unreadable. The script now hides table rows
  after the 15th in the image only; each footer still shows the full row count, and the evidence files say so.
- The stream logs were first copied as `*.log`, which `.gitignore` drops; they are committed as `.txt`.
- The `time_screens` heredoc briefly re-ran the read-only BR1 browser check by mistake; it changed nothing.

### Judgement that stayed with the team

- **Dat** decided the protocol (sheet rows T12 and T14) and that Claude runs it with Dat reviewing; the PR waits for him.
- AI-made choices flagged for Dat: run 1 is quoted for streaming, because run 2 shared the CPU with the app and a
  browser; BR4's unfiltered endpoint is reported next to what the screen really calls; the 15-row cut in the images.
- Not measured: an overload test of the stream (the `proc/s` column is headroom per batch, not a ceiling).

## Session 41 — 10 November 2026 (W46)

**Tool:** Claude Code (Opus 5.5): one agent writing, two reviewer agents, one fixer, and the main session.
**Scope:** sprint tasks T19 (done for Nguyên) and T17 (done for Tín), written from T14's raw output. Nothing was
re-measured. Documents only. First, a record: **Dat reviewed PR #45's raw output on 10 Nov and approved it** ("Các số
liệu khá tốt. Duyệt"), and it was merged after that, as Session 40 said it would be.

### What the AI produced

| Artefact | Status |
|---|---|
| `docs/evidence/correctness_8br.txt` — appended "10 November 2026: the nine-row table (T19)": BR1-BR8 from today's correctness_8br.py run, SCD2 as row 9 (6 checks × 2 dimensions), the BR4 raw-values line with its recorded reason, the ground_truth.py cross-check, excerpts of the four older gate files, the run-2 repeat. Earlier sections untouched apart from a one-line note that their BR8 rows used the old thresholds | AI-drafted from run output, reviewed |
| `docs/evidence/gate2b_screens.txt` — 8 lines: store, partitions, QueryMeta and curl p50/p95, under 2 s, screenshot | AI-drafted from `gate2b_curl_raw.txt` |
| `docs/evidence/perf_table.md` — the performance table in five columns for report section 6.2 | AI-drafted |
| `docs/evidence/README.md` — one line per evidence file: date, machine, data, runs, what it proves | AI-drafted |

### How it was checked

| Claim | How it was checked |
|---|---|
| The nine rows equal the run's output | Main session compared every row with `t14_checks.txt` run 1, and the six SCD2 check names with `checks/scd2_integrity.py` lines 23-42 |
| gate2b_screens's eight lines equal the timing output | Main session compared them with the summary and the BR4 per-R-score block in `gate2b_curl_raw.txt`; BR4 shows the worst of the five calls per column |
| Thresholds are not invented | Reviewer searched CLAUDE.md, PLAN.md, SYSTEM_DESIGN.md, EVALUATION_SURVEY.md; rows without a documented threshold say so |
| PR merges cleanly onto main after #45 | `git merge-tree` and GitHub MERGEABLE/CLEAN |

### What the AI got wrong, and was corrected on

- The first `perf_table.md` said Cassandra's right-key and wrong-key variants "ask the same question". They are two
  different queries (`benchmark/queries.sql`); a reviewer caught it and the row was rewritten.
- `gate2b_screens.txt` said "nothing else running" for the whole block, but BR4's per-R-score calls ran later, after
  the second replay. The header now says when, and that the stream had been killed at 01:29:35 (the time comes from
  the stop command's output; the stream log's last batch is 01:28:10).
- Both data-fact-checker reviews of this PR crashed without a result (the reviewer ended without returning its
  verdict). The main session's own comparison above stands in for them, flagged for Nguyên and Tín to re-read.

### Judgement that stayed with the team

- **Dat** asked for T17 and T19 to be done on Nguyên's and Tín's behalf.
- AI-made and flagged: the nine-row table counts SCD2 as checks passed out of checks (12/12), since SCD2 has no
  answer-vs-stored rows; whether report section 6.1 quotes this table or the older 8-row ones is Khang's call.

## Session 42 — 10 November 2026 (W46)

**Tool:** Claude Code (Opus 5.5), with one writer agent, a data-fact-checker, a reviewer for the model and the figures, and one fixer.
**Scope:** sprint task T15 (Dat's): report section 4.4, the three-level data model. Only documents and figures changed. A
first attempt on 10 Nov at 01:35 was lost before REPORT.md was saved, because the machine slept and then restarted;
this is the second attempt.

### What the AI produced

| Artefact | Status |
|---|---|
| `docs/REPORT.md` §4.4, conceptual level: an ERD of 11 entities and the table each lives in | AI-drafted, fact-checked by a second agent |
| `docs/REPORT.md` §4.4, logical level: the star figure; the three Kimball fact types with grain, rows and partitions; the two SCD Type 2 dimensions and `stg_rfm_snapshot`; the five Cassandra tables beside the star | AI-drafted, fact-checked by a second agent |
| `docs/REPORT.md` §4.4, physical level: the layout figure; today's benchmark with its caveats; E1, E4, E5, gin_vs_seqscan and explain_star_join, each with its conditions | AI-drafted, fact-checked by a second agent |
| `docs/REPORT.md` §4.4, the `fact_session_funnel` limitation, and a sources table under "Nguồn số liệu của mục 4" | AI-drafted, fact-checked by a second agent |
| `docs/figures/report_4_4_{erd,star,physical}.png`: light renders of the three Mermaid blocks, for the PDF export | Rendered in light and dark with mermaid-cli 11 (Mermaid 11.17.2, GitHub's settings); each render looked at |

### How it was checked

| Claim | How it was measured |
|---|---|
| fact_event has 4,754,015 rows, fact_session_funnel 970,797, fact_inventory_daily 1,909,650 = 12,731 × 5 × 30 | Read-only DuckDB counts on `data/warehouse`, rerun independently by the reviewer; Postgres equality from `pg_vs_parquet_counts.txt` |
| dim_product has 210,454 versions of 128,972 products; dim_user 319,426 versions of 258,330 users; stg_rfm_snapshot 1,291,650 = 258,330 × 5 | Read-only DuckDB counts on `data/warehouse`, rerun independently by the reviewer |
| Every benchmark figure in the 4.4 table | The reviewer compared all 21 p50/p95 pairs with `summary_20261110_010557.csv` (runs = 20), and the buffer and file counts with `plans_20261110_010557.txt` |
| event_time has no usable min/max in fact_event's Parquet | DuckDB `parquet_metadata`: each file is one row group, and event_time is INT96 with statistics in 0 of 31 chunks |
| Cassandra keys and DDL as printed | The reviewer compared them with `serving/cassandra_schema.cql` and `warehouse/ddl.sql` |

### What the AI got wrong, and was corrected on

- The draft offered E4 (CSV 177.0 ms against partitioned Parquet 9.0 ms) as evidence of directory skipping. E4 mixes
  three effects: the columnar format, reading only the needed columns, and skipping files. A reviewer caught it. The
  text now says so and isolates directory skipping with today's benchmark: DuckDB 1.565 against 3.342 ms, about 2x.
- The draft called all five dimensions conformed while defining the word as "used by several facts". Only dim_date,
  dim_product and dim_user are. Reworded.
- A benchmark-table label said DuckDB's event_time filter had min/max, two paragraphs after the text said INT96 has none.
- The pruning_off caveat said every other partition is probed by B-tree. The plan shows 30 index probes plus a seq
  scan of the empty DEFAULT partition.
- The brief told the AI to cite `docs/PRESENTATION_SLIDES.md:269` for the 3-days-loaded condition of
  explain_star_join. That file is not tracked in git, so the condition is cited from `explain_fact_event_nofilter.txt`.

### Judgement that stayed with the team

- **Dat** set the section's content in the T15 row: three figures, the fact table with its counts, and the evidence.
- Flagged, not changed (code freeze): event_time is stored as INT96, so its row groups carry no statistics.
- An edge from fact_inventory_daily to stockout_risk in the physical figure was left out. The review marked it optional.

## Session 43 — 10 November 2026 (W46)

**Tool:** Claude Code (Opus 5.5): one writer agent, a data-fact-checker, one reviewer for spoken quality, and one fixer.
**Scope:** sprint task T20, Dat's part: his six blocks in `docs/project_deck.md` (pages 08-11 and 16-17). Documents
only. Session 42 (T15) also lands in this PR, because PR #47 was merged before its log commit reached the branch; the
next bullet list says why.

### What the AI produced

| Artefact | Status |
|---|---|
| `docs/project_deck.md` pages 08 (architecture), 09 (conceptual and logical model), 10 (physical model), 11 (Spark), 16 (BR1), 17 (BR2): one title, at most 4 points, the spoken script, the evidence line and the syllable count for each page | AI-drafted, reviewed; not yet read aloud by Dat |

### How it was checked

| Claim | How it was measured |
|---|---|
| Only Dat's six blocks changed | `git diff -U0 origin/w46-dat-t15`: every hunk is inside pages 08-11 and 16-17, and no `## Trang` header changed |
| 577 syllables, about 192 s at 3.0/s (08: 111, 09: 114, 10: 113, 11: 103, 16: 68, 17: 68) | A syllable counter that reproduces all seven of Khang's stated counts exactly; the reviewer recounted with a counter of its own |
| Every spoken number has a file behind it | Each block's `Số liệu:` line names the source: `batch_timings.txt`, `streaming_perf.txt`, `summary_20261110_010557.csv`, `gate2b_curl_raw.txt` |

### What the AI got wrong, and was corrected on

- Page 09's title said "năm dimension dùng chung" (five shared dimensions). REPORT §4.4 says only three are used by more
  than one fact. A reviewer caught it, and the title no longer says "shared".
- Smaller fixes from review:
  - the SCD2 wording on page 09;
  - "B-tree ghép" on page 10, matching `warehouse/ddl.sql`;
  - "gần chín mươi mili giây" spoken out;
  - a claim on page 11's title that nothing backed was dropped;
  - GMV glossed once on page 16.
- **How Session 42 ended up here:** a merge command for PR #47 ran after its `git switch` had failed. The switch failed
  because an agent worktree still held the branch, and `set -e` did not stop the chain. The local main was reset to
  `origin/main` right away. Nothing wrong reached the remote, but PR #47 merged without its log commit.

### Judgement that stayed with the team

- **Dat** set the budget (about 540 syllables at 3.0/s) and the rule to say the English term the slide prints.
- **Open for Dat:**
  - Read the six scripts aloud once. 577 is 3 syllables under the 580 cap.
  - Pages 16-17 open the demo; the demo actions themselves belong in Nguyên's T16 script.

## Session 44 — 10 November 2026 (W46)

**Tool:** Claude Code (Opus 5.5), main session.
**Scope:** sprint task T25, draft part (Dat's): fill the Claude Slides deck "Group15_ShopInsight_Project"
(AJRotBMth9wRSAG6JwNJWM) from `docs/project_deck.md`, put the 8 screens on the BR pages, and put a draft PDF on the
group's Drive. No repo file changed except this log.

### What the AI produced

| Artefact | Status |
|---|---|
| Deck version 18: pages 01-04 and 20-22 (Khang) and 08-11, 16-17 (Dat), copied from their blocks in `project_deck.md`: title, points, the evidence line, the spoken script as speaker notes; the 8 BR pages carry a screenshot | AI-built from the file, rendered and looked at; Khang's and Dat's own review pending |
| Pages 05-07, 18-19 (Nguyên) and 12-15, 23-26 (Tín) | Left as the empty frames, because their blocks are empty |
| `Nhom15_ShopInsight_Slide_nhap_2026-11-10.pdf` in the course Drive folder, 26 pages | A local render of the deck's slide files with Chromium at 1920×1080, not the Slides app's own export |

### How it was checked

| Claim | How it was checked |
|---|---|
| No slide's content runs past the 920 px footer line | The render script measured every slide's lowest element. Page 08 first reached 994 px and the BR pages 930 px; after the fix the worst is 890 px |
| The text on the slides is the text in `project_deck.md` | Built by a script from the blocks, not retyped. The first build cut multi-line "Số liệu" lines after the first line; the script now reads the whole paragraph |
| The pages look right | Pages 01, 08, 09, 10, 16 rendered and looked at |

### What the AI got wrong, and was corrected on

- The slide screenshots are not the evidence screenshots. The evidence images (`gate2b_br*.png`) are up to 1,523 px
  tall, which is unreadable on a slide. So the slide copies were retaken on 10 Nov at 21:00 with 6 table rows and the
  same app and data. Their footers show the first-load times after a restart: for example BR4 shows 189 ms, where the
  evidence image shows 72.78 ms. Each slide says "số đo chính thức: docs/evidence/gate2b_screens.txt".
- The PDF is a local render. The Slides app may lay lists and fonts out slightly differently. The final PDF (T25 on
  11 Nov) should come from the app's own Export.

### Judgement that stayed with the team

- **Dat** asked for the draft deck and the PDF on Drive in this session.
- The PostgreSQL box on page 08's figure still has no T12 numbers; the figure would have to be redrawn. Left for
  Dat to decide.
- Nguyên's and Tín's pages stay empty until they write their blocks (T20).

## Session 45 — 12 November 2026 (W46)

**Tool:** Claude Code (Opus 5.5).
**Scope:** sprint tasks T23 (report section 5), T24 (section 6) and the reference list of T28, all Khang's. A first
draft was written on 8 Nov on Khang's machine, before the W46 PRs merged; on 12 Nov it was rebuilt on `main` at
`8736a90`, with every number in 5 and 6 taken from the 10 Nov measurements of record. No application code changed.

### What the AI produced

| Artefact | Status |
|---|---|
| `docs/REPORT.md` section 5: how to run the system (`run_demo.sh` and the batch build order), a footer table of the eight screens, one paragraph per screen with its `gate2b_br*.png` image | AI-drafted; every number read from the screenshots |
| `docs/REPORT.md` section 6: 6.1 the nine-row correctness table and the checks that show it can fail, 6.2 the eight screens' meta and curl p50/p95, batch build and stream throughput, 6.3 question-to-screen table and the survey plan, 6.4 limits, future work, conclusion; "Nguồn số liệu của mục 5 và 6" | AI-drafted; numbers quoted from `docs/evidence/`, nothing re-measured for the text |
| `docs/REPORT.md` reference list [1]–[12], and the citation marks for it in 1.1, 2.4, 2.7, 3.1, 4.1, 4.2 and 4.3 | AI-drafted |
| `docs/AI_USAGE.md` — this session | AI-drafted |

### How it was checked

| Claim | How it was checked |
|---|---|
| Section 5's screen numbers (309K, 966,143 sessions, 21:04-21:19, 31,005 buyers, 2,600 carts, 525 rows, lift 4.07, 3 / 337 / 5,475 alerts, ...) and the footer table | Each of the eight `gate2b_br*.png` was opened and read |
| BR6's 525 rows and its cards | `_LIMIT_PER_WAREHOUSE = 100` and `_NO_SALES_PER_WAREHOUSE = 5` in `serving/api/routers/br6.py`; the cards count `rows` in `BR6Page.tsx` |
| 6.1 | Quoted from the T19 section of `correctness_8br.txt`, with the 6 Nov run (Khang's machine) and the 8 Nov review re-run for the checks that can fail |
| 6.2 | Quoted from `gate2b_screens.txt`, `perf_table.md`, `batch_timings.txt` and run 1 of `streaming_perf.txt` |
| The survey plan in 6.3 | `docs/EVALUATION_SURVEY.md` |
| Sections 1 to 4.3 change only by the citation marks | Word-level diff against `main`: twelve insertions, nothing removed |
| References [1]–[12] | Each is cited at least once (`grep`) |

### What the AI got wrong, and was corrected on

- **The 8 Nov draft also wrote 3.5, 4.4 and 4.5.** By 12 Nov, 3.5 and 4.4 were on `main` (Dat, T15) and 4.5 is
  T22 (Nguyên). Those three drafts were dropped; the PR touches only Khang's sections.
- **The 8 Nov draft measured screens and engines on Khang's machine.** The team's measurements of record are the
  10 Nov ones on Dat's machine (`docs/evidence/README.md`), so 5 and 6 now quote those, and the draft's evidence
  files (`report_api_latency.txt`, `report_engine_compare.txt`, `report_screen_br*.png`) are not committed.
- **The 8 Nov draft named 1004249 as BR7's top pair.** The screen ranks by lift, so 1005230 (lift 4.07, 3 sessions)
  comes first; 1004249 is the pair bought together most often (26 sessions, lift 1.72). Both are now stated.
- **The 8 Nov draft numbered every table and figure.** Section 4.4 already uses its own figure numbers (Hình
  4.4a-c), so the numbering was dropped from this PR rather than renumber Dat's section.

### Judgement that stayed with the team

Made by AI, flagged for review:
- **6.3 has a marked gap for the survey (T18).** No result is written before the survey runs.
- **The conclusion quotes BR8's 63.9 ms curl p95 as the slowest screen.** It is the slowest of the eight timed
  calls; footers of single cold loads read higher (BR2 354.57 ms), and 6.2 says so.
- **6.4 lists BR6's cards counting only the rows on screen as a limit.** If the screen is changed before
  submission, that line and the BR6 paragraph in 5.2 change with it.
