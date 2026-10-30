---
id: T008
title: Set authoring standards for our skills
labels: [wayfinder:grilling]
status: closed
assignee: None
blocked-by: [T003]
---

## Question

Lock the standards every skill in this repo must meet: naming conventions, description style (trigger phrasing rules), HITL/AFK labeling, progressive-disclosure rules, whether skills use categories or flat layout, what validation runs before a skill lands (frontmatter lint, name/dir match, description non-empty), and whether the repo carries SCOPE.md/GLOSSARY.md like Matt's does.

## Resolution

Decided with the user (2026-10-29):

- **Smallness first (user's hard rule)**: a skill is the smallest file that makes the agent act correctly. Body target <= ~1.5k tokens, concise-procedural voice (numbered steps, decision rules). Depth lives in `references/` with explicit "read X when Y" pointers, one level deep. If a skill feels big, split the reference, not the skill.
- **Layout**: flat `skills/<name>/`. Categories only if engineering demands later.
- **Naming**: kebab-case, verb-first (`draft-spec`, `review-change`), ASCII-only.
- **Frontmatter contract**: `name` + `description` (name == dir) per spec, plus our extensions `interaction: hitl | afk | mixed` and `requires: [<external tools>]` — machine-readable, checked by `/start`; never put these in the description. Linter owns the extension keys.
- **Descriptions**: one sentence, "what it does. Use when <trigger>." — imperative, third person, keyword-rich.
- **Dual access**: every skill routes standalone AND composes in the chain.
- **Validation ladder**: Tier 1 lint always (T003 13-rule checklist via skill_lint.py + our extension checks; pre-ship gate + CI on push). Tier 2 routing evals per skill (>=3 positive + >=2 near-miss negative trigger cases, rank-1 ratchet in CI; fix mis-routing by editing the description, never the eval). Tier 3 behavioral evals opt-in, only for chain-critical skills (intake, review, teardown gate).
- **User preferences = swappable payloads** (rules-books pattern): procedures stay generic; `references/rules-*.md` carry SOLID/style/TDD rules, replaceable per user or project.
- **Repo meta-docs**: GLOSSARY.md yes (chain vocabulary), SCOPE.md no (map + tracker serve that role).
- **Onboarding**: new skills go through the integrate step — register in the router index, add trigger cases, routing check, size report (feeds T017).
