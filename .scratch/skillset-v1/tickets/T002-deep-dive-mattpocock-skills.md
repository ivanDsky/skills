---
id: T002
title: Deep-dive mattpocock/skills
labels: [wayfinder:research]
status: closed
assignee: research-mattpocock
blocked-by: []
---

## Question

We already use Matt's skills and know the pitch (small, composable, user-invoked). Go deeper: how do the engineering skills chain (grilling/to-spec/to-tickets/implement/code-review) — what artifact does each consume and produce, where does state live between sessions? How does the per-repo setup skill make skills configurable (docs/agents/*.md contract)? What do SCOPE.md, GLOSSARY.md, and the skills/<category> layout actually do for the repo? Which parts are worth keeping as-is, which should we diverge from, and why? Local installed copies exist under ~/.agents/skills/; the source repo is github.com/mattpocock/skills.

## Resolution

Findings: [research/mattpocock-skills.md](../research/mattpocock-skills.md). The chain grilling → to-spec → to-tickets → implement → code-review is artifact-driven with all inter-session state in the issue tracker (or `.scratch/` files) and none in the skills; `docs/agents/*.md` (issue-tracker / triage-labels / domain, written by setup, read by all engineering skills) is the per-repo config contract, with an explicit hard-vs-soft dependency rule for the setup pointer. SCOPE.md + `.out-of-scope/` + the repo's own GLOSSARY.md are repo-hygiene patterns worth copying for our own skills repo. Steal: config contract, tracer-bullet tickets + expand–contract (brownfield), durability rules, frontier-rounds grilling, two-axis code-review, invocation split. Skip: GitHub/GitLab tracker templates, docs-page machinery, triage/PR surface, implement-spec's worktree orchestration. Open: our installed copies are stale vs main; greenfield entry point and implement vs implement-spec deferred to T005/T006.
