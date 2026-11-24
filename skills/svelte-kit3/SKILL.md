---
name: svelte-kit3
description: Writes SvelteKit 3 and Svelte 5 runes code with the Kit 2 habits removed, using the Screen plus ViewModel plus typed-context structure and the UI SDK as the interaction layer. Use when creating or editing .svelte, .svelte.ts, +page, +layout, +server, vite.config.ts or package.json imports in a SvelteKit 3 project, or fixing a Kit 2 API that no longer exists.
interaction: afk
requires: []
---

> **TL;DR** Kit 3 moved config into `vite.config.ts`, renamed `$lib` to `#lib` and dropped the stores; write runes-only Svelte 5 with one ViewModel class per feature, and let the UI SDK own interaction, never domain state.
> **Related**: skill://svelte-core-bestpractices (runes detail), skill://svelte-code-writer (docs lookup and autofixer CLI), skill://ui-sdk, skill://tdd (its web-testing reference: Svelte 5 section), skill://deploy-cloudflare, skill://web-env

# SvelteKit 3 + Svelte 5

Your memory of SvelteKit is Kit 2. Trust the repo and these steps over it.

## 1. Read the contract

1. Read `AGENTS.md`, `PROFILE.md` and the ADRs they name (project layout, UI SDK boundary). Done when: you can name the directory your file belongs in and its allowed imports.
2. `package.json` shows `@sveltejs/kit` 3.x, `svelte` ≥ 5.57.1, `typescript` 6. A Kit 2 project is out of scope: stop and say so.

## 2. Config and imports

3. Config lives in the `sveltekit({ adapter, compilerOptions, ... })` plugin in `vite.config.ts`; options are top-level, not under `kit`. There is no `svelte.config.js`.
4. Import app code as `#lib/...` with the file extension (`#lib/core/rng.ts`), declared in `package.json` `"imports"`. `$lib` does not exist.
5. `tsconfig.json` extends `$app/tsconfig` and lists `include`/`exclude` itself.
6. Before writing any `$app/*`, `$env/*`, `@sveltejs/kit` or adapter import, check `references/removed-kit2-apis.md`. Never write: `$app/stores`, `$app/environment`, `$service-worker`, `$lib`, `platform.env`, `json()`, `pushState`, `invalidateAll`. Done when: the grep in that file returns nothing for your diff.

## 3. Components and state

7. Runes only: `$state`, `$derived`, `$props`, `onclick={}`, `{#snippet}` and `{@render}`, `{@attach}`. No `$:`, `export let`, `on:`, `<slot>`, `use:`, or stores. Detail lives in skill://svelte-core-bestpractices.
8. `$effect` is the last resort (DOM, analytics). Compute with `$derived`; react to input in the handler or a function binding.
9. Shared state is a class with `$state` fields or an exported object. `export let x = $state()` that is reassigned breaks across modules.
10. Services go through `createContext<T>()` (`[get, set, has]`, Svelte ≥ 5.40), never module-level state: module state leaks between users in SSR.
11. Ids for `for` and `aria-labelledby`: `$props.id()` at the top level of the component.
12. `.svelte.ts` files cannot run in a build script or the Worker. Code that must run there lives in plain `.ts` (shared core and domain rules).

## 4. Features

13. A feature is `<Name>Screen.svelte` plus `<Name>ViewModel.svelte.ts`: the Screen binds and renders, the ViewModel holds `$state`, `$derived` and arrow-function methods, and takes only the port slices it uses. Read `references/screen-viewmodel.md` before writing one. Done when: the ViewModel has a Vitest test with no DOM.
14. Features never import features. Only `+layout.svelte` imports adapters. Routes stay thin.
15. Any UI SDK component, primitive or board input: read `references/ui-sdk-boundary.md` first. The SDK owns interaction (focus, drag, hit-testing); the ViewModel owns state and undo.

## 5. Verify

16. Run `npx @sveltejs/mcp svelte-autofixer <file> --svelte-version <installed version>` on each changed `.svelte` file and fix what it reports.
17. Run the project's check, lint and unit-test scripts from `package.json` (not guessed names). Done when: svelte-check, lint and Vitest all pass; a failure is real, not stale cache, unless a clean reinstall says otherwise (skill://web-env).
18. A prerender or build failure on a `server` module or `$app/env` import: read `references/removed-kit2-apis.md` § Server-only and env.

Verified against https://svelte.dev/docs/kit/llms.txt (Migrating to SvelteKit v3) and https://svelte.dev/docs/svelte/llms.txt. Fresh skill; inspired by the Svelte team's `svelte-core-bestpractices` and the Screen plus ViewModel pattern.
