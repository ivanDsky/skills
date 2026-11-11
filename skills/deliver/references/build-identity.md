# Build identity — versionCode, versionName, APK name across worktrees

Parallel worktrees share one phone. Without a shared counter each agent
builds with the committed versionCode, installs fail with
`INSTALL_FAILED_VERSION_DOWNGRADE`, and same-named APKs overwrite each other
in Downloads. One allocator fixes all three: **every install gets a name no
other install has ever had**, and the ledger records it.

## The ledger

`<git-common-dir>/agent-builds/versions.jsonl`. The git common dir is the
main checkout's `.git`, the same path from every worktree. The ledger is
never committed or pushed. One JSON line per install: code, semver,
install number, version name, APK name, branch, slug, sha, worktree,
device codes seen, time.

## Ship every installable build with `ship_apk.py`

Any build that may reach a device: `deliver`, `user-check` hand-off builds, `implement` device checks,
`diagnose-bug` instrumented builds. Run it from the worktree root.
`app-id`, `app-name` and `version` come from PROFILE.md `## Version`.

```
SHIP=~/.agents/skills/deliver/scripts/ship_apk.py   # global install; in this repo: skills/deliver/scripts/
eval "$(python3 $SHIP)"                # allocate → build → verify → name → Taildrop → ledger
eval "$(python3 $SHIP --build-only)"   # same, no send; then adb install -r "$APK_PATH" or tailscale serve
```

It runs `build_identity.py allocate` (below), builds
`:<module>:assemble<Variant>` with the allocated `-PagentVersionCode` and
`-PagentVersionName` (log in `.scratch/<slug>/build.log`), and reads the APK
back with `aapt2 dump badging`. It refuses to ship unless the real
versionCode, versionName and package (PROFILE `app-id`, or `app-id.<suffix>`
for debug) equal the allocation. Then it copies the APK to
`.scratch/<slug>/$APK_NAME`, Taildrops it to the PROFILE `tailscale:`
`- device:` line, and appends one evidence line (UTC time, name, versionName,
versionCode, git sha, device or `build-only`, sha256, bytes) to
`.scratch/<slug>/ledger.md`. It prints `APK_PATH`, `APK_NAME`,
`VERSION_NAME`, `VERSION_CODE`, `SLUG`, `SHA256`, `BYTES` and `DEVICE`.
Flags: `--slug S`, `--device D`, `--variant debug|release` (default debug),
`--release` (release cut from main; implies `--variant release`),
`--module app`. `--apk PATH` re-sends an APK the script already built (a
reused user-check build, a failed send) after re-verifying it against its
ledger record; no new code is burned.

A manual build is never shipped. The harness hook
`~/.omp/agent/hooks/pre/apk-ship-guard.ts` enforces this for agent
`bash`/`eval` calls:

1. Raw `tailscale file cp` is refused (`--targets` is allowed) once
   `~/.agents/skills/deliver/scripts/ship_apk.py` is installed. The script
   calls tailscale itself and is the only Taildrop path.
2. `adb install` / `install-multiple` is refused unless the APK's file name is
   canonical (`<AppName>-<semver>[-<slug>.<n>]-<code>-<debug|release>.apk`)
   or the literal `$APK_NAME`. Gradle's `app-<variant>.apk` never installs.

### What `allocate` does

`ship_apk.py` calls it; run it directly only to inspect. The flags
`--app-id`, `--app-name` and `--semver` override PROFILE.md.

```
BI=~/.agents/skills/deliver/scripts/build_identity.py
python3 $BI allocate --variant debug [--slug S]   # prints VERSION_CODE, VERSION_NAME, APK_NAME, SLUG, GRADLE_ARGS, LEDGER
```

- `VERSION_CODE` = max(ledger, installed on every connected device via
  `adb shell dumpsys package`, committed Gradle code) + 1, taken under a
  `mkdir` lock, so parallel agents never get the same number.
- `VERSION_NAME` = `<semver>-<slug>.<n>`, a SemVer pre-release tag, e.g.
  `1.3.0-reminders.2`. App info shows it, so the phone tells you the branch
  and which install of it. `<semver>` is the release line from PROFILE.md;
  the allocator never bumps it (see below). `<n>` counts installs per slug,
  starting at 1 and never reused; `main` installs count too (`1.3.0-main.4`).
- `APK_NAME` = `<AppName>-<versionName>-<code>-<variant>.apk`, e.g.
  `Habits-1.3.0-reminders.2-1042-debug.apk`. Name and code are both unique;
  the allocator refuses a name already in the ledger.
- Slug = the last segment of the branch name, lowercase, `[a-z0-9-]`, up to
  24 characters. A detached HEAD gives `sha-<short>`. `--slug S` sets it
  explicitly (same rule; anything else is refused). Two branches with the
  same slug (`feature/sync`, `fix/sync`) share one counter, so their names
  stay unique; `which`/`list` tell the branches apart.
- `--base-code` overrides the committed code when the project keeps it
  outside `app/build.gradle(.kts)` (version catalog, properties file).
- Device unreachable → the code comes from the ledger and the committed
  code only, with a warning on stderr. Installing over a build made outside
  this clone can then still fail; `which` shows it.
- One allocation per build. Never reuse a code, never edit the ledger by
  hand, never install with `adb install -d` to force a downgrade.

## What is on the phone?

```
python3 $BI which      # each connected device: installed code → branch, sha, APK
python3 $BI list -n 10 # last allocations across all worktrees
```

`which` maps the installed versionCode to its ledger record (branch, sha,
APK). "Not in ledger" means the build came from elsewhere (another clone,
CI, Play).

## One-time Gradle wiring (on `main`, never in a worktree)

AGP 7.3+ removed the `android.injected.version.*` command-line overrides,
so the module has to read the values itself. Keep the committed fallback
as the last number on the `versionCode` line, because the allocator reads
it from there:

```kotlin
// app/build.gradle.kts → android { defaultConfig { … } }
versionCode = providers.gradleProperty("agentVersionCode").orNull?.toInt() ?: 7
versionName = providers.gradleProperty("agentVersionName").orNull ?: "1.3.0"
```

```groovy
// app/build.gradle
versionCode project.findProperty("agentVersionCode")?.toInteger() ?: 7
versionName project.findProperty("agentVersionName") ?: "1.3.0"
```

Builds without the arguments (Studio, CI) keep the committed values. If a
worktree finds the wiring missing, it stops and asks for it to land on
`main` first. Each worktree adding it separately gives a conflict on every
merge.

## Semver moves only on a release

Every install bumps `<n>`, never the semver, so parallel worktrees never
fight over `version:` in PROFILE.md. Landing a feature or fix on `main`
bumps nothing either: a release can carry many landed changes.

Cutting a release (the user asks for one) is the only bump, on `main`:

1. Bump PROFILE `version:` once for the whole release: minor by default
   (`1.3.0` → `1.4.0`), patch for a fixes-only release, major for a
   breaking one. Update the Gradle `versionName` fallback to match and
   commit both in one commit.
2. `eval "$(python3 $SHIP --release --build-only)"` (then the target's
   send, or drop `--build-only` for Taildrop): versionName is the plain
   semver (`1.4.0`), APK `Habits-1.4.0-1077-release.apk`. The allocator
   refuses `--release` outside `main`/`master` and refuses a semver already
   released, so one version is never shipped twice.

Branches cut after the release build `1.4.0-<slug>.<n>`.
