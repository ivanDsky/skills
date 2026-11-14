---
name: implement
description: >-
  Execute tracker tickets one fresh subagent per ticket in tracer-bullet order,
  fanning out research subagents for declared unknowns first and keeping the
  append-only ledger current with a Ruling line for every deviation. Use when
  the frontier has ready tickets, when resuming implementation after an
  interruption, or after write-tickets produces a ticket set.
interaction: afk
requires: []
---

> **TL;DR** Executes tracker tickets one fresh subagent per ticket in tracer-bullet order, fanning out research first; fires when the frontier has ready tickets, for user-check fast fixes, and for hardening tickets.
> **Related**: skill://write-tickets (upstream tickets), skill://fan-out-research (declared unknowns), skill://user-check (downstream: user tries the epic; sends fast fixes and hardening tickets back), skill://review-change (gate after hardening), skill://graduate-prototype (prototype re-entry), skill://structure-checks (`structure:` before DONE), skill://ship-to-trunk (`trunk` delivery: one worktree + PR per ticket, merge rules)

# Implement

You coordinate; workers code. Briefs and reports travel as files, the ledger
carries the run, and after any interruption the ledger plus git log beat
recollection.

## 1. Step zero — unknowns

1. Read the frontier (tickets open, unblocked, unclaimed), each ticket's spec
   backlink, and PROFILE.md (effort level, debug). Resuming? Trust the ledger
   and git log over your own memory.
   Delivery `pr` (PROFILE `## Delivery` or start's answer) → make sure the
   run branch `<slug>` is checked out before the first dispatch; workers
   commit on it. Never commit a `pr` run to the default branch. More than
   ~20 files or several tickets expected → a stack instead: `gh stack init
   <slug>/01-<ticket>`, then `gh stack add <slug>/<NN>-<ticket>` from the top
   before each next ticket; concurrent parallel-safe tickets share one
   layer. A fix (review round, fast fix) commits into the layer that owns
   the file, then `gh stack rebase --upstack` (`open-pr`/references/stacks.md).
   Delivery `trunk` → no run branch. Each ticket's worker gets its own
   worktree from freshly fetched `origin/main` and ends with its PR merged
   per `ship-to-trunk`/references/merge-loop.md (merge authority: the
   `ship-to-trunk` table; flip and live PRs wait for the user). Frontier =
   tickets whose parents' PRs are MERGED. Stacks only under
   `ship-to-trunk`'s exception. `pr-check: none`: a worker ends at "branch
   pushed, ready" (fast review done, no suite, no rebase, no PR, no merge,
   no polling); the orchestrator owns the merge lane
   (`ship-to-trunk`/references/merge-loop.md: `merge_lane.py land`, one
   ticket at a time as a background bash job) and calls `main_health.py
   status` before merging, holding on red. The orchestrator also runs one
   `main_health.py watch --who <slug>` background bash job, started after
   the run's first merge and after a later merge when none is running; on
   red it attributes the culprit and claims and fixes it when the culprit
   is its own merge; on green after red it lands the PRs `held` lists
   with `merge_lane.py land` on their kept worktrees (rerun rule applied by
   the script). Flow: `ship-to-trunk`/references/merge-loop.md § Red main.
2. Claim: set `status: claimed` before any work.
3. A ticket with `Unknowns` gets research subagents first, one per unknown, in
   parallel; link every findings file into the ticket before coding starts.
   Fan-out per ticket effort level (ticket `effort:` field, run default as
   fallback): fast = none (research only when a ticket is
   blocked), standard = cap 3, thorough = full parallel. Agent per
   `start`/references/effort-mapping.md's reviewer/research table: `scout`
   for code/repo questions, `task` for web/primary sources.

## 2. Dispatch

1. One fresh subagent per ticket, tracer-bullet order (01 walks the path
   first). Tickets marked parallel-safe (declared disjoint file scopes) may
   run concurrently, each on its own subagent; shared surfaces wait on their
   blocking edges. Never two implementers on one tree — if scopes overlap,
   serialize and ledger the `Ruling:`.
2. The brief is a FILE: the ticket, the spec backlink, neighbor interfaces,
   and a Standards block (at most 5 lines — see dispatch.md). Neighbor
   interfaces and file-scope facts come from one `scout` dispatch, not from
   the controller reading files — unless the ledger or earlier reports
   already hold them. The dispatch
   prompt holds only the brief path, one line of context, and the report
   contract. Never paste session history into a dispatch.
3. Report contract: the worker writes a report file and replies in at most
   15 lines — status DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT,
   commits, one-line test summary, `device:` and `structure:` lines,
   concerns. Briefs, reports and ledger in caveman voice (`start` § Voice).
4. Workers never spawn subagents — no helpers, no reviewers. Review belongs
   to review-change.
5. Knobs, enforced at dispatch: dispatch per the ticket's `tier:` using
   `start`/references/effort-mapping.md's *Tier → agent and model* table
   (agent, model and spawn `effort`); never pass `model` to scout/sonic
   (config-pinned); escalation per the same section. Missing `tier:` → the
   table's defaults. Missing `effort:` → fall back to the run default.

## 3. Inside the ticket — layered skills

1. Scope: skills/ponytail governs — understand → reuse → adapt → extend →
   new code last; the smallest change that fully solves; never cut
   validation, security, accessibility, or data-loss handling.
2. Process: skills/tdd at the seams — one failing test, minimal code to pass;
   non-trivial logic leaves one small test behind.
