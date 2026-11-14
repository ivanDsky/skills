# PROFILE.md — real PuzzleBox wording (origin/main, 2026-11-14), trimmed to the sections the scripts read; identifiers scrubbed

## Version
- app-id: com.example.puzzlebox
- app-name: PuzzleBox
- version: 0.32.0  # semver source of truth; main's release line; every merge to main publishes GitHub release v<version> (.github/workflows/release.yml, skipped when the tag exists). Bugfixes merge without a bump and ship in the next release the user asks for (user rule 2026-11-08); a release bumps this line and the Gradle versionName fallback in one commit. Installs use deliver build_identity.py: <semver>-<slug>.<n>, APK PuzzleBox-<versionName>-<code>-<variant>.apk. Gradle versionCode fallback 100 (2026-11-05: headroom above every worktree's hand-set codes, max 23).


## Deploy targets (in order; empty list = build-only)
- local: ./gradlew :app:assembleDebug
- release: .github/workflows/release.yml  # workflow "Main": push to main → two parallel test jobs (assembleDebug testCore, testUi; goldens skipped outside :app) beside the signed release build; publish to GitHub releases only when all are green; local release builds sign with the release key via ~/.gradle/gradle.properties
# releases run in one queue; a 3rd quick merge replaces the 2nd's pending run (that version is skipped; next run releases HEAD — re-dispatch from main to publish now)


## Delivery
- changes: trunk   # user ruling 2026-11-07 (replaces 2026-11-05 `pr`): ship-to-trunk — one small PR per ticket off fresh origin/main, unfinished behavior merges dark behind a release flag, the flip PR (flag on + version bump) is the release
- pr-check: none   # merge gate: `./gradlew assembleDebug test` green on the PR branch rebased onto fresh origin/main. User ruling 2026-11-07 (ADR-0023, replaces the required pr-check): PRs run no CI and main requires no status check. Main's workflow re-runs the gate after every merge; red main → stop merging, revert the culprit or fix it forward in one line. Skip `gh pr checks` waits (there are none)


## Consent ledger
- pre-approved: merge dark slices on green   # user ruling 2026-11-07: agent merges dark/non-behavioral slice PRs on a green LOCAL suite (`./gradlew assembleDebug test` on the rebased branch, ADR-0023) + clean fast review; flip PRs, live changes (migrations, persisted formats, manifest/permissions, dependency/SDK bumps, GitHub Actions version bumps) still wait for the user


## Testing style
- runner: ./gradlew :app:testDebugUnitTest   # JVM unit tests against fakes
- approach: tdd-fakes
- seams: repository/use-case interfaces (+ fakes), dispatcher provider
- structure: ./gradlew :konsist:test   # in-module structure rules (ADR-0009)
