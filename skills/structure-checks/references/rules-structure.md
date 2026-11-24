# Structure rules — catalog

Each rule: what it enforces, why, exceptions, test shape, fix. Two engines
implement the same rule ids: Kotlin (Konsist tests plus detekt; shapes
below) and web (ESLint plus dependency-cruiser; configs in
[web-engine.md](web-engine.md), whose "Web form" lines below point there).
Rule text is owned elsewhere and only its mechanical form lives here:
S1/S2/S3 by `design-architecture/references/rules-architecture.md` (17, 20,
1, 2, 13, 21), S7 by `design-architecture/references/rules-code-style.md`
(Comments), S8 by `tdd/references/testing-rules.md` (fakes over mocks).
Test shapes below follow the Konsist docs (docs.konsist.lemonappdev.com,
checked 2026-11-04) and the starter snippets; the exact calls are compiled
against the project's pinned Konsist version during setup — a shape that does
not compile is fixed there, not worked around. Files named in
`structure/allowlist.txt` are excluded; an allowlist entry that no longer
violates fails the suite. Defaults: S0–S3, S7 and S8 are on; S4–S6 (Compose
UI) are asked.

## S0 — no suppressions (always on)

- Enforces: no `@Suppress("konsist.…")` / `@file:Suppress("konsist.…")` in
  production code, and none for the detekt rules in the config block at the
  end. Suppression is a silent bypass of every other rule.
- Shape: `Konsist.scopeFromProduction().files.assertFalse(strict = true) {
  it.hasTextContaining("Suppress(\"konsist.") }` (the `konsist.`-less form
  `@Suppress("<test name>")` also works in Konsist — match your test names
  too); add the detekt rule names (`LongMethod`, `CyclomaticComplexMethod`,
  `ForbiddenComment`, `ForbiddenImport`, …) to the same text check.
- Web form: a disable directive needs `-- reason`, a bare or unlimited one
  fails, `@ts-ignore`/`@ts-nocheck` fail, an unused one fails
  (`reportUnusedDisableDirectives`), a structure rule cannot be disabled at
  all, and `eslint-suppressions.json` may not grow.
- Fix: split or move code; if the rule is wrong, change the rule in this
  file with a dated reason, not in the diff.

## S1 — one public top-level type per file (rules-architecture 20)

- Enforces: a file declares at most ONE public/default-visibility top-level
  class, interface, object, or public composable.
- Why: ten classes in one file kills SRP, merge-conflict isolation, and
  parallel agent scopes.
- Exceptions (fixed list; anything else is a rule change): private/internal
  helpers; typealiases; extension functions/properties on the file's own
  type; `@Preview` functions; nested types (a sealed parent with nested
  variants is one type); `const` and top-level `val`s of that type;
  overloads of the file's composable (same name); the `remember<Type>()`
  factory beside its state type (`TagGroupState.kt` holds
  `rememberTagGroupState`). Top-level sealed variants each get their own
  file.
- Shape: files from `scopeFromProduction()` minus the allowlist; count
  `declarations(includeNested = false, includeLocal = false)` that are
  classes/interfaces/objects with public or default visibility; assert
  `<= 1` with `strict = true`.
- Web form: core `max-classes-per-file` with `max: 1`; a `.svelte` file is
  one component by construction. Tested on `.ts` and `.svelte.ts`: it flags
  two exported classes, a default plus a named class, and an exported plus
  a private class.
- Fix: one file per type, named for the type; moving code only — no behavior
  change in the same commit.

## S2 — size and complexity caps (rules-architecture 17; on by default)

- Enforces: the caps below. This table is the only place the numbers live;
  every other file points here. Counted lines are non-blank, non-comment
  lines; comments are banned (S7), so the count tracks logic and blank
  spacing is never punished.

  | Unit | Cap |
  |---|---|
  | code file | 120 |
  | test file | 200 |
  | `.svelte` `<script>` / template / `<style>` block | 80 each |
  | function | 30 |
  | cyclomatic complexity | 10 |
  | cognitive complexity | 15 |
  | nesting depth | 3 |
  | parameters | 4 (Kotlin constructor 5) |
  | classes per file | 1 (S1) |

- Ruling: the user's bar of 2026-11-23. A project may lower a cap and may
  never raise one without a dated user ruling recorded in the project (ADR or
  PROFILE).
