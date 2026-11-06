---
name: user-check
description: >-
  Put the implemented change in the user's hands before any review, loop on
  their hands-on feedback with fast fixes that ignore code quality, then on
  their OK re-gate the run at design level (spec vs feedback vs code,
  senior-dev and architecture checks) into hardening tickets. Use when
  implement finishes, when a quick task's code is written, when the user says
  "let me try it first", "send me the build" or "I want to check it on my
  phone", or gives feedback on a running change.
interaction: hitl
requires: []
---

> **TL;DR** Hands the finished change to the user to try before review, loops on their feedback with fast fixes, then on OK re-gates the run (spec vs feedback vs code, senior-dev + architecture) into hardening tickets; fires after implement.
> **Related**: skill://implement (upstream; runs fast fixes and hardening tickets), skill://review-change (fires after hardening), skill://deliver (owns build identity; reuses this build), skill://deploy-tailscale (device install), skill://web-env (LAN dev server), skill://senior-dev (re-gate questions), skill://micro-architecture (re-gate file split), skill://design-architecture (re-gate dependency rules), skill://write-tickets (hardening tickets), skill://review-site (publishes the check doc), skill://assess-teardown (stuck feedback loop)

# User check

The user can only say what is wrong once they hold the thing. So the change
reaches their hands before review, a test suite or a PR body. While they test,
speed matters more than code quality. When they say OK, the run goes back to
design level and pays the debt down properly. One check per run (the whole
epic), not per ticket.

```
implement ─> build ─> user tries ─┬─ feedback ─> fast fix ─> build ...
                                  └─ OK ─> re-gate ─> hardening tickets ─> implement ─> review-change
```

## 1. Gate in (cheap)

The change compiles, plus the touched module's existing tests. Do not run the
full suite, a reviewer or `structure:` here; they run after the OK.

## 2. Put it in their hands

- **Android**: build identity from `deliver`
  (`deliver`/references/build-identity.md): `allocate`, build with
  `$GRADLE_ARGS`, copy to `$APK_NAME`, log to `.scratch/<slug>/build.log`.
  Install via the PROFILE `tailscale` target (`deploy-tailscale`) or
  `adb install -r`. Confirm with `build_identity.py which`. Environment
  friction → `android-env` checklist.
- **Web**: dev server on the LAN URL (`web-env`).
- **No runtime** (library, docs, skills repo): diff summary plus one demo
  command's real output.

## 3. Ask once, then stop

One message: build name (`versionName`), how to open it, 2–4 numbered verify
steps with exact entry points (deep link, `adb shell am start`, tap path) and
the expected result of each, the vetoable spec assumptions, then
"reply `ok`, or feedback by id". Feature runs also write
`.scratch/<slug>/review/REVIEW.md` per
[check-doc.md](references/check-doc.md) and publish it via `review-site` when
the run's publish decision is yes. Quick tasks get the message only. Wait for
the answer; never continue on silence.

## 4. Feedback → fast fix → step 1

- Number every point (`F1`, `F2`, …) in `.scratch/<slug>/user-check.md` with
  the build it was given against, quoted in the user's words.
- One implementer applies them **fast**: smallest change that does what the
  user asked, no tests, no refactor, no structure work. Still never cut
  validation, security, accessibility or data-loss handling. Commits are
  `fast(F2): <what>`; the ledger gets `fast-fix: F2 @ <sha>`. Stacked run →
  each fix commits into the layer that owns the file (`open-pr`/references/stacks.md).
- A point that contradicts the spec or a ticket is still done — the user
  outranks the spec. Record it as `Ruling: F3 overrides A4 — <why>`.
- Rebuild and hand back (steps 1–3); the message lists which ids changed.
- The same surface failing two rounds → `assess-teardown` before round 3.

## 5. OK → re-gate (designer hat, fresh context)

Ledger `user-check: ok <versionName> @ <sha>`. That build's behavior is now
the acceptance baseline. Then go back to design level, because the fast
rounds skipped it. Write the result to `.scratch/<slug>/regate.md`:

1. **Reconcile** — one row per F-id: what the user asked, what the code does
   now, which spec assumption or criterion it changes. Amend `spec.md` (new
   criteria with F-ids, overridden assumptions struck through). Then check
   the other direction: every spec criterion is still met or explicitly
   dropped by an F-id. Quick task (no spec): reconcile against the ask.
2. **Design check** over `git diff <base>...HEAD`, fast commits first:
   `senior-dev` questions; file split and patterns per `micro-architecture`;
   dependency direction per `design-architecture`'s
   `rules-architecture.md`; component API of public composables per
   `micro-architecture`/references/ui-components.md at the ledgered
   `ui-tier`; PROFILE `structure:` on Kotlin diffs; UI per `senior-ux`.
   Each finding names the file and the rule it breaks.
3. **Hardening tickets** via `write-tickets`: one per finding cluster, plus
   one that pins the baseline. That ticket turns the verify steps and every
   F-id into persisted tests, each watched failing by temporarily reverting
   the behavior it guards. Every hardening ticket's DoD includes "approved
   behavior unchanged".
4. Fire `implement` on the hardening tickets (TDD), then `review-change`.
   Quick task: no tracker and no hardening run; the findings stay in
   `regate.md` and `review-change` fixes them with the tests.

## Decision rules

- Hardening that must change approved behavior → stop. Back to step 2 with
  the delta named; never silently.
- A review fix that changes behavior the verify steps exercise comes back
  here for a short re-check. Refactor-only and test-only fixes do not.
- Nothing to hold (pure refactor, no behavior change) → skip this skill and
  ledger `user-check: skipped — no behavior change`.
- The user asks for code review before trying it → honor it. Ledger the skip
  and run `review-change`.

Fresh skill, written for this repo's chain; no text adapted from elsewhere.
