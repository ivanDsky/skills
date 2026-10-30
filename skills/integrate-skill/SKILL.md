---
name: integrate-skill
description: >-
  Onboard a new skill into this repo (frontmatter contract, trigger-case evals,
  size report, router registration) and land skill updates from user feedback
  through the same gate — nothing lands without lint PASS. Use when the user
  asks to add or register a new skill, when feedback took the skill-update path
  of the two-way capture, or when an edited skill needs its evals and lint
  re-run before landing.
interaction: hitl
requires: []
---

# Integrate skill

One gate for the two ways a skill changes: onboarding a new skill (path A) and
landing a skill update from feedback (path B, the `[s]kill` path of the
two-way capture). This is HITL work: the user sees the diff and the eval
changes before anything lands. Nothing lands without lint PASS.

## Read first

1. `GLOSSARY.md` — exact terms in the body and in every eval prompt.
2. Target skill's `evals/<name>.json` (exists → update it; new skill → create
   it; schema: `skill`, `positive` list, `negative` list of
   `{prompt, owner}`).
3. The roster verdict for the skill — install-as-is, adapt, or fresh — sets
   which path rules below apply (install-as-is skills are ported, never
   edited in place).

## Path A — onboard a new skill

1. Scaffold: copy `docs/skill-template` to `skills/<name>/`. Name kebab-case,
   verb-first, ASCII (`[a-z0-9-]`, no `--`, 1–64 chars); `name:` equals the
   directory name exactly, uppercase `SKILL.md`. Done when: directory +
   `SKILL.md` exist and the names match.
2. Frontmatter contract — exactly four keys: `name`, `description`,
   `interaction` (`hitl | afk | mixed`), `requires` (`[]` unless the skill
   runs external tools). Unknown keys fail lint. Never put interaction or
   requires into the description — the linter owns the extension keys.
3. Description QA: one sentence, "what it does. Use when <trigger>." —
   imperative, third person, keyword-rich. It carries the entire routing
   burden. Route test: three real-phrasing asks must rank this skill first
   over its nearest neighbor; a mis-route is fixed by editing the
   description, never the eval.
4. Trigger cases into `evals/<name>.json`: ≥3 positive prompts and ≥2
   near-miss negatives, every negative naming the `owner` skill that should
   fire instead. Done when: each negative states the boundary with its owner
   and the description already draws it.
5. Body: ≤ ~1.5k tokens, numbered steps with checkable ends, decision rules;
   depth goes to `references/`, one level deep, behind "read X when Y"
   pointers. Feels big → split the reference, not the skill. Footer credit
   line: adapted sources named with license; fresh skills credit inspiration.
6. Size report: line and word counts of `SKILL.md` and each reference,
   reported against the ≤ ~1.5k-token target.
7. Register: add the row to `start`'s Stage → skill dispatch table — a stage
   row for chain stages, a `support` row otherwise, each with its fires-when.
   The skill introduces a new term → add it to `GLOSSARY.md` with an Avoid
   line. Dual access check: the skill must route standalone AND compose in
   the chain; single-mode only → fix description or body before lint.
8. Lint gate: run the Tier 1 linter — the T003 13-rule checklist plus the
   `interaction`/`requires` extension checks (no linter script in the repo
   yet → run the checklist by hand and say so in the report). PASS → report
   path, size report, eval counts, registration. FAIL → fix and re-run;
   nothing lands on a FAIL.

## Path B — land a skill update from feedback

Feedback arrives via the two-way capture offer or a direct complaint.

1. Locate: name the skill and quote the exact step or instruction that
   misbehaved. The complaint maps to no existing skill → say so; authoring a
   new skill for it is path A and the user's call.
2. Fix in house voice: the smallest change that fully solves; numbered steps,
   decision rules, glossary terms; keep ≤ ~1.5k tokens — overflow moves into
   `references/`. Install-as-is skills: send the fix upstream instead and
   record it.
3. Update trigger cases: add ≥1 positive case phrased like the complaint; a
   boundary moved → also add the near-miss negative. The miss was routing
   (right behavior, wrong skill fired) → fix the description instead.
4. Lint gate and size report on the diff. Show before/after plus the eval
   changes; land on explicit confirm only — never silently.

## Decision rules

- Update vs project config: behavior every project should get → path B;
  project-local exception → `docs/agents/AGENTS.md` (the `[p]roject` path,
  not this skill).
- Update vs re-author: a fix touching more than half the body → run path A's
  full gate on the same skill.
- Tier 3 behavioral evals stay opt-in, chain-critical skills only (intake,
  review, teardown gate) — never a default onboarding requirement.

Registration pattern adapted from awesome-llm-apps agent_skills
(`registry.json`: fixed paths, per-skill `evals_dir`), Apache-2.0; contract
per T008 and T006 §10.
