---
name: wire-dev-settings
description: >-
  Wire a debug-only developer settings screen and reactive feature flags:
  Firebase Remote Config for dynamic remote toggles (live updates without app
  restart), local debug overrides, hidden entry points, and a playground of
  prototype screens (Showkase catalog, deep links). Use when adding feature
  flags, dev toggles, an environment switcher, prototype screen links, or an
  in-app playground, or a release flag that keeps trunk work merge dark.
interaction: afk
requires: []
---

> **TL;DR** Wires a debug-only developer settings screen with release flags (unfinished trunk work dark), reactive Firebase Remote Config ops flags, overrides, and a playground; fires when adding feature flags.
> **Related**: skill://preview-compose (prototype screens), skill://ship-to-trunk (when release flags are added, flipped, removed)

# Wire dev settings & flags

Flags change behavior without shipping; dev settings surface them (and the
prototype playground) on the device, out of the release path. Three kinds,
chosen per flag - never one blob:

1. **Release flag** - keeps unfinished trunk work dark so slices merge to
   `main` (`ship-to-trunk`). Typed key; the release value is a compile-time
   constant `false` (per-build-type source set or a `BuildConfig` field) so R8
   strips the gated code; debug reads a local override, with a forced-on
   toggle in the dev settings screen. NEVER remote-enabled before its flip PR.
   Added by ticket 01, flipped by the flip PR, removed by the cleanup ticket.
2. **Ops/rollout flag (Firebase Remote Config)** - for a FINISHED feature
   that must change AFTER install: kill switches, gradual rollouts, per-user
   targeting. Update lands live from the console; the running app reacts.
3. **Local debug toggle (DataStore, debug builds only)** - for development
   convenience: force a state, skip onboarding, fake data. Never exists in
   release code.

Default (user ruling 2026-11-07): release flags only, even when Firebase is
already in the project; add Remote Config only when a finished feature needs
a rollout or kill switch.

## Decision rules

1. Flag keys are typed (enum/sealed) with defaults in code; the remote/local
   value is a lookup into them, not a free string. MUST.
2. Precedence for ops flags, in debug: local override > remote config > code
   default; in release: remote > default. Release flags: release = the
   constant; debug = local override > code default. MUST.
3. The remote listener is single and shared: one repository owning Firebase
   Remote Config's `addOnConfigUpdateListener`, calling `activate()` on update,
   exposing a `StateFlow<Flags>` the UI collects - screens re-compose live,
   no restart, no flow interruption. MUST. (Firebase real-time RC: one shared
   HTTP connection for all listeners; remove on cleanup.)
4. Debug-only code is gated at the entry (`if (BuildConfig.DEBUG)`) and
   release-minified away; a dev toggle MUST NOT be reachable from release
   builds. MUST.
5. Flags die: when a flag is 100% rolled out or dead, removing the branch and
   the key is a ticket - stale flags are debt (ponytail-debt finds them).
   SHOULD.
6. Test both sides: every flag branch is reachable in a test (JVM state test
   per flag state; screenshot per variant). SHOULD.

## Dev settings screen (debug only)

- Hidden entry: long-press on the version label (plus a Quick Settings
  `TileService` when useful). Not in any release navigation graph.
- Contents: flag toggles (local overrides, showing remote values as
  "remote: x"), environment switch, log level, "copy logs" (feeds
  diagnose-bug), and links:
  - **Playground**: Showkase browser activity - auto-discovers every
    @Preview composable, colors, typography (references/playground.md).
  - **Prototype screens**: deep links into nav-gated prototype routes
    (`adb shell am start -W -d <uri>` jumps straight there); list them as
    tappable rows.

## References

- Remote Config recipe (fetch/activate + reactive listener -> StateFlow):
  [remote-config-recipe.md](references/remote-config-recipe.md)
- Playground & prototype links (Showkase, deep links):
  [playground.md](references/playground.md)

Footer: authored for ivanDsky/skills; grounded in Firebase Remote Config docs
(real-time best practices: addOnConfigUpdateListener) and Airbnb Showkase (MIT).
