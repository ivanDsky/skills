---
name: design-architecture
description: >-
  Design and judge code architecture — map modules, find coupling violations,
  place seams, deepen shallow modules, and record ADR-level decisions under
  the dependency rule, using the deep-module vocabulary and the swappable
  SOLID / Clean Architecture rules payload. Use when a spec needs its
  architecture section, when an architecture-heavy ticket starts (new module,
  new seam, dependency direction in play), when review must grade dependency
  direction, or when the user asks to design modules, fix coupling, or assess
  the architecture before changing it.
interaction: afk
requires: []
---

> **TL;DR** Designs and judges module architecture — seams, coupling, dependency rule, ADRs; fires when a spec needs its architecture section or review grades structure.
> **Related**: skill://draft-spec (architecture section), skill://archify (architecture diagrams), skill://review-change (dependency grading), skill://user-check (re-gate after the user's OK), skill://structure-checks (mechanical form of rules 17/20 and layer checks), skill://goldfish-review (architecture lens at stage B)

# Design architecture

Shape deep modules at honest seams before code exists; grade existing
structure against the dependency rule before changing it. Output: a module
map, seam decisions, and the decision note the next agent reads.

Vocabulary, used exactly: **module** (interface + implementation, any scale),
**interface** (everything a caller must know — not just types), **depth**
(behavior per unit of interface), **seam** (where behavior can change without
editing that place), **adapter** (concrete thing satisfying an interface at a
seam), **leverage** (caller payoff), **locality** (maintainer payoff). Say
"seam", never "boundary".
[references/deep-modules.md](references/deep-modules.md) carries the full
vocabulary and the deepening patterns.

## When to run

- Greenfield: after intake, before the spec's Solution section firms up —
  shape the modules first, so tickets cut through real seams (tracer bullet).
- Brownfield: at implement step zero of any ticket that touches a module edge
  or adds a dependency — assess seams before changes; input is the
  map-codebase project map.
- Re-gate: `user-check`'s step after the user's OK grades the whole run's
  diff (fast fixes first) against this skill's rules payload.
- Review: review-change's architecture axis grades the diff against this
  skill's rules payload at every tier.
- Any direct ask: "design the modules", "fix this coupling", "is the
  architecture OK".

## Procedure

1. **Map the modules.** Brownfield: one line per affected module — its
   interface (what callers must know: types, invariants, ordering, error
   modes) and what the implementation hides; then every dependency arrow
   between modules, with its direction. Greenfield: propose instead of map —
   sketch the 3–7 modules of the walking path, one interface line each.
   Done when: every module in scope has an interface line and no arrow
   direction is unknown.
2. **Find coupling violations.** Read
   [references/rules-architecture.md](references/rules-architecture.md) first,
   then grade the map and the diff against its decision rules. Violations: an
   arrow from inner policy to outer detail (dependency rule break); a shallow
   module (interface ≈ implementation — fails the deletion test); a
   one-adapter seam; tests reaching past an interface; knowledge of one
   concept scattered across modules (no locality). Done when: each violation
   names the payload rule it breaks.
3. **Propose seams.** Per violation pick one: deepen (more behavior behind a
   smaller interface), re-place the seam (caller side owns the interface —
   DIP), or accept and say why. Load-bearing interface → design-it-twice:
   two radically different interfaces compared on depth, locality, seam
   placement ([references/deep-modules.md](references/deep-modules.md)).
   Done when: each proposal states the interface and names its adapters.
4. **Write the decision where the next agent reads it.** Interface contracts
   land in the spec — behavior and contracts, never file paths. A durable
   choice that would otherwise be re-litigated gets an ADR at
   `docs/adr/NNNN-<kebab>.md`: context, decision, consequences, rejected
   alternatives. Respect existing ADRs; contradict one only when the friction
   is real, and name it in the note. Done when: the spec or ADR covers seams,
   interfaces, and dependency direction for the affected area.

## Decision rules

1. Dependency rule outranks style: an import from inner policy to outer
   detail (UI, DB, framework) is Critical; fix by inverting at the caller's
   seam, not by adding a layer.
2. No speculative seams: one adapter is a hypothetical seam, two make it
   real. A production adapter plus an in-memory fake in tests counts as two.
3. Deepen before splitting: prefer one deep module over several shallow ones;
   a pass-through layer fails the deletion test — delete it.
4. Brownfield: gain control before design — characterization tests around
   the touched seam first; keep behavior changes and structural refactoring
   in separate commits.
5. Module names come from the domain (GLOSSARY.md), not tech words — no
   Manager, Helper, Util, ServiceImpl. A domain term that names a new module
   goes into GLOSSARY.md.

## Integration notes

- `draft-spec` consults this skill for the spec's architecture section:
  module boundaries and interface contracts, never file paths.
- `implement` applies it at step zero of architecture-heavy tickets (new
  module, new seam, dependency direction in play) before coding starts.
- `review-change` (every tier) and `user-check`'s re-gate grade the diff against
  [references/rules-architecture.md](references/rules-architecture.md);
  findings are Critical when the dependency rule breaks.

Authored for ivanDsky/skills. Vocabulary and deepening patterns adapted from
mattpocock/skills (`codebase-design`, `improve-codebase-architecture`), MIT.
Rules-payload pattern (five-part rule template, mini sizing) from
ciembor/agent-rules-books, MIT. Book rules cite Clean Architecture (Robert C.
Martin, 2017), Domain-Driven Design (Eric Evans, 2003), A Philosophy of
Software Design (John Ousterhout, 2018), and Working Effectively with Legacy
Code (Michael Feathers, 2004) — per-rule citations in
[references/rules-architecture.md](references/rules-architecture.md).
