---
name: goldfish-review
description: >-
  Challenge a feature concept (stage A, before the spec) or a design (stage B,
  before tickets) with fresh-context subagents that never saw the
  conversation — one lens each: reuse, persona flows, data and migration,
  failure and resources, best version, verifiability; then architecture,
  patterns, file structure. The user chooses none, up to 3, or all lenses.
  Use when the user asks for fresh eyes, a blind review, a devil's advocate or
  second opinion on a plan, when intake's blind-review answer is not none, or
  when write-tickets reaches its design-review step.
interaction: mixed
requires: []
---

> **TL;DR** Fresh subagents that only know the hypothesis and hard constraints each attack one angle of a feature before code exists; the parent merges their findings into numbered assumptions and shows the user where lenses disagree. No fresh subagent, no review — never a same-context stand-in.
> **Related**: skill://run-intake (asks how many lenses), skill://draft-spec (stage A consumer), skill://write-tickets (stage B at its confirm gate), skill://review-change (stage C — the diff — and shared triage rules), skill://fan-out-research (same one-file-per-subagent contract), skill://grilling (irreversible forks), skill://micro-architecture, skill://design-architecture, skill://structure-checks, skill://ship-to-trunk (file-structure lens: `trunk` tickets merge alone and dark)

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
| **A — concept** | after intake, before the spec is drafted | hypothesis + hard constraints | reuse, persona flows, data & migration, failure & resources, best version, verifiability |
| **B — design** | `write-tickets` confirm gate | spec + module map + file maps | architecture, patterns, file structure |
| **C — diff** | `review-change` | the diff | owned by `review-change` (axes + visual reviewer); not a mode here |

The user decides the count — **none / up to 3 / all** — asked once per stage
(stage A inside the `run-intake` batch, stage B in the `write-tickets`
confirm message). Recommended default: fast → none, standard → up to 3,
thorough → all. A "none" or silence on a fast run means no goldfish; never
add one unasked.

"Up to 3" = **reuse** (always the first lens: cheapest and most often decisive)
+ two chosen by the top care-axes in PROFILE.md, or by what the feature
touches when axes are silent (screens → persona flows; storage → data &
migration; async/network → failure & resources). Say which two and why in one
line.

## 2. Run a stage

1. **Write the brief file** `.scratch/<slug>/goldfish/brief.md`:
   - Stage A: the **hypothesis** — 2-3 sentences on what is being built and
     for whom, written from the intake answers — plus the **Hard constraints**
     list copied from `intake.md`. Nothing else: no discussion, no
     rationale, no assumptions the lens could anchor on, no other lens's
     findings. The hypothesis is also quoted in the spec digest, so a
     miswritten one is visible and correctable.
   - Stage B: spec Problem/Solution/Assumptions, the module map, the tickets'
     file maps. Still no conversation.
2. **One fresh-context subagent per chosen lens**, all dispatched at once, no
   shared state. The dispatch prompt is: the lens name, the brief path, the
   lens file section to follow, the ABSOLUTE findings path
   `.scratch/<slug>/goldfish/<stage>-<lens>.md`, and the reply contract
   (≤5 lines, status only). Subagent thinking follows effort (low / medium /
   high for fast / standard / thorough).
3. **Findings format** (in the file): per finding — id (`<lens>-1`), the claim
   in one sentence, the evidence (repo path, doc URL, quoted brief line — a
   claim without evidence is dropped), what changes if it is true, and one
   proposed disposition: assumption · non-goal · success criterion · question.
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
   assumption. Stage A output lands in the spec (`draft-spec`); stage B
   output lands as ticket edits or file-map changes — never a second
   interview batch.

## 3. Anti-patterns

- Pasting conversation, rationale, or the author's preferred design into a
  brief — the lens then reviews the argument, not the idea.
- Showing one lens another's findings (they converge instead of covering).
- Treating the result as approval. It is input to the spec; the user's
  checkpoint stays the gate.
- A lens with nothing new to say still reports "no findings, checked: …" with
  what it looked at; an empty file is not run.
- Running all lenses by default: cost is one subagent each, and the user
  chose the count.

Adapted from the Elephant-Goldfish Model, github.com/google/elephant-goldfish-model
(Apache-2.0): the fresh-context-reviewer idea, concept-stage lenses, the
anchored hypothesis, and the not-run rule. Lens prompts, the merge/tension
rule, and the staging are ours.
