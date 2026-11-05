---
name: deploy-firebase
description: >-
  Distributes an Android APK/AAB build to Firebase App Distribution test
  users — tester groups, release notes, tester status, and the dashboard
  evidence a ticket closes on. Use when the PROFILE.md firebase deploy
  target is set on an Android build, when the user asks to send a build to
  Firebase testers, or when App Distribution testers or Auth test users
  need setting up for an app.
interaction: afk
requires: [firebase-cli]
---

> **TL;DR** Distributes an Android APK/AAB build to Firebase App Distribution test users; fires on the PROFILE.md firebase target for Android builds.
> **Related**: skill://deliver (dispatches targets), skill://deploy-tailscale (sibling target)

# Deploy to Firebase App Distribution

Distribute an Android build to real-device testers, set up the humans —
App Distribution testers (who can download) and Firebase Auth test users
(who can sign in) — and hand back the dashboard evidence. Dispatched by
`deliver` when the PROFILE.md firebase deploy target is set on an Android
build; routes standalone too. Web targets (hosting, functions, rules) are
not this skill — they stay in `deliver`.

## 1. Preflight

- `firebase projects:list` answers → CLI present and signed in. Missing →
  stop with the pointer: `npm install -g firebase-tools`, then
  `firebase login`. Never improvise a deploy path.
- From the PROFILE.md `firebase:` entry: project id, and the app's App ID
  (`--app`, looks like `1:1234567890:android:0a1b2c3d4e5f67890`, from
  console → Project settings → General). Either missing → stop and ask;
  never invent a config value.
- Pin the project: `firebase use <project-id>`.

## 2. Test users — two kinds, never confuse them

1. **App Distribution testers** control downloads. Console: App
   Distribution → Testers & Groups tab. CLI: create the group first, then
   fill it — `firebase appdistribution:groups:create "QA team" qa-team`
   (display name first, alias second); `firebase appdistribution:testers:add
   --group-alias qa-team a@example.com b@example.com` (space-separated, or
   `--file /path/to/testers.txt`). Limits: 500 testers per project, 200
   per group.
2. **Firebase Auth test users** control sign-in. The firebase CLI has no
   command for them — the only path is a scripted Admin SDK one-shot:
   [auth-test-users.md](references/auth-test-users.md).

## 3. Build

Gradle, per the PROFILE.md runner: `./gradlew assembleRelease` (APK) or
`./gradlew bundleRelease` (AAB — the same distribute command takes it).
Distribute the canonical-named artifact
`<app_name>-<sem_ver>-<code>-<slug>-<debug|release>.apk` (deliver's build
identity: unique versionCode from the shared ledger); the release notes
lead with the versionName (`<semver>-<slug>`) so testers see which build
and branch arrived.

- Signing: App Distribution accepts a debug-signed build, and for a small
  personal tester set that is the sanctioned fallback; a real
  `signingConfig` only when the ask says release-key build.
- The Firebase app's package name must equal `applicationId`
  (case-sensitive, immutable once registered).

## 4. Distribute

```
firebase appdistribution:distribute app-release.apk --app <APP_ID> \
    --groups qa-team --release-notes "<one line per shipped ticket>"
```

- Prefer `--groups` over `--testers` once more than one tester exists:
  group members get every release the group gets. Multi-line notes →
  `--release-notes-file`.
- Capture the three output links: `firebase_console_uri` (single release
  on the dashboard — this is the evidence), `testing_uri` (tester
  experience), `binary_download_uri` (direct download, expires after
  1 hour).

## 5. Test loop

- Who has which release: the console release page shows per-tester status
  (invited / accepted / downloaded). CLI roster:
  `firebase appdistribution:testers:list` (name, last activity, groups) —
  add a group alias to scope it; `firebase appdistribution:groups:list`
  shows tester and release counts per group.
- New tester mid-run: `appdistribution:testers:add --group-alias <group>
  <email>` — joining a group grants access to the group's releases
  (past ones included), no re-distribution needed.
- Invitations expire after 30 days; renew from the console tester-row
  drop-down. Builds stay on the dashboard 150 days.

## 6. Evidence

Done when: a release exists on the dashboard and its `firebase_console_uri`
is in hand; every tester named in the ask appears in
`appdistribution:testers:list`; Auth test users exist when the ask
includes sign-in accounts (record the emails). Hand `deliver` the
dashboard link and the tester list for the DoD check; the ledger line is
added there.

Read [auth-test-users.md](references/auth-test-users.md) when the app has
a login and testers need accounts. Read
[sources.md](references/sources.md) to re-verify any command or flag.

Fresh skill; every command grounded in the official Firebase docs cited in
references/sources.md.
