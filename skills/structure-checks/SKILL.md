---
name: structure-checks
description: >-
  Turn file-structure and layering rules into Konsist unit tests for a Kotlin
  or Android project — one public top-level type per file, file-size cap,
  layer dependencies, Compose preview and token rules — with a shrink-only
  allowlist for existing violators, so workers fix by splitting instead of
  arguing with prose. Use when setting up structure checks, when a ticket adds
  or moves Kotlin files and needs its structure evidence, when files keep
  holding many classes, or when the user says konsist, structure test, one
  class per file, or enforce the architecture rules mechanically.
interaction: mixed
requires: [Kotlin project built with Gradle]
---

> **TL;DR** Prose rules about file structure get ignored; a failing Konsist test does not. This skill installs the tests, owns the allowlist ratchet, and defines the worker contract: fix by splitting, never edit rules or suppress.
> **Related**: skill://design-architecture (rule text lives in its rules-architecture payload, rules 17 and 20 — this skill enforces, never redefines), skill://micro-architecture (file maps and one-file-per-variant), skill://write-tickets (file map + Evidence), skill://implement (`structure:` before DONE), skill://review-change (runs it in the fast tier), skill://init-profile (opt-in, `structure:` command), skill://tdd (where the tests run in the ladder)

# Structure checks

A rule the worker can skip is advice. This skill makes the structure rules
fail a build. Konsist (structural linter for Kotlin whose checks are plain
unit tests) is the engine; the value here is the rule set, the ratchet, and
who may touch what.

Provenance: checked against docs.konsist.lemonappdev.com on 2026-11-04;
Gradle `testImplementation("com.lemonappdev:konsist:<version>")` (0.15.1 in
the README at that date — pin whatever the project resolves). Three
constraints from those docs shape the design:

- **No baseline file** ("will be added in the future"). Retrofitting is
  granular scopes or `@Suppress` — so the allowlist below is ours, in the test.
- **`@Suppress("konsist.<test name>")` silences a declaration test**; it is
  the cheapest way for a worker to make a check green. Architecture
  assertions ignore it (remove files from scope instead). Rule S0 bans it.
- **An empty scope passes.** A misspelled module name verifies nothing; the
  `strict` assertion parameter fails on an empty declaration list. Use it.

## 1. Setup (HITL — the first time only)

1. Kotlin/Android project, `structure:` not yet in PROFILE.md → propose
   setup (it adds a test dependency and a test source set). Opt-in, one
   question; declined → record `structure: none` in PROFILE.md and stop.
2. Add the dependency and a `structure` test package; generate the rule
   tests from [references/rules-structure.md](references/rules-structure.md)
   for the rules the user keeps (S1 and S3 default on, S2/S4/S5 asked).
3. First run: every current violator lands in `structure/allowlist.txt` —
   one project-relative path per line, comment with the rule id. The tests
   exclude allowlisted paths from their violations **and fail on any
   allowlist entry that no longer violates** (stale entries must be deleted).
   That is the ratchet: the list can only shrink.
4. Prove the check can fail: add a deliberate two-type file, see the build go
   red with the file named, delete it. A structure suite that was never seen
   red is not evidence.
5. Write the PROFILE.md `Testing style` line `structure: <exact Gradle
   command>` (the project's unit-test task filtered to the structure package)
   and confirm it runs at least one test.

## 2. Worker contract (implement briefs carry this as a Standards line)

- Run the `structure:` command before DONE; report `structure: <result>`.
- Red → **fix by splitting or moving code**. Never edit files under
  `structure/`, never extend the allowlist, never add a `konsist.` suppress.
  Those files are protected; needing a change is NEEDS_CONTEXT or a
  `Ruling:` the controller or user signs.
- A new file lands with its responsibility in the ticket's file map. The
  split is by responsibility, not by line count — a file shredded into
  fragments to dodge the type count is a worse failure than the one it
  hides (Goodhart): reviewers read the file map against the real files.

## 3. Review contract

`review-change` runs the `structure:` command itself in the fast tier. Red is
❌; not configured on a Kotlin diff is `cannot-verify`. A diff that touches
the protected files (`structure/**`, the allowlist) without a ledgered
`Ruling:` is an Important finding. Coverage row: `structure: <n> new/moved
files, command exit <code>, protected files untouched: yes/no`.

## 4. Limits

- Counts types, cannot judge cohesion — the file map plus review do that.
- Kotlin only. Web/TS projects have their own ladder (`web-env`); no
  structure suite exists for them yet.
- Rules are the user's bar: raise or relax them in `rules-structure.md`
  with a dated reason, never per ticket.

Konsist: github.com/LemonAppDev/konsist (Apache-2.0 — dependency, no code
vendored). Rule text sources: `design-architecture` rules 17 and 20.
