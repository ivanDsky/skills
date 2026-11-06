---
name: preview-compose
description: >-
  Write, fix, and verify Jetpack Compose @Preview code — stateless composables
  with hoisted state, per-state preview variants, multipreview annotations,
  PreviewParameterProvider, Animation Preview playback, and preview screenshot
  tests. Use when writing or reviewing Compose previews in an Android project,
  when a preview pane fails to render or shows an error, when adding
  light/dark, device, or font-scale preview variants, when checking that an
  animation plays correctly from a preview, or when setting up Compose preview
  screenshot testing.
interaction: afk
requires: []
---

> **TL;DR** Writes, fixes, and verifies Jetpack Compose @Preview code — stateless composables, variants, multipreview, screenshot tests; fires on any Compose preview work.
> **Related**: skill://wire-dev-settings (Android debug screens), skill://tdd (screenshot tests), skill://micro-architecture (reusable component API — its ui-components payload)

# Preview compose

Write Compose previews that compile, cover every meaningful UI state, and are
verified with Animation Preview and screenshot tests. Every rule is grounded
in the official tooling docs (see `references/sources.md`).

## Decision rules

1. **Preview the stateless composable.** Split any screen that takes a
   `ViewModel` (or Hilt-injected deps) into a stateless overload taking plain
   data + event lambdas; the ViewModel wrapper calls it; preview the overload.
   The preview renderer (Layoutlib) cannot construct repositories, use cases,
   or DI graphs and renders an error instead. Reusable components (not
   screens) create their runtime objects (`LazyListState`, `FocusRequester`,
   an `XxxState` holder) as remembered parameter defaults and take initial
   state from parameters, not a `LaunchedEffect`, so sample data alone
   renders frame one (`micro-architecture`/references/ui-components.md rules
   6 and 10). Done when: the previewed function has no `ViewModel` parameter
   and renders.
2. **One preview per meaningful state** (loading, empty, error, content,
   extremes). Use `@PreviewParameter(Provider::class)` with a
   `PreviewParameterProvider<T>` whose `values` sequence yields one state per
   element; cap variants with `limit`; override `getDisplayName()` so panels
   read "Elise - 30" instead of "user 0"; back the sequence with a `List` for
   fast indexed access. Done when: every renderable state has a named preview.
3. **Name and configure each preview.** `name` + `group` for organization;
   `showBackground = true` plus `backgroundColor` (ARGB `Long`, e.g.
   `0xFF00FF00`); `uiMode = UI_MODE_NIGHT_YES` for dark; `device = "id:pixel_4"`
   or `spec:width=…,height=…,dpi=…`; `fontScale`, `locale`,
   `widthDp`/`heightDp`. Wrap preview content in the app theme
   (`MyApplicationTheme { ... }`). Done when: a stranger can tell panels apart.
4. **Scale variants with multipreview annotations** — `@PreviewScreenSizes`,
   `@PreviewFontScales`, `@PreviewLightDark`, `@PreviewDynamicColors`
   (ui-tooling-preview 1.6.0-alpha01+). Custom annotation classes stack
   `@Preview`s; combined annotations render independently, never as a
   cross-product. Done when: systematic variants exist without boilerplate.
5. **Keep composition preview-safe.** Previews run through Layoutlib inside
   Android Studio: no network access, no file access, some `Context` APIs
   missing. Never start IO, dates, or real data loading at composition; pass
   data in as parameters; gate with `LocalInspectionMode.current` (true inside
   previews) to show placeholders instead of fetching. Done when: previews
   render without exceptions and app code is unchanged.
6. **Treat the preview pane as a compile-time check.** Preview code executes
   during rendering, so a failing preview is usually a signature problem:
   missing defaults, a ViewModel/DI reach-in, or an unsupported call at
   composition. Fix the composable contract before touching tooling. Done
   when: the Design tab renders every panel.
7. **Verify animations with Animation Preview, honestly.** Static panels show
   one frame. Animation Preview auto-detects inspectable animations (Start
   Animation Preview icon) and supports exactly: `updateTransition`,
   `AnimatedVisibility`, `animate*AsState`, `Crossfade`,
   `rememberInfiniteTransition`, `AnimatedContent` — play, pause, scrub, loop,
   speed, coordinate multiple, freeze one, curve graphs, and pickers for
   non-enum/boolean states (latest features: Android Studio Rabbit 2 +
   compose.animation 1.12.1+). Animations outside that list cannot be scrubbed
   there: drive them in interactive mode (sandboxed click/type/gestures, also
   good for states) and pin their visual end-states with screenshot tests.
   Done when: playback is observed, or the fallback path documents why.
8. **Pin visuals with preview screenshot tests.** Annotate previews with
   `@PreviewTest` in the `screenshotTest` source set, render reference images,
   validate diffs into an HTML report. AGP test suites (AGP 9.5+) are the
   docs-recommended setup; the standalone `com.android.compose.screenshot`
   plugin is deprecated by the docs. Setup, tasks, and paths:
   [references/screenshot-testing.md](references/screenshot-testing.md).
   Done when: the update task produced references and the validate/test task
   passes.
9. **Don't trust Run Preview for variant checks.** Running a preview deploys
   it as a new `Activity` on a device or emulator, but `@Preview` annotation
   arguments (`widthDp`, `locale`, `uiMode`, …) are NOT applied to that
   deployment. Verify variants in the pane, via interactive mode, or with
   screenshot tests. Done when: no variant claim rests on Run Preview.

Out of scope: authoring animations (motion design skills), instrumented UI
tests, and unit tests (TDD skill).

Read [references/screenshot-testing.md](references/screenshot-testing.md) when
setting up Gradle screenshot testing of previews.
Read [references/sources.md](references/sources.md) for the doc pages behind
each rule.

---

Authored for ivanDsky/skills; grounded in developer.android.com.
