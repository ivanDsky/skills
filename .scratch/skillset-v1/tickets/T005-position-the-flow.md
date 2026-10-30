---
id: T005
title: Position the flow: methodology vs composable chain
labels: [wayfinder:grilling]
status: closed
assignee: None
blocked-by: [T001, T002, T003, T004, T010, T011, T012]
---

## Question

Where on the superpowers-to-mattpocock spectrum should our flow sit? Auto-triggered methodology (a router/entry skill fires as work starts, the process drives) vs user-invoked composable chain (the human summons each skill). Decide: what (if anything) triggers automatically, what the human always summons, how greenfield vs brownfield entry points are detected, and how much context each entry point loads. Write the decision as the flow's constitution for T006/T007.

## Resolution

Decided with the user (2026-10-29):

- **One flow, conditional stages** — not separate greenfield/brownfield chains: intake -> [orientation] -> spec -> tickets -> [research] -> implement -> review -> deliver. Orientation fires only on unmapped codebases; research fires when tickets declare unknowns (parallel subagent fan-out); deliver = build-only or per deploy target (firebase / tailscale / local).
- **Entry skill: `/start`** (alias `/build`) — wayfinder-style: reads PROFILE.md + tracker frontier, triages input (quick task / prototype / feature / unfamiliar codebase), decides which stages fire, marks stages HITL vs AFK.
- **Intake, two gears, always one batch**: focused (5-8 highest-impact questions, recommended defaults, one-word answers) is the default; deep (20-30) on request or high stakes. Everything else is resolved as clearly marked assumptions in the draft spec that the user reviews. The grilling skill itself is reserved for irreversible forks.
- **Prototype = a flag on the same flow**, not a separate chain: tracer-bullet tickets, reduced gates, DoD = question answered / demoable. Prototypes may ship deployable builds — each carries `deploy: main | standalone | none` (user tests on deploy targets).
- **Teardown gate**: trigger = 2 failed fix rounds (or reviewer discretion) -> spawns an independent architect subagent (fresh context, high effort) that decides fix-forward vs clean redesign. Teardown carries forward only extracted findings: root cause, interface contracts, surviving tests.
- **Effort level** (plain term; "dial" retired): quality-vs-speed setting in PROFILE.md care-axes + per-session override; orchestrator maps it to subagent thinking/effort, review depth, gates, research breadth.
- **Implementation order** (ponytail, adapted): understand -> reuse -> adapt -> extend -> new code last; smallest-change default; replies end with what was skipped and residual risk.
- **DoD mandatory per ticket**: checkable condition + evidence, or the ticket does not close.
