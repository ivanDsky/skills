# Web testing ladder (React-first, stack-adapt on-site)

Web twin of the Android ladder in this file's sibling sections. Same law:
**the cheapest rung that can see the failure class is the default, and the
evidence is a committed, re-runnable artifact — never a manual browser
session.** Adapt names to the project's actual stack (check
`package.json`: vitest vs jest, Storybook vs Ladle, Playwright vs
Cypress) during `map-codebase`; the rungs don't change.

0. **Compile + types** — `tsc --noEmit` (or the framework's typecheck):
   the SKILL.md of UI code is its typecheck. Zero browser. Every commit.
1. **Static analysis** — eslint with the project's rules (hooks rules,
   a11y rules, exhaustive-deps). Catches what types can't: stale closures,
   missing keys, unreachable states.
2. **Component logic on the host** — vitest/jest + React Testing Library:
   render, query by role/text, assert behavior with `userEvent`. Mock the
   network (MSW preferred — handlers are reusable as dev mocks). Seconds,
   no browser, every commit. (Rung 2 ≈ Android's semantic JVM tests.)
3. **Pixel evidence, no human** — rendered captures of real components:
   Storybook/Ladle stories + a screenshot test runner, or Playwright
   component testing. One capture per state × size × theme variant;
   diffed against committed references in CI. Catches overflow, spacing,
   theme breakage — what semantics miss. (Rung 3 ≈ Roborazzi/`android
   preview render`: this is the review-evidence workhorse. Reviewers cite
   these captures; a finding graded without the applicable capture is
   `cannot-verify`.)
4. **Flows in a real browser, scripted** — Playwright E2E against a
   production-like build served locally: routing, auth redirects,
   persistence, multi-component interactions. Keep hermetic: seeded data,
   no live third parties. A handful per critical user path, not per
   component. (Rung 4 ≈ instrumented tests + Journeys.)
5. **Human acceptance** — deploy (`deliver` targets), the user clicks.
   Manual browser time is the LAST resort and the user's, not the agent's:
   an agent clicking through a browser reproduces the audited Android
   anti-pattern (slow tap-screencap cycles producing discarded evidence).
   Where scripted browser evidence is genuinely insufficient, take the
   capture with Playwright and attach it — same artifact discipline.

## The browser is the emulator of web development

Every principle from the Android side transfers: booting a browser (or a
dev server + manual checking) is the slow loop; the fast tools above answer
almost everything without it. Between edits: typecheck + rung-2 tests.
For visual claims: rung-3 captures, re-run the suite on "still not right",
diff against references — never a fresh manual click-through.

## Coverage mapping (what to test where)

| Layer | Rung(s) | Cadence |
|---|---|---|
| Pure logic (utils, hooks internals, stores) | 2 | every commit |
| Component behavior + a11y roles | 2 + 1 (a11y lint) | every commit |
| Component visuals (states, themes, widths) | 3 | every commit (CI-diffed) |
| API integration | 2 with MSW; 4 for the real contract | pre-merge |
| Critical user journeys (auth, checkout, settings-save) | 4 | pre-merge |
| Visual accept, feel, motion | 5 (human) | release |
