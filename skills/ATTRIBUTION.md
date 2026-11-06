# Attribution

Installed-as-is skills keep upstream frontmatter; our additions live in the central `evals/` dir so upstream dirs stay re-vendorable.

| Skill | Upstream | Commit | License |
|---|---|---|---|
| design-taste-frontend | Leonxlnx/taste-skill | 12af471 | MIT |
| archify | tt-a1i/archify | e392089 | Apache-2.0 (+NOTICE, vendored in-dir) |
| ponytail-review / -audit / -debt | DietrichGebert/ponytail | 96608e0 | MIT |
| apple-design / emil-design-eng / animation-vocabulary | emilkowalski/skills | a81dbca | MIT |
| ui-ux-pro-max | nextlevelbuilder/ui-ux-pro-max-skill | 28b3b8d | MIT (Basic version) |

Adapt-tier skills (ponytail core mode, run-intake, tdd, scope-creep-detector, prototype) are ours; sources credited in each SKILL.md footer. `prototype` replaces the vendored mattpocock/skills `prototype` (MIT), keeping its throwaway-answers-a-question idea and variant switcher.

Adapt-tier, Apache-2.0: `goldfish-review` and the triage/convergence sections of `review-change/references/fix-loop.md` adapt concepts from google/elephant-goldfish-model (commit not pinned; fresh-context reviewers, anchored hypothesis, not-run rule). No upstream text is copied; lens prompts are ours.

Adapt-tier, Apache-2.0: `micro-architecture/references/ui-components.md` paraphrases the androidx Compose Component API Guidelines and Compose API Guidelines (androidx/androidx, `compose/docs/`, commit not pinned; requirement levels kept), and adapts ideas from chrisbanes/skills `compose-component-design` and `compose-state-and-effects` (commit not pinned). No upstream text is copied. Cited only, not adapted: Android developer docs (state hoisting, state holders), Bumble Tech "Refining Compose API for design systems" and Stream "Composition patterns in Jetpack Compose".

MIT: `design-architecture/references/rules-architecture.md` uses the five-part rule template and bias list of ciembor/agent-rules-books, Copyright (c) 2026 Maciej Ciemborowicz.
