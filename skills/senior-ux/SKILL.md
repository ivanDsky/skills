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

Distilled from a reviewed session where this method produced a board
overhaul the user approved with corrections folded in — including what was
corrected.

## Judge with a framework, not vibes

A report like "numbers are hard to see" gets a senior question back: which
job is this pixel failing? Evaluation axis, outer to inner:

1. **Four human needs**: safety, understanding, achievement, joy.
2. **Seven lenses**, in order: perception → motor → cognitive → state →
   motion → accessibility → craft.
3. A **10-pass rubric**, each pass checkable on a preview matrix — not a
   mood-based walkthrough.

"Deeper, not bigger" is the direction of travel: a P0–P3 list of non-obvious
findings (magnetic trace-start capture; a deuteranopia clash where the halo
turns out to be an accessibility device; 1:1 drag with mid-gesture
interruptibility; computed label floors at n-max) beats more surfaces.

## Measure, don't eyeball

- User taste references ("feels like Duolingo") become **prototype axes**;
  the reference's shipped product gets **measured and cited** (dot = 0.60
  of cell, glyph ≈ 0.4 of dot, gridline 0.032–0.037 of pitch) before
  adopting its look.
- Design values are **computed**: WCAG contrast math (≥4.5:1 labels), 48dp
  targets, minimum sizes computed at the worst case (n-max board: dot 27dp,
  glyph ~10dp) — the legibility floor exists **before** the user has to say
  "I can't see the numbers".
- Values become **named tokens** ("zero ad-hoc colors"), and the floors
  become **JVM tests** — contrast bars as test assertions.

## Decide with the user's hardware, not argument

- Taste disputes get a **debug-only A/B switcher** on the user's device
  (3 typography × 3 palettes, user flips, verdict is final); losers and
  their bytes are deleted, no shims.
- The **variant matrix is the prototype**: real components across sizes ×
  states × themes, published to the review site so a remote user judges
  before implementation locks.
- Fix in the **shared layer** so every consumer inherits; one screen is the
  first consumer, not the scope.

## Policies, states, and truth

- Design decisions become **measurable policies, JVM-tested**: "two-pane
  requires Expanded width AND landscape; portrait is always single-pane";
  "board caps at ~480dp". Layout policy keys on width **and** orientation —
  width-class-only shipped two-pane on portrait tablets once.
- **Walk every state on a real device** before changing any — including the
  states that look broken but are correct ("No entries yet today" on Nov 1
  is by design). Every walk stop is green before work starts.
- **Error copy tells the truth about the cause**: "Check your connection"
  while the network demonstrably works is a UX defect in itself, ticketed
  like any other.
- **Motion**: minimal, tokenized, exit faster than enter (200ms in /
  140ms out, not 700ms defaults), justified per surface, reduced-motion
  fallbacks, previews stay resting-state. Delight is the beat, not
  particles.

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
