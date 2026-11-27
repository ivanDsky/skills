# Web engine — ESLint + dependency-cruiser

The web form of the rule set in [rules-structure.md](rules-structure.md), for
a SvelteKit / Svelte 5 / strict TypeScript project. ESLint carries S0, S1,
S2, S7 and S8; dependency-cruiser carries S3. Both run from one lint script,
and that script is the PROFILE `structure:` command.

Provenance: every tool was installed and run in scratch labs on 2026-11-23
(ESLint 10.15, eslint-plugin-svelte 3.24, svelte-eslint-parser 1.12,
typescript-eslint 8.74, eslint-plugin-sonarjs 4.2, eslint-comments 4.8,
@vitest/eslint-plugin 1.6, Vitest 5.1, dependency-cruiser 18.9, Vite 8.3).
Each rule family was run on its own; the combined files below were not run as
one, so the setup's prove-it-fails step is the first proof. Anything that was
not run says `[unverified]`.

## Install and pin

- `eslint@10`, `typescript-eslint@^8.74`, `eslint-plugin-svelte@^3.24`,
  `eslint-plugin-sonarjs@^4.2`, `@eslint-community/eslint-plugin-eslint-comments`,
  `@vitest/eslint-plugin`, `dependency-cruiser@^18.9`, all as dev dependencies.
