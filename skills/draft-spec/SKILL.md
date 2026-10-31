---
name: draft-spec
description: >-
  Write the working spec with an explicit numbered Assumptions section and post the
  single "correct me or I go" checkpoint before autonomous execution. Use after
  intake answers exist — when the user says draft the spec, write the spec, turn
  the answers into a spec, or spec it up, or when an intake batch has been answered
  and feature or prototype work needs its spec stage.
interaction: mixed
requires: []
---

> **TL;DR** Writes the working spec with numbered Assumptions and posts the single correct-me-or-I-go checkpoint; fires after intake answers exist.
> **Related**: skill://run-intake (intake answers), skill://design-architecture (architecture section), skill://write-tickets (next stage)

# Draft the spec

Turn the intake answers into the working spec, then spend ONE checkpoint message
buying the rest of the run: the user corrects the assumptions or the run goes
autonomous. The intake batch was the interview — never ask again.

## 1. Consume intake

1. Read `.scratch/<slug>/intake.md`: answers plus the numbered assumption list
   (A1, A2, ...). Standalone, no intake file: synthesize from the ask and your
   repo reading instead, and write down every default you filled in — a default
   the user never saw is one they could not reject.
2. Read PROFILE.md for care-axes and the effort level. Never re-ask anything
   intake or the repo already settles.

## 2. Write the spec

Write `.scratch/<slug>/spec.md`, exactly these sections:

1. **Problem** — from the user's side: what hurts, who feels it. Grounded in
   the PROFILE.md Product frame (purpose, users, core loop) when present.
2. **Solution** — what gets built, stated as behavior.
3. **Assumptions** — every A-item from intake plus your own fills, each one
   concrete and checkable ("A1: single tenant, Postgres only"). This section is
   what the checkpoint sells; no silent gaps, nothing unnumbered.
4. **Success criteria** — checkable outcomes; they seed the tickets' DoD. UI
   features also record the visual direction here: the references the user
   named (apps/screens), theme constraints, and feel words — or the explicit
   assumption "no direction given: house style + design-skill judgment".
5. **Out of scope** — explicit non-goals, so review can reject creep.
6. **Deploy** — prototype runs only: the intake `deploy:` answer
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

1. Digest ≤30 lines: problem, solution in a sentence, success criteria, then
   the FULL assumption list A1..An — the assumptions are the point, show all
   of them, not a sample.
2. End with exactly: "Correct me or I go." No second question, no menu, no
   approval form.
3. Blocking by effort (prototype never blocks, any effort):
   - **fast** — post and proceed in the same run; later corrections become
     ticket edits.
   - **standard / thorough** — end the turn on the checkpoint. Any reply that
     is not a correction counts as "go"; silence = the user saw it, the run
     resumes on their return.
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

Checkpoint passed → hand the spec to `write-tickets` (chain) or report it
ready (standalone). The numbered assumptions survive into the tickets and
later count as decisions: reviewers grade the build against them.

Adapted from Matt Pocock's to-spec and Jesse Vincent's superpowers brainstorming (both MIT).
