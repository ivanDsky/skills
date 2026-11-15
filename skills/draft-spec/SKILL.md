---
name: draft-spec
description: >-
  Write the working spec with numbered UX-visible assumptions, internal
  assumed: lines and a scope matrix for every setting or mode, then post the
  single "correct me or I go" checkpoint before autonomous execution. Use
  after intake answers exist — when the user says draft the spec, write the
  spec, turn the answers into a spec, or spec it up, or when an intake batch
  has been answered and feature or prototype work needs its spec stage.
interaction: mixed
requires: []
---

> **TL;DR** Writes the working spec with numbered Assumptions and posts the single correct-me-or-I-go checkpoint; fires after intake answers exist.
> **Related**: skill://run-intake (intake answers, prior-art findings), skill://design-architecture (architecture section), skill://write-tickets (next stage), skill://goldfish-review (stage A lenses after the checkpoint confirms scope)

# Draft the spec

Turn the intake answers into the working spec, then spend ONE checkpoint message
buying the rest of the run: the user corrects the assumptions or the run goes
autonomous. The intake batch was the interview — never ask again.

## 1. Consume intake

1. Read `.scratch/<slug>/intake.md`: answers, the A-items, the `assumed:`
   lines, and `prior-art.md` when linked (its catalog and walkthrough feed
   the Solution). Standalone, no intake file: synthesize from the ask and
   your repo reading instead, and write down every default you filled in —
   a default the user never saw is one they could not reject.
2. Read PROFILE.md for care-axes and the effort level. Never re-ask anything
   intake or the repo already settles.

## 2. Write the spec

Write `.scratch/<slug>/spec.md`, exactly these sections:

1. **Problem** — from the user's side: what hurts, who feels it. Grounded in
   the PROFILE.md Product frame (purpose, users, core loop) when present.
2. **Solution** — what gets built, stated as behavior. Authoring flows open
   with the confirmed "how does a user create one" walkthrough; rule
   catalogs are listed in full, each rule in or out.
3. **Scope matrix** — features that add or change a setting or mode: every
   surface × every setting, no empty cell
   ([how](references/assumptions-and-scope-matrix.md)).
4. **Assumptions** — two lists, split by § Shown vs assumed in the same
   reference. **Shown**: the UX-visible A-items from intake plus your own
   fills, each concrete and checkable ("A1: a draft board autosaves on
   exit"). **Assumed**: internal `assumed: <decision> — <why>` lines,
   decided by you. Features include an **Extension points** line from
   intake's extension question: either "variation points X, Y via
   <pattern>; part N+1 = a new file" or "no seam; a second variant triggers
   a refactor ticket". No silent gaps, nothing unnumbered.
5. **Success criteria** — checkable outcomes; they seed the tickets' DoD. UI
   features also record the visual direction here: the references the user
   named (apps/screens), theme constraints, and feel words — or the explicit
   assumption "no direction given: house style + design-skill judgment".
6. **Out of scope** — explicit non-goals, so review can reject creep.
7. **Deploy** — prototype runs only: the intake `deploy:` answer
   (`main | standalone | none`).

Decision rules:

- Durability rule: behavior and decisions only — no file paths, no line numbers;
  they rot before the tickets land. Name interface contracts; inline a snippet
  only when it encodes a decision better than prose, trimmed to the decision.
- Use GLOSSARY.md terms throughout; respect existing ADRs in the area.
- Keep it buildable by a fresh context: a competent builder plans from it
  without asking the user anything the spec should have answered.
- Reach for the knowledge layer before writing Solution and Success criteria:
  a UI surface means consulting the installed design skills (apple-design,
  emil-design-eng; ui-ux-pro-max for stack-specific guidelines) instead of
  inventing principles. Motion anywhere in the spec is named with canonical
  animation terms — resolve "the bouncy thing" via `animation-vocabulary`,
  never as adjectives. An architecture decision means running
  `design-architecture` — module boundaries, dependency direction, and the
  SOLID payload get settled there and land in the spec as interface
  contracts, never as file paths. An architecture discussion also earns a
  diagram (archify when installed, else inline mermaid). PROFILE.md
  care-axes rank what to pull; skill descriptions route the rest.

## 3. Post the checkpoint

The flow's only standing blocking gate besides intake. ONE message:
0. Before posting, diff the draft against `intake.md`: every intake answer
   is reflected, none contradicted, no Out-of-scope item re-added by the
   Solution, the scope matrix has no empty cell, and every A-item passes
   the shown test while every `assumed:` line fails it.

1. Digest ≤30 lines: problem, solution in a sentence, success criteria, then
   the FULL A-item list A1..An — show all of them, not a sample — and one
   line `N internal decisions assumed (spec.md § Assumptions)`.
2. End with exactly: "Correct me or I go." No second question, no menu, no
   approve/reject choice.
3. Blocking by effort (prototype never blocks, any effort):
   - **fast** — post in chat and proceed in the same run; later corrections
     become ticket edits.
   - **standard / thorough** — post it through the ask tool (`start` §
     Waiting on the user): the digest as the form text, one free-text field
     "Corrections (empty = go)". Any answer that is not a correction counts
     as "go".
4. Log the checkpoint in `.scratch/<slug>/ledger.md` (posted, and later: the
   verdict).

## 4. Fold corrections in

1. A correction edits the spec in place, assumption line included — never a
   second interview, never a new question batch.
2. A newly surfaced irreversible fork (production deploy, data migration,
   money, deletions) escalates to `grilling`: round-by-round until settled,
   never buried in an assumption.
3. Calls made afterwards without the user are `Ruling:` lines in the ledger,
   not spec edits.

## 5. Hand off

Checkpoint passed = scope confirmed. Then `goldfish-review` stage A (the
orchestrator picks 0–2 lenses by risk; its output edits the spec), then hand
the spec to `write-tickets` (chain) or report it ready (standalone). Both
assumption lists survive into the tickets and count as decisions:
reviewers grade the build against them.

Adapted from Matt Pocock's to-spec and Jesse Vincent's superpowers brainstorming (both MIT).
