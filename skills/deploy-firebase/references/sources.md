# Sources

Every CLI command, flag, and API call in this skill, traced to an official
source (fetched 2026-10-30).

| Fact in this skill | Source |
|---|---|
| `appdistribution:distribute <binary>` and its options table: `--app` (required, the App ID from Project settings → General), `--release-notes` / `--release-notes-file`, `--testers` / `--testers-file` (comma-separated), `--groups` / `--groups-file` (group aliases), `--debug`, `--token` | https://firebase.google.com/docs/app-distribution/android/distribute-cli |
| Output links `firebase_console_uri`, `testing_uri`, `binary_download_uri` (expires after one hour) | https://firebase.google.com/docs/app-distribution/android/distribute-cli |
| "You must sign the APK with your debug key or app signing key" (debug-signing fallback) | https://firebase.google.com/docs/app-distribution/android/distribute-cli (Step 1) |
| Package name must match the registered app; case-sensitive, immutable | https://firebase.google.com/docs/app-distribution/android/distribute-cli (Before you begin) |
| Releases available 150 days; testers have 30 days to accept an invitation; renewal via the drop-down menu on the tester row | https://firebase.google.com/docs/app-distribution/android/distribute-cli (Next steps section) |
| `testers:add` / `testers:remove` take space-separated emails or `--file`; `--group-alias` scopes them to a group | https://firebase.google.com/docs/app-distribution/android/distribute-cli (Manage testers and groups) |
| Command set: `appdistribution:testers:add/remove/list`, `appdistribution:groups:create/delete/list`, `appdistribution:distribute --app` | https://firebase.google.com/docs/cli (App Distribution commands table) |
| `groups:create <displayName> [alias]` — display name first, alias second; singular `group:create` is a legacy alias, same command | https://github.com/firebase/firebase-tools/blob/master/src/commands/appdistribution-groups-create.ts |
| `testers:add [emails...]` options: `--file`, `--group-alias` | https://github.com/firebase/firebase-tools/blob/master/src/commands/appdistribution-testers-add.ts |
| `distribute` accepts `.apk` and `.aab` binaries (anything else errors) | https://github.com/firebase/firebase-tools/blob/master/src/appdistribution/distribution.ts |
| No `appdistribution:get-latest-release` CLI command exists; latest-release status lives in the console release page | command lists in both rows above |
| Console path "Testers & Groups tab of the App Distribution page"; limits 500 testers/project, 200/group; group members gain access to all releases distributed to that group | https://firebase.google.com/docs/app-distribution/manage-testers |
| `getAuth().createUser({email, password, displayName, emailVerified, ...})`; `getUserByEmail` rejects with `auth/user-not-found` | https://firebase.google.com/docs/auth/admin/manage-users |
| `npm install firebase-admin`; `initializeApp()` from `firebase-admin/app`; `GOOGLE_APPLICATION_CREDENTIALS`; service-account key generation steps | https://firebase.google.com/docs/admin/setup |

The firebase.google.com CLI reference and the distribute guide disagree on
spelling (`groups:create` vs `group:create`) — resolved by the
firebase-tools source: both are accepted; this skill uses the canonical
plural form.
