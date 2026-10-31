---
name: init-profile
description: >-
  Interview once in one batch with recommended one-word defaults, then write
  PROFILE.md (project deltas only), check the global user layer at
  ~/.agents/AGENTS.md, seed .scratch/ and the tracker, and add the one /start
  entry line to the harness config. Use on the first /start in a project
  without PROFILE.md, after installing the skillset (the skills CLI fires no
  hooks), when a session starts in a repo whose config is missing, or when the
  user says /setup or wants to set project defaults.
interaction: hitl
requires: []
---

# Init profile

One-time per-project setup. `npx skills add ivanDsky/skills` places files and
fires nothing — no hooks exist — so this ritual is the entire integration, and
its whole product is one line: "Work in this repo starts with /start."
Alias: `/setup`.

## Triggers

| Trigger | What happens |
|---|---|
| Install (`npx skills add`) | Files placed, nothing fires. Nothing runs until `/start` or `/setup` — never invent an install hook. |
| First `/start`, no PROFILE.md | `start` delegates here; after setup, re-triage the original ask. |
| New session, config missing | Same as first `/start`. |
| `/setup` | Manual re-run — idempotent, diff-first (step 5). |

## 1. Read state

1. `PROFILE.md` at project root: present → skip to the idempotent path (step 5).
2. `~/.agents/AGENTS.md`: present, and does it cover the user layer (step 2)?
3. Harness config to host the entry line: append to whichever of project
   `AGENTS.md` / `CLAUDE.md` exists — never create both, never create the
   other; neither exists → create `AGENTS.md`; a harness with neither (e.g.
   prime-agent) → the session's prompt note.

## 2. Check the global user layer (once, ever)

`~/.agents/AGENTS.md` holds the USER-level defaults every project inherits:
preferred stack, default platform, UI taste, hard style rules. Missing or thin
→ offer to create or extend it with a second small batch, same one-word
format. Never write project facts there. The project `PROFILE.md` holds only
deltas: deploy targets, testing style, effort default, and a platform override
only when the project differs from the user default. Precedence everywhere:
session override > project config > global layer > skill body > skill defaults.

## 3. Ask ONE batch (intake style)

Numbered questions, arrow line with the recommendation, "yes" accepts, one-word
replies. Lookups are never questions: ask only what the repo and the global
layer do not already answer.

1. Care-axes rank — 3, most important first. The rank order is the review
   priority order and selects the `references/rules-*.md` payloads.
2. Effort level: `fast | standard | thorough` — recommend `standard`.
3. Deploy targets, in order — recommend build-only (`- local: <run command>`).
4. Testing style: `tdd-fakes | tdd-real | smoke-only`, runner, seams.
5. Tracker location — default `.scratch/<slug>/tickets/`; lands in PROFILE.md
   only when the project points elsewhere.
6. Platform override — only when the project differs from the user default.
7. Product frame — the agent proposes from the ask, the user confirms or
   edits: purpose in one line (what the app is for, what it says), who it is
   for, and the core loop (the main flow a user repeats). Understanding pain
   points and what users care about starts here — every later spec builds on
   this frame instead of re-asking it.

Send the batch and stop. Never a second batch.

## 4. Write everything

`PROFILE.md` at the project root, exactly this shape:

```markdown
# PROFILE.md — written by init-profile, read by /start

## Product (frame)
# purpose: <one line — what this app is for and says>
# users: <who it is for>
# core loop: <the main flow a user repeats>
# pain points: <what users struggle with that this addresses>

## Care-axes (ranked: what quality means here)
1. architecture/SOLID
2. UI/UX                     # premium | standard
3. readability

## Effort
- level: standard            # fast | standard | thorough; override: /start <level>
- debug: off

## Platform & stack (deltas only)
# Preferred stack + default platform live in ~/.agents/AGENTS.md.
# platform: <only when this project differs from the user default>
# stack: <only when this project diverges from the preferred stack>

## Deploy targets (in order; empty list = build-only)
- local: <run command>
# - firebase: <project id>
# - tailscale: <host>

## Testing style
- runner: <command>
- approach: tdd-fakes        # tdd-fakes | tdd-real | smoke-only
- seams: <where tests attach>
```

The four contract sections are Care-axes, Effort, Deploy targets, Testing
style — extra sections are allowed, never required. The effective platform
(override, else user default) routes the UI rules payload
(`rules-ui-<platform>.md`), the platform review axes, and the screenshot
source for fast-tier review — the UI verification ladder
(`tdd`/references/android-testing.md): JVM screenshot suites
(Roborazzi / AGP preview tests) first; emulator/device only at acceptance.

Then, in order:

1. `.scratch/` seed: create the directory if absent; `tickets/` under the
   tracker location from the batch.
2. The entry line: append exactly one line to the harness config from step 1 —
   `Work in this repo starts with /start.` No heading, no section, no hooks,
   no injection budget; ~0 tokens until `/start` runs.
3. Report in ≤5 lines: what was written where (PROFILE.md, global layer,
   entry line, `.scratch/`). Debug answered `on` → create
   `.scratch/run-log.md` (chain skills append one ≤4-line entry each).

## 5. Idempotent re-run (/setup)

Existing PROFILE.md → show the proposed edits as a diff and apply only
accepted lines; never overwrite care-axes silently. Missing pieces elsewhere —
global layer, entry line, `.scratch/` — get one offer each. Nothing to change
→ say so in one line.

## Decision rules

- **Missing section heals**: a chain skill that finds a missing PROFILE.md
  section asks once, writes the answer back, and moves on — it degrades
  silently and never points at `/setup`. This skill is the only place in the
  skillset with an explicit "run /setup" pointer; every other skill treats
  setup as a soft dependency.
- Effort default `standard`; the per-session `/start <level>` override always
  wins over PROFILE.md.
- A batch answer edits one file, never starts a re-interview: corrections to
  setup go through the same diff in step 5.

Adapted from mattpocock/skills (`grilling` — one-batch, yes-accepts-default
questioning; config-as-files) and obra/superpowers ("the bootstrap is the
entire integration"), both MIT.
