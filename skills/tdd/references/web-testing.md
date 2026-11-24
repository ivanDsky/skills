# Web testing ladder (React-first, Svelte 5 section below, stack-adapt on-site)

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
   render, query by role/text, assert behavior with `userEvent`. The network
   is faked at a port by a memory adapter, never by `vi.fn`/`vi.mock`
   (testing-rules 6, lint-enforced); MSW is allowed only inside the real
   fetch adapter's own contract test (`*.real.test.ts`). Seconds, no
   browser, every commit. (Rung 2 ≈ Android's semantic JVM tests.)
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
| API integration | 2 against the memory adapter; MSW only in the real adapter's `*.real.test.ts`; 4 for the real contract | pre-merge |
| Critical user journeys (auth, checkout, settings-save) | 4 | pre-merge |
| Visual accept, feel, motion | 5 (human) | release |

## Svelte 5 / SvelteKit

Same rungs, Svelte tools. Source: https://svelte.dev/docs/svelte/llms.txt (Testing).

- **Rung 0:** `svelte-check` (the project's `check` script); `tsc --noEmit` cannot read `.svelte` files.
- **Rung 1:** eslint with `eslint-plugin-svelte`.
- **Rung 2, no DOM (the default):** state lives in classes in `.svelte.ts` files; test them with plain Vitest. A test file that itself uses runes (`$state`, `$effect.root`) must have `.svelte` in its name (`x.svelte.test.ts`). Effects run after a microtask: call `flushSync()` from `'svelte'`, and wrap effect tests in `$effect.root(() => { ... })` and call the returned cleanup. Fakes for ports go in through the constructor.
- **Rung 2, component:** `@testing-library/svelte` (`render`, `screen`) with `@testing-library/user-event`, in `jsdom`. For two-way bindings, context or snippet props, render a wrapper component made for the test. Low level: `mount`/`unmount` from `'svelte'`; effects only run after `flushSync()`. Think first whether the logic belongs in a class, where it needs no component test.
- **Vitest config:** Vitest runs in Node, so add `resolve: process.env.VITEST ? { conditions: ['browser'] } : undefined` (it makes Vitest load packages' `browser` entry points) and `test.environment: 'jsdom'` (or `// @vitest-environment jsdom` per file) for component tests.
- **UI SDK primitives (own, not the library's):** `mount` and `checkPattern` from `@ui-sdk/core/testing`, in jsdom; see `skill://ui-sdk` `references/testing.md`.
- **Rungs 3-4:** Playwright against the built app (`webServer: { command: 'npm run build && npm run preview', port: 4173 }`), projects for Chromium and WebKit when the UI is touch-first. Touch, sheets, focus and fast pointer sweeps are rung 4, because jsdom has no layout or real pointers.
