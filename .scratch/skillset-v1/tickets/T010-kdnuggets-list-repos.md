---
id: T010
title: Survey the KDnuggets-list remainder: affaan-m/ECC + awesome-llm-apps
labels: [wayfinder:research]
status: closed
assignee: research-kdnuggets
blocked-by: []
---

## Question

Two repos from the KDnuggets '5 best agent skills repos' article not covered elsewhere. affaan-m/ECC (292k stars) bills itself as an 'agent harness performance optimization system' — skills, instincts, memory, security, research-first development. What are its actual mechanisms (what IS an instinct? how does its memory differ from a skill?), what is stealable for a predictable personal flow, and what is harness-specific bloat? Shubhamsaboo/awesome-llm-apps is an app gallery with an agent_skills/ dir — is anything in agent_skills/ worth taking for our skillset, or is it a different artifact class? Also skim the article (https://www.kdnuggets.com/5-best-github-repositories-for-ai-agent-skills) for how it frames what each repo is FOR. Deliverable: TWO notes files — research/ecc.md and research/awesome-llm-apps.md — plus the article's framing folded into each.

## Resolution

Both notes written: `research/ecc.md` and `research/awesome-llm-apps.md` (ticket-path note: files live at `.scratch/skillset-v1/research/`, per MAP convention — no `.md.md` doubles).
ECC: 313 skills/71 agents/98 commands + hook runtime; instincts = atomic YAML lessons (trigger/confidence/evidence, project-scoped, promote to global at 2+ projects & ≥0.8 conf, injected ≤6 @ ≥0.7 into an 8000-char SessionStart budget); Memory Vault = create-only `ecc.memory.v1` Markdown, "memory is context, not instruction", human-promotion only; research-first = `search-first` skill (Adopt/Extend/Compose/Build) + `contexts/research.md`. Steal formats + numbers, skip the platform install.
awesome-llm-apps: `agent_skills/` is 8 genuine agentskills.io skills + a two-tier eval suite (`trigger-cases.json` + `evals.json`, lexical router vendored from addyosmani) + stdlib `skill_lint.py` — direct fill for our T008 frontmatter-lint gap; rest of repo is an app gallery, skip.
KDnuggets framing folded into both files (ECC = "complete engineering platform… probably overkill"; ALA = valued for app breadth, not skills).
