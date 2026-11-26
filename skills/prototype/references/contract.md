# Prototype loop (chain stage)

All taste decisions for a redesign happen up front on served pages, looping
with the user until they say it is right. The frozen result is the contract
the build implements and the gate checks against, so the build runs AFK and
`user-check` confirms instead of discovering design. Read this when `start`'s
redesign check routes work here: a feature after spec and before tickets, or
a bug or quick fix before any code.

## When it applies

- Applies: the work adds a screen, redesigns one (layout, hierarchy, flow,
  navigation placement, phone/tablet adaptation), or adds motion, and no
  approved prototype or contract already fixes the look. The user often
  does not know a fix needs a redesign: `start` decides from the evidence (a
  bug whose root cause is the layout or flow itself, a fix that cannot land
  without moving or adding UI), says so in one line, and asks "Prototype
  first? ➡️ yes".
- Skips, no question: no visible design change (logic, data, infra,
  refactor), small UI fixes (spacing, copy, colour on an existing screen),
  the fixes-batch path. A `user-check` layout or motion F-item follows
  `user-check`'s own rule.
- Close call → ask the question; the user's "no" costs one word, a missed
  redesign costs a rebuild. The answer is a `Decision: prototype <slug> —
  yes|no` ledger line.

## Before the first round

1. Inventory from the spec (a bug or quick fix: from the ticket and the
   screens it touches): every screen × state (default, empty, loading,
   error, longest content, plus feature states) × phone and tablet, light
   and dark where dark changes layout or contrast rather than only colour
   tokens. Every motion: trigger, what moves, enter and exit.
2. Paste PROFILE `## Taste rules` and the `Decision:` lines in scope into
   every page brief; a page that breaks a taste rule is fixed before the
   user sees it, never shown to be rejected.
3. Open design questions the spec left (the user has not picked a
   direction) → one exploration round per `prototype` §§ 1-3: variants,
   screenshot-free, picked by the user. No open question → straight to the
   contract pages; most UI features need zero or one exploration round.

## Contract pages

One page per screen (`<NN>-<screen>.html`, one subagent each with the page
brief at `Kind: contract`) plus `motion.html`, all in
`.scratch/<slug>/prototype/`, built to the page brief plus:

- **Real layouts at both sizes**: no fixed phone frame. Layout follows the
  app's breakpoints (Compose window size classes: compact < 600 dp, medium
  600-839 dp, expanded ≥ 840 dp); the tablet frame is designed, not the
  phone layout stretched.
- **Addressable frames**: `?s=<state>` picks the state, `?theme=light|dark`
  the theme, `?frame=1` hides the header strip and switcher so a capture
  shows the screen alone.
- **`frames.tsv`**, written by the parent from the inventory: one row per
  screen × state (columns `screen`, `state`, `page`, `themes`; kebab-case
  names). It drives the index page and the capture script.
- **Index page** (parent): every frame as a phone-width and a tablet-width
  iframe labelled with its frame id, the reference file stem
  (`results__empty__tablet__dark`), so the user names frames in one answer
  and the same id runs through acceptance, tickets and the gate.
- **Motion page**: one replay button per motion, its values (duration,
  easing or spring stiffness and damping, delay, stagger) shown and
  adjustable with sliders, reduced-motion variant one tap away. Motion named
  with `animation-vocabulary` terms.

Motion HTML cannot prove (springs and gesture-driven motion, shared-element
transitions, haptics, frame rate on the device, anything Compose renders
differently) → a debug-only playground screen on the tablet with sliders
for the same values (`wire-dev-settings`, playground and prototype screens).
It is one quick-task port built and installed before the first round, so
the loop still costs one build.

## The loop

Each user round: serve and check every URL (`prototype` § 3 Serve), then one
ask-tool form (`start` § Waiting on the user): the index URL, the motion URL
(and the playground route when built), one free-text question "every frame
OK, or list `<frame id>: <note>` — or say what still feels off", plus at
most four rulings the user must pick (variant choices, an empty-state
policy). Never preselect a variant. Each answer becomes a `Decision:
<screen> — <rule>` ledger line the same turn; a rejection that generalizes
becomes a PROFILE `## Taste rules` line (`start` § Decisions and waiting).

