---
id: T019
title: Build the install + adapt tier (10 skills)
labels: [wayfinder:task]
status: closed
assignee: none
blocked-by: []
---

## Question

Author the 6 install-as-is skills (incl. ui-ux-pro-max, T022) (vendored per adoption verdicts, attribution kept) and 4 adapt skills (ponytail, run-intake, tdd, scope-creep-detector) per T008 standards: small bodies, frontmatter contract, references/, trigger cases, lint-clean. Recommended first (fastest wins).

## Resolution

10/10 skills built; all PASS the linter with 0 errors (2026-10-29; design-taste-frontend carries 2 accepted upstream warnings: 528-line body / ~9.6k tokens, upstream-owned under install-as-is): 6 install-as-is vendored with licenses + ATTRIBUTION.md (taste, archify+NOTICE, 3 ponytail lenses, ui-ux-pro-max), 4 adapt authored (ponytail, run-intake, tdd, scope-creep-detector) each with references/, credit footer, and central evals/<name>.json trigger cases. scripts/lint_skills.py ported (Apache-2.0). Follow-up: lint allowlist for interaction/requires keys lands with the T020 runner.
