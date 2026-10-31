# Sources

All claims in `SKILL.md` are grounded in these official pages, fetched
2026-10-30:

1. **Preview your UI with composable previews** —
   https://developer.android.com/develop/ui/compose/tooling/previews
   Grounds rules 1–6 and 9: `@Preview` parameter list (`name`, `group`,
   `widthDp`/`heightDp`, `device`, `locale`, `fontScale`, `showBackground`,
   `backgroundColor` ARGB Long, `uiMode`, `wallpaper`, `apiLevel`),
   multipreview templates (ui-tooling-preview 1.6.0-alpha01+), custom
   multipreview annotation classes (independent, not cross-product),
   `PreviewParameterProvider` + `@PreviewParameter` (`limit`,
   `getDisplayName()`), `LocalInspectionMode`, interactive mode, Run Preview
   (annotation args not applied), Layoutlib limitations (no network, no file
   access, partial `Context`), and the ViewModel-to-stateless-overload
   pattern from the "Limitations and best practices" section.
2. **Animation Preview** —
   https://developer.android.com/develop/ui/compose/tooling/animation-preview
   Grounds rule 7: auto-detection via the Start Animation Preview icon;
   supported APIs listed verbatim as `updateTransition`, `AnimatedVisibility`,
   `animate*AsState`, `CrossFade` (docs' spelling — the real API is
   `Crossfade`), `rememberInfiniteTransition`, `AnimatedContent`; play, pause,
   scrub, loop, speed, coordinate, freeze; curve graphs; pickers for
   non-enum/boolean states; Android Studio Rabbit 2 + compose.animation
   1.12.1+ for the latest features.
3. **Compose Preview Screenshot Testing** —
   https://developer.android.com/studio/preview/compose-screenshot-testing
   Grounds rule 8 and the legacy path in the setup reference: `@PreviewTest`,
   `screenshotTest` source set, flags, plugin, dependencies, update/validate
   tasks, reference paths and naming, HTML report, heap-size troubleshooting,
   rename-breaks-references caveat, KMP limitation, and the docs caution that
   the standalone plugin is no longer maintained.
4. **Screenshot testing with test suites (AGP, recommended)** —
   https://developer.android.com/studio/preview/compose-screenshot-testing-with-testsuites
   Grounds the recommended path in the setup reference: AGP 9.5.0-alpha03+ /
   engine 0.0.1-alpha16+ / Android Studio Rabbit 1 Canary 4+ / JDK 17+,
   experimental flags, `testOptions.screenshotTests` DSL, suite source set,
   `update{Suite}{Target}{Variant}TestSuite` /
   `test{Suite}{Target}{Variant}TestSuite` tasks, reference and report paths,
   migration table from the legacy plugin.

## Deltas from the brief

- The brief cited
  https://developer.android.com/develop/ui/compose/tooling/best-practices —
  it returns 404. The equivalent official content is the "Limitations and
  best practices" section of source 1; rules 1, 5, and 6 are grounded there.
- The screenshot-testing docs were found at the `/studio/preview/…` URLs
  above; they now steer readers from the standalone plugin to AGP test
  suites, so the setup reference presents test suites as the default path.
