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
