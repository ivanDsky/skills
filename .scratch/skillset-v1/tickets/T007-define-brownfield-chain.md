---
id: T007
title: Spec the conditional stages - orientation, research, prototype, deploy targets
labels: [wayfinder:task]
status: closed
assignee: none
blocked-by: []
---

## Question

Per T005's resolution: spec the conditional stages of the one flow — orientation (repo recon + archify diagrams, fires on unmapped codebases), research fan-out (tickets declare unknowns; parallel subagents), prototype mode (tracer-bullet tickets, reduced gates, deploy: main|standalone|none, graduation step that cherry-picks prototype modules into real tickets), and the teardown gate (2 failed fix rounds -> independent architect subagent decides fix-forward vs redesign; findings extraction).

## Resolution

Spec delivered and verified: ../specs/T007-conditional-stages.md (10.7k chars). Four mechanisms as skills (map-codebase, fan-out-research, graduate-prototype, adjudicate-teardown) + two thin contracts (prototype-flag deltas, teardown trigger) honored by the T006 chain skills. Skill names to be reconciled with the T018 roster before build.
