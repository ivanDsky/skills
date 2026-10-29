---
id: T014
title: Adopt? Leonxlnx/taste-skill
labels: [wayfinder:research]
status: closed
assignee: research-taste-skill
blocked-by: []
---

## Question

ADOPTION CANDIDATE. 'Agent skills that give coding agents taste: art direction, reference images and a browser check instead of generic AI pages' (105k stars, MIT). Map skills/ (each skill's job), tests/ (does it evaluate its own skills? how?), install.sh mechanics, and what the browser check requires at runtime. The user already runs design skills (emil-design-eng, apple-design, animation/tooling) — does this overlap, complement, or replace them? Per-skill verdict + exact steps. MIT: vendoring allowed with attribution.

## Resolution

Adopted: **install-as-is** `design-taste-frontend` (the repo's only skill — older ones moved to taste-skill-classics). Verified 105,510 stars, MIT, v2.1.5 (2026-10-25), zero-dependency runtime we already meet (Node 22+, any installed Chrome/Edge/Chromium). Fills our real gap (art-directed pages + app screens with a measured browser gate); complements emil-design-eng/apple-design, minor routing + style conflicts noted. Caveats: ~30-45 min & few hundred k tokens per page build, opinionated bans (mitigated by `--allow`/`--keep`).
Findings: .scratch/skillset-v1/research/taste-skill.md
