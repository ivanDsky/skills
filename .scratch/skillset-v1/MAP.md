---
labels: [wayfinder:map]
---

## Destination

`github.com/ivanDsky/skills` — a shipped, `npx skills add ivanDsky/skills`-installable personal skillset: v1 flow chains for greenfield and brownfield work, skills analyzed from the major repos then written/adapted as our own, configurable per project.

## Notes

- Authoring bar: `writing-great-skills` (installed) — predictability, routing-oriented descriptions, progressive disclosure, checkable completion criteria.
- Every skill must pass frontmatter validation (name matches dir, description non-empty) or it silently never loads.
- Research findings land as files under `.scratch/skillset-v1/research/` — any session can zoom them.
- Research roster (one notes file per repo under `.scratch/skillset-v1/research/`): obra/superpowers (T001), mattpocock/skills (T002), agentskills.io spec + anthropics/skills (T003), npx skills ecosystem (T004), affaan-m/ECC + awesome-llm-apps from the KDnuggets list (T010), ciembor/agent-rules-books (T011), addyosmani/agent-skills (T012).
- Adoption candidates (install-as-is or integrate — user-supplied): DietrichGebert/ponytail (T013), Leonxlnx/taste-skill (T014), pbakaus/impeccable (T015), tt-a1i/archify (T016).
- The user adds personal priorities/wants once the repo is deploy-ready.
- Distribution decision already made: `npx skills` (vercel-labs/skills CLI); local tracker for planning (see docs/agents/issue-tracker.md).

## Decisions so far

- [Stand up the repo](tickets/T009-stand-up-the-repo.md) — pushed private to github.com/ivanDsky/skills; local markdown tracker configured; install.py retired in favor of npx skills.

## Not yet specified

- **Skill inventory & disposition** — which of the user's installed skills stay as-is, which get ported, which gaps need new skills; hangs on T005 (positioning) and on the user's priorities.
- **User priorities & wants** — the user will spec what they care about once the repo is deploy-ready; may redraw parts of the map.
- **Multi-harness distribution** — plugin manifests (Claude Code / Codex / etc.) like superpowers and mattpocock maintain; hangs on positioning + ecosystem research.
- **v1 porting plan** — sequencing of writing/adapting skills once chains are defined; hangs on T006/T007/T008.
- **Frontmatter lint tooling** — a validator script or CI check; hangs on T008.

## Out of scope

- Migrating this effort's map to GitHub Issues — user chose the local markdown tracker for this effort; revisit only if the destination is redrawn.
