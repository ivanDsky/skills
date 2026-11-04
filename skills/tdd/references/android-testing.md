<!-- Android grounding for the tdd skill. Sources: developer.android.com testing fundamentals (URLs at bottom). Re-verify if Google revises the pages. -->

# Android testing — grounded in developer.android.com fundamentals

The most important distinction on Android is **where a test runs**: **instrumented** tests run on a device or emulator (in `androidTest/`), **local** tests run on the host JVM (in `test/`).

## Test doubles — Android's definitions

| Double | Android's definition | Android's guidance |
|---|---|---|
| **Fake** | Working implementation that is good for tests but unsuitable for production (e.g., an in-memory database). | Needs no mocking framework, lightweight. **Preferred.** |
| **Stub** | Programmed behavior, no interaction expectations; usually from a mocking framework. | Fakes preferred over stubs for simplicity. |
| **Mock** | Programmed behavior **plus interaction expectations**; fails the test if interactions don't match what you defined (e.g., verify a method was called exactly once). | The tool for interaction contracts. |
| **Dummy** | Passed around but never used (e.g., an empty function passed as a click callback). | Fine as a parameter filler. |
| **Spy** | Wrapper over a real object that also tracks extra information. | Usually avoided — adds complexity; fakes or mocks preferred. |
| **Shadow** | A fake used in Robolectric. | Robolectric's substitute for framework internals. |

Android adds: doubles live in the test source set and never ship; make big tests **hermetic** (no network or other external dependencies); use dependency injection — Google recommends Hilt — to swap doubles in instrumented and end-to-end tests, not just unit tests.

**Reconciliation with [testing-rules](testing-rules.md):** no contradiction. Android prefers fakes for the same reason rule 6 does, and Android's mock example (verify called exactly once) is exactly rule 8's case — assert call counts only when they are the contract. The one addition Android makes explicit: inject fakes through Hilt into instrumented UI tests too, so hermetic E2E stays possible.

## Test strategies — the pyramid

- Small tests are fast and reliable; big tests have more fidelity but need complex, hard-to-maintain setups. Most apps should have **many small tests and relatively few big tests** — a pyramid.
- Bug-cost argument from the docs: a bug caught by a unit test is fixed in minutes; the same bug found by an end-to-end test can take days and pull in multiple people. A bug that reaches production has the longest, most expensive feedback loop — but an inefficient strategy is still better than none.
- The traditional split is **unit / integration / end-to-end**. The docs refine it into 5 layers defined by scope, network access, execution, build type, and trigger:

| Layer | Scope | Execution | Trigger |
|---|---|---|---|
| Unit | Single method/class, minimal deps, no Android framework | Local | Every commit |
| Component | One module/component — UI behavior, Compose Preview screenshot tests | Local, Robolectric, emulator | Every commit |
| Feature | Two+ components; network mocked | Local, Robolectric, emulator, devices | Pre-merge |
| Application | Whole app in a debuggable build — localization, foldable config changes | Emulator, devices | Post-merge |
| Release candidate | Minified release build — critical user journeys, performance | Emulator, many devices | Pre-release |

- **Docs' rule of thumb: choose the lowest layer that gives the team the right level of feedback.** Test category doesn't dictate test type, and no feature needs every layer.
- Delta note: this page prescribes the pyramid shape and the cadence table above; it gives **no numeric ratio** (there is no "70/20/10" in the current doc) — don't quote one.

## Decision rule: JVM unit vs Robolectric vs instrumented

