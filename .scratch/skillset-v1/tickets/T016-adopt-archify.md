---
id: T016
title: Adopt? tt-a1i/archify
labels: [wayfinder:research]
status: closed
assignee: research-archify
blocked-by: []
---

## Question

ADOPTION CANDIDATE. 'Turn any idea, plan, or codebase into a beautiful interactive diagram' (91k stars, Apache-2.0 + NOTICE). What is the archify/ package actually (skill, CLI, or both — it also ships archify.zip), what are the runtime dependencies (browser renderer? node?), how is output produced and viewed, and where would diagramming earn its place in our flow (spec visualization? brownfield codebase orientation? map rendering?)? Verdict: install-as-is / integrate-adapt / skip + exact steps.

## Resolution

ADOPT: install the `archify` skill as-is — `npx skills add tt-a1i/archify -g` (Node ≥18; local Chrome only powers the browser-verification gate; no npm install; 5.4 MB on disk, ~5k tokens on invocation). It fills our missing capability: validated, source-linked interactive diagrams for brownfield orientation (pinned-commit evidence) and spec viz (10 types + architecture delta compare). Integrate-adapt: keep the explainer mode request-only (no `[archify explainer: proactive]` rules lines) and ship `ARCHIFY_UPDATE_CHECK_DISABLED=1` for offline-first posture. Skip: the repo's four dev-only skills under `.agents/skills/` (archify's own QA workflow, not published). Apache-2.0 + NOTICE (originated from Cocoon-AI/architecture-diagram-generator; prior MIT grants preserved).

Findings: .scratch/skillset-v1/research/archify.md (15.7 KB, every claim source-cited)
