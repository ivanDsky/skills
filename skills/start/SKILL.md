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
The thinking half is best effort; the real thinking budget is the spawn
`effort` (references/effort-mapping.md).

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
  review page) reaches the user only as a served, checked URL — they are on
  a tablet or phone (`prototype` § 3 Serve, before the ask).
- Read PROFILE.md `## Consent ledger` before every ask: what it
  pre-approves is done, not asked. The user delegates a class of asks ("do
  it yourself", "deploy it yourself", "you pick") → append it as a
  `pre-approved:` line the same turn and name it in the next status.
  Never pre-approvable, however delegated: the flag flip or release, a
  production deploy, data deletion, anything public.
- Budget: ≤5 questions per form, recommended option first; approvals for
  several PRs share one form; a question that blocks nothing waits for the
  next checkpoint form instead of its own ask.
- Reversible decision with a recommended default → preselect it. An answer
  that comes back as the untouched default (the harness submits preselected
  values on timeout) is taken: ledger `assumed: <decision> — default` and
  keep going; the next milestone digest lists every assumption so the user
  overturns them in one place.
- Approvals and irreversible actions never preselect the approving option:
  an omitted or unchecked answer means not approved, so the run keeps
  waiting or asks again once — it never acts on silence — and every lane
  that does not depend on the answer keeps moving.
- Progress reaches the user once per milestone — spec frozen, slices
  merged, user-check build ready, review done, shipped — as one digest of
  ≤10 lines: what landed, `assumed:` lines since the last digest, what is
  next. A milestone that needs an answer puts the digest in its checkpoint
  form instead. No chat per merge, ticket or verdict: between milestones the
  ledger and `fleet-status` hold the state, and a turn that ends with
  nothing new for the user is the status line alone.
- Harness without an ask tool → one plain message whose last line is the
  question (`run-intake` step 4 fallback).
- Every chat message that ends a turn closes with one line:
  `blocked on you: <what>` or `not blocked: <next step>`.
- User rules and corrections → § Decisions and waiting.

## Decisions and waiting (orchestrator)

Compaction drops what the user said (one audited run restated a scope rule
three times), so user statements persist the same turn, before acting:

- A rule, preference, scope ruling or correction scoped to this run → one
  append-only ledger line, `Decision: <scope> — <rule>`
  (`Decision: friends mode — leaderboards rank among friends only; global
  untouched`). A correction appends a new line ending `(supersedes <old>)`;
  the latest line per scope wins. `Ruling:` lines stay the agent's calls.
- Project-wide → PROFILE.md, never the ledger: standing facts to
  `## Environment facts`, delegated asks to `## Consent ledger`, a visual
  rejection to one `## Taste rules` line phrased as the rule (`no large
  empty space below content`). UI briefs and visual reviewers get the whole
  `## Taste rules` section pasted.
- After every compaction or resume, `grep '^Decision:'
  .scratch/<slug>/ledger.md` first; each spawn brief carries the
  `Decision:` lines whose scope its ticket touches, verbatim.
- Never poll workers, CI or PRs (`gh run watch`, `sleep` loops, status
  reads): workers report when done and `merge_lane.py`/`main_health.py`
  background jobs push their result lines. Idle → harness wait.

## Orchestrator lifecycle

This session keeps intake, spec, contract, taste and every ask. Once spec
and contract freeze, each execution milestone runs in one fresh Sonnet
captain subagent fed `.scratch/<slug>/resume.md`; this session waits for its
digest. Third compaction → one `blocked on you:` rollover at the next
milestone. Brief, file format, models: [Lifecycle](references/lifecycle.md).

## Read first

1. `PROFILE.md` (care-axes, effort level, deploy targets, testing style,
   debug flag). Missing file → run `init-profile` first (one batch →
   PROFILE.md + `.scratch/` seed + the "/start" entry line), then re-triage
   the original ask.
2. `docs/agents/AGENTS.md` when present — project-local overrides. A missing
   file is normal; defaults hold.
3. Backlog: PROFILE `## Tracker`, then `backlog.py list --frontier` and the
   tickets claimed by this worktree (`work-tickets`/references/backlog.md).
4. A missing PROFILE.md section → ask once, write the answer back, move on.

## Triage — first match wins, in this order

0. **Backlog session** — the ask is feedback, bugs or ideas to file for
   later, or a request to check what merged → `file-tickets`. The ask is
   to pick up backlog work ("pick up tickets in leaderboard", "take #42")
   → `work-tickets`. Nothing else fires.
1. **Quick task** — ALL true: ≤3 files touched, no new public interface, no
   irreversible op, no deploy → code only (ponytail; no tests, no checks) →
   `user-check` (build or demo, one message, wait) → on OK, its re-gate
   inline and `review-change` at the fast tier (tests for the change, suite
   once, design check) → land.
   No spec, no tickets; the reply ends with `skipped:` and `residual risk:`
   lines.
1b. **Bug report or one-shot fix** — broken behavior (crash, glitch, wrong
   result), or one contained change with no design question → one backlog
   ticket landed by a worker, never the feature chain. Bug: `diagnose-bug`
   gathers evidence first, and its diagnosis becomes the ticket's brief
   (filed as in `file-tickets` § 2). Then `work-tickets --ids <id>` lands
   it here as one PR. "File it" or "later" → stop after filing; any
   worktree's `work-tickets` picks it up.
2. **Unmapped codebase** — chain work ahead + no orientation artifacts →
   run `map-codebase`, fill PROFILE.md care-axes from the map, re-triage.
3. **Prototype** — user flag ("prototype", "quick sketch", "just a demo",
   "show me options") or the ask is really a question ("would X work?").
   Two sizes:
   - **Quick** (default) — one question answerable on a page, nothing real
     touched → `prototype` directly: one throwaway page per task, no
     intake, spec or tickets.
   - **Big** — needs real app code or persisted data, spans modules, or is
     meant to ship → full chain + prototype flag: reduced gates, DoD =
     question answered or demoable, the last ticket carries
     `deploy: main | standalone | none`.
   Close call → quick; its answer decides whether the big one is worth it.
4. **Feature** — default → full chain: intake → spec → contract (new or
   redesigned screens or motion: `prototype` § 5) → tickets → implement
   (TDD at the seams) → `user-check` on the whole epic (feedback rounds are
   fast fixes) → on OK, re-gate into hardening tickets → implement →
   `review-change` (suite once) → deliver → land. The user reviews code
   last, in the PR. Delivery `trunk` differs: slices merge dark (fast review
   each) as tickets close, `user-check` runs on a debug build from `main`
   with the release flag forced on, and the flip PR waits for user-check OK
   plus thorough review (`ship-to-trunk`).

Tickets still claimed by this worktree → the run plan lists them and offers
resume (feature epic → `implement`, otherwise `work-tickets`); the new ask is
still classified normally either way.

## Effort level

Per task, not per run: triage sets the *run default*; each task or ticket
gets its own level from its shape — `thorough` only for architecture,
planning and other big-view work, `standard` for ordinary features, `fast`
for contained fixes. Precedence: session override (`/start
fast|standard|thorough`) > `docs/agents/AGENTS.md` > PROFILE.md; default
`standard`. A prototype caps gates at the fast tier at any effort. Knobs,
gates, stage behavior and per-ticket rules: [Effort
mapping](references/effort-mapping.md).

## Run plan, then fire

Print one line per stage: fires/skips · HITL or AFK (read each skill's
`interaction` frontmatter, effort overrides applied) · gate · artifact path.
Ask at most one question, only if triage is genuinely ambiguous — then fire.
Three decisions bundle into the plan, never a separate round trip (rules
and question wording: [Run plan](references/run-plan.md)):
- Review-site publish (PROFILE `Review site publish:`): `always` → plan
  lists `review-site` after deliver; `off` → skip; `ask` (default) → one
  yes/no for this run.
- Delivery (PROFILE `## Delivery` `changes:`): `pr` → `open-pr` after
  deliver, run branch cut before the first commit; `trunk` →
  `ship-to-trunk`, which needs a required PR check or `pr-check: none`;
  `main` → default branch; `ask` → one question for this run, before
  `implement`. Start never switches the style on its own.
- UI tier: the ask builds or changes a reusable composable → ledger
  `Ruling: ui-tier <module> = library|app — <why>`; ambiguous → one
  question.

## Debug run log

PROFILE.md `debug: on`, or "debug on" said this session → every chain skill
appends one ≤4-line entry to `.scratch/run-log.md`; format and `depth`
rules: [Run plan](references/run-plan.md) § Debug run log. Off = no log.

## Hats — pick one per session, per subagent

Before dispatching anything, name the hat: **implementer** (writes to the
ticket, optimistic), **reviewer** (grades a diff it didn't write),
**designer** (decides what the thing should be, before code),
**diagnostician** (finds cause, fixes nothing yet), **challenger** (a
`goldfish-review` lens: fresh context, one angle, finds what is wrong with a
concept or design, fixes and decides nothing). `implement` dispatches
implementers by ticket `tier:`, `review-change` reviewers (agent and model:
references/effort-mapping.md, *Tier → agent and model*), `goldfish-review`
challengers; `diagnose-bug` stays diagnostician until the fix is a ticket.
One agent never wears two hats on the same work product — the implementer
"reviewing" its own diff is the audited source of "all done" → full-rework
incidents. Switching hats closes the current one first (commit, stop, or
hand off).

## Stage → skill dispatch

| Stage | Skill | Fires when |
|---|---|---|
| intake | `run-intake` | feature, prototype |
| orientation | `map-codebase` | unmapped codebase + chain work |
| spec | `draft-spec` | feature, prototype |
| spec/tickets | `goldfish-review` | stage A after the spec checkpoint confirms scope (orchestrator picks 0–2 lenses by risk); stage B at `write-tickets`' design-review question (user picks none / up to 3 / all) |
| tickets | `write-tickets` | feature, prototype (ticket sets are parallel-first: minimal file overlap; device checks get one aggregate ticket, or none); publishes to the shared backlog with `--epic` |
| backlog | `file-tickets` | triage 0: feedback, bugs or ideas to file; the batched hands-on check of `needs-check` tickets; triage 1b filing |
| backlog | `work-tickets` | triage 0: pick up backlog tickets by area, type, epic or ids; triage 1b: land the one filed ticket |
| research | `fan-out-research` | ticket/spec declares an Unknown |
| implement | `implement` | ready frontier ticket; `user-check` fast fixes; re-gate hardening tickets |
| user check | `user-check` | implement done (feature tickets) or quick-task code written — the user tries the whole change before any review (trunk: after the last slice merged dark, before the flip PR); on OK it re-gates the run into hardening tickets |
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
| prototype | `prototype` | quick prototype (one page per question; big ports via `graduate-prototype`); feature contract stage (§ 5) |
| support | `assess-teardown` | teardown gate: 2 failed fix rounds or reviewer discretion |
| support | `diagnose-bug` | bug report (triage 1b) or a `bug` ticket in `work-tickets`: evidence ladder, user-time-last |
| support | `skill-doctor` | the user asks for a session or workflow audit, or to re-measure after skill changes; never fired by the chain itself |

`map-codebase`, `fan-out-research`, `graduate-prototype`, `assess-teardown`
are the chain contract and land separately — when one fires and the skill is
absent, say so and stop that branch instead of improvising.

Direct paths the chain mandates mid-run beyond the table (do not wait to be
asked): "let me try it first" / hands-on check → `user-check`; Compose UI →
`preview-compose`; flags/dev settings → `wire-dev-settings`; animations →
`animation-vocabulary` + `apple-design`; principles → `emil-design-eng`,
`ui-ux-pro-max`; diagrams → `archify`; architecture → `design-architecture`;
screenshots/tests → `tdd` (`tdd`/references/android-testing.md; web testing
ladder, React-first, browser as the emulator of web:
`tdd`/references/web-testing.md); Android tooling (renders, analysis, docs,
emulators, deploys, signals) → `android-cli`; stacked PRs per ticket (`gh
stack`, fixes into the owning layer) → `open-pr`/references/stacks.md.

Close calls (quick vs feature vs prototype): read
[Triage cases](references/triage-cases.md).

Adapted from mattpocock/skills (`triage`, `wayfinder` — triage/routing
mechanics only), MIT.
