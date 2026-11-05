# Build identity — versionCode, versionName, APK name across worktrees

Parallel worktrees share one phone. Without a shared counter each agent
builds with the committed versionCode, installs fail with
`INSTALL_FAILED_VERSION_DOWNGRADE`, and same-named APKs overwrite each other
in Downloads. One allocator fixes all three.

## The ledger

`<git-common-dir>/agent-builds/versions.jsonl`. The git common dir is the
main checkout's `.git`, the same path from every worktree. The ledger is
never committed or pushed. One JSON line per allocation: code, version name,
APK name, branch, slug, sha, worktree, device codes seen, time.

## Allocate before every installable build

Any build that may reach a device: `deliver`, `implement` device checks,
`diagnose-bug` instrumented builds. Run it from the worktree root.
`app-id`, `app-name` and `version` come from PROFILE.md `## Version`; the
flags `--app-id`, `--app-name` and `--semver` override them.

```
BI=~/.agents/skills/deliver/scripts/build_identity.py   # global install; in this repo: skills/deliver/scripts/
eval "$(python3 $BI allocate --variant debug)"
./gradlew :app:assembleDebug $GRADLE_ARGS
cp app/build/outputs/apk/debug/app-debug.apk ".scratch/<slug>/$APK_NAME"
```

- `VERSION_CODE` = max(ledger, installed on every connected device via
  `adb shell dumpsys package`, committed Gradle code) + 1, taken under a
  `mkdir` lock, so parallel agents never get the same number.
- `VERSION_NAME` = `<semver>` on `main`/`master`, otherwise
  `<semver>-<slug>` (shown in App info, so the phone tells you the branch).
- `APK_NAME` = `<AppName>-<semver>-<code>[-<slug>]-<variant>.apk`, e.g.
  `Habits-1.3.0-1042-reminders-ui-debug.apk`. The code alone makes it
  unique.
- Slug = the last segment of the branch name, lowercase, `[a-z0-9-]`, up to
  24 characters. A detached HEAD gives `sha-<short>`.
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

## Semver bumps only on `main`

Worktree builds never write `version:` back to PROFILE.md. The bump
(breaking → major, feature → minor, fix → patch) happens once, when the
change lands on `main`. With delivery `main` it goes in the landing commit.
With delivery `pr` it is a one-line commit on `main` right after the merge.
The bump also updates the Gradle `versionName` fallback when one exists.
