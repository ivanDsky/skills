# Visual gate and feedback rounds

Read when `user-check` step 1 meets a UI change (any golden PNG changed), and
when step 4 receives layout, spacing or motion feedback. The user's device is
the slowest oracle in the chain; everything a script or the orchestrator's own
eyes can see happens before the APK leaves.

## Run the gate

```bash
python3 skills/user-check/scripts/visual_gate.py --out .scratch/<slug>/gate \
  [--pairs .scratch/<slug>/gate/pairs.tsv] \
  $(git diff --name-only --diff-filter=AM <base>...HEAD -- '*.png')
```

(installed globally: the skill's installed script path.) Python stdlib only,
offline, about a second. Inputs:

- Changed goldens as arguments. Each golden's own directory is also scanned:
  a changed golden that is byte-identical to an unchanged sibling is a
  duplicate. `--existing <dir>` adds more directories.
- `--pairs`: two tab-separated columns, `golden_png`, `reference_png`
  (reference may be empty; a `golden_png` header row is skipped). With a
  contract (`.scratch/<slug>/contract/`), one row per UI ticket
  `Reference:` line: the golden path or test name's PNG, then
  `contract/reference/<screen>__<state>__<phone|tablet>__<light|dark>.png`.
  Paths resolve against the cwd, then the TSV's directory.
- Name conventions the grouping reads: `compact|phone|pixel` is phone,
  `expanded|medium|tablet` is tablet, `light|dark` the theme, the rest is
  screen and state. Mid-animation frames: `frame<N>`, `frame-<N>` or
  `t<N>ms` in the stem; the gallery lays them out as an ordered strip.

Output: `<out>/index.html` (golden, reference and a pixel-diff image per
pair; phone and tablet, light and dark grouped per screen and state), and the
last stdout lines
`visual-gate: N goldens, D duplicates, M missing reference, P pairs` plus the
serve command. Exit 1 on a byte-identical duplicate or a pair whose golden is
missing. A missing reference only counts into M; no contract, no `--pairs`.

## Read the gallery yourself

Serve it per `review-site` § 3 (`--directory <out>`), then open the pages:

1. Fix every blocking line (duplicates, missing goldens), rerun until exit 0.
2. Per screen: phone and tablet both present? Light and dark both? A
   one-form group is flagged; capture the missing one or say why not.
3. Per pair: read the diff image. Red outside what the ticket changed is a
   regression; a golden that differs from its reference without a recorded
   ruling is a finding. Size mismatch means no pixel diff; compare by eye.
4. Frame strips: the motion goes through the states the ticket says, in order.
5. Tell the user nothing yet. Fix, rerun, then send one link.

## What PNGs cannot show

Touch targets under 48dp and text overflow are not readable from pixels, and
the gate never guesses them. It lists them as a required Compose check: a
semantics-based JVM test in the module tests asserting every clickable node's
touch bounds are at least 48dp on both axes and that text does not overflow
at the widest font scale (`tdd` references/android-testing.md rung 2;
component previews: `preview-compose`). The test missing or red counts as a
blocking finding; the APK waits.

## One link with the APK

After the gate is green the user gets one message (the step 3 form): build
name, the gallery link (the long-lived server, tailnet URL first, LAN second,
curl-checked per `prototype` § 3 Serve), and the verify steps. The gallery is
the visual evidence; the build is for feel.

## Feedback rounds (step 4)

**Batch.** The user's reply to the check form is the whole round; never
wait for more items. Number every point `F1…` before dispatching anything,
then widen each instance-level point to its class on the same surface and
gallery (one 43dp target means check all targets in the screen). One
implementer takes the whole batch in one go.

**Prototype first.** An F-item that changes layout, spacing or motion is not
a fast fix yet:

1. Static layout and spacing: a prototype round (`prototype`), served, the
   candidate values on screen at phone and tablet sizes.
2. Motion HTML cannot prove (spring feel, timing, reveal choreography):
   a playground screen in the app's dev settings (`wire-dev-settings`) with
   the values adjustable live on the tablet.
3. The user confirms there. Record the numbers in `.scratch/<slug>/user-check.md`
   (`F2 tuning: <values>, confirmed on <prototype URL | playground>`) and
   write them into the `motion.md` of the contract when one exists.
4. Only then the fast fix applies the confirmed values. Never guess them in
   code and rebuild.

Colors, copy, wiring and plain bug fixes skip the prototype and go straight
to the fast fix.
