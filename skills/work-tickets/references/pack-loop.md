# Pack loop details

## Brief

A backlog ticket carries behaviour and acceptance, not the `write-tickets`
fields. Before dispatch, the session writes `implement`'s brief file
(`implement`/references/dispatch.md) and fills the missing fields from one
`scout` pass over the code. They go in the brief only. The ticket stays
behaviour-level, because file paths go stale.

| Brief field | Source |
|---|---|
| What to build | the ticket's `## Expected` (bug: plus `## Reproduce`) |
| DoD | one checkable condition from `## Acceptance`; hands-on tickets also keep the user-facing line for the check batch |
| Evidence | a re-runnable command: the regression test for a bug, the preview render for UI, `structure:` when files move |
| File scope | from the scout pass: the files this fix may touch |
| tier / effort | `start`/references/effort-mapping.md; a p1 bug with a clear repro is usually `standard` / `fast` |
| flag | user-visible change → `flag: <Key>` (new or existing release flag, via `wire-dev-settings`); pure fix of broken behaviour → `flag: none`, merged live |
| Out of scope | the ticket's `## Out of scope`, verbatim |

A brief that cannot get a DoD from the ticket means the ticket is
underspecified. `set ID --state needs-info` with the missing question; never
guess a DoD.

## Pack order and parallelism

- `claim` returns tickets highest priority first, then oldest. Dispatch in
  that order.
- Disjoint file scopes run in parallel, one worktree and one worker each.
  Overlapping scopes serialize in priority order, with a ledger `Ruling:`.
- A ticket whose fix turns out to overlap another open ticket's scope in
  another session's claim: finish yours, and the merge loop's rebase handles
  the rest. Never coordinate by editing their ticket.

## Ledger

`.scratch/backlog-$ME/ledger.md`, append-only, one line per event:

```
claim: #12 #15 #19 (area leaderboard)
slice: #12 PR #301 merged @ abc1234 → done
slice: #15 PR #302 merged @ def5678 → needs-check (flag LeaderboardV2)
unclaim: #19 — repro needs a tablet; ready-for-human
```

After an interruption, the ledger plus `list --state claimed` with your name
beat recollection.

## Stale claims

`list --state claimed` shows each claim's age. A claim of yours with no
commit and no PR after a crash gets `unclaim` with "interrupted". Another
session's claim is never touched. Report claims older than a day in the
digest, and the feedback session offers the unclaim.

## Multiple machines

Claims are atomic only between sessions on one machine. A second machine on
the same GitHub backlog can double-claim. Then the loser sees `claimed-by`
change under it on the next `show` and drops the ticket without a PR.
