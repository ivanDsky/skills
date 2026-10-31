<!-- Per-user swappable payload (rules-books pattern): replace these rules per user or project; the tdd procedure does not depend on them. -->

# Testing rules — this user: fakes over mocks

Every test names the break it catches: a wrong branch, missing side effect, missing validation, broken contract — never an intentional decision like a constant's value or message wording.

## Writing tests

1. Name the production change that would make the test fail before writing the body. Cannot name one → redesign the test around an observable behavior.
2. Derive expected values by hand — literals or hand-checked fixtures. Never compute the expected value with the code under test or its helpers; it passes no matter what the code does.
3. Assert behavior, not text: run scripts and artifacts, assert outputs, side effects, exit codes. Grepping source for a line proves only that the source is the source.
4. Test your boundary contract; upstream framework mechanics are the framework's tests. A genuinely surprising upstream behavior earns one narrow characterization test naming the assumption.
5. Constructors, getters, constants, and trivial forwarding get tests only when they validate, normalize, derive, or cause side effects — otherwise assert the first consumer-visible result.

## Fakes over mocks

6. Prefer a hand-written fake or in-memory double over a mocking framework; reach for a mock only when the real dependency is slow or external.
7. Learn the real method's side effects before faking it. Keep the ones the test depends on real; fake only the slow or external layer below them.
8. The fake earns no assertions. Assert the component's behavior; assert call arguments or counts only when they are the contract.
9. Fakes mirror the complete real structure — every documented field — not just the fields the test reads. Partial fakes fail silently.
10. Mock setup larger than the test, or you cannot say why the mock is there → switch to an integration test with real components.
11. Test-only cleanup and helpers live in test utilities, never as methods on production classes.

## Before finishing

12. Mutation check: for each realistic mutation — wrong constant, wrong branch, missing side effect, empty return, missing validation of empty/zero/unauthorized input — at least one test fails. A mutation nothing catches marks the behavior unprotected or the test tautological.
