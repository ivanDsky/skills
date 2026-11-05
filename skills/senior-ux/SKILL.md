---
name: senior-ux
description: >-
  The questions a senior UX engineer asks about any product surface, plus
  the method that answers them: framework-judged pixels (not vibes),
  measured references, computed values as tested tokens, A/B decisions on
  the user's hardware. Use for UI/UX design or review work; knowledge
  skills (emil-design-eng, ui-ux-pro-max, apple-design) supply taste, this
  supplies method.
interaction: afk
---

> **TL;DR** Ask first (which need fails, which hat decides, will the next surface inherit this), then judge pixels on a framework, measure instead of eyeball, decide on the user's hardware, and serve evidence where the user is.
> **Related**: skill://senior-dev (the general questions), skill://review-change (review-ux enforcement), skill://micro-architecture (shared-layer fixes), skill://preview-compose (the variant matrix), skill://review-site (evidence where the user is), skill://prototype (throwaway variant pages before implementation locks)

# The questions (most important part)

1. **Which user need fails today, on which lens?** A change starts as a
   named failure on the framework below — never as "redesign the screen".
   No named failure → the deliverable is a deep review that finds one,
   deeper not bigger.
2. **Who decides this, and when do they see it?** Design parameters are
   picked by the USER on real hardware (A/B matrix, published for remote
   judgment) **before implementation locks** — the audited cost of
   skipping this: a full shipped-and-replaced rework.
3. **Will the next surface inherit this?** Fixes land in the shared layer
   as named tokens and tested policies (size caps, contrast bars as tests,
   a shared motion vocabulary) — if the second surface can't reuse it, it
   was decoration, not design.
4. **Am I copying their identity or their craft?** A reference is measured
   for craft (proportions, weights — numbers, not adjectives); its product
   identity (social loops, brand choices) is refused with reasons.

# The method

- **Framework, not vibes**: four human needs (safety, understanding,
  achievement, joy) × seven lenses (perception → motor → cognitive →
  state → motion → accessibility → craft) × a 10-pass rubric, each pass
  checkable on a preview matrix. "Numbers are hard to see" → which of the
  seven jobs is this pixel failing?
- **Measure, don't eyeball**: WCAG math (≥4.5:1), 48dp targets, minimum
  sizes computed at the content's worst case (densest state, longest
  label) — the floor exists before the user has to say "I can't see it".
  Values become named tokens; floors become tests.
- **Decide on hardware**: debug-only A/B switcher (user flips, verdict is
  final, losers deleted); walk every state on the device before changing
  any — including states that look wrong but are correct. Before any app
  code exists, the switcher is a `prototype` page served to the phone.
- **Policies, tested**: "two-pane requires large width AND landscape";
  "content caps at a readable maximum". Layout keys on size AND
  orientation. Error copy tells the truth about the cause. Motion: exit
  faster than enter, tokenized, reduced-motion fallbacks.

## HITL gates (stop and ask)

- Parameters/variant choice before implementation locks (the A/B verdict is
  the user's, always).
- Every design decision that shapes the feature (the P-list priorities,
  refused references, policy thresholds) — confirmed, not assumed.
