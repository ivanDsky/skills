---
id: T012
title: Survey addyosmani/agent-skills
labels: [wayfinder:research]
status: closed
assignee: research-addyosmani
blocked-by: []
---

## Question

'Production-grade engineering skills' (111k stars). Map the full layout: skills/, commands/, agents/, references/, evals/, hooks/, plugin.json, AGENTS.md. Special attention: the evals/ practice — how does this repo TEST its skills (inputs, expected behaviors, harness)? Neither mattpocock nor superpowers emphasize evaluation, so this may be the thing to steal for our authoring standards. Also: what lives in commands/ vs skills/, what do the agents/ and references/ dirs do, and how does the README communicate the system to humans? What concretely belongs in our authoring standards and repo layout?

## Resolution

Surveyed via primary sources (git tree, README, AGENTS.md, evals/README.md, run-evals.js, skill-lint.js, CI workflow, sample skills/cases/graders). Findings: .scratch/skillset-v1/research/addyosmani-agent-skills.md
Core steal: their three-tier eval framework — free CI structural lint + description-routing evals (≥3 positive/≥2 negative prompts with owner-pairwise checks, collision detection, rank-1 ratchet) + opt-in headless-`claude` behavioral evals (expectations[], git-baselined fixture workspaces, fenced-trace grading, pressure fixtures). Routing failures are fixed by editing the description, not the eval — that loop is the authoring-standard practice to adopt.
Skip: 24-skill lifecycle breadth, 11-host adapter sprawl, repo-root references/ (breaks per-skill npx installs — we invert it), hooks, personas, plugin A/B evals until post-v1.
