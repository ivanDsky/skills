---
labels: [wayfinder:map]
---

## Destination

`github.com/ivanDsky/skills` — a shipped, `npx skills add ivanDsky/skills`-installable personal skillset: v1 flow chains for greenfield and brownfield work, skills analyzed from the major repos then written/adapted as our own, configurable per project.

## Notes

- Authoring bar: `writing-great-skills` (installed) — predictability, routing-oriented descriptions, progressive disclosure, checkable completion criteria.
- Every skill must pass frontmatter validation (name matches dir, description non-empty) or it silently never loads.
- Research findings land as files under `.scratch/skillset-v1/research/` — any session can zoom them.
- Synthesis: [`REFERENCE-MAP.md`](REFERENCE-MAP.md) — per-repo digests (novelty, organization, what we take) + state-of-the-art briefing. Read it before working any grilling ticket.
- Research roster (one notes file per repo under `.scratch/skillset-v1/research/`): obra/superpowers (T001), mattpocock/skills (T002), agentskills.io spec + anthropics/skills (T003), npx skills ecosystem (T004), affaan-m/ECC + awesome-llm-apps from the KDnuggets list (T010), ciembor/agent-rules-books (T011), addyosmani/agent-skills (T012).
- Adoption candidates (install-as-is or integrate — user-supplied): DietrichGebert/ponytail (T013), Leonxlnx/taste-skill (T014), pbakaus/impeccable (T015), tt-a1i/archify (T016).
- The user adds personal priorities/wants once the repo is deploy-ready.
- Distribution decision already made: `npx skills` (vercel-labs/skills CLI); local tracker for planning (see docs/agents/issue-tracker.md).

## Decisions so far

- [Stand up the repo](tickets/T009-stand-up-the-repo.md) — pushed private to github.com/ivanDsky/skills; local markdown tracker configured; install.py retired in favor of npx skills.
- [Survey obra/superpowers](tickets/T001-survey-superpowers.md) — auto-trigger = one SessionStart hook; the asset is the artifact spine + subagent-driven execution with dual-verdict review.
- [Deep-dive mattpocock/skills](tickets/T002-deep-dive-mattpocock-skills.md) — chain = skills passing artifacts through the tracker; per-repo config via docs/agents/*.md; local copies are stale, refresh before judging.
- [Extract the agentskills.io spec contract](tickets/T003-extract-agentskills-spec.md) — 13-rule linter checklist ready; the standard covers only loading — chaining, HITL/AFK, config are ours to invent.
- [Ecosystem mechanics: npx skills + skills.sh](tickets/T004-skills-ecosystem-mechanics.md) — repo checklist for `npx skills add` exists; skills.sh.json is display-only; top-level dirs with SKILL.md are discovered.
- [Survey the KDnuggets-list remainder](tickets/T010-kdnuggets-list-repos.md) — ECC is a platform, not a skillset; steal instinct microformat + stdlib skill_lint.py; awesome-llm-apps adds trigger-case eval pattern.
- [Survey ciembor/agent-rules-books](tickets/T011-survey-agent-rules-books.md) — adopt the pattern (skill = procedure + swappable rule payload), not the 14-book corpus; mini-tier compression + 5-part rule template.
- [Survey addyosmani/agent-skills](tickets/T012-survey-addyosmani-skills.md) — three-tier evals (lint → routing → behavioral); routing failures are fixed by editing the description, not the eval.
- [Adopt? ponytail](tickets/T013-adopt-ponytail.md) — adopt mostly: npx-install review/audit/debt skills; own the core mode prompt; skip always-on hooks (760 vs 400 tok/session).
- [Adopt? taste-skill](tickets/T014-adopt-taste-skill.md) — install-as-is design-taste-frontend; fills art-direction gap; browser check is zero-dep CDP; heavy per page (30-45 min).
- [Adopt? impeccable](tickets/T015-adopt-impeccable.md) — adopt as external self-updating tool (`npx impeccable install`), not vendored; complements apple-design/emil-design-eng.
- [Adopt? archify](tickets/T016-adopt-archify.md) — install-as-is for brownfield orientation + spec viz; ship with update-check disabled; heaviest skill carried (5.4 MB, ~5k tok/invocation).

## Not yet specified

- **Skill inventory & disposition** — which of the user's installed skills stay as-is, which get ported, which gaps need new skills; hangs on T005 (positioning) and on the user's priorities. Adoption verdicts for the four candidates are decided (see T017); the rest of the inventory waits.
- **User priorities & wants** — the user will spec what they care about once the repo is deploy-ready; may redraw parts of the map.
- **Multi-harness distribution** — plugin manifests (Claude Code / Codex / etc.) like superpowers and mattpocock maintain; hangs on positioning + ecosystem research.
- **v1 porting plan** — sequencing of writing/adapting skills once chains are defined; hangs on T006/T007/T008.
- **Frontmatter lint tooling** — a validator script or CI check; hangs on T008.

## Out of scope

- Migrating this effort's map to GitHub Issues — user chose the local markdown tracker for this effort; revisit only if the destination is redrawn.
