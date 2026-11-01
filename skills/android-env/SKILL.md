---
name: android-env
description: >-
  Android environment bootstrap — one pass at session start: adb/SDK PATH,
  local.properties, worktree-aware git, device connect over tailscale,
  Gradle failure triage (stale incremental → clean), Studio modal handling
  (detect and escalate, never automate dialogs). Use when an Android
  command fails with "command not found", a build can't find the SDK, git
  misbehaves inside a worktree, adb can't see the device, or a Gradle
  failure smells like stale incremental state.
interaction: afk
requires: [Android SDK, android CLI (see android-cli)]
---

> **TL;DR** Run the environment checklist before the first Android command of any session — PATH, `local.properties`, worktree git, device reachability — and never re-derive these fixes mid-session; Gradle "failures" that survive a `clean` are real, everything else is stale state.
> **Related**: skill://android-cli (tooling routing, Studio project-open protocol), skill://deliver (deploy targets), skill://deploy-tailscale (device registry)

# Android environment — derive once per session, not once per command

These five failures consumed 2–3 minutes per session, every session, across
six audited sessions. Run the checklist up front; record project-specific
outcomes in PROFILE.md `## Environment facts`.

## 1. PATH (hit in 4 of 6 audited sessions)

`adb: command not found` → the SDK lives at `~/Library/Android/sdk`:

```sh
export PATH="$PATH:$HOME/Library/Android/sdk/platform-tools:$HOME/Library/Android/sdk/emulator"
```

Do this once at session start (or verify `adb version` works). If the android
CLI is installed (`android-cli`), prefer it — it knows the SDK location via
`android info` and does not need adb on PATH for most actions.

## 2. local.properties

Missing → write it once, at the repo root:

```sh
echo "sdk.dir=$HOME/Library/Android/sdk" > local.properties
```

Never commit it (`.gitignore`).

## 3. Worktree git (`git worktree` repos)

In a worktree, `.git` is a **file** pointing at the real gitdir, not a
directory. Tools that assume a directory (some `gh` operations, hooks, naive
path joins) break with confusing errors. When a git/`gh` command fails oddly
inside a worktree: check `cat .git` first; run the command from the main
checkout if the tool can't handle worktrees; never "fix" it by deleting
`.git`.

## 4. Device over tailscale

The user's tablet is reached by its tailscale IP, not USB. Connect:
`adb connect <tablet-tailscale-ip>:5555`, verify with `adb devices`. Connection
details live in PROFILE.md `## Environment facts` — read them, don't rediscover.
`deploy-tailscale` owns the full delivery flow; this is just the connect step.

## 5. Gradle failure triage (before believing any red build)

Order, cheapest first:

1. **Stale incremental state** — a failure in resources/mipmaps/manifests
   that "should be fine", or an error referencing files you didn't touch:
   run `./gradlew clean` (or `android build` after a clean) **before**
   reading the error as a code problem. Audited cost of skipping this: a
   false red herring chased across a session.
2. **Task name** — wrong Gradle task names burned 7 attempts in one session.
   List first: `./gradlew tasks --all | grep -i <keyword>`; don't guess
   `assembleDebug` variants.
3. **Then** it's a real failure — read the actual error, diagnose normally.

Build churn discipline: batch changes before building; never run
`assembleDebug` in a loop to "check if it works now" (audited: 6
consecutive full builds in one crash-loop session). Use
`android preview render` for UI checks between builds.

## 6. Studio modals — detect, escalate, never automate

Automating Android Studio dialogs (open+sleep+check loops, osascript clicks,
pkill pattern roulette) burned 19 minutes in one audited session and ended
with the user clicking one button. Rule:

- A Studio command that should work but hangs/returns nothing → assume a
  modal is up (`android studio check` state + the known culprits: trust
  dialog — see `android-cli` project-open protocol, update prompts, indexing
  in progress).
- Escalate to the user with `ask` **immediately**: "Studio is showing a
  dialog — approve it?" One click beats ten tool calls.
- Never pkill Studio processes to "reset" — that loses the user's open
  editors and state.
