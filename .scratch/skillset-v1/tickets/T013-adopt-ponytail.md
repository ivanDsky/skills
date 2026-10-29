---
id: T013
title: Adopt? DietrichGebert/ponytail
labels: [wayfinder:research]
status: closed
assignee: research-ponytail
blocked-by: []
---

## Question

ADOPTION CANDIDATE (user intent: install as-is or integrate — not a repo to imitate). 'Makes your AI agent think like the laziest senior dev in the room — the best code is the code you never wrote' (180k stars, MIT, active). What exactly does installing it add (skills? commands? hooks? what do INSTALL.md and the plugin manifests set up?), what gets injected into every session and at what context cost, and does it complement or collide with our planned greenfield/brownfield flow? Per-skill verdict: install-as-is / integrate-adapt / skip, with exact install steps. MIT: vendoring allowed with attribution.

## Resolution

Surveyed from primary sources (README, INSTALL, AGENTS.md, all six SKILL.md, plugin manifest, hooks, benchmarks). Ponytail is one ~3KB behavior prompt (lazy-senior-dev ladder) plus 5 companion skills, wrapped for ~20 hosts; MIT; 180k stars verified; its agentic benchmark (585 sessions, hidden adversarial checks, mutation-tested tests) is real and unusually honest. Verdict: install-as-is `ponytail-review`, `ponytail-audit`, `ponytail-debt` via `npx skills add`; integrate-adapt the core `ponytail` prompt (own the ~760-token ladder text instead of the always-on Node-hook persona); skip `ponytail-gain` (static marketing card) and `ponytail-help`. Full findings: .scratch/skillset-v1/research/ponytail.md