1. No Android framework dependency (ViewModel state, repository, use case, validator, formatter) → local JVM unit test in `test/` with a fake. The docs' essential-unit-test list: ViewModels/presenters, data layer (especially repositories), domain layer, utility classes.
2. Needs real framework/device behavior — the docs' example is verifying SQLite integration across API levels → **small instrumented test** in `androidTest/`. Not all unit tests are local, not all E2E tests are instrumented.
3. Framework-dependent but you want JVM speed → **Robolectric**, the docs' "big local test" example; its shadows are its fakes for the framework. The docs run component-layer UI behavior tests on Robolectric.
4. Compose UI **appearance** → component screenshot test; the docs name Compose Preview screenshot tests as component tests.
5. Compose UI **behavior on one screen** → instrumented UI test with the compose test APIs, as in the hub's example: `composeTestRule.onNodeWithText("Continue").performClick()` then `.assertIsDisplayed()`. One test class per screen is the docs' starting point.
6. Multi-screen flows and navigation → feature/application layer on Robolectric or emulator, kept hermetic with fakes and Hilt.
7. Critical user journeys → release-candidate E2E on device against a staging server (the docs' example: "End-to-end Compose UI behavior test running on device").

## What to test in a Compose app — the docs' categories mapped

- **Unit** (JVM, `test/`): ViewModel/reducer logic, repositories, domain use cases, validators, formatters. Edge cases belong here: negative/zero/boundary math, every network error state, malformed JSON, full storage, state restoration after process recreation.
- **Integration**: repository ↔ Room against the real framework → small instrumented test; UI ↔ auth manager → the docs' example table maps "integration with the auth manager" to a **JVM test with fakes** at the feature layer.
- **E2E** (instrumented, `androidTest/`): screen UI tests for critical user interactions, and user-flow/navigation tests covering the most common paths — the docs flag navigation tests as catching run-time crashes in initialization. Screenshot, performance, and monkey tests are the specialized extras.
- Don't unit-test activities/fragments/services: the docs say those tests have little value because they cover mostly framework code. Keep business logic out of framework entry points (move it to ViewModel/Composable/domain) and cover the entry points with instrumented UI tests instead.

## Sources

- https://developer.android.com/training/testing/fundamentals/test-doubles
- https://developer.android.com/training/testing/fundamentals/strategies
- https://developer.android.com/training/testing/fundamentals/what-to-test
- https://developer.android.com/training/testing/fundamentals


## UI verification ladder (device last)

The emulator is the LAST rung, not the default. Each rung applies only when
the cheaper one cannot see the failure class. (Sources: robolectric.org;
Roborazzi README - Robolectric Native Graphics 4.10+; developer.android.com
studio/test/gradle-managed-devices; AGP Compose preview screenshot testing.)

1. **Compile + previews** — SKILL.md of UI code is its compile; previews must
   render (preview-compose skill). Catches broken composition. Zero devices.
2. **Semantic JVM tests** — Compose UI tests on the JVM (`createComposeRule`
   + Robolectric, `@GraphicsMode(NATIVE)`): assert the semantic tree - text,
   contentDescription, enabled states, and UI state-machine transitions.
   Seconds, no device, runs on every commit.
3. **JVM screenshot tests** — pixel truth without any device: Roborazzi
   (Robolectric RNG) or AGP Compose Preview Screenshot Test suites (Layoutlib),
   or `android preview render` (Android CLI — renders @Previews to PNG, no
   device, no IDE, no Gradle test setup; ideal when the project lacks a
   Roborazzi suite).
   One capture per state/size/dark variant; diff in CI. Catches what semantics
   miss: overflow, spacing, alignment, theme breakage.
4. **Instrumented UI tests on a Gradle Managed Device** — headless ATD images
   (API 27+), configured in Gradle for reproducibility. Only for what the JVM
   cannot see: real input pipeline, window insets/focus, density, text shaping.
   Complement: Journeys (`android` CLI) — natural-language user-path checks on
   a device; acceptance-layer, one per critical path, never per-commit.
5. **Human acceptance on the real target** — install the APK
   (`deploy-tailscale` / `deploy-firebase`), feel the animations, judge
   premium. The emulator lives HERE - as one optional device, never the
   default evidence.

Review rule: screenshots as evidence mean JVM screenshots (rung 3) by
default; device/emulator screenshots appear only at acceptance (rung 5).

Persistence rule: rung-3 captures are committed artifacts, not disposable
output. When a user reports "still not right" — colors, spacing, state
rendering — the response is `runner` (re-run the screenshot suite) and a diff
against the reference images, never an emulator boot. Record colors and theme
values as assertions or capture variants (light/dark/font-scale), so any
visual claim from a previous round is re-verifiable in seconds by any later
run without a device.

## Tap flow → persisted JVM test (instead of guessing coordinates)

A flow you would otherwise verify by tapping through a device ("open the
sheet, pick an item, see the total") is written as a rung-2 test, once, and
re-run by command:

1. Locate the targets semantically, not by position: text, `contentDescription`,
   or a `testTag` added to the composable. Need the real tree? `android layout
   --output hierarchy.json` (Android CLI) shows the semantics a test can see.
2. `createComposeRule` + Robolectric (`@GraphicsMode(NATIVE)`): set content with
   fake state, then `onNodeWithText("Continue").performClick()` and assert the
   next state with `assertIsDisplayed()` / `assertTextEquals(...)`.
3. Commit the test; its Gradle task is the ticket's Evidence (exit code), and
   "still broken" next round means re-running it, not opening a device.
4. Only what semantics cannot see (insets, real input pipeline, text shaping)
   climbs to rung 4, and then as an aggregate acceptance ticket.
