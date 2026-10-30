# Skillset inventory — roster v2 FINAL (T018)

Reconciled with the T006/T007 specs (2026-10-29). Two layers:
1. **Flow layer (this repo)** — 21 skills below; `npx skills add ivanDsky/skills`.
2. **Knowledge layer (already installed, stays)** — apple-design, emil-design-eng, animation pack, pick-ui-library, ... `PROFILE.md` care-axes route to them; never copied here.
External tools (not skills): impeccable (`npx impeccable install`), archify CLI. Naming: fresh tier verb-first per T008; install/adapt tiers keep source-derived names for provenance.

## A. Install-as-is (5)

| Skill | Source | Why |
|---|---|---|
| design-taste-frontend | Leonxlnx/taste-skill | art direction + measurable browser gate |
| archify | tt-a1i/archify | source-linked diagrams; orientation + spec viz (update-check off) |
| ponytail-review / ponytail-audit / ponytail-debt | DietrichGebert/ponytail | read-only review lenses (~400 tok descriptions via skills route) |

## B. Adapt (4)

| Skill | Source | The tinker |
|---|---|---|
| ponytail | ponytail core prompt | own the text; drop always-on hooks; skip/risk endings |
| run-intake | mattpocock grilling + T005 | two gears, one batch, defaults, assumptions-in-draft |
| tdd | superpowers TDD | concise voice; fakes-over-mocks + code-style rules as payloads |
| scope-creep-detector | port, Apache-2.0 | protects tracer-bullet scope (ADOPTED) |

Declined for v1: commit-archaeologist (map-codebase covers orientation), thinking-out-loud (no clear slot; revisit on demand).

## C. Fresh (12)

| Skill | interaction | Purpose |
|---|---|---|
| start | mixed | entry/router: triage, effort -> gates, stage switches, run-log owner |
| draft-spec | hitl | spec + marked assumptions; one "correct me or I go" checkpoint |
| write-tickets | hitl | tracer-bullet tickets, checkable DoD, small-chunk sizing |
| implement | afk | per-ticket subagent execution; ponytail ordering |
| review-change | afk | tiered gates; fix rounds; triggers assess-teardown |
| deliver | afk | build-only or deploy targets + evidence |
| map-codebase | afk | repo recon; archify soft-required (degrades to mermaid); project map |
| fan-out-research | afk | one subagent per unknown; findings = cited absolute paths |
| graduate-prototype | hitl | cherry-pick prototype modules into real tickets |
| assess-teardown | afk | independent architect: fix-forward vs rebuild; findings memo only |
| init-profile | hitl | install/new-project/new-session ritual; PROFILE.md + entry-line bootstrap |
| integrate-skill | hitl | new-skill onboarding AND skill updates from feedback (T006 §10) |

Payloads (not skills): references/rules-*.md — SOLID/architecture, code-style (no comments), fakes-over-mocks, UI standards. GLOSSARY seed: T006 §6 (20 terms with avoid-lists).
Conventions added at reconciliation: feedback two-way capture (T006 §10), debug run log (T006 §11).
