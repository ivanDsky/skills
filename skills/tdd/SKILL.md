---
name: tdd
description: Implement every feature and bug fix test-first — write one failing test, watch it fail, add the minimal code that passes, refactor while green. Use when building or changing behavior in code, when the user says TDD, test-driven, red-green-refactor, test first, or failing test, when writing tests before implementation, or when reproducing a bug as a test.
interaction: afk
requires: []
---

> **TL;DR** Implements every change test-first — failing test, minimal passing code, refactor while green; fires on TDD, red-green-refactor, or bug repro as test.
> **Related**: skill://implement (ticket execution), skill://diagnose-bug (bug repro), skill://preview-compose (screenshot tests)

# TDD

No production code without a failing test you have watched fail. A test written after the code passes immediately, which proves nothing.

## Cycle

For each behavior, in order:

1. **Red.** Write one minimal test for one behavior — "and" in the name means two tests. Clear name, real code, literal expected value, assertion on real behavior (never on a stub).
2. **Watch it fail.** Run that test. It must fail because the feature is missing — not error on a typo, import, or fixture. Fix and re-run until the failure is the expected one.
3. **Green.** Write the smallest code that passes. No extra options, no early generalizing.
4. **Watch it pass.** Run the project's full suite, not just your file. Report and fix every failure it shows, including ones you did not cause, before calling the change done.
5. **Refactor.** Remove duplication, improve names, extract helpers. Tests stay green; add no behavior.
6. Repeat from 1 for the next behavior.

## Decision rules

- Test passes on the first run → it tests existing behavior. Rewrite it for the new one.
- Code got written before its test anyway → delete it and implement fresh from the test. Keep no "reference" copy.
- Need to explore first → explore freely, throw the exploration away, start the cycle on what you learned.
- Bug report → the first failing test reproduces it; the fix follows the cycle. A fix without its test is not done.
- Test is hard to write → the design is hard to use. Simplify the interface; do not force the test.

## Exceptions

Only discarded throwaway prototypes, generated code, and pure config changes skip the cycle. If a throwaway turns into something kept, restart it test-first.

## Done when

- Every new behavior has a test that was watched failing for the right reason.
- Minimal implementation, full suite green, output clean.
- Each test would fail under a realistic mutation: wrong branch, missing side effect, missing input validation.

Read [testing-rules](references/testing-rules.md) when writing or changing tests, choosing fakes over mocks, or checking what a test really catches.
Read [android-testing](references/android-testing.md) when testing Android or Compose apps — choosing JVM-unit vs Robolectric vs instrumented tests, or mapping what to test at each layer.

---

Adapted from [obra/superpowers](https://github.com/obra/superpowers) (`test-driven-development`), MIT License.
