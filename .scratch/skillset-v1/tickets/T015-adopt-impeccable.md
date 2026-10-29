---
id: T015
title: Adopt? pbakaus/impeccable
labels: [wayfinder:research]
status: closed
assignee: research-impeccable
blocked-by: []
---

## Question

ADOPTION CANDIDATE. 'The design vocabulary for your coding agent. Steer with polish and bolder, review with critique and audit, catch AI slop before it ships' (95k stars, Apache-2.0). What are the actual artifacts (vocabulary files, skills, commands?), how does it load across harnesses (many adapter dirs), what is the per-session context footprint, and does it complement or duplicate the user's existing design skills? Per-skill verdict: install-as-is / integrate-adapt / skip + exact steps. Apache-2.0: vendoring allowed with NOTICE.

## Resolution

ADOPT (mostly install-as-is): impeccable is one skill + a deterministic 62-rule Rust detector, not a skill collection — the whole-repo mirror is 5,059 paths, but only `skill/impeccable` (~2.18 MB) matters. Core skill, craft-floor ban list, and detector/hook are install-as-is (complements apple-design / emil-design-eng knowledge skills); live browser mode and whole-repo vendoring are skip. Recommended path: `npx impeccable install` as a self-updating external tool rather than vendoring into our `npx skills add` repo; Apache-2.0 + NOTICE (ehmo MIT attribution) if we do vendor.

Findings: .scratch/skillset-v1/research/impeccable.md (11,279 bytes, verified)
