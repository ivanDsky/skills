---
name: start
description: >-
  Triage an ask (quick task / prototype / feature / unmapped codebase) and print
  the run plan — stages x effort level x HITL/AFK gates — then fire the matching
  chain. Use when the user says /start or /build, when work starts in a project
  that has PROFILE.md, or when an ask needs classifying and routing to the right
  flow.
interaction: mixed
requires: []
---

> **TL;DR** Triages an ask — quick task, prototype, feature, unmapped codebase — prints the run plan, and fires the matching chain; use on /start.
> **Related**: skill://init-profile (prerequisite setup), skill://run-intake (first stage), skill://map-codebase (unmapped triage)

# Start

Classify the ask, read project state, print the run plan, fire the chain.
One run = one classification; the chain skills own everything after the plan.
Setup is part of this run: an unset project gets configured here, inside the
first `/start` — never via a separate command the user had to remember.

## Read first

1. `PROFILE.md` (care-axes, effort level, deploy targets, testing style,
   debug flag). Missing file → run `init-profile` first (one batch →
   PROFILE.md + `.scratch/` seed + the "/start" entry line), then re-triage
   the original ask.
2. `docs/agents/AGENTS.md` when present — project-local overrides. A missing
   file is normal; defaults hold.
3. Tracker frontier: tickets `open`, `assignee: none`, no unclosed
   `blocked-by` (layout and ops: `docs/agents/issue-tracker.md`).
4. A missing PROFILE.md section → ask once, write the answer back, move on.

## Triage — first match wins, in this order

1. **Quick task** — ALL true: ≤3 files touched, no new public interface, no
   irreversible op, no deploy → inline ponytail run, zero artifacts, no
   chain; the reply ends with `skipped:` and `residual risk:` lines.
1b. **Bug report** — the ask reports broken behavior (crash, glitch, wrong
   result) rather than requesting new behavior → `diagnose-bug` owns the
   intake and evidence gathering; its output ticket re-enters the normal
   chain for the fix.
2. **Unmapped codebase** — chain work ahead + no orientation artifacts →
   run `map-codebase`, fill PROFILE.md care-axes from the map, re-triage.
3. **Prototype** — user flag ("prototype", "quick sketch", "just a demo") or
   the ask is really a question ("would X work?") → full chain + prototype
   flag: reduced gates, DoD = question answered or demoable, the last ticket
   carries `deploy: main | standalone | none`.
4. **Feature** — default → full chain.

Frontier non-empty → the run plan lists in-flight tickets and offers resume
(resume = jump straight to `implement`); the new ask is still classified
normally either way.

## Effort level

- Per task, not per run: triage classifies the *run default*, but each task or
  ticket gets its own effort chosen from its shape — `thorough` only for
  architecture, planning, and other big-view work; `standard` for ordinary
  features; `fast` for contained fixes. Full rules:
  [Effort mapping](references/effort-mapping.md).
- Downgrade ask: picking a lower level than the run default is stated in one
  line ("downgraded to fast: <reason>"); when the agent believes a different
  level would accelerate development, it asks the user rather than deciding
  silently.
- Precedence: session override (`/start fast|standard|thorough`) >
  `docs/agents/AGENTS.md` > PROFILE.md; default `standard`.
- Map the level to subagent knobs, gates, and stage behavior with
  [Effort mapping](references/effort-mapping.md). A prototype caps gates at
  the fast tier at any effort.

## Run plan, then fire

Print one line per stage: fires/skips · HITL or AFK (read each skill's
`interaction` frontmatter, effort overrides applied) · gate · artifact path.
Ask at most one question, only if triage is genuinely ambiguous — then fire.
Exception: the review-site publish decision. PROFILE.md `Review site
publish:` decides — `always` → the plan lists `review-site` firing after
deliver; `off` → skip silently; `ask` (the default) → one yes/no bundled
into the plan ("publish the review dashboard when this run ships?") and the
answer routes deliver's report step for this run only.

