---
name: tdd
description: Implement every feature and bug fix test-first — write one failing test, watch it fail, add the minimal code that passes, refactor while green — and own the test policy of what to test and what not to. Use when building or changing behavior in code, when the user says TDD, test-driven, red-green-refactor, test first, or failing test, when writing tests before implementation, when deciding which tests, goldens or flake fixes a change needs and which are redundant, or when reproducing a bug as a test.
interaction: afk
requires: []
---

> **TL;DR** Implements every change test-first — failing test, minimal passing code, refactor while green — and owns the what-to-test policy; fires on TDD, red-green-refactor, bug repro as test, or "which tests does this need".
> **Related**: skill://implement (ticket execution), skill://diagnose-bug (bug repro), skill://preview-compose (screenshot tests), skill://structure-checks (structure suite as Kotlin evidence), skill://goldfish-review (verifiability lens)

# TDD

No production code without a failing test you have watched fail. A test written after the code passes immediately, which proves nothing.

## Cycle

For each behavior, in order:

1. **Red.** Write one minimal test for one behavior — "and" in the name means two tests. Clear name, real code, literal expected value, assertion on real behavior (never on a stub).
2. **Watch it fail.** Run that test. It must fail because the feature is missing — not error on a typo, import, or fixture. Fix and re-run until the failure is the expected one.
3. **Green.** Write the smallest code that passes. No extra options, no early generalizing.
4. **Watch it pass.** Run the touched module's (or file's) tests, not only the new one. Report and fix every failure they show, including ones you did not cause. The full suite runs once per run, in `review-change` after its fix loop converges — never per cycle.
5. **Refactor.** Remove duplication, improve names, extract helpers. Tests stay green; add no behavior.
6. Repeat from 1 for the next behavior.

## Decision rules

- Test passes on the first run → it tests existing behavior. Rewrite it for the new one.
- Code got written before its test anyway → delete it and implement fresh from the test. Keep no "reference" copy. The code-first cases under Exceptions are the only way around this.
- Need to explore first → explore freely, throw the exploration away, start the cycle on what you learned.
- Bug report → the first failing test reproduces it; the fix follows the cycle. A fix without its test is not done.
- Test is hard to write → the design is hard to use. Simplify the interface; do not force the test.

## Exceptions

Only discarded throwaway prototypes, generated code, and pure config changes skip the cycle. If a throwaway turns into something kept, restart it test-first.

Code-first by design: a quick task's code and `user-check` fast fixes are written before their tests so the user can try them sooner. After the user's OK, tests go only to logic those fixes changed — rules, state machines, data, persistence — in the re-gate's hardening tickets or fix batch, or in `review-change`. A purely visual fast fix is covered by its golden and gets no pin test. Each test is watched failing by temporarily reverting the change it guards. A test that still passes with the change reverted proves nothing; rewrite it.

## What to test, what not to

The one test policy for every skill; `write-tickets`, `implement` and `user-check` link here and never restate it.

**Admission.** Every new test names, in one line in the PR body or the ledger, the bug it catches. No answer → the test is not written.

**Keep writing:**
- pure-rule tests — merges, state machines, rankers, parsers, hint deductions;
- ViewModel state-transition tests with fakes;
- one e2e per user journey;
- sync conflict and idempotency cases;
- corpus and property tests for solvers;
- codec fuzz for share and import formats;
- one regression test per logic bug found by review or the user, at the lowest layer that can catch it.

**Stop writing:**
- flag-off tests for a flag headed for removal — at most one flag-off smoke test per flag;
- retro pin tests of approved visual behavior;
- echo, forwarding and constant tests;
- hex or dp assertions where a golden exists;
- a UI test that repeats a ViewModel assertion;
- DI-resolves tests beyond one graph check;
- replay e2e tests that duplicate an existing journey.

**Goldens** (committed screenshot references, rung 3 of the testing ladder).
- One hero state per composable, light and dark, at phone width. Tablet only where the layout branches.
- Shared and design-system goldens (component browser, theme) have one owner; feature workers never re-record them.
- One record job per milestone, followed by an md5 duplicate check.

**Flakes.**
- A test that flakes twice is quarantined, with a tracked ticket.
- A known-failing test is fixed or deleted in the run that meets it, never carried.
- A wall-clock sleep in a test becomes a test clock.

## Done when

- Every new behavior the policy above admits has a test that was watched failing for the right reason; each test passes the admission line.
- Minimal implementation, touched-module tests green, output clean.
- Each test would fail under a realistic mutation: wrong branch, missing side effect, missing input validation.

Read [testing-rules](references/testing-rules.md) when writing or changing tests, choosing fakes over mocks, or checking what a test really catches.
Read [android-testing](references/android-testing.md) when testing Android or Compose apps — choosing JVM-unit vs Robolectric vs instrumented tests, or mapping what to test at each layer.
Read [web-testing](references/web-testing.md) when testing web/React apps — the six-rung ladder (types → lint → component logic → pixel captures → scripted browser flows → human), browser-as-emulator rule, and coverage mapping.

---

Adapted from [obra/superpowers](https://github.com/obra/superpowers) (`test-driven-development`), MIT License.
