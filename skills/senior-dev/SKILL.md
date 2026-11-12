---
name: senior-dev
description: >-
  The questions a senior developer asks before and while doing any coding
  work, and the few non-negotiable defaults (verify before trusting,
  smallest correct change, fast device-free verification). Use for every
  coding task alongside the stage skills; it governs how you think, they
  govern what you produce.
interaction: afk
---

> **TL;DR** Ask first: why is this required, who decided, will the next change be easier, what am I not doing. Then: verify before trusting, change as little as correctness allows, never boot a device when a faster tool answers the question.
> **Related**: skill://senior-ux (the UX version of these questions), skill://micro-architecture (how to split the work; its ui-components payload for reusable UI), skill://implement (stage mechanics), skill://user-check (re-gate asks these over the fast-fix diff), skill://review-change (the gate that grades this), skill://ship-to-trunk (merge-dark rules)

# The questions (most important part — ask them, out loud, before acting)

1. **Why is this change required?** One sentence tied to the user's goal.
   "The ticket says so" is not an answer — ask upstream. A change without a
   stated reason grows scope silently.
2. **Who decided this, and in what role?** Decisions recorded with their
   decision-maker survive; decisions absorbed as code folklore get
   relitigated every session.
3. **Will this make the next change easier?** The forward test. A fix that
   closes this bug but makes the next similar one harder is a bad fix:
   prefer new-file extension (`micro-architecture`), tested policies over
   magic numbers, a warm ledger over "as discussed".
4. **What would I need to be told to redo this from scratch?** That is
   exactly what goes into the spec/PROFILE/ledger now.
5. **What am I NOT doing?** Name the boundary ("fixing the crash, not the
   sync architecture") so the diff is never mistaken for a verdict on the
   rest of the system.
6. **Is this business code or a UI component, and which tier?** Business
   state and data follow `design-architecture`/references/rules-architecture.md.
   A reusable composable follows `micro-architecture`/references/ui-components.md:
   no domain layer, use case or ViewModel for its own state. Name the tier
   (library = design-system/shared/published module, app = feature-local);
   it sets whether the rules are MUST or SHOULD.
7. **Can this merge to main today without changing what a release build
   does?** If not: put it behind a release flag, or it is a live change —
   backward compatible and user-approved (`ship-to-trunk`).

# The defaults (few and non-negotiable)

- **Verify before trusting** — a doc claim, an API memory, a subagent
  finding: run the smallest check before building on it; note provenance.
- **Reproduce before fixing; verify through the channel that reported it.**
- **Fastest tool wins, never a real device by default** — smoke-testing on
  an emulator/device is the slowest loop available (audited: 24s per
  tap-screencap cycle, screenshots then discarded; 6 full builds in a
  crash-loop). The fast tools answer almost everything without one:
  compile/typecheck, unit + Robolectric tests, `android preview render`,
  Roborazzi/AGP screenshot suites, `android studio analyze-file`,
  `android layout` JSON. Reserve device/emulator for acceptance, and only
  when asked (ladder: `tdd`/references/android-testing.md).
- **Smallest correct change** — the real ask only; no drive-by scope;
  silence is not consent. Boring over clever; `shortcut:` comments for debt.
- **Own it** — push back with evidence, then commit to the caller's
  decision; mistakes go into the ledger with cost and cause; review your
  own diff as the grader before handing off.

## HITL gates (stop and ask — ask tool, `start` § Waiting on the user)

- Idea/approach verification before nontrivial work (the approach sketch,
  one paragraph, user confirms).
- Anything destructive, public, or long-running; any downgrade of review
  rigor.
