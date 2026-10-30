---
name: run-intake
description: >-
  Interview the user in one batch of the highest-impact questions, each with a
  recommended one-word default, before a spec is drafted, then turn every point
  not asked into a numbered assumption list handed to the spec. Use when feature
  or prototype work starts, when requirements are gathered or an ask is scoped,
  or when the user says intake, "ask me what you need", or "what do you need to
  know before drafting".
interaction: hitl
requires: []
---

# Run intake

Extract the load-bearing decisions in ONE batch. Everything you do not ask
becomes a marked assumption the user reviews later — never a silent gap, and
never a second batch.

1. Read first: PROFILE.md (care-axes, effort, deploy targets), the tracker
   frontier, and the ask. Facts are your job, decisions are the user's: look up
   in the repo whatever the repo answers (stack, patterns, test setup). Lookups
   are never questions. Vague feel-words in a UI ask ("smooth", "the bouncy
   thing when you overscroll") are lookups too: resolve them to canonical
   animation names via `animation-vocabulary` and confirm the name inside the
   batch — one word answers it.
2. Pick the gear and say so in one line:
   - **Focused** (default): 5-8 highest-impact questions.
   - **Deep**: 20-30 questions, when the user asks for it or stakes are high —
     an irreversible fork is on the table: production deploy, data migration,
     money, deletions.
3. Build ONE batch in frontier order: a question joins only if nothing else in
   the batch must be answered first. In a prototype run the batch always
   includes the deploy question (`deploy: main | standalone | none`).
4. Format every question so a one-word reply answers it: number it, word it so
   "yes" accepts your recommendation, and put the recommendation on an arrow
   line. Then send the batch and stop — the reply "1-4 yes, 5: no" must be a
   complete answer.

   ```
   ❓ **1 — Auth**: Add OAuth login on top of email/password?
   ➡️ yes
   ```
5. Never ask what the repo or PROFILE.md already answers, and never re-ask a
   settled decision.
6. Write the handoff: answers plus the numbered assumption list (A1, A2, ...)
   to `.scratch/<slug>/intake.md`. Each assumption is a concrete reviewable
   statement ("A1: single tenant, Postgres only"). The spec stage consumes that
   file; standalone runs put the same content in the reply.
7. Read [Question craft](references/question-craft.md) when running the deep
   gear or when the batch is hard to fill with load-bearing questions.
8. An irreversible fork discovered mid-flight gets the grilling treatment:
   round-by-round questions until it is settled. Never bury an irreversible in
   a default or an assumption.
9. Done when the batch is answered and the assumption list is written — not
   when every possible question is asked.

Adapted from mattpocock/skills (`grilling`, `grill-with-docs`), MIT.
