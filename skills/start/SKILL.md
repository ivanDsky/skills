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

# Start

Classify the ask, read project state, print the run plan, fire the chain.
One run = one classification; the chain skills own everything after the plan.

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

- Precedence: session override (`/start fast|standard|thorough`) >
  `docs/agents/AGENTS.md` > PROFILE.md; default `standard`.
- Map the level to subagent knobs, gates, and stage behavior with
  [Effort mapping](references/effort-mapping.md). A prototype caps gates at
  the fast tier at any effort.

## Run plan, then fire

Print one line per stage: fires/skips · HITL or AFK (read each skill's
`interaction` frontmatter, effort overrides applied) · gate · artifact path.
Ask at most one question, only if triage is genuinely ambiguous — then fire.

## Debug run log

PROFILE.md `debug: on`, or "debug on" said this session → create
`.scratch/run-log.md`; every chain skill appends one bounded entry (≤4 lines):

`<skill> | fired by <trigger> | contributed: <what changed> | depth: ok | skipped: <none | what + why>`

`depth != ok` when a size estimate is exceeded, >2 fix rounds run, research
fan-out tops 3 subagents, or a gate re-ran — always with the cause. Off = no
log. The per-run ledger (`.scratch/<slug>/ledger.md`) is a different file.

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
| support | `graduate-prototype` | prototype promoted to feature work |
| support | `assess-teardown` | teardown gate: 2 failed fix rounds or reviewer discretion |

`map-codebase`, `fan-out-research`, `graduate-prototype`, `assess-teardown`
are the chain contract and land separately — when one fires and the skill is
absent, say so and stop that branch instead of improvising.

Close calls (quick vs feature vs prototype): read
[Triage cases](references/triage-cases.md).

Adapted from mattpocock/skills (`triage`, `wayfinder` — triage/routing
mechanics only), MIT.
