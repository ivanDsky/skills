---
name: review-change
description: >-
  Run the effort-tiered review gate over the change — scripted checks plus
  screenshots, then code review, then a dual-verdict fresh-context subagent —
  and own the fix loop, the ledger, and the teardown escalation. Use after
  implementation and before deliver, when a finished diff or branch needs its
  review gate, or when the user says review the change, run the review gate,
  or check this before shipping.
interaction: afk
requires: []
---

> **TL;DR** Runs the effort-tiered review gate — scripted checks, screenshots, code review, dual-verdict subagent — and owns the fix loop; fires before deliver.
> **Related**: skill://implement (upstream tickets), skill://deliver (downstream ship), skill://assess-teardown (teardown escalation), skill://scope-creep-detector (drift catch)

# Review change

Run the review gate over the whole change, then own what follows: fix rounds,
the ledger, and the teardown escalation. Findings and verdicts live in a file;
chat carries only the user-facing report.

1. Pin the inputs: the diff vs base (`git diff <base>...HEAD` — verify the base
   resolves and the diff is non-empty before dispatching anything), the spec
   (numbered assumptions count as decisions), the ledger, and PROFILE.md.
   Care-axes are ranked — the rank is the review priority order and selects
   which `references/rules-*.md` payloads load. Write findings to
   `.scratch/<slug>/review.md`; that file is the handoff to the fix loop.
2. Run the tier gates for the ticket's `effort:` level (fall back to the run
   default when absent), in order, accumulating; a failed
   tier goes to the fix loop (step 6):
   - **Fast**: lint + typecheck/compile, plus visual evidence of every touched UI
     surface following the UI verification ladder (`tdd` skill,
     references/android-testing.md): JVM screenshot tests (Roborazzi / AGP
     preview suites) or `android preview render` first; emulator/device only
     when no JVM capture exists for
     that surface, and never inside a fix round. On Android,
     `android studio analyze-file` (when the IDE is open) supplements lint on
     the touched files. A prototype run caps
     here plus the demo, at any effort.
   - **Standard**: plus one reviewer subagent on a stronger tier than the
     implementer.
   - **Thorough**: plus one fresh-context dual-verdict subagent on the most
     capable model.
3. Brief reviewers minimally: diff command, commit list, spec excerpt,
   care-axes with their rules payloads, relevant ledger lines, and the evidence
   ladder — reviewers cite JVM screenshot-test captures as proof and never boot
   an emulator to gather evidence. On Android diffs the reviewer runs the
   Android CLI checks itself (`android-cli` skill, mandatory, not delegated to
   the implementer). **`android studio analyze-file` comes first** — run it on
   every touched Kotlin/Java file before reading the diff; its inspections
   catch what eyeballing misses. Project-open protocol (`android-cli` skill):
   if `android studio check` shows no READY project or the wrong one, open
   this worktree (`open -a "Android Studio Preview" <repo-root>`), poll
   `check` until READY, verify the path matches this worktree, and pin every
   studio call with `--project`; unresolvable (no Studio installed) → fall
   back to lint-only, never skip silently. Then: `android preview render` for
   any preview claim it
   grades, `android layout --output hierarchy.json` for touch-target/density
   verdicts, and `android studio version-lookup` before accepting any
   dependency change.
   An Android finding graded without the applicable CLI check is
   `cannot-verify`, not ✅. Never session history — the reviewer judges
   the work product, not the process.
4. Dual verdict (thorough) — two axes, reported separately, never merged:
   spec-compliance ✅ / ❌ / ⚠️ cannot-verify, every claim backed by quoted
   evidence; and quality Approved / Needs-fixes. Findings graded
   Critical / Important / Minor; each axis ≤400 words.
5. Architecture in the diff (new/boundary-crossing modules, dependency
   direction) → thorough tier grades against `design-architecture`'s
   `../design-architecture/references/rules-architecture.md` payload; findings are Critical when the
   dependency rule breaks.
6. UI in the diff → load [review-ux.md](references/review-ux.md) and run the UX
   axis at every tier; check against `design-taste-frontend` when installed.
7. Visual review doc — at verdict time produce `.scratch/<slug>/review/REVIEW.md`
   per [review-doc.md](references/review-doc.md): numbered screenshots (reuse
   JVM captures), motion clips from the wireless-adb device when reachable,
   archify diagram for structure changes, the vetoable assumptions, and the
   id-based feedback contract. The user reviews without testing; their
   artifact-id replies re-enter this fix loop. Publish it browsable via
   `review-site` when the run's review-site decision is yes — thorough tier
   defaults to yes (the doc is the primary review surface at that depth);
   fast/standard follow the PROFILE `Review site publish:` setting or the
   session answer, and the doc itself is always written either way.
8. Fix loop: findings go back to the same implementer as a resumed brief;
   re-review is scoped to the fix diff only. Minors are ledgered as deferred —
   never silently fixed. Count failed fix rounds per module in the ledger.
9. Teardown gate: 2 failed fix rounds on the same module (fire before round 3),
   or reviewer discretion once with a logged reason → invoke `assess-teardown`.
   The architect decides fix-forward vs clean redesign; a redesign carries
   forward only root cause, interface contracts, and surviving tests.
8. Report the verdict to the user: verdicts, findings by grade, what was
   skipped, residual risk. Append the ledger line; when debug is on, add the
   ≤4-line run-log entry (`depth: not ok` when fix rounds were exceeded or a
   gate re-ran — always with the cause).

Read [review-prompts.md](references/review-prompts.md) before dispatching a
reviewer or writing up a dual verdict. Read
[fix-loop.md](references/fix-loop.md) when a fix round starts or the teardown
gate fires.

Adapted from superpowers (`requesting-code-review`, `receiving-code-review`) and
mattpocock/skills (`code-review`), both MIT.
