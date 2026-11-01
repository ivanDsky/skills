---
name: senior-ux
description: >-
  How a senior UX engineer actually works a product surface — judge pixels
  against a framework instead of vibes, settle taste disputes with A/B
  prototypes on the user's hardware, compute design values as named tokens
  with test-enforced floors, walk every state before changing one, refuse
  with reasons. Use for any UI/UX design or review work on product
  surfaces, alongside the knowledge skills (emil-design-eng,
  ui-ux-pro-max, apple-design) which supply taste; this supplies method.
interaction: afk
---

> **TL;DR** A senior judgment framework: which of the seven jobs is this pixel failing → measure the reference → A/B on real hardware → tokens and JVM-tested policies → walk every state → publish evidence where the user is → deeper, not bigger.
> **Related**: skill://review-change (review-ux checks this enforces), skill://micro-architecture (fix in the shared layer so all consumers inherit), skill://senior-dev (general judgment defaults), skill://preview-compose (the variant matrix is the prototype), skill://review-site (evidence served where the user is)

# Senior UX engineering method

Distilled from reviewed product-surface work where this method produced
approvals with corrections folded in — including what was corrected.
Examples are generic; any product surface (screen, page, view) applies.

## Judge with a framework, not vibes

A report like "the numbers are hard to see" gets a senior question back:
which job is this pixel failing? Evaluation axis, outer to inner:

1. **Four human needs**: safety, understanding, achievement, joy.
2. **Seven lenses**, in order: perception → motor → cognitive → state →
   motion → accessibility → craft.
3. A **10-pass rubric**, each pass checkable on a preview matrix — not a
   mood-based walkthrough.

"Deeper, not bigger" is the direction of travel: a P0–P3 list of non-obvious
findings (magnetic gesture-start capture; a color clash where the halo
turns out to be an accessibility device; 1:1 drag with mid-gesture
interruptibility; computed minimum sizes at the content's worst case)
beats more surfaces.

## Measure, don't eyeball

- User taste references ("feels like <app X>") become **prototype axes**;
  the reference's shipped product gets **measured and cited** (proportions,
  sizes, weights — numbers, not adjectives) before adopting its look.
- Design values are **computed**: WCAG contrast math (≥4.5:1 labels), 48dp
  targets, minimum sizes computed at the content's maximum (the densest
  state, the longest label) — the legibility floor exists **before** the
  user has to say "I can't see it".
- Values become **named tokens** ("zero ad-hoc colors"), and the floors
  become **tests** — contrast bars as test assertions.

## Decide with the user's hardware, not argument

- Taste disputes get a **debug-only A/B switcher** on the user's device
  (e.g. 3 typography × 3 palettes; user flips, verdict is final); losers
  and their bytes are deleted, no shims.
- The **variant matrix is the prototype**: real components across sizes ×
  states × themes, published to the review site so a remote user judges
  before implementation locks.
- Fix in the **shared layer** so every consumer inherits; one screen is the
  first consumer, not the scope.

## Policies, states, and truth

- Design decisions become **measurable policies, tested**: "two-pane
  requires large width AND landscape; portrait is always single-pane";
  "content caps at a readable maximum". Layout policy keys on size **and**
  orientation — width-class-only layouts break on large portrait screens.
- **Walk every state on a real device** before changing any — including the
  states that look broken but are correct ("No entries yet" on day one is
  by design). Every walk stop is green before work starts.
- **Error copy tells the truth about the cause**: "Check your connection"
  while the network demonstrably works is a UX defect in itself, ticketed
  like any other.
- **Motion**: minimal, tokenized, exit faster than enter (e.g. 200ms in /
  140ms out, not 700ms defaults), justified per surface, reduced-motion
  fallbacks, previews stay resting-state. Delight is the beat, not
  particles.

## Ask what a senior asks

Before designing or judging a surface, the questions come first:

- **Why is this change required — what user need fails today?** A change
  starts as a named failure on the evaluation framework (which of the seven
  jobs is this pixel failing), not as "redesign the screen". No named
  failure → the first deliverable is the deep review that finds one,
  deeper not bigger.
- **Which hat is this?** Designer, reviewer, and implementer are different
  hats. The designer picks parameters before implementation locks (the
  variant matrix exists for exactly that); the reviewer judges against the
  framework, never grades its own design; the implementer builds the locked
  decision. Announce the hat; don't let one hat silently do another's job
  (the audited "all done" → full rework shipped because the implementer
  never handed the design to the user's eyes).
- **Will this make the next surface easier to build?** The forward test:
  fixes land in the shared layer as named tokens and tested policies so
  every future screen inherits them (a size cap, contrast bars as tests, a
  shared motion vocabulary) — not as one-off values tuned into a single
  screen. If the second surface can't reuse it, it was decoration, not
  design.

## Refuse, integrate, serve

- **Refuse with reasons**: a reference's social loop (streak/percentile
  carousels), imitation of features the product deliberately diverges on
  (dark-first as the differentiator), decorative libraries. A senior pushes
  back in the spec, not after the build.
- **Integrate the user's domain expertise** as prioritized follow-ups —
  their idea ("breathing n+1 circle") enters the P-list, their rulings
  ("drop TalkBack for now") get recorded, nothing relitigated.
- **Serve evidence where the user actually is**: wave reports, diagrams,
  and the variant matrix as HTML on the LAN review site; builds land on the
  device. And the evidence channel meets the product's own bar — a review
  page that breaks in dark mode is itself a defect (observed and fixed).

## Anti-patterns (all observed and corrected in-session)

- Dispatching work because the user answered questions — **approval is
  explicit per gate**, never inferred.
- Decorative previews that violate the product's own rules (a
  visit-every-cell game whose preview shows skipped cells must be
  rule-true even when illustrative).
- Legibility floors invented after user complaint instead of computed
  up front.
- Two agents sharing one file instead of pre-split ownership — parallelism
  is bought by disjoint files, never by sharing (micro-architecture).
