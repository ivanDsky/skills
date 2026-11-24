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

6. MUST cross a seam with a hand-written fake or in-memory double, never a mocking framework. The mocking APIs are banned by lint: `vi.fn`, `vi.spyOn`, `vi.mock`, `vi.stubGlobal`, `vi.useFakeTimers` and sinon on web; mockk and Mockito on Kotlin (`structure-checks` S8). A dependency that is slow or external gets a port and a memory fake, not a mock. Why: prefer the real thing, else a fake proven against it; interaction mocks pin how the code works and break on refactors ([Software Engineering at Google, ch. 13](https://abseil.io/resources/swe-book/html/ch13.html)).
7. Learn the real method's side effects before faking it. Keep the ones the test depends on real; fake only the slow or external layer below them.
8. The fake earns no assertions. Assert the component's behavior (state, output). Assert call arguments, counts or order only when they ARE the behavior, and then through a hand-written recording fake that stores the calls, never a spy.
9. Fakes mirror the complete real structure — every documented field — not just the fields the test reads. Partial fakes fail silently.
10. Fake setup larger than the test, or you cannot say why the fake is there → switch to an integration test with real components.
11. Test-only cleanup and helpers live in test utilities, never as methods on production classes.
12. Every port has ONE contract test suite that runs against both the real adapter and the memory fake. A fake is trusted only because that suite passes on both. State assertions are the default.
13. Time and randomness are ports (`Clock`, `Random`) with memory fakes: a clock the test advances by hand, a random source that is seeded or scripted. Fake timers are never needed and are banned.
14. Only the real adapter's own contract test (`*.real.test.ts` on web) may stub platform globals such as `fetch`, storage or DOM APIs; that file is the single allowlisted place. Every other test crosses the port with the memory fake.

## Before finishing

15. Mutation check: for each realistic mutation — wrong constant, wrong branch, missing side effect, empty return, missing validation of empty/zero/unauthorized input — at least one test fails. A mutation nothing catches marks the behavior unprotected or the test tautological.
