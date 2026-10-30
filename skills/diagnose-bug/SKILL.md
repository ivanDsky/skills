---
name: diagnose-bug
description: >-
  Diagnose a reported bug through an evidence ladder that spends the user's
  time last: one batch of assumption questions, then remote evidence from the
  user's own device (wireless adb, Crashlytics, user screenshots) before any
  emulator repro, and screen-recording frame analysis only as the last
  resort. Use when the user reports broken behavior, a crash, a visual glitch,
  or a test keeps failing for unclear reasons.
interaction: hitl
requires: []
---

# Diagnose a bug

The expensive mistake this skill exists to prevent: an agent screen-recording
an emulator and analyzing video frame by frame while the user waits 20 minutes
for a half-fix. Evidence is pulled toward the user's real device and toward
questions that take seconds to answer. Emulator repro is the last rung, and
frame-by-frame video analysis is below it.

## 1. Question batch first (one batch, intake format)

Before touching any device, send ONE batch (numbered, arrow defaults, "1-3 yes
4: text" answers it):

- Expected vs actual, in one line each.
- Always, or sometimes? If sometimes: after which action / on which data?
- Started after which change (ticket, commit, dependency, OS update)?
- A screenshot from your phone says more than a paragraph — ask for one
  (they can share it over the same channel as the build; see deploy-tailscale
  for the reverse path).
- What would you accept as fixed? (this becomes the fix's DoD)

The user was THERE when it broke - their answers eliminate more hypotheses
than ten shell commands. Only reproduce what remains unexplained.

## 2. Evidence ladder — cheapest first, emulator near the end

1. **User's answers + screenshot** (rung 0, from the batch).
2. **Crash + telemetry you already have**: Crashlytics dashboard (stack
   traces, breadcrumbs, affected users), existing analytics events around the
   reported action. Zero user time. If the project has no Crashlytics and the
   bug is a crash, adding it is the first fix ticket.
3. **Wireless adb to the user's physical device** - the user keeps testing on
   their phone; you read logs over Wi-Fi:
   - One-time pairing: Developer options -> Wireless debugging -> pair with
     code; `adb pair <phone-ip>:<pair-port>` (code prompt), then
     `adb connect <phone-ip>:<debug-port>`.
   - Then: `adb -s <device> logcat` filtered by package/tag;
     `adb bugreport bugreport.zip` (logs + dumps in one file) when the picture
     is murky.
   - Note in PROFILE.md so the next run skips discovery.
4. **Temporary in-app instrumentation** - when remote logs are too thin:
   add a debug-only event ring buffer (file or logcat tag) around the
   suspected path, ship a debug build via `deploy-tailscale`, have the user
   reproduce once, pull the log file back. Cheap, targeted, disposable.
5. **Emulator repro** - only for what rungs 1-4 cannot explain, typically
   only-input behaviors. Never as the first look.
6. **Screen recording + frame analysis** - LAST and with the user in the
   loop: ask the USER to record the phone (they see it live) and, if frame
   analysis is truly needed, to mark the moment ("it flickers right after the
   card leaves the stack"). An agent scrubbing unmarked video is the
   costliest path in the codebase.

## 3. Diagnose, then hand off

1. State the hypothesis in one line with the evidence that supports it and
   the evidence that ruled out the top alternative.
2. The fix becomes a ticket with the DoD from step 1 (the user's own
   acceptance test) and the evidence channel for verifying it
   (Crashlytics clean / logcat clean / user reproduces once more).
3. Confirm the fix through the same channel that reported it - user
   reproduces on their phone, not on the emulator.

Footer: authored for ivanDsky/skills; adb wireless debugging per
developer.android.com/studio/command-line/adb and
developer.android.com/studio/debug/wireless-debugging (verify pair/connect
flags against `adb --help` on first use).
