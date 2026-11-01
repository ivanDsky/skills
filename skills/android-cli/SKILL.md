---
name: android-cli
description: >-
  Routing map for the Android CLI (android, stable 1.x) — command index wired
  into the workflow: device-free Compose preview rendering, Android Studio
  engine access (analyze, find-usages, version-lookup), docs search,
  scripted emulator/device control, Journeys, Crashlytics signals. Use when
  an Android task needs renders, static analysis, docs, device/emulator
  control, APK deploy, UI hierarchy, or crash telemetry — before reaching
  for raw adb/avdmanager or opening Android Studio manually.
interaction: afk
requires: [android CLI 1.x (brew install android-cli)]
---

> **TL;DR** The `android` CLI is the terminal entry to Android tooling — device-free preview renders, Studio analysis, docs, emulators, deploys, Journeys, Crashlytics signals; this skill routes each need to its command and the workflow skill that owns it.
> **Related**: skill://preview-compose (preview rendering ladder), skill://diagnose-bug (layout/screen/signals evidence), skill://tdd (testing ladder + Journeys), skill://deliver (build/deploy targets), skill://android-env (session bootstrap, Gradle triage, Studio modal handling), skill://adopt-tool (adoption checklist)

# Android CLI — adopted commands and routing

Google's official agent surface for Android, stable since 1.0. Where a
command exists here, it replaces raw `adb`/`avdmanager`/SDK-Manager clicking
and IDE round-trips. One-time per machine: `brew install android-cli`; one-time
per project: `android init` (installs the official android-cli skill plus
environment config — run it during onboarding, `init-profile`/`map-codebase`).

## Command → workflow routing

| Need | Command | Owned by |
|---|---|---|
| Render Compose previews to PNG, no device, no IDE | `android preview list` / `android preview render` (optional component-tree JSON) | `preview-compose` — ladder rung 1→3 evidence |
| Semantic find-usages / find-declaration | `android studio find-usages` / `find-declaration` (needs Android Studio Quail+ running, `android studio check` first) | `implement` (renames, blast radius), `ponytail-review` |
| File inspections beyond lint | `android studio analyze-file` | `review-change` fast gate (alongside lint) |
| Dependency version lookup | `android studio version-lookup` | `implement`, dependency-bump tickets |
| Official docs search/fetch | `android docs search "<query>"` → `android docs fetch kb://...` | `draft-spec`, `fan-out-research`, `implement` |
| Scripted emulator control | `android emulator list/create/start/stop` | `tdd` ladder last rung, `diagnose-bug` — scripted, never hand-launched |
| Deploy APK without launching | `android install --apks=<apk>` (incremental, faster than adb) | `deliver`, `deploy-tailscale` verify installs |
| Deploy + launch | `android run --apks=<apk> --activity=<...>` | `deliver` local target |
| Screen capture with annotations | `android screen capture --annotate` | `diagnose-bug` evidence, `review-site` screenshots |
| UI hierarchy to JSON | `android layout --output hierarchy.json` | `review-ux` scripted checks (touch targets, density), `diagnose-bug` |
| Crashlytics stability telemetry | `android signals` | `diagnose-bug` — crash evidence before any repro |
| Natural-language E2E journeys | Journeys tools/skills (`android skills find journey`) | `tdd` ladder — between instrumented tests and human acceptance |
| APK/AAB metadata | `android analyze <apk>` — versions, permissions, size | `deliver` DoD check, release naming verification |

## Verified strengths (checked against `android help`, CLI 1.1)

- **File-level static analysis (the reviewer's first tool)** —
  `android studio analyze-file <path>` runs Android Studio's editor
  inspections on one file. Reviewers run it on every touched Kotlin/Java
  file *before* reading the diff; it catches unused symbols, nullability
  issues, API misuse and deprecations that eyeballing the diff misses. It
  *supplements* Gradle lint on the touched files; it does not replace
  `./gradlew lint` (different check sets).
  Project-open protocol (mandatory): if `android studio check` shows no
  READY project (or the wrong one), open this worktree first — macOS:
  `open -a "Android Studio Preview" <repo-root>` (or `open -a "Android
  Studio" ...`), then poll `android studio check` until the project lists
  READY. Verify the READY entry's path matches the worktree under review
  before running any studio command, and pin every studio call with
  `--project <name-or-path>` so results never attach to a different open
  project. **Coverage proof:** the reviewer lists every touched
  Kotlin/Java file with its analyze-file result (clean / findings) in the
  review — "lint passed" or APK analysis does not count as coverage
  (audited miss: reviewer ran lint+APK only and the user had to ask "did
  you run analyze-file on everything?"). Trust dialog: the first open of an
  untrusted folder blocks on a
  modal. Fix once per machine by adding `-Didea.trust.all.projects=true` to
  the Studio `studio.vmoptions` (macOS:
  `~/Library/Application Support/Google/AndroidStudio<version>/`) — trusts
  every project, acceptable on a dev-only machine; per-project trust via
  `options/trusted-settings.xml` is the conservative alternative. Flag takes
  effect on the next Studio launch; if Studio is already running, restart it
  or approve the dialog by hand once.
- **Documentation images from previews** — `android preview render
  --output <dir> --fqn <fqn>` builds the target and writes per-preview PNGs
  (plus optional `--component-tree` JSON: bounds, semantics, parameters,
  modifiers). This is the pipeline for README/docs screenshots of UI
  components and for `review-site` images — real renders, not mockups.
- **Dependency/version suggestion verification** — `android studio
  version-lookup <artifacts...>` returns latest available versions of Maven
  artifacts, Android versions, and SDK tools. Verify any "you should
  upgrade X" suggestion here before applying it. It does not validate other
  kinds of suggestions (refactors, lint fixes) — those need
  `analyze-file`/inspection runs.

## Placement rules

- `android preview render` is device-free JVM evidence: it counts on the
  testing ladder like Roborazzi/AGP preview suites (per-review evidence),
  and it feeds `review-site` screenshots directly. Prefer it when a project
  lacks Roborazzi setup; the rendered PNGs are per-preview, per-variant.
- `android studio *` requires the IDE open with the project (`check` first —
  READY state). Never launch Android Studio from a headless flow; those
  commands are a bonus when the user has the IDE open.
- Raw `adb` remains valid for what the CLI does not expose (wireless pairing
  per `deploy-tailscale`); do not mix both for the same action.
- Journeys run against a device/emulator — they are acceptance-layer checks,
  not per-commit evidence. One journey per critical user path, saved in the
  project.

## Skill library

Official Android skills (`android skills list/find/add --skill=<name>`)
complement this repo: install project-relevant ones during onboarding
(e.g. testing-setup, adaptive-ui, styles, perfetto-sql). They live beside
these skills, not instead of them — this repo owns the workflow chain,
Google's skills own Android-specific patterns.
