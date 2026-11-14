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
> **Related**: skill://init-profile (prerequisite setup), skill://run-intake (first stage), skill://map-codebase (unmapped triage), skill://goldfish-review (blind lenses at spec and tickets), skill://user-check (hands-on check before review), skill://structure-checks (Konsist structure evidence), skill://open-pr (PR landing when delivery = pr), skill://prototype (quick one-page prototypes), skill://ship-to-trunk (delivery = trunk: one small PR per ticket, merge dark, flip PR releases), skill://caveman (external: terse voice for chat, briefs, reports, ledgers)

# Start

Classify the ask, read project state, print the run plan, fire the chain.
One run = one classification; the chain skills own everything after the plan.
Setup is part of this run: an unset project gets configured here, inside the
first `/start` — never via a separate command the user had to remember.

## Voice (every chain skill)

Text that only the user reads in chat, or only agents read, uses the
caveman voice (`skill://caveman`, installed from JuliusBrussee/caveman):
chat replies and status lines, controller briefs and dispatch prompts,
worker/scout/reviewer/challenger reports, the ledger, findings files
(`review.md`, `regate.md`, research findings). Not installed → the floor:
answer first; no greeting, hedging, recap or closer; fragments fine, but
every not/never/no/only stays; code, paths, numbers and errors verbatim;
≤20 words per sentence. Every dispatch prompt carries one voice line —
"think in short notes: fact, decision, next step; report and reply in
caveman voice; values, paths, errors verbatim; never ask the user —
questions go in the report as NEEDS_CONTEXT" — because subagents do not
inherit the session's mode and only the orchestrator talks to the user.
Plain full sentences instead: questions to the user (ask tool), security or
irreversible-action warnings, and anything persisted for humans — code,
comments, commits, PR bodies, specs, tickets, check docs, `REPORT.md`.
The thinking half of the line is best effort: the model may not follow it,
and the displayed thinking may be a harness summary. The real thinking
budget is the spawn `effort` (references/effort-mapping.md).

## Waiting on the user (every chain skill)

This rule binds the orchestrator — the top-level agent in the user's
session. Subagents and workers never talk to the user: they never call the
ask tool, and they report BLOCKED or NEEDS_CONTEXT to the orchestrator,
which asks the user when only the user can answer.

