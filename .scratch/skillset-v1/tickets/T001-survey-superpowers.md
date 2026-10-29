---
id: T001
title: Survey obra/superpowers
labels: [wayfinder:research]
status: closed
assignee: research-superpowers
blocked-by: []
---

## Question

How does the most popular process-skills repo actually work, mechanically? Map the methodology end to end: the using-superpowers entry skill (how does it auto-trigger, what does it inject?), the brainstorm-to-spec-to-plan-to-execute chain (exact skill names and handoff artifacts between them), subagent-driven execution and its review loop, what lives in hooks/, and how the many plugin manifests (.claude-plugin, .codex-plugin, etc.) are generated. What is concretely stealable for our own flow, and what only works because of Claude Code specifics?

## Resolution

Closed 2026-10-29. Findings: [research/superpowers.md](../research/superpowers.md).
- Auto-trigger = one SessionStart hook (`startup|clear|compact`) injecting the `using-superpowers` router skill; all other skills are model-invoked via the Skill tool with routing-tuned descriptions. Bootstrap re-injection after compaction is load-bearing.
- The real product is the artifact spine: spec (docs/superpowers/specs/) → plan (docs/superpowers/plans/, with Spec backlink, Global Constraints, Review Focus, Interfaces blocks) → git-ignored per-plan SDD workspace with ledger + briefs + review packages; Ruling:/Deferred-minors ledger conventions; dual-verdict reviews (spec + quality) with scoped re-reviews, round caps, and "Declined to judge" lists.
- Steal: router/bootstrap pattern, spec→plan file spine, plan format, ledger + dispatch discipline (brief files, ≤15-line status contract, model ladder), review contracts, verification-before-completion + receiving-code-review guardrails, <20k-byte skill limit + references/ progressive disclosure.
- Skip: 16-harness manifest matrix, visual companion, eval-lab machinery. Noted tension: superpowers rejects `npx skills` installs as "not real integrations" — our npx distribution still needs a per-harness bootstrap story.
