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
> **Related**: skill://preview-compose (preview rendering ladder), skill://diagnose-bug (layout/screen/signals evidence), skill://tdd (testing ladder + Journeys), skill://deliver (build/deploy targets)

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