Route the reply:

| Reply | Next |
|---|---|
| Every frame OK, "perfect", "let's go", "out of the loop" | Freeze. No lens round. |
| First round, nameable notes only | One revision pass covering every note, re-serve, next user round listing only the changed frames. |
| Something still feels off: a note on a frame already revised, a second not-OK round, or "off" the user cannot name | Revision of the named notes, then a lens round, then the next user round. |
| "Lens feedback is irrelevant" | Restore `prototype/pre-lens/`, keep only the user-note fixes, freeze. |

Lens round: copy the pages to `.scratch/<slug>/prototype/pre-lens/`, then
run `goldfish-review` stage P on the served prototype with the user's
verbatim notes. Every finding with evidence is fixed in the pages; a
finding that contradicts a user `Decision:` line is dropped, never applied.
The next user form lists each lens-driven change in one line under the
notes it answers, so the user can judge them. Two lens rounds and the same
frame still off → one ask with two options: freeze the closest version with
the note as a `Decision:`, or rethink the screen (`senior-ux` question 1).
The user ends the loop; the agent never freezes on its own judgment.

## Freeze

The loop's exit freezes the contract. Write
`.scratch/<slug>/contract/`:

- `reference/<screen>__<state>__<phone|tablet>__<light|dark>.png`,
  captured from the approved pages, never redrawn:
  `python3 <prototype skill>/scripts/capture_reference.py --base-url
  <served prototype URL> --frames .scratch/<slug>/prototype/frames.tsv
  --out .scratch/<slug>/contract/reference`
  (phone 412×915 and tablet 1280×800 by default; `--viewport` and `--scale`
  match the project's golden devices when PROFILE names them). Exit 0 =
  every PNG present at its size; then open one phone and one tablet PNG to
  confirm they show the screen, not a blank or the switcher. This is the
  only screenshot step in the prototype skill: exploration rounds stay
  screenshot-free.
- `acceptance.md`: one checkable line per screen × state, naming the
  reference file and what must hold
  (`- results / empty: one-line hint above the fold, no illustration —
  reference/results__empty__tablet__light.png`).
- `motion.md`: per motion, its name, trigger, values, reduced-motion
  behavior, and where they were confirmed (`prototype` or `playground`).
- `contract.md`: the served prototype URL, the freeze date, the `Decision:`
  lines of the loop verbatim, each lens round's changes, and the taste
  rules applied.

Then ledger `Decision: contract <slug> — frozen <date>`, send the milestone
digest (`start` § Waiting on the user), and hand off: a feature to
`write-tickets`, which carries the `Contract:` and `Reference:` lines into
each UI ticket; a bug or quick fix to its fix ticket, which gains the same
two lines.

## After freeze — AFK

- No taste asks until `user-check`. An unknown the contract does not answer
  takes the nearest ruling in `contract.md`, else the reversible default,
  ledgered `assumed: <decision> — <ruling or default>` (`start` § Waiting on
  the user). The milestone digest lists them.
- Workers implement to the `Reference:` pairs (`implement` § 3).
- Fidelity review: the slice reviewer gets each pair (golden PNG path,
  reference PNG path) and the ticket's `acceptance.md` lines, opens both
  images, and fails visible drift: layout or hierarchy, alignment, spacing
  rhythm, text that wraps or truncates differently, missing or extra
  elements, a colour role swapped, tablet showing the phone layout. Not
  drift: font antialiasing, real data in place of fake data, platform
  chrome. A motion slice is checked against `motion.md` values in code.
- `user-check` confirms the build against the contract (`user-check` owns
  that step); the try-it message names the acceptance list.

## Changing a frozen contract

Only the user changes it. Their correction is a new `Decision: <screen> —
<rule> (supersedes <old>)`; update the page, re-capture just that screen
(`capture_reference.py … --only <screen>`), edit its `acceptance.md` lines,
and the tickets carrying those references reopen. A worker or reviewer that
thinks a reference is wrong reports it as a concern; it never edits the
contract.
