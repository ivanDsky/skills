# Structure rules — catalog

Each rule: what it enforces, why, exceptions, test shape, fix. Rule text for
S1/S2 is owned by `design-architecture/references/rules-architecture.md`
(17, 20); this file is only the mechanical form. Test shapes below follow
the Konsist docs (docs.konsist.lemonappdev.com, checked 2026-11-04) and the
starter snippets; the exact calls are compiled against the project's pinned
Konsist version during setup — a shape that does not compile is fixed there,
not worked around. Files named in `structure/allowlist.txt` are excluded;
an allowlist entry that no longer violates fails the suite.

## S0 — no Konsist suppressions (always on)

- Enforces: no `@Suppress("konsist.…")` / `@file:Suppress("konsist.…")` in
  production code. Suppression is a silent bypass of every other rule.
- Shape: `Konsist.scopeFromProduction().files.assertFalse(strict = true) {
  it.hasTextContaining("Suppress(\"konsist.") }` (the `konsist.`-less form
  `@Suppress("<test name>")` also works in Konsist — match your test names
  too).
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
- Fix: one file per type, named for the type; moving code only — no behavior
  change in the same commit.

## S2 — file size cap (rules-architecture 17; asked at setup)

- Enforces: a file stays under N lines (starting default 300, tunable per
  project; code files, excluding generated sources).
- Why: length is a symptom of a second responsibility; rule 17 says split by
  responsibility, so treat this as a tripwire, not a goal.
- Exceptions: generated code; `@Preview` galleries (their own file).
- Shape: `files.assertTrue { it.text.lines().size <= MAX }` with the
  allowlist applied.
- Fix: find the second responsibility and extract it; never trim by
  deleting comments or compressing lines.

## S3 — layer dependencies (rules-architecture 1; on by default)

- Enforces: the dependency rule across package layers (domain depends on
  nothing; data and presentation depend inward).
- Shape (verified against the docs' architecture example):
  `Konsist.scopeFromProduction().assertArchitecture { val domain =
  Layer("Domain", "<root>.domain.."); val data = Layer("Data",
  "<root>.data.."); val ui = Layer("UI", "<root>.ui.."); domain.dependsOnNothing();
  data.dependsOn(domain); ui.dependsOn(domain) }`. By default every file in
  scope must belong to a declared layer — keep `app`/DI wiring in a layer of
  its own, don't widen the scope's rule.
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
