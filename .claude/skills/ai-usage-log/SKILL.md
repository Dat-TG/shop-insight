---
name: ai-usage-log
description: Record an AI-assisted session in docs/AI_USAGE.md, the file the report and the grader use to tell which parts of ShopInsight were generated, which were verified, and how.
when_to_use: At the end of a session where AI drafted documents, schema, Spark code or measurements; when asked to "log this session", "update AI_USAGE", or "write up what the AI did"; before committing AI-drafted work that a human has not yet run.
---

## Rules that do not bend

- The file is **appended to, never rewritten.** New sessions go at the end, after
  whatever is already there, so the record stays chronological. Never re-edit an
  earlier session to make it read better; if it was wrong, say so in the new one.
- **AI may draft and may measure; a human decides.** Every decision recorded must
  name who made it.
- AI-generated SQL and Spark code is **not committed until it has been run**. If
  it has not been run, its status says so.
- Any number that reaches the report **carries the command that produced it**.
- AI does **not** produce measurement results that go into the evaluation
  section. The benchmark harness, the correctness comparison and the three W44
  measurement sets are run by the owner named in `PLAN.md`, on their machine.

## Which existing session to copy

`docs/AI_USAGE.md` holds two sessions and they are **not** the same shape. Read
both, then copy Session 1.

| Block | Shape |
|---|---|
| Session 1 (14 Sep 2026) | **Canonical.** Tool / Scope, then `What the AI produced`, `How it was checked`, `What the AI got wrong, and was corrected on`, `Judgement that stayed with the team`. The template below is this shape. |
| `## Standing conventions` | **Not a session.** A standing block that happens to sit *between* the two sessions. Never append inside it, never number it, never rewrite it. |
| Session 2 (15 Sep 2026) | **A deliberate deviation.** Carries none of the template's headings except `Judgement that stayed with the team`; its corrections are folded into `The correction that mattered most`, and it adds `How the tracker was rebuilt` and `Where the tracker lives`. It is a correction-led session, and it was kept that way on purpose. |

So "append at the end" means after Session 2, at the bottom of the file — which
is the end even though the conventions block is not last among the sessions.
Use the template unless the session really is correction-led like Session 2; if
you deviate, say in one line why.

## Section template to append

```markdown
## Session N — D Month YYYY (Wnn)

**Tool:** Claude Code (model).
**Scope:** one or two sentences. Say plainly if no application code was written.

### What the AI produced

| Artefact | Status |
|---|---|
| `path/or/document` — what changed in it | AI-drafted, human review pending / human-approved in advance / run and verified |

### How it was checked

Name the actual commands or files, not the intent. Measured claims go in a
second table: | Claim | How it was measured |.

### What the AI got wrong, and was corrected on

Bullets. One per defect: what the draft said, why it was wrong, what replaced it.

### Judgement that stayed with the team

Which decisions were put to a human and answered by a human, and which were made
by AI and are flagged for review. Record open questions here too.
```

**Corrections are not optional; the heading is.** Session 1 files them under
`What the AI got wrong, and was corrected on`; Session 2 makes them the whole
session under `The correction that mattered most`. Either is fine, absent is not:
the corrections are what makes the record credible to a grader — a log with no
corrections reads as unreviewed, not as flawless. If a session genuinely produced
no defect, say what was checked that could have found one.

## Before you append

- Is every number traceable to a command someone else can re-run?
- Is every decision attributed to the human who made it, or explicitly flagged as
  AI-made and awaiting review?
- Is anything still flagged for review that has not been reviewed? Carry it
  forward; do not let it disappear between sessions.
- Does any new artefact contain unrun SQL or Spark code? Then its status is
  "not yet run" and it stays out of the commit.
