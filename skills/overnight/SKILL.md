---
name: overnight
description: >-
  Hand a big chunk of work to agents or a bot team for one unattended session:
  grill the user up front until every load-bearing decision, contingency and
  approval sits in a night brief, run the session without a single blocking
  ask (questions are logged, defaulted, isolated and work continues), and end
  with one morning check of everything that landed. Use when the user says
  overnight, "while I sleep", "hand this whole chunk to the bots", "work on it
  all night", "long unattended run" or "set me up for a big check in the
  morning".
interaction: mixed
requires: []
---

> **TL;DR** Evening grill → night brief + go → night run that never blocks on the user (ask-and-continue) → one morning check doc and build; fires on "overnight" or any long unattended handoff.
> **Related**: skill://grilling (round format), skill://start (chain, lifecycle, waiting rules), skill://run-intake (replaced by the brief), skill://user-check (the morning check is its step 3), skill://goldfish-review (night gates), skill://assess-teardown (stuck lanes park), skill://review-site (morning doc)

# Overnight

The user is asked twice: in the evening, a lot, and in the morning, once.
Everything between runs on the brief. Every question a worker would ask at
3 a.m. is either answered at 10 p.m. or has a written default it can take
without waiting.

```
grill ─rounds─> brief ─preflight─> go ─> night run ─────────> morning check ─> user-check § 4
                                         Q: default + continue    one doc, one build, one reply
                                         P: park lane, continue
```

## 1. Grill (evening, HITL)

1. Read first: PROFILE.md, the backlog frontier, `grep '^Decision:'` on the
   ledger, the ask. Facts are lookups (scouts in parallel), never
   questions. Done when every question left is a decision only the user can
   make.
2. Size the chunk against the night: the brief's hours at the run's effort
   level. Too big → the first question proposes the cut ("tonight: A and B;
   next night: C").
3. Grill in rounds, `grilling`'s format (whole frontier per round,
   numbered, recommendation on the arrow line, worded so "yes" accepts),
   walking every branch of [grill-tree.md](references/grill-tree.md). The
   ask tool when it works, else plain text. ≤8 questions per round. Done
   when the frontier is empty, not when the user tires; a branch the user
   waves off becomes an `assumed:` line they see in the digest.
4. Last round is the pre-mortem: "It is 8 a.m. and the night was wasted.
   Why?" Offer the 3-5 likeliest causes from what you saw (environment
   down, missing secret, an open design fork, a flaky suite, scope creep);
   each gets a contingency answer.
5. Preflight while the user is still awake: main builds and its suite is
   green; every tool, device, server, token and auth the night needs
   answers; the morning delivery path (build → device or served URL) works
   once as a dry run. A failure is fixed now or becomes a grill question.
6. Write the brief per [brief.md](references/brief.md) to
   `.scratch/<slug>/overnight/brief.md`, mirror every decision as a
   `Decision: overnight <slug> — …` ledger line, then one ask with the
   ≤15-line digest: "Start the night run? Morning check at <time>." Only an
   explicit yes starts it; silence, "ok" to another question or a timeout
   default never does.

## 2. Night run (AFK, no blocking ask)

Executor, as the brief says:
- **This session**: `start`'s chain with the brief as the intake output,
  gates replaced per the table, one captain per execution milestone
  (`start`/references/lifecycle.md). The orchestrator waits only on its own
  agents; it never ends a turn waiting on the user.
- **A bot team**: one handoff message to the team lead naming the brief's
  absolute path (fresh worktrees do not see `.scratch/`). A team that
  honors only PROFILE's Consent ledger gets one dated line on `main`,
  `pre-approved: overnight <slug> until <date> <time> — the gates in
  .scratch/<slug>/overnight/brief.md`; the morning check removes it.

| Daytime gate | At night |
|---|---|
| intake batch, spec checkpoint | the brief; spec freezes when it meets the brief's acceptance; `goldfish-review` stage A, ≤2 lenses by risk; a finding that changes scope → Q entry, default = the brief |
| ticket checkpoint, design review | auto; stage B lenses as the brief lists (default: architecture) |
| `user-check` try-it | the morning check |
| merges | per the brief's delivery line: dark slices merge, PRs only the user may merge stay open and listed |
| release, flag flip, prod deploy, anything public, data deletion | never; park |

**Ask-and-continue** — each question that comes up, first match wins:
1. The brief, a `Decision:` line, a contingency or PROFILE answers it →
   apply it; no entry.
2. Reversible with a sane default → `Qn` entry in
   `.scratch/<slug>/overnight/questions.md` (question, options, default
   taken, the work that depends on it, cost to undo), ledger `assumed: Qn —
   <default>`. The dependent work lands in its own commit or ticket tagged
   `Qn`, so a morning "no" reverts only that. Keep going. A channel that
   notifies without waiting (a push, a chat line) may carry one line per Q;
   the blocking ask tool never runs at night.
3. Irreversible, on the never list, or outside the brief's envelope → `Pn`
   park entry; that lane stops, every other lane keeps moving.
4. The user answers during the night → persist it as a `Decision:` line
   first; a "no" to Qn reverts and redoes the Qn work before anything else.

Keep the night productive:
- A lane failing two fix rounds → `assess-teardown`; an unresolved verdict
  parks the lane as Pn. Never loop on one failure until morning.
- `main` red → first priority over every lane.
- Brief's DoD met early → the stretch list, in order; then hardening of
  what landed (tests at seams, `structure:` clean). Never new scope.
- All lanes parked, budget spent, or 1 hour before the morning time →
  stop dispatching and build the morning check.
- No chat to the user except Q/P lines; state lives in the ledger and
  `resume.md`.

## 3. Morning check

Ready before the brief's morning time, per [morning.md](references/morning.md):
1. `user-check` § 1–2: gate-in green, build delivered or served, URL
   opened once by you.
2. `.scratch/<slug>/review/REVIEW.md` in `user-check`'s check-doc shape
   plus the night sections: acceptance scorecard, Q list, P list, landed,
   parked, next night. Published via `review-site` when served URLs exist.
3. Remove the dated Consent line, then one ask: build, link, "`ok`, or
   reply by id: T2 … · Q3 no · P1 yes". The answer enters `user-check` § 4
   (F-ids, fast fixes); Q "no" answers revert the tagged work; P "yes"
   answers run now. OK → `user-check` § 5 re-gate.

## Decision rules

- Brief vs a later artifact (spec, ticket) → the brief wins; the user said it.
- A user message mid-night supersedes the brief through its `Decision:`
  line; the brief file only gains an `## Amendments` section.
- Chunk unfinished → the morning doc says partial, `resume.md` names the
  next night's first step; nothing is rushed to look done.
- Never act on a default for anything irreversible, however confident.

Fresh skill, written for this repo's chain; grill rounds reuse mattpocock/skills
`grilling` mechanics (MIT).
