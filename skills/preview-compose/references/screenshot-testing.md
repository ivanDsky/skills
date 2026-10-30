# Compose preview screenshot testing — setup essentials

From developer.android.com/studio/preview/compose-screenshot-testing and
developer.android.com/studio/preview/compose-screenshot-testing-with-testsuites
(fetched 2026-10-30).

What it is: screenshot tests render each `@PreviewTest` preview host-side (no
emulator), compare against committed reference images, and fail with an HTML
report on mismatch. `@Preview` parameters (`uiMode`, `fontScale`) and
multi-previews scale the test matrix.

## Recommended: AGP test suites (AGP 9.5+)

Requirements: Android Studio Rabbit 1 Canary 4+, AGP 9.5.0-alpha03+,
screenshot engine 0.0.1-alpha16+, JDK 17+, Compose enabled (Compose Compiler
Gradle plugin recommended). Docs flag the DSL as experimental.

1. Root `gradle.properties`:

   ```
   android.experimental.enableScreenshotTest=true
   android.experimental.testSuiteSupport=true
   ```

2. Module `build.gradle.kts`:

   ```kotlin
   android {
       testOptions {
           screenshotTests.create("screenshotTest") { // suiteName is customizable
               engineVersion = "0.0.1-alpha16"
               targetVariants.add("demoDebug") // add your variants
               dependencies {
                   implementation(libs.androidx.compose.ui.tooling)
                   implementation("com.android.tools.screenshot:screenshot-validation-api:0.0.1-alpha16")
               }
           }
       }
   }
   ```

3. Source set: `{module}/src/{suiteName}/kotlin/` (e.g.
   `app/src/screenshotTest/kotlin/…`).

4. Tests — `@PreviewTest` (from `com.android.tools.screenshot.PreviewTest`)
   plus `@Preview` or multi-previews, wrapped in the app theme:

   ```kotlin
   @PreviewTest
   @Preview(showBackground = true)
   @Composable
   fun ForYouScreenPreview() {
       AppTheme { ForYouScreen(isSyncing = false) }
   }
   ```

5. Tasks and outputs:

   - Generate/update references:
     `./gradlew update{SuiteName}{Target}{Variant}TestSuite` (e.g.
     `updateScreenshotTestDefaultDemoDebugTestSuite`) → images land in
     `src/{suiteName}{Target}{Variant}/reference/`.
   - Validate: `./gradlew test{SuiteName}{Target}{Variant}TestSuite`.
   - Report: `{module}/build/reports/tests/{taskName}/index.html` — per-test
     status, error categories (Reference Image Missing / Image Size Mismatch /
     Pixel Mismatch), dynamic visual diff.

## Legacy standalone plugin (deprecated per the docs)

The docs caution that `com.android.compose.screenshot` is no longer
maintained; use it only if pinned (runs with AGP 8.5.0+, Kotlin 1.9.20+,
JDK 17+):

- `android.experimental.enableScreenshotTest=true` in `gradle.properties`,
  plus `experimentalProperties["android.experimental.enableScreenshotTest"] = true`
  in the `android {}` block.
- Version-catalog plugin `com.android.compose.screenshot` 0.0.1-alpha16; then
  `screenshotTestImplementation` of `screenshot-validation-api` and
  `androidx.compose.ui:ui-tooling`.
- Tasks: `./gradlew updateDebugScreenshotTest` (references →
  `{module}/src/screenshotTestDebug/reference/`) and
  `./gradlew validateDebugScreenshotTest` (report →
  `{module}/build/reports/screenshotTest/preview/{variant}/index.html`).

## Gotchas

- Renaming a `@PreviewTest` function breaks the association with existing
  reference images — regenerate references after renames.
- Host-side rendering is memory-hungry; raise the test JVM heap with
  `android.compose.screenshot.maxHeapSize=4g` in `gradle.properties`.
- KMP: Android targets only; non-Android targets are unsupported.
- IDE integration (gutter icons to run/update, built-in diff viewer) needs
  Android Studio Panda 1 Canary 4+ with AGP 9.0+; bare Gradle tasks need only
  AGP 8.5+.
