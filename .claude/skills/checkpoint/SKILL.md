---
name: checkpoint
description: Draft one person's Wednesday checkpoint post for ShopInsight from the repo — what landed in git since the last checkpoint, which gate artefact this week owes, and whether a pre-agreed handover trigger has fired. The post replaces the weekly meeting; a human posts it.
when_to_use: It is Wednesday, or someone asks for "my checkpoint", "the status post", "what did I finish this week", "what do I owe the gate", "am I blocked". Also before a gate closes, to check whether the artefact it demands exists yet. Do NOT use to write code (spark-job, streaming-job, br-slice) or to log an AI session (ai-usage-log).
---

# The Wednesday post, drafted from the repo

PLAN.md replaces meetings with four mechanisms; this is the first of them. Every
Wednesday before 22:00 each person posts **three lines** to the group chat — what I
finished / what I am blocked on / what I do next week — plus one review of a teammate's
PR. 15 minutes, any hour of the day. 9 weeks x 4 people = 36 posts, 0.25 h each, and
that 9.00 h line is protected from every scope cut. Only two moments in the whole project
need all four people at once: the W43 rehearsal and the W44 talk.

**This skill drafts and checks. A human posts.** Never post on someone's behalf, and
never write "finished" for something git cannot show.

## 1. Read the repo first

| Question | Command |
|---|---|
| Which week is it, what is it for | `echo '{}' \| python3 .claude/hooks/session_status.py` — it already prints the week, its purpose, the data tiers, and which SYSTEM_DESIGN section 10 scripts exist |
| What landed since last Wednesday | `git log --since=<last-Wed> -i --author=<name> --date=short --format='%h %ad %s'` |
| Which files that touched | `git log --since=<last-Wed> -i --author=<name> --name-only --format=` \| `sort -u` |
| What is still open | `git status --short`, `git branch -vv`, `gh pr list --state open` if `gh` is there |

Author names are inconsistent (`Dat Le`, `Cong-Dat Le`), so match with `-i` and a first
name. The hook's tier/script table is the mechanical answer to "is bronze there yet",
"does `batch_silver.py` exist" — use it instead of asking.

## 2. Fill the three lines

| Line | Holds | Counts as evidence |
|---|---|---|
| Finished | merged commits and the artefact each produced | a commit, a row count posted with the command that printed it, a screenshot, a file path |
| Blocked on | what, since when, who can unblock it | nothing else; if it has been 48 h, the red flag goes up *now*, not in the post — the reviewer answers within 24 h |
| Next week | the rows for next week in the Drive tracker | the tracker is the single source of truth and has no copy in this repo |

Plus one line: which teammate's PR was reviewed, with at least one comment left — part of
the same 0.25 h row, not extra work.

Work in a branch, not merged, is **in progress**, never finished. A number without the
command that produced it is not a result. PRs merge inside the week; no branch lives
longer than seven days.

## 3. In a gate week, name the artefact

Every gate condition is a viewable artefact posted to the chat. Nobody meets to approve
a gate, and nobody declares "it works" without one.

| Gate | Due | Artefact it demands |
|---|---|---|
| 1a | end W40 | BR1 on Structured Streaming: screenshot of the micro-batch log + rows in `gmv_by_minute` |
| 1b | end W41 | the same for BR3 |
| 2a | end W41 | all 8 BRs demonstrable |
| 2b | end W42 | every screen under 2 s, measured through the QueryMeta footer, before the code freeze |
| 3 | **Wed W43** | presentation video assembled and edited — hard date, no further slip |
| 4 | end W44 | correctness + performance measured; the 5-person effectiveness survey may slip to W45 (2 of 3 accepted) |

Report evidence — CQL, star DDL, star-join query plan, GIN index, screenshots — is filed
in `docs/evidence/`. Checked 2026-09-16: that directory does not exist yet; the first
gate artefact creates it. In a gate week, `ls docs/evidence/` and say in the post whether
the artefact is there, not whether it is nearly there. There is no buffer week left: a
missed gate is paid for from the cut ladder, not from slack, which is 0.00 h.

## 4. On Wednesday W39, ask the handover question

The schedule already found this and already answered it. Do not re-open it.

- Dat runs 3.75 / 3.75 / 3.75 across W38-W40 — three consecutive weeks at 94% of the
  4.00 h ceiling — while owning both critical handovers (`batch_silver` + the warehouse
  skeleton for W39, the streaming reference for W41). Tin is at 3.75 in W39-W40.
- **Pre-agreed, not a discussion:** if the Wednesday W39 checkpoint shows Dat slipping,
  `fact_event` (0.75 h) moves to Khang immediately.
- That contingency is underfunded — it costs 0.75 h and only Khang's 0.25 h reserve is
  free — so the second half is also pre-agreed: Dat drops `fact_session_funnel` (cut
  ladder #7, BR2 falls back to reading silver) rather than let `fact_event` slip, because
  the other three people's dimensions plug into `fact_event`.

So on W39 the draft answers one question from git: has the `processing/batch_warehouse.py`
skeleton landed? PLAN.md gives it the first two days of W39 so the other three can plug in
their pieces, which makes it the only W39 item with a mid-week deadline. If it has not, the
post states that the trigger fired and that `fact_event` moves to Khang; it does not propose
alternatives. `fact_event` itself is due by the end of W39, so its absence on Wednesday is
progress to report, not the trigger.

## Do not

- Do not invent a ritual PLAN.md does not have: no stand-up, no call, no burndown chart.
- Do not raise the 25 h per person budget, and do not spend the 9.00 h status line or the
  1.75 h of mandatory meeting time on anything else.
- Do not commit a copy of the tracker: four people edit the Drive sheets, and a second
  copy under version control is stale within a day.