- **Pin TypeScript to 6** (`"typescript": "~6"`) or the first 7.x every tool
  supports. typescript-eslint 8.74 refuses TypeScript 7.0
  ([tracking issue](https://github.com/typescript-eslint/typescript-eslint/issues/10940)),
  and dependency-cruiser 18.9 supports only `>=2 <7` or `>=7.1 <8`: on 7.0 it
  prints `missing-tsc-transpiler` and **silently skips every TS source**, so a
  green run proves nothing. After any TypeScript bump, run the lint script and
  grep its output for `missing-tsc-transpiler`.
- Script (the `structure:` command): `"lint": "eslint . && depcruise src --config .dependency-cruiser.mjs"`.
  dependency-cruiser took 1.4 s on a 1,649-file tree with no cache.

## Rule map

| Rule | Tool | Config |
|---|---|---|
| S0 suppressions | `@eslint-community/eslint-comments` (`require-description`, `no-unlimited-disable`, `no-restricted-disable`), `reportUnusedDisableDirectives: "error"`, `ban-ts-comment`, the growth check below | `eslint.config.js` |
| S1 one class per file | core `max-classes-per-file`, max 1 | `eslint.config.js` |
| S2 size and complexity | `max-lines`, `max-lines-per-function`, `complexity`, `sonarjs/cognitive-complexity`, `max-depth`, `max-params`, `svelte/max-lines-per-block` | `eslint.config.js` |
| S3 layers | dependency-cruiser: one rule per boundary, `$1` captures | `.dependency-cruiser.mjs` |
| S7 no comments | custom `local/no-comments` rule | `tools/eslint/no-comments.js` |
| S8 no mocking APIs | `no-restricted-imports`, `vitest/no-restricted-vi-methods`, `vitest/no-mocks-import` | `eslint.config.js` |

Caps in `CAPS` mirror the S2 table in rules-structure.md; the table is the
source, so raising one is a dated user ruling, never an edit here.

## `eslint.config.js`

```js
import svelte from "eslint-plugin-svelte";
import ts from "typescript-eslint";
import vitest from "@vitest/eslint-plugin";
import sonarjs from "eslint-plugin-sonarjs";
import comments from "@eslint-community/eslint-plugin-eslint-comments";
import { defineConfig } from "eslint/config";
import { noComments } from "./tools/eslint/no-comments.js";

const CAPS = { codeFile: 120, testFile: 200, block: 80, fn: 30, complexity: 10, cognitive: 15, depth: 3, params: 4 };
const counted = { skipBlankLines: true, skipComments: true };
const MOCK = "No mocks or spies. Use a memory-* fake; wrap third parties in a port.";
const TEST_FILES = ["**/*.{test,spec}.ts", "tests/**/*.ts"];
const GUARDED = [
  "max-classes-per-file", "max-lines", "max-lines-per-function", "max-depth", "max-params",
  "complexity", "sonarjs/*", "svelte/max-lines-per-block", "local/*",
  "no-restricted-imports", "vitest/*", "@typescript-eslint/*",
];

export default defineConfig(
  ts.configs.base,
  svelte.configs.base,
  { files: ["**/*.svelte"], languageOptions: { parserOptions: { parser: ts.parser } } },
  {
    files: ["src/**/*.{ts,svelte}", "tests/**/*.ts"],
    linterOptions: { reportUnusedDisableDirectives: "error" },
    plugins: { local: { rules: { "no-comments": noComments } }, sonarjs, comments, "@typescript-eslint": ts.plugin },
    rules: {
      "local/no-comments": "error",
      "comments/require-description": "error",
      "comments/no-unlimited-disable": "error",
      "comments/no-restricted-disable": ["error", ...GUARDED],
      "@typescript-eslint/ban-ts-comment": ["error", {
        "ts-expect-error": "allow-with-description", "ts-ignore": true, "ts-nocheck": true, minimumDescriptionLength: 10 }],
      "max-lines-per-function": ["error", { max: CAPS.fn, ...counted }],
      complexity: ["error", CAPS.complexity],
      "sonarjs/cognitive-complexity": ["error", CAPS.cognitive],
      "max-depth": ["error", CAPS.depth],
      "max-params": ["error", CAPS.params],
      "max-classes-per-file": ["error", { max: 1, ignoreExpressions: true }],
    },
  },
  { files: ["src/**/*.ts"], rules: { "max-lines": ["error", { max: CAPS.codeFile, ...counted }] } },
  { files: ["src/**/*.{test,spec}.ts", "tests/**/*.ts"], rules: { "max-lines": ["error", { max: CAPS.testFile, ...counted }] } },
  { files: ["src/**/*.svelte"], rules: {
    "svelte/max-lines-per-block": ["error", { script: CAPS.block, template: CAPS.block, style: CAPS.block, ...counted }] } },
  { files: ["src/lib/ports/**/*.ts", "src/lib/core/**/contract.ts"],
    rules: { "local/no-comments": ["error", { allowTsdoc: true }] } },
  { files: ["src/lib/core/**/*.ts", "src/lib/ports/**/*.ts", "src/lib/plugins/*/rules/**/*.ts"],
    rules: { "no-restricted-globals": ["error", "window", "document", "navigator", "localStorage", "sessionStorage", "location"] } },
  { files: TEST_FILES, plugins: { vitest }, rules: {
    "no-restricted-imports": ["error", { paths: [
      { name: "vitest", importNames: ["vi", "vitest"], message: MOCK },
      { name: "@vitest/spy", message: MOCK },
      { name: "sinon", message: MOCK },
    ] }],
    "vitest/no-restricted-vi-methods": ["error", {
      fn: MOCK, spyOn: MOCK, mock: MOCK, doMock: MOCK, mocked: MOCK, stubGlobal: MOCK, stubEnv: MOCK,
      useFakeTimers: "Inject a Clock port; use a memory clock.",
    }],
    "vitest/no-mocks-import": "error" } },
  { files: ["src/lib/adapters/**/*.real.test.ts"],
    rules: { "no-restricted-imports": "off", "vitest/no-restricted-vi-methods": "off" } },
  { files: ["**/*.generated.ts", "**/*.d.ts", "tests/**/golden/**"],
    rules: { "max-lines": "off", "max-lines-per-function": "off", "local/no-comments": "off" } },
);
```

What each block relies on, and where the research stopped:

- **S2 counting.** `skipBlankLines` and `skipComments` on every cap. Core
  `max-lines` counts a whole `.svelte` file including `<style>`, so `.svelte`
  files get only `svelte/max-lines-per-block` (it also ran on `.ts` files when
  included, hence the `src/**/*.svelte` scope). `max-lines-per-function`,
  `max-params` and `max-depth` fire on functions in `<script>`.
- **S0.** `require-description` accepts `-- reason` and flags a bare directive;
  `no-unlimited-disable` flags a bare `/* eslint-disable */`;
  `ban-ts-comment` rejects `@ts-ignore`, `@ts-nocheck` and an undescribed
  `@ts-expect-error`. All verified. `no-restricted-disable` was verified with
  `@typescript-eslint/*`; `GUARDED` extends the same option to the S1, S2, S7
  and S8 rules so a structure rule cannot be disabled even with a reason
  `[unverified]`. A disable directive for any other rule needs `-- reason`.
- **S8.** The import ban is the hard gate; the method rule gives each ban a
  message agents read. Gaps: `import()` in dynamic form is not covered, and a
  namespace `vt.vi.fn()` slips the method rule but the `import * as vt` is
  caught by the import ban. Keep Vitest `globals` off (its default), or the
  `vi` global bypasses the import ban. Only the real adapter's own
  `*.real.test.ts` may stub platform globals.
- **Exempt by path, never by comment:** generated TypeScript must carry the
  `.generated.ts` suffix; golden vectors live under `tests/**/golden/**`;
  baked data files that ESLint does not lint (JSON) need no entry. A TSDoc
  exception covers only ports and the file declaring the plugin contract (the
  second `src/lib/core/**/contract.ts` glob is a placeholder to adjust).
- **DOM globals** in pure layers: dependency-cruiser cannot see them, so the
  `no-restricted-globals` block above (list `[unverified]`) or a tsconfig for
  those folders without the `DOM` lib; the tsconfig makes `tsc` fail on use.

## `tools/eslint/no-comments.js` (S7)

Allowed comments are exactly the allowlist in `design-architecture`'s
rules-code-style.md; this is its mechanical form. It handles `<script>`
comments, markup `<!-- -->` comments and `<style>` comments. Verified end to
end on all three. In `.svelte` files `getAllComments()` returns only the
`<script>` comments, which is why the two Svelte visitors exist. A
directive in markup or `<style>` passes the allowlist without a reason check
`[unverified]`: write disables inside `<script>`.

```js
const ALLOWED =
  /^\s*(?:@ts-expect-error\s+\S|eslint-(?:disable|enable)\b|@license\b|@vitest-environment\b|SPDX-License-Identifier:|WHY:\s*\S|#(?:end)?region\b)/;
const CSS_COMMENT = /\/\*([\s\S]*?)\*\//g;

export const noComments = {
  meta: {
    type: "suggestion",
    schema: [{ type: "object", properties: { allowTsdoc: { type: "boolean" } }, additionalProperties: false }],
    messages: { banned: "Comment not allowed. Rename, extract or add a type. Allowed: 'WHY: <reason>', '@ts-expect-error <reason>', eslint-disable with '-- reason', SPDX." },
  },
  create(context) {
    const sc = context.sourceCode;
    const allowTsdoc = context.options[0]?.allowTsdoc === true;
    const isAllowed = (c) => ALLOWED.test(c.value) || (allowTsdoc && c.type === "Block" && c.value.startsWith("*"));
    const report = (loc) => context.report({ loc, messageId: "banned" });
    return {
      Program() {
        for (const c of sc.getAllComments()) if (c.type !== "Shebang" && !isAllowed(c)) report(c.loc);
      },
      SvelteHTMLComment(node) { if (!ALLOWED.test(node.value)) report(node.loc); },
      SvelteStyleElement(node) {
        for (const text of node.children) {
          for (const m of text.value.matchAll(CSS_COMMENT)) {
            if (ALLOWED.test(m[1])) continue;
            const from = text.range[0] + m.index;
            report({ start: sc.getLocFromIndex(from), end: sc.getLocFromIndex(from + m[0].length) });
          }
        }
      },
    };
  },
};
```

## `.dependency-cruiser.mjs` (S3)

Layer policy for the generic `src/lib` layout. `<x>` is one feature or one
plugin (a game, a tool, a provider: a self-contained unit).

| Layer | May import | Rule |
|---|---|---|
| `core` | `core` only; no npm | `core-pure` |
| `ports` | `ports`, `core`; no npm | `ports-pure` |
| `plugins/<x>/rules` | `core`, its own `rules`; no npm | `plugin-rules-pure` |
| `plugins/<x>` | `core`, `ui`, itself, npm; never another plugin | `plugin-inward`, `no-plugin-to-plugin` |
| `adapters` | `ports`, `core`, `adapters`, npm; never `features`, `ui`, `app`, `plugins`, routes | `adapters-no-upward` |
| `app` | `ports`, `core`, `app`, npm | `app-inward` |
| `ui` | `ui`, `core`, npm | `ui-leaf` |
| `features/<x>` | `ports`, `core`, `app`, `ui`, `plugins`, itself; never another feature, never adapters | `no-feature-to-feature`, `adapters-only-from-composition-root` |
| `src/routes` | anything except adapters | `adapters-only-from-composition-root` |
| composition root `src/routes/+layout.svelte` | the one file that may import adapters | exception inside the same rule |

```js
const L = '^src/lib';
const NPM = 'node_modules/';
const forbid = (name, from, to) => ({ name, severity: 'error', from, to });

export default {
  forbidden: [
    forbid('no-feature-to-feature', { path: `${L}/features/([^/]+)/` },
      { path: `${L}/features/([^/]+)/`, pathNot: `${L}/features/$1/` }),
    forbid('no-plugin-to-plugin', { path: `${L}/plugins/([^/]+)/` },
      { path: `${L}/plugins/([^/]+)/`, pathNot: `${L}/plugins/$1/` }),
    forbid('adapters-only-from-composition-root',
      { pathNot: ['^src/routes/\\+layout\\.svelte$', `${L}/adapters/`] }, { path: `${L}/adapters/` }),
    forbid('adapters-no-upward', { path: `${L}/adapters/` },
      { path: [`${L}/(features|ui|app|plugins)/`, '^src/routes/'] }),
    forbid('ports-pure', { path: `${L}/ports/` }, { pathNot: `${L}/(ports|core)/` }),
    forbid('core-pure', { path: `${L}/core/` }, { pathNot: `${L}/core/` }),
    forbid('plugin-rules-pure', { path: `${L}/plugins/([^/]+)/rules/` },
      { pathNot: [`${L}/core/`, `${L}/plugins/$1/rules/`] }),
    forbid('plugin-inward', { path: `${L}/plugins/([^/]+)/` },
      { pathNot: [`${L}/(core|ui)/`, `${L}/plugins/$1/`, NPM] }),
    forbid('app-inward', { path: `${L}/app/` }, { pathNot: [`${L}/(ports|core|app)/`, NPM] }),
    forbid('ui-leaf', { path: `${L}/ui/` }, { pathNot: [`${L}/(ui|core)/`, NPM] }),
    forbid('not-to-unresolvable', {}, { couldNotResolve: true }),
    { name: 'no-circular', severity: 'error', from: {}, to: { circular: true } },
  ],
  options: {
    tsConfig: { fileName: 'tsconfig.json' },
    tsPreCompilationDeps: true,
    doNotFollow: { path: 'node_modules' },
    exclude: { path: ['\\.(test|spec)\\.ts$', '^svelte/internal/'] },
  },
};
```

- **Verified** (17 of 17 planted violations caught: feature to feature by
  alias, relative path and from a `.svelte` file; feature to adapter by static
  import, dynamic import and re-export; route to adapter; core to `svelte`;
  rules to ports, ui and adapters; plugin to plugin; ports to adapter; a
  type-only import; an unresolvable `#lib` import): `no-feature-to-feature`,
  `no-plugin-to-plugin`, `adapters-only-from-composition-root`,
  `adapters-no-upward`, `ports-pure`, `core-pure`, `not-to-unresolvable`,
  `no-circular`, and the lab form of `ui-leaf` and `plugin-rules-pure`.
  Written after that run, not re-run `[unverified]`: the `$1` form of
  `plugin-rules-pure`, `plugin-inward`, `app-inward`, and the `NPM` allowance
  in `ui-leaf` (the lab form had none, so it flagged every npm import from
  `ui`). The prove-it-fails probes cover them.
- **Captures.** One rule covers every feature and every plugin, so adding
  `features/<new>` needs no config edit. Native `$1` in `pathNot`.
- **Required options.** `tsPreCompilationDeps: true` is what makes type-only
  imports visible. The `couldNotResolve` rule makes an unresolvable import
  fail loudly instead of vanishing. `exclude: ^svelte/internal/` removes
  phantom edges from compiled `.svelte` output. **Never** `includeOnly:
  '^src/'`: it hides npm edges such as `core` to `svelte`.
- **Resolution.** `.svelte` files are read (since dependency-cruiser 16.6.0)
  and `#lib/*` subpath imports resolve through enhanced-resolve. SvelteKit
  virtual modules (`$app/*`, `$env/*`, `$service-worker`) have no file: if the
  first run reports exactly those as unresolvable, exempt exactly those with
  `pathNot` on `not-to-unresolvable`, never `#lib/*` or relative paths
  `[unverified]`.
- **Test files are not cruised** (`exclude`), so layer rules do not gate what
  a test imports.
- **Glob registries** (micro-architecture § 2 auto-discovery): the tool sees
  no edge from the registry module to the plugin files, which have zero
  dependents; the layer rules still apply to the plugin files themselves. Do
  not add a `no-orphans` rule over plugin folders.

## Ratchet and growth check

Greenfield: zero suppressions, so `eslint-suppressions.json` does not exist.
An existing project adopts one new rule by running
`eslint --fix --suppress-all` once for that rule (bulk suppressions apply only
to rules at `"error"`, [docs](https://eslint.org/docs/latest/use/suppressions)),
never to excuse new code. CI fails when the file gains entries relative to
`main`. This check is our proposal, not an ESLint feature; the script was run
on a scratch repo:

```sh
count() { jq '[.[][].count] | add // 0'; }
base=$(git show origin/main:eslint-suppressions.json 2>/dev/null | count); base=${base:-0}
now=$([ -f eslint-suppressions.json ] && count < eslint-suppressions.json || echo 0)
[ "$now" -le "$base" ] || { echo "eslint-suppressions.json grew: $base -> $now"; exit 1; }
```

### e2e budget

Browser end-to-end specs are the slowest tests a web project has, and one
spec per ticket grows main's CI without bound. The budget: one spec per user
journey, each listed as a line `- <journey> — tests/e2e/<file>.spec.ts` in
`tests/e2e/JOURNEYS.md` (`tdd` § What to test). `tools/e2e-budget.sh`, run
from the `structure:` lint script, compares HEAD with `origin/main` and fails
when the spec files not named in `JOURNEYS.md` grow (shrink-only: existing
unlisted specs are the ratchet's old code), or when the `test()` calls under
`tests/e2e/` grow without a new journey line. `test.describe` and hooks do
not count; `test.only/skip/fixme/fail` do. Run on a scratch repo through
six cases (no change, an added test, a new unlisted spec, a new journey with
its spec, a deleted spec, an added `test.only`), each with the expected
verdict:

```sh
#!/bin/sh
set -eu
ref=${1:-origin/main} dir=tests/e2e
j=$dir/JOURNEYS.md
specs() { git ls-tree -r --name-only "$1" -- "$dir" | grep -E '\.spec\.ts$' || true; }
unlisted() { specs "$1" | while read -r f; do git show "$1:$j" 2>/dev/null | grep -qF "$f" || echo "$f"; done | wc -l | tr -d ' '; }
tests() { specs "$1" | while read -r f; do git show "$1:$f" | grep -cE '\btest(\.(only|skip|fixme|fail))?\(' || true; done | awk '{s+=$1} END {print s+0}'; }
journeys() { git show "$1:$j" 2>/dev/null | grep -c '^- ' || true; }
u0=$(unlisted "$ref") u1=$(unlisted HEAD) t0=$(tests "$ref") t1=$(tests HEAD) j0=$(journeys "$ref") j1=$(journeys HEAD)
[ "$u1" -le "$u0" ] || { echo "e2e budget: spec files outside $j grew: $u0 -> $u1"; exit 1; }
[ "$t1" -le "$t0" ] || [ "$j1" -gt "$j0" ] || { echo "e2e budget: test() calls grew $t0 -> $t1 with no new journey line in $j"; exit 1; }
echo "e2e budget: $t1 tests, $j1 journeys, $u1 unlisted specs"
```

It reads committed trees only: commit before running it. A new journey line
is legitimate only when the ticket names that journey (`write-tickets` UI
ticket Evidence); review grades a journey line no ticket asked for as
Important. Adopting it in a project whose specs predate `JOURNEYS.md`: list
the specs that really are journeys, leave the rest unlisted, and the count
only falls from there.

## Protected files

`eslint.config.*`, `tools/eslint/**`, `.dependency-cruiser.*`, `tools/e2e-budget.sh`,
`eslint-suppressions.json`, and the CI growth check. A worker never edits
them; a change needs a ledgered `Ruling:`.

## Prove-it-fails probes

Setup adds each probe, runs the `structure:` command, sees it red with the
probe's file named, and deletes the probe:

1. A file with two exported classes (S1).
2. A narrating `// increment` comment in a `.ts` file, a `<!-- -->` comment in
   a template and a `/* */` comment in a `<style>` block (S7).
3. A bare `// eslint-disable-next-line` with no reason (S0).
4. A test using `vi.fn()` (S8).
5. A file in `core` importing `svelte`, and a feature importing a sibling
   feature (S3).
6. A function with 31 counted lines (S2).

Then confirm the dependency-cruiser output contains no `missing-tsc-transpiler`.

## Known gaps

- Template nesting is not measured: `{#if}` chains in markup go unchecked, so
  extract components to keep templates shallow.
- Classes inside `<script module>` were not tested against
  `max-classes-per-file` `[unverified]`.
- `svelte/comment-directive` adds `eslint-disable` support in templates; its
  suppression effect was not tested `[unverified]`.
- The `eslint-plugin-no-comments` package exists but was not vetted
  `[unverified]`; the custom rule above replaces it.

## Optional editor feedback

`eslint-plugin-boundaries` 7.4 gives layer feedback in the editor and is never
a second gate: two copies of one policy drift. If used: `boundaries/dependencies`
with `default: 'disallow'`, `checkUnknownLocals: true`, and
`settings['import/resolver'] = { typescript: { alwaysTryTypes: true, project: './tsconfig.json' } }`.
Without the TypeScript resolver every `#lib` import is silently skipped
(only 2 of the lab's violations were caught). Declare elements with
`partialMatch: false` and `capture`; mark `src/routes/+layout.svelte` with
`boundaries/files` `category: 'composition-root'`. Policies are last-match-wins.
Sources: [boundaries docs](https://www.jsboundaries.dev/docs/rules/dependencies),
[TypeScript support](https://www.jsboundaries.dev/docs/guides/typescript-support).

Sources: [dependency-cruiser options](https://github.com/sverweij/dependency-cruiser/blob/main/doc/options-reference.md),
[.svelte support issue](https://github.com/sverweij/dependency-cruiser/issues/962),
[`max-classes-per-file`](https://eslint.org/docs/latest/rules/max-classes-per-file),
[`svelte/max-lines-per-block`](https://sveltejs.github.io/eslint-plugin-svelte/rules/max-lines-per-block),
[`no-restricted-imports`](https://eslint.org/docs/latest/rules/no-restricted-imports),
[`vitest/no-restricted-vi-methods`](https://github.com/vitest-dev/eslint-plugin-vitest/blob/main/docs/rules/no-restricted-vi-methods.md).
