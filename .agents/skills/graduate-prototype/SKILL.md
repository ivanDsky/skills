---
name: graduate-prototype
description: >-
  Cherry-pick working prototype modules into real tracker tickets that re-enter
  the standard flow at implement with full gates, or end the prototype in a
  clean discard with a findings file. Use when a prototype answered its question
  or its demo was approved, when the user says graduate it, keep it, promote it,
  or throw it away, or when a finished prototype run needs its exit.
interaction: hitl
requires: []
---

# Graduate a prototype

Every prototype ends in graduate or discard — never in limbo. Graduation is a
human-in-the-loop cherry-pick: the user picks the modules worth keeping, the
picks become real tickets that re-enter the FULL gates, and the prototype
branch merges only through those tickets.

## The flag being exited (prototype run contract)

One flow, reduced gates — the prototype flag bends stages, it never branches
the chain:

- **Spec**: lightweight — one page max, assumptions marked inline, deep intake
  off, grilling only for irreversible forks.
- **Review**: fast tier only (lint + typecheck/compile + screenshots + the
  demo) at any effort level; dual-verdict review happens after graduation,
  never before.
- **DoD**: the question answered or the demo runs. No DoD, no close.
- **Deploy**: one line on the prototype — `deploy: main | standalone | none`.
- The flag stays on until this skill decides graduate or discard.

## 1. Trigger

The user answers the prototype's question or approves the demo. Also fires on
"graduate it", "keep the good parts", "promote this prototype", "throw it
away", or whenever a prototype run is done and needs its exit.

## 2. Inventory

1. List the prototype's modules from the diff on the prototype branch.
2. Classify each — **keep** (passing tests cover its behavior), **rewrite**
   (the direction is validated but the code is demo-only glue), **discard**
   (the question was answered without it). Passing tests are evidence; a
   running demo is not — a demo-only module that looks shippable classifies
   as rewrite.
3. Write `.scratch/<slug>/graduation.md`: one line per module — name,
   classification, why. Show the list.

## 3. The user picks (the HITL gate)

Present the inventory and wait. The user rules per module — keep as-is,
rewrite, discard, or split; their picks override the classification.
Graduation is never autonomous: no picks, no tickets.

## 4. Cherry-pick into real tickets

One ticket per picked module, tracker format
(docs/agents/issue-tracker.md frontmatter), published to
`.scratch/<slug>/tickets/NN-<slug>.md`, all mandatory write-tickets fields
present:

- **What to build** (behavior, not a diff dump) / **Blocked by** in
  dependency order / **File scope** / **Unknowns** / **DoD** — one checkable
  condition / **Evidence**. No DoD, no ticket.
- Keep tickets cite the prototype branch + commit to lift the code from;
  their DoD adds what the prototype run skipped (tests, the never-cut list).
- Rewrite tickets carry design notes from the prototype findings — never the
  code — each citing branch + commit for the archaeologist.
- Interfaces crossing tickets get `blocked-by:` edges.

Full gates apply from here: the tickets enter the standard flow at
`implement` and get dual-verdict review. `deploy: main` delivers like a
feature; `deploy: standalone` keeps its own branch on the test target the
user tries. Either way the prototype branch merges ONLY via these tickets —
never directly.

## 5. Discard path

An all-discard pick, or any `deploy: none` ending: write
`.scratch/<slug>/findings.md` — what was learned (the answer to the
question), what is worth reusing, links to the demo — then archive the
branch (rename or tag, kept out of main). No tickets are created.

## 6. Close

Append the ledger line (`.scratch/<slug>/ledger.md`,
`Ruling: graduate — N tickets | discard — reason`), clear the prototype
flag, hand the tickets to `implement`, and report: picks, ticket list,
branch disposition. Debug on → one ≤4-line entry in
`.scratch/run-log.md`.

Adapted from mattpocock/skills (`prototype` — capture-the-validated-decision
mechanics only), MIT.
