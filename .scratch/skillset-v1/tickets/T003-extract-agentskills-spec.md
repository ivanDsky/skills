---
id: T003
title: Extract the agentskills.io spec contract
labels: [wayfinder:research]
status: closed
assignee: research-spec
blocked-by: []
---

## Question

Extract the portable contract: the Agent Skills standard at agentskills.io (frontmatter fields, name rules, directory layout, what every compliant harness guarantees) and how anthropics/skills implements it (skills/ layout, template/, spec/ dirs, their authoring guidance). Deliverable: the exact validation rules our repo must enforce so skills load everywhere, plus what the standard does NOT cover that we must decide ourselves (chaining, HITL/AFK, config).

## Resolution

Findings: [research/agentskills-spec.md](../research/agentskills-spec.md). The whole standard is one page: a skill = dir with SKILL.md (six frontmatter fields; only name+description required), recommended scripts/references/assets dirs, three-tier progressive disclosure. Exact linter checklist written out (13 ERROR rules incl. name==dirname / charset / no `--` / 64 & 1024 char caps; WARN rules for >500-line bodies, unresolved relative paths, unpinned script versions) from agentskills.io spec + the official skills-ref validator source + Anthropic's quick_validate.py. Standard does NOT cover chaining, HITL/AFK, per-project config, or Python-backed extensions — all need our own conventions (recommend `metadata` keys + Prime Agent's `disable-model-invocation`). Open charset question (spec prose says Unicode, validators say ASCII) resolved as: enforce ASCII.