The user gets a notification only when the orchestrator calls the harness's
ask tool (`ask`, `AskUserQuestion` or equivalent); a chat message that ends
the turn reaches nobody. So every point where the run needs the user ends in
one ask-tool call, never in chat text: a question or decision; an approval
(a PR only the user may merge, a destructive or public action, a downgrade
of review rigor); a checkpoint (spec digest, ticket list); a hands-on step
(`user-check`'s try-it message, recording the phone, a console log); a
worker's BLOCKED or NEEDS_CONTEXT only the user can clear.

- The context goes inside the form (digest, verify steps, PR link, options);
  the chat reply holds no second copy.
- Visual context (a prototype, design options, drawings, screenshots, a
  review page) reaches the user only as a served URL — they are on a tablet
  or phone. Never a local file path, never "I'll send it next". Follow
  `prototype` § 3 Serve (served directory, long-lived server, tailnet URL,
  curl check) before the ask.
- Approvals and irreversible actions never preselect the approving option:
  an omitted or unchecked answer means not approved, so the run keeps
  waiting or asks again — it never acts on silence.
- Reports that need nothing back (merged, delivered, a verdict) stay chat.
- Harness without an ask tool → one plain message whose last line is the
  question (`run-intake` step 4 fallback).

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
   irreversible op, no deploy → code only (ponytail; no tests, no checks) →
   `user-check` (build or demo, one message, wait) → on OK, its re-gate
   inline and `review-change` at the fast tier (tests for the change, suite
   once, design check) → land.
   No spec, no tickets; the reply ends with `skipped:` and `residual risk:`
   lines.
1b. **Bug report** — the ask reports broken behavior (crash, glitch, wrong
   result) rather than requesting new behavior → `diagnose-bug` owns the
   intake and evidence gathering; its output ticket re-enters the normal
   chain for the fix.
2. **Unmapped codebase** — chain work ahead + no orientation artifacts →
   run `map-codebase`, fill PROFILE.md care-axes from the map, re-triage.
3. **Prototype** — user flag ("prototype", "quick sketch", "just a demo",
   "show me options") or the ask is really a question ("would X work?").
   Two sizes:
   - **Quick** (default) — one question answerable on a page, nothing real
     touched → `prototype` directly: one throwaway HTML page per task (one
     subagent per task when there are several), no intake, spec or tickets.
   - **Big** — needs real app code or persisted data, spans modules, or is
     meant to ship → full chain + prototype flag: reduced gates, DoD =
     question answered or demoable, the last ticket carries
     `deploy: main | standalone | none`.
   Close call → quick; its answer decides whether the big one is worth it.
4. **Feature** — default → full chain: intake → spec → tickets → implement
   (TDD at the seams) → `user-check` on the whole epic (feedback rounds are
   fast fixes) → on OK, re-gate into hardening tickets → implement →
   `review-change` (suite once) → deliver → land. The user reviews code
   last, in the PR. Delivery `trunk` differs: slices merge dark (fast review
   each) as tickets close, `user-check` runs on a debug build from `main`
   with the release flag forced on, and the flip PR waits for user-check OK
   plus thorough review (`ship-to-trunk`).

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
Every question to the user, here and in every chain skill, goes through the
harness's ask tool (§ Waiting on the user), never as plain text ending a turn.
Exceptions (each bundles into the plan, never a separate round trip):
- Review-site publish. PROFILE.md `Review site publish:` decides — `always`
  → the plan lists `review-site` firing after deliver; `off` → skip
  silently; `ask` (the default) → one yes/no ("publish the review dashboard
  when this run ships?") that routes deliver's report step for this run only.
- Delivery. PROFILE.md `## Delivery` `changes:` decides — `pr` → the plan
  lists `open-pr` after deliver and the run branch is cut before the first
  commit (several tickets or > ~20 files → a `gh stack`, one layer per
  ticket); `trunk` → the plan lists `ship-to-trunk`: no run branch, one
  worktree + slice PR per ticket off fresh `origin/main`, ticket 01 adds the
  release flag, the flip PR is the release (stacks only by its exception);
  `main` → commits land on the default branch; `ask` (typed by the user at
  setup, or an old PROFILE without the answer) → one question ("trunk
  (small PRs into main), one PR, or straight to main?") answered for this
  run only. The style is the user's per-project decision from
  `init-profile` question 9; start never switches it on its own. Asked
  before `implement` starts, because the branch must exist before the first
  commit. Trunk needs a required PR check (a workflow on
  `pull_request` that main's protection requires): missing → the plan's
  first ticket is the check setup and slices wait for it plus the user's
  branch protection (`ship-to-trunk`); local gates substitute only when
  PROFILE says `pr-check: none` (CI on main only; merge gate = local suite
  on the rebased branch). No
  `merge dark slices on green` consent line → say once that every PR waits
  for the user.
- UI tier. The ask builds or changes a reusable composable → infer the tier
  per module (`micro-architecture`/references/ui-components.md, "Tier
  first"): design-system, shared or published module → `library`;
  feature-local → `app`. Record it as a ledger line
  `Ruling: ui-tier <module> = library|app — <why>`. When it is ambiguous
  (single module, shared `ui/components` package), ask one question
  ("library rules (MUST) or app rules (SHOULD) for <module>?").

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
**diagnostician** (finds cause, fixes nothing yet), **challenger** (a
`goldfish-review` lens: fresh context, one angle, finds what is wrong with a
concept or design, fixes and decides nothing). The dispatch table
below is hat-routed: `implement` dispatches implementers by ticket `tier:`,
`review-change` dispatches reviewers (agent and model for both:
references/effort-mapping.md, *Tier → agent and model*), `goldfish-review` dispatches
challengers, `diagnose-bug` stays
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
| spec/tickets | `goldfish-review` | the user chose lenses (none / up to 3 / all): stage A after intake and before the spec is drafted; stage B at the write-tickets confirm gate |
| tickets | `write-tickets` | feature, prototype (ticket sets are parallel-first: minimal file overlap; device checks get one aggregate ticket, or none) |
| research | `fan-out-research` | ticket/spec declares an Unknown |
| implement | `implement` | ready frontier ticket; `user-check` fast fixes; re-gate hardening tickets |
| user check | `user-check` | implement done (feature tickets) or quick-task code written — the user tries the whole change before any review (pr/main) or after the last slice merged dark, from `main` with the flag forced on and before the flip PR (trunk); on OK it re-gates the run into hardening tickets |
| review | `review-change` | hardening tickets closed after `user-check` OK (quick task: right after OK) |
| deliver | `deliver` | review passes and `suite: green @ HEAD` is ledgered |
| land | `open-pr` | run's delivery decision = pr (PROFILE `## Delivery` `changes:` or session answer), fired by `deliver`; = trunk → once per slice PR and for the flip PR (`ship-to-trunk`) |
| land | `ship-to-trunk` | delivery = trunk: slice size, fresh-base worktree per ticket, merge authority, live changes, flag lifecycle through the flip PR |
| support | `android-env` | first Android command of a session fails, or before the first build/device action (bootstrap checklist) |
| support | `web-env` | first web/Node command of a session fails, or before the first dev-server/build action (bootstrap checklist) |
| support | `adopt-tool` | a new tool/capability is being adopted into the workflow |
| spec/tickets | `micro-architecture` | designing a feature's file split before tickets — parallel-safe decomposition, OCP extension points |
| spec/review | `senior-ux` | UI/UX design or review work — evaluation framework, A/B-on-hardware, tokens-with-floors method |
| always-on | `senior-dev` | every coding session — judgment defaults alongside the stage skills |
| implement/review | `structure-checks` | Kotlin/Android ticket adds or moves files, or the diff touches Kotlin — the PROFILE `structure:` command is Evidence and a fast-tier review check |
| report | `review-site` | run's publish decision = yes (PROFILE `Review site publish:` or session answer) |
| support | `graduate-prototype` | prototype promoted to feature work |
| prototype | `prototype` | quick prototype: one question per page, one subagent per task; small ports land directly, big ones via `graduate-prototype` |
| support | `assess-teardown` | teardown gate: 2 failed fix rounds or reviewer discretion |
| support | `diagnose-bug` | bug report: evidence ladder, user-time-last |

`map-codebase`, `fan-out-research`, `graduate-prototype`, `assess-teardown`
are the chain contract and land separately — when one fires and the skill is
absent, say so and stop that branch instead of improvising.

Direct paths for knowledge skills the chain mandates mid-run (do not wait to
be asked): "let me try it first" / hands-on check → `user-check`; Compose UI → `preview-compose`; flags/dev settings →
`wire-dev-settings`; animations → `animation-vocabulary` + `apple-design`;
principles → `emil-design-eng`, `ui-ux-pro-max`; diagrams → `archify`;
architecture → `design-architecture`; screenshots/tests → `tdd`
(`tdd`/references/android-testing.md); web testing ladder (React-first, browser
as the emulator of web) → `tdd` (`tdd`/references/web-testing.md); web/Node
environment bootstrap → `web-env`; Android tooling (renders, analysis, docs,
emulators, deploys, signals) → `android-cli`; environment bootstrap (PATH,
local.properties, worktree git, device connect, Gradle triage, Studio
modals) → `android-env`; capability adoption checklist → `adopt-tool`;
feature file-split design (parallel-safe, open/closed, one responsibility
per file) → `micro-architecture`; judgment defaults → `senior-dev`; UX
method (framework-judged pixels, A/B on hardware, tokens with floors) →
`senior-ux`; blind concept/design lenses → `goldfish-review`; mechanical
file-structure and layering checks (Konsist) → `structure-checks`; PR
description and landing → `open-pr`; stacked PRs per ticket (`gh stack`,
fixes into the owning layer) → `open-pr`/references/stacks.md; trunk based
/ small PRs / merge dark / keep main releasable → `ship-to-trunk`;
throwaway one-page prototypes → `prototype`.

Close calls (quick vs feature vs prototype): read
[Triage cases](references/triage-cases.md).

Adapted from mattpocock/skills (`triage`, `wayfinder` — triage/routing
mechanics only), MIT.
