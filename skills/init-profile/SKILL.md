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

> **TL;DR** Interviews once with recommended one-word defaults, then writes PROFILE.md and seeds tracker and scratch; fires on a project's first start.
> **Related**: skill://start (first run), skill://integrate-skill (repo onboarding), skill://structure-checks (opt-in question 8; writes the `structure:` line), skill://ship-to-trunk (`changes: trunk`, the `merge dark slices on green` consent line)

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

1. Care-axes rank — 3, most important first, each optionally with up to 2
   hard-rule sub-bullets. The rank order is the review priority order,
   selects the `references/rules-*.md` payloads, and picks which hard rules
   ride in each brief's Standards block.
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
8. Structure checks — Kotlin/Android projects only: opt in to
   `structure-checks` (Konsist tests: one public type per file, layer
   dependencies)? Recommend yes; it adds a test dependency. `yes` records the
   command under Testing style after `structure-checks` setup runs; `no`
   records `structure: none`.

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
   - one public type per file; part N+1 is a new file    # hard rules, ≤2 per axis: the rank picks which ride in each brief's Standards block
2. UI/UX                     # premium | standard
3. readability

## Effort
- level: standard            # fast | standard | thorough; override: /start <level>
- debug: off

## Platform & stack (deltas only)
# Preferred stack + default platform live in ~/.agents/AGENTS.md.
# platform: <only when this project differs from the user default>
# stack: <only when this project diverges from the preferred stack>

## Version
- version: 0.1.0             # semver major.minor.patch; bumped ONLY when cutting a release on main (minor default), never per install or per landed change
- app-id: <applicationId>    # build-identity allocator (deliver): device versionCode lookup
- app-name: <AppName>        # APK prefix: <app_name>-<version_name>-<code>-<variant>.apk

## Review site
- publish: ask               # ask (default: start asks each run) | always | off

## Delivery
- changes: ask              # ask (default: start asks each run) | trunk (small PRs into main, ship-to-trunk) | pr | main

## Consent ledger            # what the agent may do without asking
- pre-approved: merge to main after green review; lint fixes; dependency bumps; secret-free fixture redaction; commit+push to the project repo
# - pre-approved: merge dark slices on green   # trunk projects: agent merges dark/non-behavioral slice PRs on green check + clean fast review; flip PRs and live changes still ask
- always ask: public pushes; publish/delete; runs longer than ~30 min of dispatch; anything touching user data

## Environment facts         # stated once, never re-derived
- (device topology, e.g. tablet on LAN via tailscale, has no terminal)
- (review site must be LAN-exposed, not localhost)
- (artifact naming, theming defaults, version policy — project specifics)

## Deploy targets (in order; empty list = build-only)
- local: <run command>
# - firebase: <project id>
# - tailscale: <host>

## Testing style
- runner: <command>
- approach: tdd-fakes        # tdd-fakes | tdd-real | smoke-only
- seams: <where tests attach>
- structure: <command | none>  # Gradle task running the structure-checks suite; set by structure-checks setup
```

The four contract sections are Care-axes, Effort, Deploy targets, Testing
style — extra sections are allowed, never required. `## Version` is seeded
(`0.1.0`, plus `app-id`/`app-name` read from the app module) when missing
so every project ships named artifacts
(`<app_name>-<version_name>-<code>-<debug|release>.apk`). Setup on main
also lands the one-time Gradle wiring from
`deliver`/references/build-identity.md (versionCode/versionName read from
`-PagentVersionCode`/`-PagentVersionName`), so worktrees never edit build
files; `## Review site` is seeded
(`ask`) so each run can opt into the localhost review dashboard; `##
Delivery` is seeded (`ask`) so each run chooses trunk (small PRs into main,
`ship-to-trunk`), one PR, or straight to main before the first commit; `## Consent
ledger` is seeded with the defaults above (merge-to-main after green review
is the standard stop point — the agent never infers consent from silence;
a trunk project adds the commented `merge dark slices on green` line only
when the user opts in)
and `## Environment facts` is seeded empty so one-time facts (device
topology, LAN exposure, naming) are captured instead of re-derived every
session; missing
sections are asked
about once. The effective platform
(override, else user default) routes the UI rules payload
(`rules-ui-<platform>.md`), the platform review axes, and the screenshot
source for fast-tier review — the UI verification ladder
(`tdd`/references/android-testing.md): JVM screenshot suites
(Roborazzi / AGP preview tests) first; emulator/device only at acceptance.

Then, in order:

1. Android project → `android init` (Android CLI: env setup + official
   android-cli skill) once, and note the CLI in PROFILE.md; skip on
   non-Android platforms.

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