3. Guard: skills/scope-creep-detector the moment a diff touches files the
   ticket never named — its keep / split / justify verdicts decide.
4. Knowledge: read what the brief's Standards block names, nothing more.
   - UI/view tickets: `preview-compose` before any composable (author its
     `@Preview`s with it); method from `senior-ux` (evaluation framework,
     computed floors, A/B on the user's hardware); taste from
     `emil-design-eng`, `ui-ux-pro-max`, `apple-design`; motion named via
     `animation-vocabulary`. A new or changed reusable composable (public
     API, `XxxState`, `XxxDefaults`) follows
     `micro-architecture`/references/ui-components.md at the ledgered
     `ui-tier`: no use case, domain model or ViewModel for UI-only state.
   - Feature flags, remote config, dev-facing settings: `wire-dev-settings`
     before touching configuration code.
   - Architecture-heavy tickets (new module, new boundary, dependency
     direction in play): `design-architecture` first, diff graded against its
     `../design-architecture/references/rules-architecture.md`. Feature
     split follows `micro-architecture` (stable core + one-file variants,
     tracer bullet before fan-out); conduct follows `senior-dev`. Brownfield
     work reuses the map-codebase project map; diagrams via archify.
   - Android CLI (`android-cli` skill) where it beats raw tooling: renames
     and blast-radius via `android studio find-usages` (IDE open) or LSP;
     dependency bumps via `android studio version-lookup`; API questions via
     `android docs search`; preview renders via `android preview render`
     when no Roborazzi suite exists.
   - Verification stops at rung ≤3 of the testing ladder
     (`tdd`/references/android-testing.md): unit tests and device-free
     captures only. Never boot an emulator, deploy to a device, or tap
     through a screen to "check how it looks/works" mid-implementation —
     that is acceptance evidence, owned by `user-check` and the user. A flow you
     would verify by hand becomes a persisted semantic JVM test (recipe in
     the same reference). Report `device: none`; any use needs
     `device: used because <reason>`, and the installed build comes from
     `deliver`'s `ship_apk.py` (`deliver`/references/build-identity.md):
     a unique versionCode from the ledger shared by all worktrees, so
     parallel agents never downgrade or overwrite each other.
     Environment/build friction (missing adb, SDK, suspicious Gradle red)
     goes through `android-env`'s checklist before being believed or
     re-derived.
5. Style while writing, not after: `design-architecture`'s
   `rules-code-style.md` (in design-architecture) governs comments (self-explanatory code;
   comments only for WHY) and names the AI-slop patterns a worker must not
   emit; review grades against the same file.
6. Event triggers while writing: creating a file → its one-sentence
   responsibility is written down first (the ticket's file map; none
   present → add it to the report); about to add a variant by editing a
   shared `when`/registry/factory → stop, write a `Ruling:`; introducing a
   pattern → state its forcing function (a second real variant, or the
   Extension points assumption in the spec) in the commit body. The
   `structure:` command from PROFILE.md is green before DONE — fix by
   splitting; never edit the rules or the allowlist (`structure-checks`).
7. Every worker reply ends `skipped: … / residual risk: …`.

## 4. Status handling

- DONE_WITH_CONCERNS: concerns go to the ledger as deferred findings for
  review-change. DONE: nothing extra.
- NEEDS_CONTEXT: answer as a brief addendum file, resume the same worker.
  Only the user can answer → the orchestrator asks through the ask tool
  first (`start` § Waiting on the user); workers never ask the user.
- BLOCKED: ledger a `Ruling:`, reopen the ticket, take another frontier
  ticket. Four things stop the run and ask the user (ask tool, `start` §
  Waiting on the user): an irreversible or destructive operation, a
  security-sensitive action, a side effect outside the worktree norms say
  to ask about first, a ticket so broken every path forward is a guess.

## 5. Close and loop

1. DoD evidence must exist or the ticket stays open. On close: append the
   ledger line, take the next frontier ticket. `trunk`: close = PR merged,
   ledgered `slice: <NN> PR #<n> merged @ <sha>`. `pr-check: none`: the
   ticket stays `claimed` from `ready` until the lane merges it; the
   frontier counts only merged parents (no change in meaning).
2. Every deviation from ticket or spec lands as
   `Ruling: what — why — cost if wrong`.
3. Frontier empty → hand off by ticket kind. Feature tickets → `user-check`
   (the user tries the whole epic, not each ticket). Hardening tickets from
   `user-check`'s re-gate → `review-change`. `trunk`: hand off once the
   last feature slice merged — the user checks a debug build from `main`
   with the flag forced on; the flip and cleanup tickets wait for
   user-check OK and thorough review (`ship-to-trunk` lifecycle).
4. Fast-fix briefs from `user-check` (`mode: fast-fix`, F-ids listed): the
   quality bar is off on purpose. No tests, no refactor, no `structure:`;
   only the smallest change the user asked for, committed `fast(F<n>): …`.
   The section-3 never-cuts (validation, security, accessibility, data
   loss) still hold. The re-gate pays the rest down. `trunk`: each fast fix
   and each hardening ticket is a new slice — own worktree, own PR, same
   merge loop.
5. Debug on (PROFILE.md): append one ≤4-line entry per ticket to
   `.scratch/run-log.md`.

Read [references/dispatch.md](references/dispatch.md) before writing the
first brief — brief, report, and ledger templates live there.

Adapted from mattpocock/skills (`implement`) and obra/superpowers
(`subagent-driven-development`, `executing-plans`), MIT.
