# `.claude/` — Claude Code config for Group 15

Shared through git, so a trap one person writes down here reaches the other three on the
next `git pull`; the exception is `settings.local.json`, gitignored and yours only. A
skill is a markdown file one of us wrote; its slash name is the **directory** name under
`skills/`, not the `name:` field inside the file.

## Every file here

| Path | What it does |
|---|---|
| `settings.json` | Permission allow/deny lists, and the wiring for all three hooks |
| `skills/spark-job/SKILL.md` | Batch PySpark house rules: shape, pins, partitioning, the six silver rules, SCD2 |
| `skills/streaming-job/SKILL.md` | Structured Streaming traps: schema, checkpoints, watermarks, `foreachBatch` |
| `skills/cassandra-table/SKILL.md` | Partition and clustering keys designed backwards from the screen; null-key sentinels |
| `skills/br-slice/SKILL.md` | One BR = Spark query + API endpoint + React screen. Section 0 is the BR / owner / sink / screen table; weeks live only in `PLAN.md` |
| `skills/checkpoint/SKILL.md` | Drafts one person's Wednesday checkpoint post from git, names the gate artefact due, checks the W39 handover trigger |
| `skills/ai-usage-log/SKILL.md` | How to append a session record to `docs/AI_USAGE.md` |
| `agents/spark-reviewer.md` | Reviews PySpark against the trap list |
| `agents/data-fact-checker.md` | Measures a claimed number on this machine and prints the command |
| `agents/br-slice-auditor.md` | Checks one BR across Spark query, sink, endpoint and screen |
| `hooks/guard_data.py` | Refuses commands that delete or commit `data/`, force-push, or commit on / push to `main` |
| `hooks/check_python.py` | Compiles a just-written `.py` and reports the project traps it hits |
| `hooks/session_status.py` | Prints the real repo state at session start |
| `README.md` | This file |

An agent runs as a separate session with its own tools; none has Write or Edit, so
all three report rather than fix: *"Use the spark-reviewer agent on `batch_gold.py`."*

## Hooks

Wired in `settings.json`. All three **fail open**, and this table was checked by
running them.

| Hook | Event | What it does | Can it block? |
|---|---|---|---|
| `guard_data.py` | `PreToolUse`, Bash only | Tokenizes the command (quotes respected, `;` `\|` `&&` split) and denies four shapes: a delete touching `data/` (`rm`, or `find` with `-delete` / `-exec rm`), `git add`/`git commit` naming a `data/` path (a `.gitkeep` excepted — the empty tree is tracked), `git push --force`/`-f`, and a `git commit` on `main` or a push that lands on `main` (it follows a `git switch -c` earlier on the same line; heredoc bodies are skipped). It does **not** refuse a write under `data/`: `cat > data/x.txt` passes it. Writes are stopped by the separate `Write(data/**)`/`Edit(data/**)` deny rules in `settings.json`, a different mechanism that covers the Write and Edit tools only | **Yes — the only hook that denies** |
| `check_python.py` | `PostToolUse`, Write/Edit of a `.py` inside the repo | Compiles the file, then runs 14 regex checks from the trap list (`readStream` without `.schema`, `writeStream` without `checkpointLocation`, a delete on `abandoned_carts`, a missing `9999.0` sentinel, a banned import). Max 5 warnings, each naming the consequence | **No** — a syntax error exits 2 and is reported to Claude, but the write has already happened. The 14 trap checks are advisory |
| `session_status.py` | `SessionStart` | Prints the ISO week, what that week is for and the days left to 2026-11-15, then whether the raw CSV is present, which data tiers hold files, which SYSTEM_DESIGN section 10 scripts exist, whether Cassandra and Postgres are up — read from disk, not from `CLAUDE.md`. It names a gate only in the week that gate closes; the next gate is in `PLAN.md` | No |

`/hooks` lists them and disables one for this session. **A hook added while a session is
already running may not load** — after a `git pull` brings one, open `/hooks` once.

## `settings.local.json`

Optional and personal — paste into `.claude/settings.local.json`, never into the committed
one. Holds your `JAVA_HOME`, status line and "don't ask again" permissions. Never a key:

```json
{
  "env": { "JAVA_HOME": "/usr/lib/jvm/java-21-openjdk-amd64" },
  "statusLine": {
    "type": "command",
    "command": "printf 'ShopInsight W%s - %s days to 2026-11-15' \"$(date +%V)\" \"$(( ($(date -d 2026-11-15 +%s) - $(date -d \"$(date +%F)\" +%s)) / 86400 ))\""
  }
}
```

The countdown deliberately reuses `session_status.py`'s arithmetic instead of its own:
`date +%F` anchors it at midnight today, the same whole-day subtraction as `(DEADLINE -
today).days`. Plain `date +%s` subtracts the time of day too and prints one day fewer —
why the old snippet said 59 and the banner 60. Both now print 60 on 16 Sep 2026.

## If Claude does something wrong here

Hooks match text; nothing checks judgement. These three are what this project hits.

| It does this | Paste this back |
|---|---|
| Proposes a new technology — Airflow to schedule the batch jobs, dbt for the star, Redis in front of a slow screen, the Spark-Cassandra connector instead of `foreachBatch` | "CLAUDE.md rule 1: do not add technologies. Do it with the locked stack, or tell me it cannot be done." The connector case is rule 2 by name |
| Works horizontally — four Spark queries written, or every API endpoint stubbed, before one BR is visible on a screen | "CLAUDE.md rule 6: vertical slices. Finish BR*n*'s Spark query, endpoint and React screen before touching another BR." Four half-finished BRs demo as zero, and rule 7 puts demonstrated BRs above everything else |
| Asserts a number it did not measure — "about 8M rows", "roughly 200 ms faster", "this should be 3x quicker" | "Which command produced that number? If there isn't one, delete the sentence." Rule 3 and `docs/AI_USAGE.md` make it standing policy: every number that reaches the report carries its command. `data-fact-checker` settles exactly this |
