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

> **TL;DR** Executes tracker tickets one fresh subagent per ticket in tracer-bullet order, fanning out research first; fires when the frontier has ready tickets.
> **Related**: skill://write-tickets (upstream tickets), skill://fan-out-research (declared unknowns), skill://review-change (downstream gate), skill://graduate-prototype (prototype re-entry)

# Implement

You coordinate; workers code. Briefs and reports travel as files, the ledger
carries the run, and after any interruption the ledger plus git log beat
recollection.

## 1. Step zero — unknowns

1. Read the frontier (tickets open, unblocked, unclaimed), each ticket's spec
   backlink, and PROFILE.md (effort level, debug). Resuming? Trust the ledger
   and git log over your own memory.
2. Claim: set `status: claimed` before any work.
3. A ticket with `Unknowns` gets research subagents first, one per unknown, in
   parallel; link every findings file into the ticket before coding starts.
   Fan-out per ticket effort level (ticket `effort:` field, run default as
   fallback): fast = none (research only when a ticket is
   blocked), standard = cap 3, thorough = full parallel.

## 2. Dispatch

1. One fresh subagent per ticket, tracer-bullet order (01 walks the path
   first). Tickets marked parallel-safe (declared disjoint file scopes) may
   run concurrently, each on its own subagent; shared surfaces wait on their
   blocking edges. Never two implementers on one tree — if scopes overlap,
   serialize and ledger the `Ruling:`.
2. The brief is a FILE: the ticket, the spec backlink, neighbor interfaces.
   The dispatch prompt holds only the brief path, one line of context, and
   the report contract. Never paste session history into a dispatch.
3. Report contract: the worker writes a report file and replies in at most
   15 lines — status DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT,
   commits, one-line test summary, concerns.
4. Workers never spawn subagents — no helpers, no reviewers. Review belongs
   to review-change.
5. Knobs, enforced at dispatch: implementer on the cheapest capable tier;
   subagent thinking follows the ticket's `effort:` field (fall back to the
   run default when absent) — low / medium / high for fast / standard /
   thorough.

## 3. Inside the ticket — layered skills

1. Scope: skills/ponytail governs — understand → reuse → adapt → extend →
   new code last; the smallest change that fully solves; never cut
   validation, security, accessibility, or data-loss handling.
2. Process: skills/tdd at the seams — one failing test, minimal code to pass;
   non-trivial logic leaves one small test behind.
3. Guard: skills/scope-creep-detector the moment a diff touches files the
   ticket never named — its keep / split / justify verdicts decide.
4. Knowledge: UI/view tickets consult the installed UX skills before writing
   UI code — method from `senior-ux` (evaluation framework, computed floors,
   A/B on the user's hardware); taste from `emil-design-eng`,
   `ui-ux-pro-max`, `apple-design`, `animation-vocabulary`.
   views — ui-ux-pro-max for stack-specific guidelines, apple-design and
   emil-design-eng for principles. Jetpack Compose UI tickets read
   `preview-compose` before writing any composable and author its `@Preview`s
   with it; tickets touching feature flags, remote config, or dev-facing
   settings read `wire-dev-settings` before touching configuration code.
   Architecture-heavy tickets (new module,
   new boundary, dependency direction in play) apply `design-architecture`
   first and grade the diff against its `../design-architecture/references/rules-architecture.md`.
   Brownfield work reuses the map-codebase project map; diagrams via archify.
   Feature split follows `micro-architecture` (stable core + one-file
   variants, tracer bullet before fan-out); conduct follows `senior-dev`
   (smallest correct change, verify before trusting, no drive-by scope).
   Android CLI (`android-cli` skill) where it beats raw tooling: renames and
   blast-radius via `android studio find-usages` (IDE open) or LSP;
   dependency bumps verified with `android studio version-lookup`; Android
   API questions via `android docs search`; preview renders via
   `android preview render` when no Roborazzi suite exists.
   During implementation, verification stops at rung ≤3 of the testing
   ladder (`tdd`/references/android-testing.md): unit tests and device-free
   captures only. Never boot an emulator or deploy to a device to "check
   how it looks/works" mid-implementation — that is acceptance evidence,
   owned by review and the user. Environment/build friction (missing adb,
   SDK, suspicious Gradle red) goes through `android-env`'s checklist
   before being believed or re-derived.
5. Style while writing, not after: `design-architecture`'s
   `rules-code-style.md` (in design-architecture) governs comments (self-explanatory code;
   comments only for WHY) and names the AI-slop patterns a worker must not
   emit; review grades against the same file.
6. Every worker reply ends `skipped: … / residual risk: …`.

## 4. Status handling

- DONE_WITH_CONCERNS: concerns go to the ledger as deferred findings for
  review-change. DONE: nothing extra.
- NEEDS_CONTEXT: answer as a brief addendum file, resume the same worker.
- BLOCKED: ledger a `Ruling:`, reopen the ticket, take another frontier
  ticket. Four things stop the run and ask the user: an irreversible or
  destructive operation, a security-sensitive action, a side effect outside
  the worktree norms say to ask about first, a ticket so broken every path
  forward is a guess.

## 5. Close and loop

1. DoD evidence must exist or the ticket stays open. On close: append the
   ledger line, take the next frontier ticket.
2. Every deviation from ticket or spec lands as
   `Ruling: what — why — cost if wrong`.
3. Frontier empty → hand off to review-change.
4. Debug on (PROFILE.md): append one ≤4-line entry per ticket to
   `.scratch/run-log.md`.

Read [references/dispatch.md](references/dispatch.md) before writing the
first brief — brief, report, and ledger templates live there.

Adapted from mattpocock/skills (`implement`) and obra/superpowers
(`subagent-driven-development`, `executing-plans`), MIT.
