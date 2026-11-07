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

> **TL;DR** Interviews the user in one batch of highest-impact questions with defaults, turning the rest into numbered assumptions; fires before a spec.
> **Related**: skill://draft-spec (spec next), skill://start (chain entry), skill://goldfish-review (blind concept review, asked for here), skill://micro-architecture (pattern table for the extension question)

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
   includes the deploy question (`deploy: main | standalone | none`). Four
   more always-join rules:
   - **DoD** — every feature ask gets one definition-of-done question ("what
     must be true for you to call this done?"), recommended default = review
     passes + build green + the happy path demos. It seeds the spec's success
     criteria and every ticket's DoD.
   - **UI surface** — asks that touch screens get a visual-direction question:
     references (apps or screens whose look/feel the user wants), theme
     constraints (existing app theme vs new tokens), and feel words for motion
     (resolve feel-words per animation-vocabulary). Build on the PROFILE.md
     Product frame — never re-ask purpose the frame already answers.
   - **Extension direction** — features only, not fixes. Look up the repo's
     existing variation points first (a registry, a `when` over types, a
     provider list), then ask once: name the variation points this feature
     has (providers, formats, rules, screens) and the pattern that would make
     part N+1 a new file (`micro-architecture`'s table; Kotlin sealed/enum
     before Factory/Registry). Recommended default: **no seam** — per-variant
     files are free, but an interface + registry needs a second variant the
     user names. Also ask whether a part N+1 is on the roadmap. The answer
     becomes a numbered assumption in the spec ("Extension points").
   - **Blind review** (standard and thorough runs; fast skips) — "Want fresh
     eyes on the concept before I draft the spec: none / up to 3 / all
     lenses?" (`goldfish-review`). Recommended default: up to 3 at standard,
     all at thorough. Each lens costs one subagent run; say so.
4. Ask through the harness's ask tool (`ask`, `AskUserQuestion` or
   equivalent), never as plain-text questions that end the turn. The whole
   batch goes in ONE call: one entry per question with a short header, 2–4
   options, your recommendation first and marked recommended; open-ended
   questions list the likely answers and leave the rest to the tool's free
   text. Any context the user needs to decide (findings, a draft) goes in
   the message before the call. Plain-text fallback, only when the harness
   has no ask tool: number each question, word it so "yes" accepts the
   recommendation, put the recommendation on an arrow line, send and stop —
   "1-4 yes, 5: no" must be a complete answer.

   ```
   ❓ **1 — Auth**: Add OAuth login on top of email/password?
   ➡️ yes
   ```
5. Never ask what the repo or PROFILE.md already answers, and never re-ask a
   settled decision.
6. Write the handoff: answers plus the numbered assumption list (A1, A2, ...)
   to `.scratch/<slug>/intake.md`, with a **Hard constraints** list (stack,
   deadlines, "must not" statements — facts, never rationale; with the
   hypothesis, all a blind reviewer will see). Each assumption is a concrete
   reviewable statement ("A1: single tenant, Postgres only"). The spec stage
   consumes that file; standalone runs put the same content in the reply.
7. Read [Question craft](references/question-craft.md) when running the deep
   gear or when the batch is hard to fill with load-bearing questions.
8. An irreversible fork discovered mid-flight gets the grilling treatment:
   round-by-round questions until it is settled. Never bury an irreversible in
   a default or an assumption.
9. Done when the batch is answered and the assumption list is written — not
   when every possible question is asked.

Adapted from mattpocock/skills (`grilling`, `grill-with-docs`), MIT.
