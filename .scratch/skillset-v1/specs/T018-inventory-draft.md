# Skillset inventory — draft v1 (T018)

Target: ~20 repo skills in three dispositions, per the user's plan. Two layers exist:
1. **Flow layer (this repo)** — the table below; installed via `npx skills add ivanDsky/skills`.
2. **Knowledge layer (already installed, stays)** — apple-design, emil-design-eng, animation-vocabulary, find/improve/review-animations, pick-ui-library, etc. `PROFILE.md` care-axes route to these; this repo does not copy them.
External tools (not skills): impeccable (`npx impeccable install`), archify CLI.

## A. Install-as-is (copy-paste)

| # | Skill | Source | Why |
|---|---|---|---|
| 1 | design-taste-frontend | Leonxlnx/taste-skill | art direction + measurable browser gate; fills the gap |
| 2 | archify | tt-a1i/archify | source-linked diagrams; orientation + spec viz (update-check disabled) |
| 3-5 | ponytail review / audit / debt lenses | DietrichGebert/ponytail | read-only review lenses, MIT, cheap (~400 tok descriptions via skills route) |

## B. Adapt (copy-paste + tinker)

| # | Skill | Source | The tinker |
|---|---|---|---|
| 6 | smallest-change | ponytail core prompt | own the text; drop always-on hooks; add skip/risk ending convention |
| 7 | intake | mattpocock grilling + ours | two gears (focused 5-8 / deep 20-30), one batch, defaults, assumptions-in-draft |
| 8 | tdd | superpowers TDD | concise voice per T008; fakes-over-mocks + user code-style rules as payload |
| 9 | scope-creep-detector | port candidate (Apache-2.0) | protects tracer-bullet scope; verdict pending |
| 10 | commit-archaeologist | port candidate (Apache-2.0) | brownfield orientation helper; verdict pending |
| 11 | thinking-out-loud | port candidate (Apache-2.0) | optional; verdict pending |

## C. Fresh (authored)

| # | Skill | interaction | Purpose |
|---|---|---|---|
| 12 | start | mixed | entry/router: triage, effort level -> gates, stage switches |
| 13 | draft-spec | hitl | spec + marked assumptions; one checkpoint message |
| 14 | ticket-set | hitl | tracer-bullet tickets, checkable DoD, small-chunk sizing |
| 15 | implement | afk | per-ticket subagent execution; ponytail ordering |
| 16 | review-change | afk | tier gates per effort level; dual-verdict when thorough |
| 17 | deliver | afk | build-only or deploy targets (firebase/tailscale/local) + evidence |
| 18 | orient-repo | afk | repo recon; archify diagrams; project map |
| 19 | research-unknowns | afk | parallel findings fan-out; verify-on-disk |
| 20 | prototype | mixed | tracer-bullet mode, deploy: main\|standalone\|none, graduation step |
| 21 | assess-teardown | afk | 2-failed-rounds trigger -> independent architect; fix vs rebuild |
| 22 | setup-project | hitl | install / new-project ritual; writes PROFILE.md + docs/agents config |
| 23 | integrate-skill | hitl | new-skill onboarding: index, trigger cases, routing check, size report |

Payloads (not skills): references/rules-*.md — SOLID, code-style (no comments), fakes-over-mocks, UI standards. GLOSSARY.md seed from T006 spec.
