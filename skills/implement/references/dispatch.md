# Dispatch templates

## Brief file: `.scratch/<slug>/briefs/NN-brief.md`

One brief per ticket; exact values (numbers, strings, signatures, test cases)
appear only here, verbatim. A `mechanical` brief carries every value the
worker needs: names, signatures, target files, verbatim strings. The
mechanical worker (Haiku) makes no decisions; a missing value means BLOCKED,
never a guess.

```markdown
# Brief: NN — <ticket title>

Tier: <mechanical | standard | deep> → <agent>[, model] (`start`/references/effort-mapping.md)
Ticket: <path — source of requirements>
Spec: <backlink path — binding authority; its assumptions count as decisions>
File scope: <paths this ticket may touch; disjoint for parallel-safe tickets>
Neighbor interfaces: <signatures/contracts from earlier tickets this brief cannot know>
Unknowns: <one link per resolved findings file, or "none">
DoD: <the checkable condition>
Evidence: <re-runnable command with an exit code; screenshot/deploy output only on the device-acceptance ticket>
Trunk: <`trunk` runs only — worktree from origin/main @ <sha7>; flag: <Key> | none; live: <what> — <why backward compatible>, or omit>
Standards: <≤5 lines, see below>
```

### Standards block

The controller picks at most 5 lines — concrete, checkable, each naming its
source file — by ticket type and the top care-axis in PROFILE.md. Never a
skill wall; the worker reads only what a line names. Selection:

- adds/moves files → file map in the ticket is binding; `structure:` command
  green (`structure-checks`); one responsibility per file
  (`design-architecture/references/rules-architecture.md` 17, 20)
- spec names an Extension points assumption → follow it; pattern per
  `micro-architecture`'s table; no seam beyond it
- UI → `preview-compose` previews for each state; tokens not literals;
  motion named via `animation-vocabulary`
- verification → rung ≤3; no device or emulator; semantic JVM test for any
  tap flow (`tdd/references/android-testing.md`)
- care-axes rank 1-3 hard rules from PROFILE.md fill the rest

Event triggers (creating a file, editing a shared variant site, introducing
a pattern) live in `implement` §3 and are not repeated here.

The dispatch prompt carries four things only: one line on where this ticket
fits, the brief path introduced as "read this first — it is your
requirements", and the report path + contract below.

## Report file: `.scratch/<slug>/reports/NN-report.md`

The worker writes the full report there and replies in at most 15 lines:

```
status: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
commits: <base7>..<head7>
pr: <`trunk` runs — #<n> merged @ <sha7> | waiting on user (<why>)>
tests: <one line — runner, passed/failed>
dod: <met? evidence path>
skipped: <what>
device: none | used because <reason>
structure: <command and result, or "not configured">
residual risk: <what could be wrong>
concerns: <numbered, or none>
```

NEEDS_CONTEXT questions go in `concerns:`; the controller answers as a brief
addendum file and resumes the same worker.

## Ledger lines (`.scratch/<slug>/ledger.md`, append-only)

- Ticket close: `NN: done (commits <base7>..<head7>, evidence <path>)`
- `trunk` runs add `ship-to-trunk`'s ledger lines (`slice:`, `flag:`,
  `live:`)
- Deviation: `Ruling: <what> — <why> — <cost if wrong>` (tier escalation:
  `Ruling: NN escalated <from>→<to> — <why> — <cost if wrong>`)
- Deferred finding: `NN deferred: <concern> (for review-change)`
