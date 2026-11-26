---
name: goldfish-review
description: >-
  Challenge a feature concept (stage A, once the user confirmed scope), a
  design (stage B, before tickets) or a served prototype the user still
  finds off (stage P) with fresh-context subagents that never saw the
  conversation — one lens each: reuse, persona flows, data and migration,
  failure and resources, best version, verifiability; architecture,
  patterns, file structure; spec fit, persona walk, UX and taste. Use when
  the user asks for fresh eyes, a blind review, a devil's advocate or second
  opinion on a plan, when a spec checkpoint has passed, when write-tickets
  reaches its design-review step, or when the prototype loop calls a lens
  round.
interaction: mixed
requires: []
---

> **TL;DR** Fresh subagents that only know the hypothesis and hard constraints each attack one angle of a feature before code exists; the parent merges their findings into numbered assumptions and shows the user where lenses disagree. No fresh subagent, no review — never a same-context stand-in.
> **Related**: skill://draft-spec (stage A follows its checkpoint), skill://run-intake (prior-art step), skill://write-tickets (stage B at its design-review step), skill://prototype (stage P inside its loop, § 5), skill://review-change (stage C — the diff — and shared triage rules), skill://fan-out-research (same one-file-per-subagent contract), skill://grilling (irreversible forks), skill://micro-architecture, skill://design-architecture, skill://structure-checks, skill://ship-to-trunk (file-structure lens: `trunk` tickets merge alone and dark)

# Goldfish review

The agent that wrote the plan has read the whole conversation, so it
rationalizes the plan. A goldfish has read none of it: it gets a short
statement of what is being built and what is non-negotiable, and finds what
the author cannot see. Each lens is one angle with its own objective and its
own evidence — lenses that merely restate each other are merged, not
multiplied.

## 1. Stages and who picks the lenses

| Stage | When | Input | Lenses (catalog: [references/lenses.md](references/lenses.md)) |
|---|---|---|---|
| **A — concept** | after the spec checkpoint confirms scope, before `write-tickets` | hypothesis + hard constraints + Out of scope | reuse, persona flows, data & migration, failure & resources, best version, verifiability |
| **B — design** | `write-tickets` design-review step (item 9) | spec + module map + file maps | architecture, patterns, file structure |
| **P — prototype** | prototype loop, only after a user round that is not OK (`prototype` § 5) | served index URL + `frames.tsv` + success criteria + A-items + hard constraints + taste rules + the user's notes verbatim | spec fit, persona walk, UX & taste — all three every round |
| **C — diff** | `review-change` | the diff | owned by `review-change` (axes + visual reviewer); not a mode here |

**Stage A — the orchestrator picks; the user is not asked.** Never before
scope is confirmed: no checkpoint verdict yet, or a fast or prototype run
whose checkpoint never blocks → no stage A. Then at most 2 lenses, the top 2
rows below by cost if wrong; no row matches → 0 lenses, and the next digest
says `stage A: skipped — low risk`. More than 2 only when the user asks.
Ledger `Ruling: stage A lenses <a>, <b> — <risk>`.

| The change … | Lens |
|---|---|
| stores, migrates or syncs data | data & migration |
| touches network, background work, permissions or an external integration | failure & resources |
| adds a screen, flow or authoring flow | persona flows |
| has success criteria that need a device or elapsed time to prove | verifiability |
| builds something sizable and the intake prior-art step did not run | reuse |

Best version only when the user asks: it adds scope a confirmed spec cut.

**Stage B — the user picks** none / up to 3 / all at `write-tickets` item 9,
which owns when the question is asked and what it recommends (blind review
column: `start`/references/effort-mapping.md). A "none", or no question
asked, means no goldfish; never add one unasked.

**Stage P — no pick.** The prototype loop calls it; all three lenses run
each round (persona walk is not run when PROFILE names no personas). Never
before the user's first round: the user reviews first, lenses only answer a
reply that says something is still off.

## 2. Run a stage

1. **Write the brief file** `.scratch/<slug>/goldfish/brief.md`:
   - Stage A: the **hypothesis** — 2-3 sentences on what is being built and
     for whom, written from the confirmed spec's Problem and Solution — plus
     the **Hard constraints** list copied from `intake.md` and the spec's
     **Out of scope** list (a lens never re-adds cut scope). Nothing else:
     no discussion, no rationale, no assumptions the lens could anchor on,
     no other lens's findings.
   - Stage B: spec Problem/Solution/Assumptions, the module map, the tickets'
     file maps. Still no conversation.
   - Stage P: the checked index URL, `frames.tsv`, the spec's success
     criteria and A-items (a bug or quick fix: its expected behavior and
     DoD), hard constraints, PROFILE `## Taste rules`, the loop's
     `Decision:` lines, and the user's notes verbatim. Lenses open the pages
     in a browser tool when one exists, else read the HTML.
2. **One fresh-context subagent per chosen lens**, all dispatched at once, no
   shared state. The dispatch prompt is: the lens name, the brief path, the
   lens file section to follow, the ABSOLUTE findings path
   `.scratch/<slug>/goldfish/<stage>-<lens>.md`, and the reply contract
   (≤5 lines, status only), and the voice line from `start` § Voice.
   Spawn `effort` per `start`/references/effort-mapping.md (subagent
   thinking column).
3. **Findings format** (in the file): [lenses.md](references/lenses.md)
   § Findings format — a claim without evidence is dropped.
4. **Not run ≠ clean.** A lens that could not be dispatched (no fresh
   subagent available), returned no file, or failed twice is **not run**. Say
   so in the digest, name the missing coverage, and never count it as zero
   findings. There is no same-context fallback: a review in the author's own
   context is not a goldfish review. No subagents at all → report "goldfish
   not run" and continue the flow.
5. **Merge (the parent does it — no extra synthesizer agent).** Dedupe only
   identical findings. Where two lenses pull opposite ways — reuse says cut
   it, best version says add it; patterns says a seam, reuse says YAGNI —
   keep BOTH positions and record a **tension** with your pick and why.
   Never average a tension away and never hide it.
6. **Triage** every finding with the rules in
   `review-change/references/fix-loop.md` (accepted → assumption /
   non-goal / success criterion; contested only with evidence a lens could have
   read; comprehension complaints are never contestable). Irreversible forks
   (deploy, data migration, money, deletion) go to `grilling`, never into an
   assumption. Stage A output edits the spec without a second checkpoint:
   internal → `assumed:` lines; UX-visible → a new A-item applied as a
   reversible default and listed in the next milestone digest (`start` §
   Waiting on the user); a finding that adds scope beyond the confirmed
   Solution → declined, reason `scope confirmed`, unless the user reopens
   it. Stage B output lands as ticket edits or file-map changes — never a
   second interview batch. Stage P output lands as page fixes, never as
   spec scope; the loop owns what the user sees next.

## 3. Anti-patterns

Read [lenses.md](references/lenses.md) § Parent anti-patterns before writing
a brief or merging. The result is input to the spec, never approval: the
user's checkpoint stays the gate.

Adapted from the Elephant-Goldfish Model, github.com/google/elephant-goldfish-model
(Apache-2.0): the fresh-context-reviewer idea, concept-stage lenses, the
anchored hypothesis, and the not-run rule. Lens prompts, the merge/tension
rule, and the staging are ours.
