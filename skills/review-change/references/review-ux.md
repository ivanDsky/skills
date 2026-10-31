# UX review axis

Read this when the diff touches UI — at every tier, not only thorough. Three
layers, cheapest first; stop adding layers once one exposes systemic issues.

1. **Scripted checks** (every tier, alongside the fast-gate screenshots): touch
   targets, density, safe areas, state restoration, offline behavior on
   mobile; focus order, keyboard access, empty and error states on web.
   Platform review axes come from the platform routes in PROFILE.md.
   On Android, `android layout --output hierarchy.json` gives the machine-
   checkable tree for touch-target/density checks.
   Android UI in the diff also passes preview coverage (`preview-compose`):
   every new or changed composable has `@Preview`s with state and
   light/dark/font-scale variants (multipreview annotations), and any animated
   component is verifiable in Animation Preview — a component without preview
   evidence is a finding, not a preference. Flag-backed UI (`wire-dev-settings`)
   must show both flag branches in previews or tests.
2. **Stack guidelines** (ui-ux-pro-max; 22 stacks incl. Jetpack Compose and
   SwiftUI): load the stack's guideline set and check the diff's screens
   against it. When `references/rules-ui-<platform>.md` is empty, seed it from
   ui-ux-pro-max's design-system generation.
3. **Knowledge layer** (platform-agnostic): apple-design and emil-design-eng
   principles — motion with purpose, interruption, hierarchy, restraint.
   Web-only surfaces add the taste gates: `design-taste-frontend`'s
   real-browser inspector and impeccable's critique, each when installed.

Screenshot evidence follows the UI verification ladder
(`tdd` skill, references/android-testing.md): JVM screenshot tests
(Roborazzi / AGP preview suites) are the default per-review evidence; a real
device or emulator screenshot is acceptance evidence, taken once at delivery —
not the per-review default.

UX findings land in the same review file, graded like any finding and tagged
`ux`. UX passes on screenshots, not descriptions — no screenshot of a surface,
no ✅ for it.
