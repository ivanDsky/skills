---
name: review-change
description: >-
  Run the effort-tiered review gate over the change — scripted checks plus
  screenshots, then code review, then a dual-verdict fresh-context subagent —
  and own the fix loop, the one full-suite run, the ledger, and the teardown
  escalation. Use after user-check approved the behavior and its hardening
  tickets closed, before deliver, when a finished diff or branch needs its
  review gate, or when the user says review the change, run the review gate,
  or check this before shipping.
interaction: afk
requires: []
---

> **TL;DR** Runs the effort-tiered review gate — scripted checks, screenshots, code review, dual-verdict subagent — owns the fix loop and the one full-suite run; fires after user-check OK and hardening, before deliver.
> **Related**: skill://user-check (upstream: approved behavior + hardening tickets; behavior-changing fixes go back to it), skill://implement (upstream tickets), skill://deliver (downstream ship), skill://assess-teardown (teardown escalation), skill://scope-creep-detector (drift catch), skill://structure-checks (fast-tier command), skill://goldfish-review (earlier blind lenses; shares its triage rules)

# Review change

Run the review gate over the whole change, then own what follows: fix rounds,
the one full-suite run, the ledger, and the teardown escalation. The user has
already tried the change (`user-check`), so behavior is approved; this gate
checks it is tested and cleanly designed. Findings and verdicts live in a
file; chat carries only the user-facing report.

1. Pin the inputs: the diff vs base (`git diff <base>...HEAD` — verify the base
   resolves and the diff is non-empty before dispatching anything), the spec
   (numbered assumptions count as decisions), the ledger, PROFILE.md, and
   `.scratch/<slug>/regate.md`. No `user-check: ok` or `user-check: skipped`
   line in the ledger → stop and fire `user-check`. Care-axes are ranked — the
   rank is the review priority order and selects
   which `references/rules-*.md` payloads load. Write findings to
   `.scratch/<slug>/review.md`; that file is the handoff to the fix loop.
2. Run the tier gates for the ticket's `effort:` level (fall back to the run
   default when absent), in order, accumulating; a failed
   tier goes to the fix loop (step 8). Tests for the change are checked at
   every tier: each F-id and verify step from `user-check` has a persisted
   test, and code that arrived without tests (quick task, fast fix) has them
   now — written by the implementer and watched failing by temporarily
   reverting the change. A missing one is ❌ Important.
   - **Fast**: lint + typecheck/compile, plus visual evidence of every touched UI
     surface following the UI verification ladder (`tdd` skill,
     references/android-testing.md): JVM screenshot tests (Roborazzi / AGP
     preview suites) or `android preview render` first; emulator/device only
     when no JVM capture exists for
     that surface, and never inside a fix round. On Android,
     `android studio analyze-file` (when the IDE is open) supplements lint on
     the touched files. On Kotlin diffs, run PROFILE.md's `structure:` command
     (`structure-checks`) yourself: red is ❌ Important; not configured on a
     Kotlin diff is `cannot-verify`, said out loud. Plus one design-only
     reviewer subagent (diff, tickets' file maps, `rules-architecture.md`)
     that fills the step-5 architecture, file-structure and patterns rows. A
     prototype run caps here plus the demo, at any effort. Plus, before
     anything is pushed:
     one secret scan over the diff and new fixtures (keys, tokens,
     session IDs, connection strings) — audited cost of skipping: a
     JSESSIONID shipped to GitHub and had to be redacted.
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
   direction) → graded at every tier against `design-architecture`'s
   `../design-architecture/references/rules-architecture.md` payload (fast:
   the design-only reviewer; thorough: also the dual verdict); findings are
   Critical when the dependency rule breaks. `regate.md` findings already
   ticketed count as checked only when their hardening ticket is closed.
   Coverage proof, every tier that reviews code: the report carries one row
   per axis — spec, architecture, file structure, patterns, UI — with what
   was checked and the count (`structure: 14 new/moved files vs file map, 0
   findings`). File structure = the diff's real files against the tickets'
   file maps and the one-responsibility rule (a file needing "and" to state
   its job, several public types, a shared `when` edited to add a variant);
   patterns = the Extension points assumption honored, each introduced
   pattern carrying its forcing function, repo-consistent with the pattern
   table in `micro-architecture`. A row without evidence is `cannot-verify`,
   never ✅. A worker report saying `device: used because …` with a weak
   reason, or a diff showing device-driven edits with `device: none`, is an
   Important finding.
6. UI in the diff → load [review-ux.md](references/review-ux.md) and run the UX
   axis at every tier; check against `design-taste-frontend` when installed.
   Thorough adds one fresh-context visual reviewer that sees only preview
   renders and screenshots — layout, icons, motion, microinteractions graded
   against `apple-design` / `emil-design-eng` / `animation-vocabulary` /
   `ui-ux-pro-max`; it proposes, never policing taste the user owns.
7. Route every fix before it starts. A fix that changes behavior the
   `user-check` verify steps or F-ids exercise → after it lands, back to
   `user-check` for a short re-check of that delta (the user approved the
   old behavior, not this one). Refactor-only and test-only fixes stay here,
   with a `Ruling:` line saying why they are behavior-neutral.
8. Fix loop: findings go back to the same implementer as a resumed brief;
   re-review is scoped to the fix diff only; triage and convergence rules in
   [fix-loop.md](references/fix-loop.md). Minors are ledgered as deferred —
   never silently fixed. Count failed fix rounds per module in the ledger.
   Fix rounds run only the touched module's tests. When the loop converges,
   run the PROFILE.md test runner **once** over HEAD, log it to
   `.scratch/<slug>/suite.log`, and ledger `suite: green @ <sha>`. This is
   the run's only full-suite run; `deliver` and `open-pr` reuse it. Red →
   one more fix round, then rerun.
9. Teardown gate: 2 failed fix rounds on the same module (fire before round 3),
   or reviewer discretion once with a logged reason → invoke `assess-teardown`.
   The architect decides fix-forward vs clean redesign; a redesign carries
   forward only root cause, interface contracts, and surviving tests.
10. Report the verdict to the user: verdicts, findings by grade, what was
   skipped, residual risk. Append the ledger line; when debug is on, add the
   ≤4-line run-log entry (`depth: not ok` when fix rounds were exceeded or a
   gate re-ran — always with the cause).

Read [review-prompts.md](references/review-prompts.md) before dispatching a
reviewer or writing up a dual verdict. Read
[fix-loop.md](references/fix-loop.md) when a fix round starts or the teardown
gate fires.

Adapted from superpowers (`requesting-code-review`, `receiving-code-review`) and
mattpocock/skills (`code-review`), both MIT.