- Why: agents edit and review best in windows of about 100 lines. In
  SWE-agent a 100-line viewer scored 18.0% on SWE-bench Lite, 30 lines 14.3%
  and the whole file 12.7% ([Yang et al., NeurIPS 2024](https://arxiv.org/abs/2405.15793));
  models use the middle of long context worse
  ([Liu et al., TACL 2024](https://arxiv.org/abs/2307.03172)). Human evidence
  is weak and confounded by size: Hatton found faults grow about
  logarithmically up to roughly 200 lines and quadratically beyond, a
  U-shaped curve, so tiny files do not win either
  ([Hatton](https://www.leshatton.org/Documents/Ubend_IS697.pdf)). Every
  number is a heuristic anchored to those two, so treat a cap as a tripwire:
  rule 17 says split by responsibility, not by line count.
- Exceptions: generated code (TypeScript carries a `.generated.ts` suffix so
  the exemption is by path, never by comment), `.d.ts`, golden test vectors,
  baked data; Kotlin `@Preview` galleries (their own file).
- Kotlin shape: detekt for everything but file length (config at the end);
  a Konsist test for files: `scopeFromProduction().files.assertTrue { counted(it) <= 120 }`
  and `scopeFromTest()` with 200, where `counted` keeps non-blank lines that
  do not start with `//`, `/*` or `*`, with the allowlist applied. detekt has
  no file-length rule. The blank filter is an addition to the docs' `lines().size`
  and is compiled at setup.
- Web form: `max-lines`, `max-lines-per-function`, `complexity`,
  `sonarjs/cognitive-complexity`, `max-depth`, `max-params`, and
  `svelte/max-lines-per-block` scoped to `**/*.svelte`, all with
  `skipBlankLines` and `skipComments`.
- Fix: find the second responsibility and extract a named module; never trim
  by compressing lines, and never `utils2` or `part2`.

## S3 — layer dependencies (rules-architecture 1, 2, 13, 21; on by default)

- Enforces: the dependency rule across package layers (domain depends on
  nothing; data and presentation depend inward).
- Shape (verified against the docs' architecture example):
  `Konsist.scopeFromProduction().assertArchitecture { val domain =
  Layer("Domain", "<root>.domain.."); val data = Layer("Data",
  "<root>.data.."); val ui = Layer("UI", "<root>.ui.."); domain.dependsOnNothing();
  data.dependsOn(domain); ui.dependsOn(domain) }`. By default every file in
  scope must belong to a declared layer — keep `app`/DI wiring in a layer of
  its own, don't widen the scope's rule.
- Web form: dependency-cruiser is the only gate: one `forbidden` rule per
  boundary with `$1` captures so one rule covers every feature and plugin,
  `tsPreCompilationDeps: true`, a `couldNotResolve` rule, `no-circular`, and
  one composition-root exception for adapter imports. The layer table and the
  config are in web-engine.md. `eslint-plugin-boundaries` is optional editor
  feedback, never a second gate.
- No `@Suppress` here (not supported for architecture assertions): a
  legitimate exception means removing that file from scope in the test, which
  is a protected-file change needing a Ruling.
- Skip when the build system already enforces the boundary with Gradle
  modules.

## S4 — Compose previews (UI opt-in)

- Enforces: every file with a public `@Composable` also has at least one
  `@Preview` function (per `preview-compose`).
- Shape: `files` with a public composable function, `assertTrue { file
  has a function annotated with Preview }` (docs: `functions()
  .withAnnotationOf(Preview::class)`).
- Fix: add previews for each state; never an empty preview.

## S5 — no raw design literals outside theme (UI opt-in)

- Enforces: no `Color(0x…)` and no hard-coded `.sp`/`.dp` design values in
  composables outside the `theme` package; tokens only.
- Shape: text-based `assertFalse { it.hasTextContaining("Color(0x") }` over
  files outside the theme package; spacing literals by agreed pattern per
  project (layout-only `0.dp` and divider `1.dp` excepted by an explicit list).
- Fix: add or reuse a token in the theme.

## S6 — component API (UI opt-in)

- Enforces the mechanical half of `micro-architecture`'s ui-components
  payload (rules 4, 6, 7) on public top-level `@Composable` functions
  (previews excluded):
  - (a) a Unit-returning one has a `modifier: Modifier = Modifier` parameter;
  - (b) none takes a `State<…>`/`MutableState<…>` parameter;
  - (c) only route composables take a `…ViewModel` parameter.
- Route = name ends with a suffix agreed at setup (default `Route`,
  `Screen`). Routes are exempt from (a) and (c); the suffix list lives in the
  test, so changing it is a protected-file change.
- Why: these three are the component-API findings a reviewer can miss and a
  type check can't. Parameter order, slots vs params and the tier stay
  review work.
- Web form: no Konsist twin. The mechanical part of the Svelte rules in
  ui-components is S1 (one component per file), S2 (block caps), S3
  (`ui-leaf`: nothing under `ui` imports ports, adapters or app services) and
  S7; the other Svelte rules stay review work.
- Shape (verified with Konsist 0.17.3 on 2026-11-05: green on a real app,
  red on probes for all three): `Konsist.scopeFromProduction().functions(
  includeNested = false, includeLocal = false).withAnnotationNamed(
  "Composable").withoutAnnotationNamed("Preview").filter { it.isTopLevel &&
  it.hasPublicOrDefaultModifier }`. Then:
  - (a) filter `returnType == null || returnType?.name == "Unit"`, drop
    routes, `assertTrue(strict = true) { f -> f.parameters.any {
    it.name == "modifier" && it.type.name == "Modifier" && it.defaultValue
    == "Modifier" } }`;
  - (b) `assertFalse` on `p.type.name.substringBefore('<') in
    setOf("State", "MutableState")`;
  - (c) drop routes, `assertFalse` on
    `it.type.name.endsWith("ViewModel")`.

  Exempt routes by name, never by "has a ViewModel param": that exemption
  let a probe with both a ViewModel and no `modifier` pass (a).
- Fix: (a) add the parameter and apply it first at the root; (b) take `T`
  or `() -> T` plus an event lambda, or a `@Stable` holder; (c) pass the
  state slice and lambdas from the route.

## S7 — no agent-written comments (rules-code-style Comments; always on)

- Enforces: no comment outside the allowlist in `rules-code-style.md`
  (Comments). The allowlist lives there; the checks below encode it. A
  comment is never how code gets explained: rename, extract or add a type.
- Why: wrong comments hurt agents and agents write wrong comments (evidence
  and links in rules-code-style), and only a negative constraint with a
  failing lint holds where prose guidance does not.
- Kotlin shape: detekt `style>ForbiddenComment` with a catch-all regex that
  admits only `WHY:` and `SPDX-License-Identifier:`, `excludes` on port and
  API paths where KDoc is the allowed contract, `UndocumentedPublicClass` on
  those same paths, and `DocumentationOverPrivateFunction`/`Property`
  (1.23.x names: `CommentOverPrivateFunction`/`Property`). Verified on
  detekt 1.23.8 and 2.0.0-alpha.6; the path globs are a suggested layout
  `[unverified]`. Konsist has no plain-comment API, only `hasKDoc` on
  declarations. Config at the end.
- Web form: the custom `local/no-comments` rule, which covers `<script>`,
  markup `<!-- -->` and `<style>` comments (web-engine.md has the source).
- Fix: delete the comment. A real constraint becomes one line `WHY: <reason>`;
  otherwise make the name or type say it. Never a comment in place of code.

## S8 — no mocking APIs (tdd testing-rules, fakes over mocks; always on)

- Enforces: a test crosses a seam with a hand-written fake, never a mocking
  framework. Only the real adapter's own contract test (`*.real.test.ts`) may
  stub platform globals.
- Why: prefer the real implementation, else a fake that a contract test also
  runs against the real one; interaction tests are change-detector tests
  ([Software Engineering at Google, ch. 13](https://abseil.io/resources/swe-book/html/ch13.html)).
- Kotlin shape: detekt `style>ForbiddenImport` for `io.mockk.*` and
  `org.mockito.*` (documented, not run in the research). Alternatives:
  leave mockk and Mockito out of the version catalog, the cheapest option
  `[unverified]`, or a Konsist test `files.assertFalse { it.hasImport { i ->
  i.name.startsWith("io.mockk") } }` `[unverified]`, not compiled.
- Web form: `no-restricted-imports` on `vi`, `vitest`, `@vitest/spy` and
  `sinon`, `vitest/no-restricted-vi-methods` on `fn`, `spyOn`, `mock`,
  `doMock`, `mocked`, `stubGlobal`, `stubEnv`, `useFakeTimers`, and
  `vitest/no-mocks-import`, off only for `src/lib/adapters/**/*.real.test.ts`
  (verified: 6 errors on a test using the banned calls, none on the
  allowlisted file).
- Fix: write or extend the port's memory fake; time and randomness are ports
  with memory fakes, so fake timers are never needed.

## Kotlin detekt config (S2, S7, S8)

Adopt on an existing project with `./gradlew detektBaseline`; the baseline
only shrinks and is a protected file, like the allowlist.

```yaml
complexity:
  LongMethod: { active: true, allowedLines: 30 }
  NestedBlockDepth: { active: true, allowedDepth: 3 }
  LongParameterList: { active: true, allowedFunctionParameters: 4, allowedConstructorParameters: 5 }
  CyclomaticComplexMethod: { active: true, allowedComplexity: 10 }
  CognitiveComplexMethod: { active: true, allowedComplexity: 15 }
comments:
  DocumentationOverPrivateFunction: { active: true }
  DocumentationOverPrivateProperty: { active: true }
  UndocumentedPublicClass:
    active: true
    includes: ["**/ports/**", "**/api/**"]
style:
  ForbiddenComment:
    active: true
    excludes: ["**/ports/**", "**/api/**"]
    comments:
      - reason: "Only WHY: or SPDX comments are allowed."
        value: '(?s)\A(?!\s*(WHY:|SPDX-License-Identifier:)).+'
  ForbiddenImport:
    active: true
    forbiddenImports:
      - { value: 'io.mockk.*', reason: "Use a hand-written fake behind the port." }
      - { value: 'org.mockito.*', reason: "Use a hand-written fake behind the port." }
```

detekt 1.23.x names the first two comment rules `CommentOverPrivateFunction`
and `CommentOverPrivateProperty`. `CognitiveComplexMethod` is off by default,
so it must be activated as above.
