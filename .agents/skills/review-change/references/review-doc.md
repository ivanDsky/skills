# Visual review doc (REVIEW.md)

Produced at review verdict time so the user can review and give feedback
WITHOUT testing. Short on text, rich on visuals: the user should need under
two minutes and reply with artifact ids, not sentences.

## Location and shape

`.scratch/<slug>/review/REVIEW.md`, assets beside it in `review/assets/`.
Total prose <= ~20 lines. Every visual is numbered; text only explains what
the visual cannot show.

```markdown
# Review: <slug> — <one-line what changed>

## Screens
S1 <state caption>        ![s1](assets/s1.png)
S2 ...

## Motion
V1 <what the motion is; recorded from device>  ![v1](assets/v1.gif)
(no device reachable -> "motion needs your eyes: `deploy-tailscale` + look",
say so explicitly instead of a fake video)

## Architecture (only if structure changed)
D1 <one-line what to notice>  <diagram>

## Assumptions you may veto
A3, A7 from the spec - shown again, one line each.

## Feedback
Reply with ids: "S2: tighter padding - V1: spring too slow".
Each reply maps to a finding and re-enters the fix loop.
```

## Sourcing the visuals

- Screens: reuse the JVM screenshot-test captures (Roborazzi / AGP suites) -
  they already exist per state/size/dark; do not re-shoot on an emulator.
- Motion: `adb screenrecord` on the wireless-adb-connected device
  (pairing per diagnose-bug), converted to GIF/MP4. No device -> say motion
  is unverified and needs the user's eyes; never fake it.
- Architecture: archify diagram, or the project map excerpt.

## Feedback loop

User replies reference artifact ids. Each reply becomes a review finding
(graded like any finding) and re-enters the fix loop; UX feedback with no
nameable defect still lands as a finding with the id quoted. The doc is
regenerated after fixes: same ids, new assets, changed items marked
"(updated)".
