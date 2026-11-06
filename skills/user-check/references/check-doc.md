# Check doc (REVIEW.md)

Read when a feature run reaches `user-check` step 3. The doc goes with the
build so the user knows what to try and can answer with ids, not sentences.
It is short on text and rich on visuals; reading it takes under two minutes,
and trying the build is the point.

## Location and shape

`.scratch/<slug>/review/REVIEW.md`, assets beside it in `review/assets/`.
The path is fixed, because `review-site` reads it from there. Total prose
≤ ~20 lines; every visual and step is numbered.

```markdown
# Check: <slug> — <one-line what changed>

Build: <versionName> (<APK_NAME> | LAN URL | demo command)
Open: <how — tailscale link, `adb shell am start …`, URL>

## Try these
T1 <entry point> → <action> → expect <result>
T2 ...            (2-4 steps; the ones the spec's success criteria name)

## Screens
S1 <state caption>        ![s1](assets/s1.png)

## Motion
V1 <what the motion is>   ![v1](assets/v1.gif)
(no device recording → "motion: try T2 and look"; never a fake video)

## Architecture (only if structure changed)
D1 <one-line what to notice>  <diagram>

## Assumptions you may veto
A3, A7 from the spec - one line each.

## Feedback
Reply `ok`, or by id: "T2: should open the list, not the detail - S1: too dense".
```

## Sourcing the visuals

- Screens: reuse the JVM screenshot-test captures (Roborazzi / AGP suites)
  that already exist. Never re-shoot on an emulator. None exist → drop the
  section; the build is the evidence.
- Motion: only when a recording already exists or the wireless-adb device
  is reachable (`adb screenrecord`, pairing per diagnose-bug). Otherwise say
  the user's eyes check it.
- Architecture: an archify diagram or the project-map excerpt.

## Feedback loop

Every reply becomes an F-id in `.scratch/<slug>/user-check.md`, quoting the
artifact id it refers to (`F2 ← T2`). Fast fixes follow `user-check` step 4.
After each round, regenerate the doc for the new build: same ids, new
assets, changed items marked "(updated)", and the build line naming the new
`versionName`. On `ok`, the doc stays as the record of what was approved;
the re-gate reads it.
