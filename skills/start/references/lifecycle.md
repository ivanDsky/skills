# Orchestrator lifecycle

Read when a feature or big-prototype chain freezes its spec, when a captain
returns, or when the main session has been compacted a third time.

Why: one audited orchestrator ran 5 days with 48 compactions, and
orchestrators were $876 of Opus spend in 6 days. Context bloat drove
re-reads after every compaction, and user feedback was lost across them.
Execution work (dispatch, merge, fix loops) needs Sonnet judgment, not Opus,
and it needs a context that starts empty each milestone.

## Who orchestrates which stage

Models: effort-mapping.md, *Orchestrator by stage*.

- **Main session** (the user's top-level session, on the model the user
  launched): triage, intake, spec, UI contract, ticketing, goldfish gates,
  user-check F-id triage and taste rulings, every ask, every approval, the
  flip, milestone digests. Only the main session talks to the user
  (start § Waiting on the user).
- **Captain** (one fresh subagent per execution milestone, Sonnet): runs the
  milestone's ticket work as `implement`'s controller: worker dispatch,
  merge lane, re-dispatch on BLOCKED, the `review-change` fix loop, the
  deliver build. It routes and merges; it never implements a ticket or
  reviews a diff itself.
- Quick task, quick prototype, bug diagnosis: no captain; the main session
  runs them directly.

Execution milestones, each one captain run: slices merged; user-check build
ready; one user-check fix round (fast fixes + rebuild); hardening tickets
closed + review done; delivered. A milestone that needs the user between two
of these returns to the main session first.

## Main session steps

1. Spec (and UI contract, when one exists) frozen and tickets confirmed →
   write `.scratch/<slug>/resume.md` (§ Resume file), then spawn the captain
   with § Captain brief. Async; idle → harness wait. Never poll the captain.
2. A user message arrives while a captain runs → persist it first
   (start § Decisions and waiting), then relay it with
   `write agent://<captain>`.
3. Captain returns → read its digest. Questions in `blocked on user:` → one
   ask (≤5 questions); the answer goes back with `write agent://<captain>`
   (this revives a parked captain with its context intact). Milestone done →
   the digest or checkpoint form to the user, then spawn a fresh captain for
   the next execution milestone.
4. Rollover: the third compaction of the main session → at the next
   milestone boundary, update the resume file, then end the turn with
   `blocked on you: fresh session — type /new, then send "Resume <slug>
   from .scratch/<slug>/resume.md"`. Once per milestone at most; never
   repeated in later turns. `/new` keeps the current model and settings.
5. A session whose first ask names a resume file → read it, `grep
   '^Decision:'` the ledger, and continue at its `Next:` line; no re-triage,
   no intake.

## Captain brief

Paste into the spawn task, filled in. `agent: task`; model and spawn
`effort`: effort-mapping.md, *Orchestrator by stage*.

```
Captain for <slug>, milestone: <name>. Done when: <checkable condition>.
Read first: .scratch/<slug>/resume.md; grep '^Decision:' .scratch/<slug>/ledger.md; PROFILE.md.
Run this milestone as implement's controller (dispatch per skill://start/references/effort-mapping.md;
ship-to-trunk / review-change / deliver as the milestone needs). Route and merge; never implement
or review yourself.
Workers get the skill://implement/references/hard-rules.md block verbatim (implement dispatch.md).
You merge only through the merge lane, under ship-to-trunk merge authority and PROFILE ## Consent ledger.
Never call the ask tool, never post status. User-only questions: keep every other lane moving;
stop when all lanes wait on the user. Never poll: workers and background jobs push results.
Stop also after your second compaction: finish in-flight merges, then return `partial`.
Before returning: overwrite .scratch/<slug>/resume.md (format: skill://start/references/lifecycle.md).
Return ≤10 lines: done | partial | blocked; landed; assumed:; blocked on user: (each question
with a recommended option); next.
<voice line from start § Voice>
```

## Resume file

`.scratch/<slug>/resume.md` is overwritten at every milestone boundary (by
the captain, or by the main session at spec freeze and before a rollover);
history stays in the ledger. Format:

```
# Resume — <slug> — after <milestone> — <date>
Ledger: .scratch/<slug>/ledger.md (ledger wins over the copies below)
Spec: <path>. Contract: .scratch/<slug>/contract/ | none. Tickets: <tracker path>
## Decisions
<every live Decision: line, verbatim, latest per scope>
## Open tickets
<NN title — open | in flight: <agent id, branch> | blocked: <why>>
## Waiting
<PRs awaiting the user, background jobs (merge lane, main health), open asks>
## Next
Next: <milestone> — first step: <one line> — done when: <checkable>
Resume: main session spawns a captain (skill://start/references/lifecycle.md § Captain brief);
fresh session: /new, then "Resume <slug> from .scratch/<slug>/resume.md".
```

## Harness facts this relies on

- Subagents cannot ask: the ask tool needs an interactive UI. Questions go in
  the captain's report.
- Default `task.maxRecursionDepth` is 2: main → captain → workers and
  reviewers. Workers never spawn subagents, so the depth holds.
- Finished subagents park after the idle TTL; `write agent://<id>` revives
  them with their transcript.
- The agent cannot switch the main session's model or open a new session:
  `/model`, `/new` and `/resume` are user commands. `/handoff` and
  `new_context` compact in place on the same model, so they count as
  compactions and change no model.
