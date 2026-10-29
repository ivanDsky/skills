---
id: T004
title: Ecosystem mechanics: npx skills + skills.sh
labels: [wayfinder:research]
status: closed
assignee: research-ecosystem
blocked-by: []
---

## Question

What makes a repo a first-class citizen of the npx skills ecosystem? Study vercel-labs/skills (CLI docs: docs/commands.md, docs/agents.md) and vercel-labs/agent-skills (their own skills repo incl. skills.sh.json): how does `npx skills add <owner>/<repo>` discover skills (which layouts does it scan), what is skills.sh.json for, how do badges/listing work, and what should github.com/ivanDsky/skills contain so `npx skills add ivanDsky/skills` just works, including picking a target agent like prime-agent/pi?

## Resolution

Findings: `.scratch/skillset-v1/research/skills-ecosystem.md`.
`add` discovery = repo-root SKILL.md (early-returns), known containers (`skills/` first) walked 3 deep, any top-level dir at depth 1, `skills.sh.json` `paths`, plugin manifests, then recursive fallback; frontmatter needs string `name` + `description` only (no name/dir check — our lint must cover it). skills.sh.json is display-only groupings on skills.sh; listing + badge + counts are telemetry-driven from installs; `pi` targets `.agents/skills/`.
Repo checklist delivered in the findings file; urgent item: `_template/` currently surfaces as installable skill `template` — mark `metadata.internal: true`.
