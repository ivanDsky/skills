---
name: deliver
description: >-
  Build the change and deploy to the PROFILE.md deploy targets — build-only,
  firebase, tailscale, or local — then attach the build/deploy output as
  evidence so the final tickets close. Owns build identity across parallel
  worktrees: a shared versionCode ledger (never below the device), branch
  slug in versionName and APK name. Use when review passes and the run is
  ready to ship, when the user says /deliver, "ship it", "wrap up the run",
  or "build and deploy", when a feature or prototype run needs its delivery
  summary, or when asked which build is on the device or about versionCode
  or APK-name collisions.
interaction: afk
requires: [firebase CLI when target=firebase, tailscale CLI when target=tailscale]
---

> **TL;DR** Builds the change and deploys to PROFILE.md targets with output attached as evidence; never reruns the suite; fires when review passes and the run ships.
> **Related**: skill://review-change (gate before delivery; owns the one suite run), skill://user-check (approved build; reuses build identity), skill://deploy-firebase (firebase target), skill://deploy-tailscale (tailscale target), skill://implement (tickets to close), skill://open-pr (land step when delivery = pr), skill://android-env (worktrees share the build ledger)

# Deliver

Produce the evidence that closes the run: a green build, a deploy when a
target is set, closed tickets, and an honest delivery summary. Review has
passed; this stage adds no code.

1. Verify the gate on the tree you ship — never rerun the suite. The ledger
   needs `user-check: ok` (or `skipped`) and `suite: green @ <sha>` from
   `review-change`, with `<sha>` equal to HEAD. HEAD moved since → back to
   `review-change` (it reruns the suite once); missing user check → back to
   `user-check`. Fixes go back through `implement` + `review-change`.

2. Pick the delivery mode, in precedence order (session override > project
   config > global defaults):
   - **Prototype run**: the ticket's `deploy:` flag decides. `main` = the
     project's deploy targets below, in listed order. `standalone` = a
     separate deploy that never touches the main target (own site, channel,
     or path). `none` = build-only.
   - **Feature run**: PROFILE.md `Deploy targets`, in listed order. Section
     empty or missing → deploy-target defaults from `~/.agents/AGENTS.md`
     (firebase / tailscale / local). Neither defines a target → build-only,
     and say so in the summary.

3. Build first, always. On Android, run the `android-env` checklist once
   before the first build (PATH, `local.properties`, stale-incremental
   triage) — deliver has no time to rediscover environment fixes. The
   `user-check` build is reused when its sha equals HEAD and the variant
   matches the target; `build_identity.py which` names it. Otherwise:
   - **Build identity before the build**, because parallel worktrees share
     one phone: `scripts/build_identity.py allocate`, per
     [Build identity](references/build-identity.md). It takes a unique
     versionCode from the ledger shared by all worktrees, never lower than
     what is on the device; versionName is `<semver>-<branch-slug>.<n>`
     (`1.3.0-reminders.2`, `n` = that branch's install count, `main.<n>` on
     main), so no two installs ever share a name. Gradle wiring missing → stop and ask for it to
     land on main first; never add it in a worktree.
   - Run the project build with its `$GRADLE_ARGS` and capture the log to
     `.scratch/<slug>/build.log`. A failed build stops everything — a
     deploy never starts on a red build.
   - Copy the artifact to `$APK_NAME`
     (`<app_name>-<version_name>-<code>-<debug|release>.apk`) before any
     deploy target touches it. Deploy targets and evidence lines reference
     that name, never Gradle's `app-<variant>.apk`.
   - Semver is NOT bumped by installs or by landing on main. Only a release
     the user asks for bumps it (minor by default, once for all its
     features), on main, then builds with `allocate --release` for the
     plain `1.4.0` name; see [Build identity](references/build-identity.md).

4. Deploy per target, in listed order. Mobile distribution has dedicated
   playbooks — dispatch, don't improvise: `firebase` target on an Android
   build -> `deploy-firebase` (test users, tester groups, APK/AAB
   distribution); `tailscale` target -> `deploy-tailscale` (device
   registry + APK sharing). Everything else follows the checklist in
   [Deploy targets](references/deploy-targets.md) (local run, web hosting).
   Decision rules:
   - Target CLI missing or not logged in → stop with the install pointer
     from the checklist. Never improvise a deploy path or swap in another
     target.
   - A failed target stops the list; later targets wait. Record the partial
     state as a ledger line.
   - Deploying over production or migrating data is a one-way door — name it
     in the summary.

5. DoD-final check, before any summary: every ticket's DoD is checkable
   against evidence in hand (command output, screenshot path, deploy
   output), and each spec success criterion has a green answer. Close each
   final ticket only now: set `status: closed`, append the evidence to its
   Resolution, add the ledger line. A ticket without evidence stays open,
   and the summary names it.

6. Write the user-facing report — `.scratch/<slug>/report/REPORT.md`, small
   (≈1 screen), so the user never reverse-engineers what happened:
   - **What changed & how**: per ticket, one or two sentences, behavior level.
   - **Screenshots**: embed the JVM capture images (`preview-compose`
     suites / check doc assets) — reuse existing captures, never re-shoot.
   - **User check**: the approved build name, its verdict line from the
     ledger (`user-check: ok <versionName> @ <sha>`), and the F-ids that
     changed the spec. Never re-list verify steps the user already ran.
   - **Architecture changes** (new/boundary-crossing modules, dependency
     direction): replace prose with a diagram via `archify` (the matching
     diagram type), linked inline, plus ≤5 bullets of high-level decisions.
   Read the referenced skills for their output formats; do not improvise a
   new report shape.

7. Land the change, per the run's delivery mode (PROFILE `## Delivery`
   `changes:`, or the session answer from start's plan; precedence
   session > project, default `ask` = start already asked):
   - `pr` → fire `open-pr` (one PR, or one per stack layer); its URL(s) and
     merged/open state go in the summary.
   - `main` → the commit(s) go to the default branch per the consent ledger
     (`commit+push to the project repo`); report the commit id.
   Neither bumps semver; that waits for a release (step 3).
   Missing delivery answer on a standalone run → ask once, never infer `main`.

8. Post the delivery summary — the run's last message, always this shape:

   - **Shipped**: one line per ticket, behavior only, no paths.
   - **Report**: path to `REPORT.md` (the user-facing evidence write-up).
     Publishing follows the run's review-site decision (start's plan; PROFILE.md
     `Review site publish:`): yes → run `review-site` and give the LAN URL;
     no → file path only.
   - **Evidence**: build log path, `suite.log` + its sha, deploy URL or
     output, closed ticket ids, and the check doc path
     (`.scratch/<slug>/review/REVIEW.md`) when one exists.
   - **Landed**: PR url + state, or the commit id on `main`.
   - **Test on the deploy target**: only when the target build differs from
     the one the user checked (release variant, new commits) — 1-3 checks,
     with the URL or start command. Same build → omit.
   - **Skipped**: what was deferred or left unbuilt.
   - **Residual risk**: what could break, one line.

Done when evidence exists, tickets are closed or named as blocked, and the
summary is posted. Standalone: same steps — read PROFILE.md first; no
PROFILE.md → build-only plus a one-line pointer to /start.

Adapted from obra/superpowers (`finishing-a-development-branch`) and mattpocock/skills (`pr`), MIT.
