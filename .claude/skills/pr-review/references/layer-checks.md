# Layer checks — what to look for in each bucket

Read only the sections for buckets the PR touches. Every check names its source of truth.
Open that source rather than trusting the one-line summary here: where the two disagree,
the source wins, and you say in the terminal notes that this file is stale. The tag after
each check is the one it gets when it fails. "Question" means ask, do not assert.

Spark files are not here. Check them against the trap list in
`.claude/agents/spark-reviewer.md`, the single home of the PySpark rules. Read it as a
checklist in the review's own context; do not spawn the agent.

## Contents

- DDL (`sql`)
- Cassandra CQL (`cql`)
- API (`api`)
- Screens (`web`)
- Fixtures and the API contract (`fixtures`)
- Tests and checks (`tests`)
- Docs (`docs`)
- Claude Code config (`claude`)
- Seed and config (`seed`, `config`)
- Hygiene: vendored, generated and data files

## DDL (`sql`) — against SYSTEM_DESIGN 5.3–5.5

- **Names and types match 5.4 and 5.5**: every table, column, type, `NOT NULL`, `CHECK`
  and `UNIQUE`. Postgres is loaded from the same DataFrames that are written as Parquet
  (5.6 step 6). A renamed or retyped column breaks that load, or the DuckDB-vs-Postgres
  comparison in section 12. `wrong-numbers`, or `breaks-the-demo` if the load fails.
- **Partitioning matches 5.3 and 5.5**: the partition *column* (`event_date`,
  `session_start_date`, `warehouse_id`) and the partition *bounds*. Compare bounds with
  the real date range, which section 4 gives for silver. A partition set for the wrong
  month or the wrong column still loads — every row lands in `DEFAULT` — but pruning,
  and every EXPLAIN in `docs/evidence/` built on it, then proves nothing. `wrong-numbers`.
- **The primary key of a partitioned table includes the partition key.** Postgres
  refuses the table otherwise. `breaks-the-demo`.
- **Surrogate keys are `bigint` assigned in Spark**, not `SERIAL`, `IDENTITY` or a
  sequence. The Parquet and Postgres copies must carry identical keys. `wrong-numbers`.
- **SCD2 columns** have the types 5.4 gives: `valid_from` and `valid_to` as `date`,
  `valid_to` exclusive with `9999-12-31` meaning open. Each SCD2 dimension has exactly
  one partial unique index `WHERE is_current`. A timestamp `valid_to` against Spark's
  date-exclusive logic misfiles the boundary day. `wrong-numbers`.
- **Seed rows are copied from 5.4**, for example `dim_event_type`'s five rows. Codes the
  feed never sends and missing codes the design has both count. `wrong-numbers` if a
  BR joins on them, question otherwise.
- **Indexes**: 5.4 and 5.5 name each index and why. An index not in the design is a
  question, not a finding. Hard rule 3 cuts both ways.
- **It applies.** Do this only if the reviewer asks and Postgres is already running
  (`docker compose ps`). Apply the file to a throwaway database, report the result, then
  drop the database. Never start the container. Otherwise ask the author for the `psql`
  output.
- **DDL and `batch_warehouse.py` agree** on every column the Spark job writes.

## Cassandra CQL (`cql`) — against SYSTEM_DESIGN 6 and 6.1

Load the `cassandra-table` skill and run its checklist. The short version: each
`CREATE TABLE` copies section 6 exactly, direction lives only in
`WITH CLUSTERING ORDER BY`, and only the two tables that section 6 gives that clause
may have it. No key column may ever be null. The stale-row strategy per table lives
only in the `streaming-job` skill, section 4. Read it there.

## API (`api`) — against br-slice section 3 and SYSTEM_DESIGN 6–8

- **Every value a router passes to a response model is allowed by it.** Compare each
  `Literal` or enum in `models.py` with the values the routers pass, case included.
  `warehouse="fixture"` against `Literal["Fixture", ...]` is a 500 on every call:
  `breaks-the-demo`. If fastapi is already in `.venv`, one `TestClient` call per changed
  route confirms it in seconds. Do not install anything to run it.
- **Shape**: one router per BR under `serving/api/`, route `/api/br<N>/<noun>`, filters
  as query parameters, and the response envelope the contract freezes. br-slice
  section 3 names one shape; once `docs/API_CONTRACT.md` exists, the contract wins and
  br-slice is the doc to fix. `breaks-the-demo` when the screen cannot consume it.