## Debug run log

PROFILE.md `debug: on`, or "debug on" said this session → create
`.scratch/run-log.md`; every chain skill appends one bounded entry (≤4 lines):

`<skill> | fired by <trigger> | contributed: <what changed> | depth: ok | skipped: <none | what + why>`

`depth != ok` when a size estimate is exceeded, >2 fix rounds run, research
fan-out tops 3 subagents, or a gate re-ran — always with the cause. Off = no
log. The per-run ledger (`.scratch/<slug>/ledger.md`) is a different file.

## Hats — pick one per session, per subagent

Before dispatching anything, name the hat: **implementer** (writes to the
ticket, optimistic), **reviewer** (grades a diff it didn't write, never its
own), **designer** (decides what the thing should be, before code),
**diagnostician** (finds cause, fixes nothing yet). The dispatch table
below is hat-routed: `implement` dispatches implementers, `review-change`
dispatches a reviewer on a stronger tier, `diagnose-bug` stays
diagnostician until the fix is a ticket. Never let one agent wear two hats
on the same work product — the implementer "reviewing" its own diff is the
audited source of "all done" → full-rework incidents. Switching hats means
closing the current one first (commit, stop, or hand off).

## Stage → skill dispatch

| Stage | Skill | Fires when |
|---|---|---|
| intake | `run-intake` | feature, prototype |
| orientation | `map-codebase` | unmapped codebase + chain work |
| spec | `draft-spec` | feature, prototype |
| tickets | `write-tickets` | feature, prototype |
| research | `fan-out-research` | ticket/spec declares an Unknown |
| implement | `implement` | ready frontier ticket |
| review | `review-change` | implement done |
| deliver | `deliver` | review passes |
| support | `android-env` | first Android command of a session fails, or before the first build/device action (bootstrap checklist) |
| support | `adopt-tool` | a new tool/capability is being adopted into the workflow |
| spec/tickets | `micro-architecture` | designing a feature's file split before tickets — parallel-safe decomposition, OCP extension points |
| spec/review | `senior-ux` | UI/UX design or review work — evaluation framework, A/B-on-hardware, tokens-with-floors method |
| always-on | `senior-dev` | every coding session — judgment defaults alongside the stage skills |
| report | `review-site` | run's publish decision = yes (PROFILE `Review site publish:` or session answer) |
| support | `graduate-prototype` | prototype promoted to feature work |
| support | `assess-teardown` | teardown gate: 2 failed fix rounds or reviewer discretion |
| support | `diagnose-bug` | bug report: evidence ladder, user-time-last |

`map-codebase`, `fan-out-research`, `graduate-prototype`, `assess-teardown`
are the chain contract and land separately — when one fires and the skill is
absent, say so and stop that branch instead of improvising.

Direct paths for knowledge skills the chain mandates mid-run (do not wait to
be asked): Compose UI → `preview-compose`; flags/dev settings →
`wire-dev-settings`; animations → `animation-vocabulary` + `apple-design`;
principles → `emil-design-eng`, `ui-ux-pro-max`; diagrams → `archify`;
architecture → `design-architecture`; screenshots/tests → `tdd`
(`references/android-testing.md`); Android tooling (renders, analysis, docs,
emulators, deploys, signals) → `android-cli`; environment bootstrap (PATH,
local.properties, worktree git, device connect, Gradle triage, Studio
modals) → `android-env`; capability adoption checklist → `adopt-tool`;
feature file-split design (parallel-safe, open/closed, one responsibility
per file) → `micro-architecture`; judgment defaults → `senior-dev`; UX
method (framework-judged pixels, A/B on hardware, tokens with floors) →
`senior-ux`.

Close calls (quick vs feature vs prototype): read
[Triage cases](references/triage-cases.md).

Adapted from mattpocock/skills (`triage`, `wayfinder` — triage/routing
mechanics only), MIT.
