---
name: deliver
description: >-
  Build the change and deploy to the PROFILE.md deploy targets — build-only,
  firebase, tailscale, or local — then attach the build/deploy output as
  evidence so the final tickets close. Use when review passes and the run is
  ready to ship, when the user says /deliver, "ship it", "wrap up the run",
  or "build and deploy", or when a feature or prototype run needs its
  delivery summary.
interaction: afk
requires: [firebase CLI when target=firebase, tailscale CLI when target=tailscale]
---

# Deliver

Produce the evidence that closes the run: a green build, a deploy when a
target is set, closed tickets, and an honest delivery summary. Review has
passed; this stage adds no code.

1. Verify green on the tree you ship. Run the PROFILE.md test runner once
   more — a green run from earlier proves only the tree it ran on. A failure
   stops delivery: report it and stop; fixes go back through
   `implement` + `review-change`.

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

3. Build first, always. Run the project build and capture the log to
   `.scratch/<slug>/build.log`. A failed build stops everything — a deploy
   never starts on a red build.

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

6. Post the delivery summary — the run's last message, always this shape:

   - **Shipped**: one line per ticket, behavior only, no paths.
   - **Evidence**: build log path, deploy URL or output, closed ticket ids.
   - **Test on the deploy target**: 1-3 checks to do by hand, with the URL
     or start command.
   - **Skipped**: what was deferred or left unbuilt.
   - **Residual risk**: what could break, one line.

Done when evidence exists, tickets are closed or named as blocked, and the
summary is posted. Standalone: same steps — read PROFILE.md first; no
PROFILE.md → build-only plus a one-line pointer to /start.

Adapted from obra/superpowers (`finishing-a-development-branch`) and mattpocock/skills (`pr`), MIT.