- **`meta` is measured, not typed in**: `elapsed_ms`, `store`, `partitions_read`,
  `row_count` come from the actual query. Hard-coded meta is fabricated evidence for the
  evaluation section. `wrong-numbers`.
- **Cassandra BRs (1, 3, 5, 6, 8) query on the full partition key** from section 6. A
  missing key column, `ALLOW FILTERING`, or reading a whole table and filtering in
  Python is `breaks-the-demo`: the query is refused, or the screen misses 2 seconds.
- **BR5 sorts by `cart_value` in the API**, because the key gave up on-disk order
  (section 6.1).
- **Parquet BRs (2, 4, 7, 9) use DuckDB over the Parquet files directly**: `data/gold/`,
  or `data/warehouse/` for BR9. Postgres is the comparison tier and never serves a
  screen (section 12). Spark never runs inside a request. `breaks-the-demo`.
- **Column names are the sink's, unchanged**: section 6 for Cassandra, section 7 for
  Parquet gold, and `docs/API_CONTRACT.md` once it exists. A rename silently breaks the
  screen and the DuckDB correctness comparison. `breaks-the-demo`.
- **Slow by construction**, as opposed to untuned: for example a new Cassandra
  `Cluster().connect()` or DuckDB connection per request. Ask for the QueryMeta timing
  before calling it a finding. Question.

## Screens (`web`) — against br-slice sections 4–5 and SYSTEM_DESIGN 9

- **The components and filters in its BR's row** of br-slice section 4.
  `breaks-the-demo` for a missing filter the BR's question needs; question for the rest.
- **The QueryMeta footer**: elapsed ms, store, partitions read, row count, printed
  from the response `meta`. It is never computed or hard-coded in the screen. A screen
  without it is not finished (br-slice section 5), because the footer is the live
  evidence for Gate 2b and the report. `breaks-the-demo`.
- **BR6 filters to one day** and aggregates across warehouses. `stock_on_hand` is
  semi-additive, so summing it over dates is nonsense (SYSTEM_DESIGN 5.5).
  `wrong-numbers`.
- **Fixtures first is allowed**: a screen may render the contract fixtures before its
  query exists (br-slice section 3). Switching to the live endpoint must not rename a
  field.
- **Owner**: a screen for someone else's BR is a question to that BR's owner.
- **Not findings**: CSS, layout and visual polish (PLAN.md gives W45 to polish), and
  component structure or state-management taste.

## Fixtures and the API contract (`fixtures`)

- **Field names equal the sink's columns** in SYSTEM_DESIGN 6 and 7, and in
  `docs/API_CONTRACT.md`. The script prints each fixture's row and meta fields, so
  compare those lists. Do not read the JSON. A fixture that disagrees with the contract
  builds a screen against the wrong shape. `breaks-the-demo` at switch-over. If the
  fixture is right and the doc is stale, it goes to the team.
- **Values are plausible for this dataset**: dates in November 2019 (Vietnam time
  runs to 2019-12-01), real categories including `unknown` (about a third of events),
  and segments from `dim_user`'s CHECK list. Question when implausible.
- **Fixture numbers are illustrative.** If one appears in a doc, a slide or the report
  as a result, it is `wrong-numbers`.
- **After the contract is frozen, a rename is a team decision**, not an edit.

## Tests and checks (`tests`)

- **Run them only if they are quick and need nothing but the tree and `.venv`**, for
  example pure-Python fixture tests:
  `cd <tree> && <repo>/.venv/bin/python -m pytest -q <paths>`. Report pass or fail with
  the last lines of output. A test that needs Spark, a service or a missing module is
  "could not run". Ask the author for its output instead of installing anything.
- **A check that runs Spark** was routed to the `spark` bucket by the script. Here,
  confirm it tests what its gate needs. For Gate 4's SCD2 integrity (PLAN.md), that is
  non-overlapping `valid_from`/`valid_to` and exactly one `is_current` row per natural
  key, on both `dim_product` and `dim_user`.
- **A check must be able to fail.** A check that compares an output with the same
  function that produced it passes whatever the code does. So does one that checks
  only that fields are present, when the risk is extra or renamed fields. Say what it
  would miss. Question, or `wrong-numbers` if a gate relies on it.
- **Do not ask for tests the project does not require.**

## Docs (`docs`)

- **One copy of every fact.** A doc that restates something another file owns is drift
  waiting to happen: weeks (PLAN.md), keys (SYSTEM_DESIGN 6), stale-row fixes
  (`streaming-job` section 4), the BR table (`br-slice` section 0), pins (SYSTEM_DESIGN
  11.1). Ask for a pointer instead. Non-blocking, unless the copy is already wrong.
- **Pairs move together**: `docs/SETUP_SPARK.md` with `docs/SPARK_GUIDE_VI.md`
  (CLAUDE.md). A new pipeline script updates the README run order and SYSTEM_DESIGN 11.
  A new top-level directory updates SYSTEM_DESIGN 10.
- **Numbers go to data-fact-checker.** A number with no command behind it is not a
  result (AI_USAGE standing conventions).
- **Evidence in `docs/evidence/` is real output** (EXPLAIN, DESCRIBE, logs) from the
  code in this same PR. Evidence that contradicts the DDL it claims to show, or that
  could not have come from it, is `wrong-numbers`.
- **Language is not a finding for docs.** PLAN.md and `SPARK_GUIDE_VI.md` are
  Vietnamese on purpose. CLAUDE.md's English rule covers code comments, docstrings and
  commit messages.

## Claude Code config (`claude`)

- `.claude/README.md`'s "Every file here" table lists every file under `.claude/`.
- A new hook is wired in `settings.json`, fails open, and states whether it can block.
- A skill or agent that restates a fact another file owns gets the same one-copy note
  as docs.
- A widened `permissions.allow` covering anything destructive (delete, push, a write
  outside the repo) is a question.

## Seed and config (`seed`, `config`)

- **`seed/holidays_2019.csv`**: the header and the four `holiday_type` values are in
  SYSTEM_DESIGN 3.2. Check every row inside `dim_date`'s range (Oct-Dec 2019), not just
  the three retail events. A row on a dataset day turns `dim_date.is_holiday` true for
  that day. An "All Saints Day" observance on 1 Nov, for example, marks day one of the
  data as a holiday. Each such row must be a real holiday for this market on that
  date: `wrong-numbers`. Rows outside the range are dead weight, a nit.
- **`requirements.txt`**: every line pinned with `==` (CLAUDE.md code conventions),
  `pyspark==4.1.3` (SYSTEM_DESIGN 11.1), nothing rule 1 bans. The script flags these
  mechanically. `hard-rule`.
- **`web/package.json`**: libraries inside React (charts, icons, routing, a linter,
  Vite) are fine. A new server, database, queue or cloud service is rule 1, `hard-rule`.
- **`docker-compose.yml`**: image tags pinned to the patch. Memory and heap values are
  config of record, and changes wait for the W41 benchmarks (SYSTEM_DESIGN 11.1).
  `hard-rule`.
- **`conf/spark-defaults.conf`** keeps the driver memory and the UTC session time zone.
  Without the time-zone pin, bronze gets 31 partitions instead of 30 (SYSTEM_DESIGN
  11.1). `wrong-numbers`.
- **`.gitignore`** never un-ignores what goes inside `data/`. New negations are only
  for a `.gitkeep` skeleton directory (SYSTEM_DESIGN 10). `repo`.

## Hygiene: vendored, generated and data files

Never read these line by line. Decide whether they belong in the PR at all.

- **`data/`**: anything but a `.gitkeep` is `repo`, blocking. No data moves through git;
  all four machines regenerate it deterministically.
- **`vendored`** (for example `.agents/`, `node_modules/`): third-party content the
  project does not run. After merge it stays in history for good, and every agent tool
  that scans that directory loads its instructions. Ask for it to leave the PR, and to
  be `.gitignore`d if it is one person's tool setup. `repo`, blocking.
- **`generated`**: a lockfile belongs in git, because four machines need identical
  installs. Review `package.json`, never the lockfile's lines.
- **Secrets**: a committed `.env`, a token, or a password that is not `.env.example`'s
  local default. `repo`, blocking, and tell the reviewer to rotate it: removing it in a
  later commit does not remove it from history.
