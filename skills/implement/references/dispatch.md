# Dispatch templates

## Brief file: `.scratch/<slug>/briefs/NN-brief.md`

One brief per ticket; exact values (numbers, strings, signatures, test cases)
appear only here, verbatim.

```markdown
# Brief: NN — <ticket title>

Ticket: <path — source of requirements>
Spec: <backlink path — binding authority; its assumptions count as decisions>
File scope: <paths this ticket may touch; disjoint for parallel-safe tickets>
Neighbor interfaces: <signatures/contracts from earlier tickets this brief cannot know>
Unknowns: <one link per resolved findings file, or "none">
DoD: <the checkable condition>
Evidence: <command | screenshot path | deploy output>
```

The dispatch prompt carries three things only: one line on where this ticket
fits, the brief path introduced as "read this first — it is your
requirements", and the report path + contract below.

## Report file: `.scratch/<slug>/reports/NN-report.md`

The worker writes the full report there and replies in at most 15 lines:

```
status: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
commits: <base7>..<head7>
tests: <one line — runner, passed/failed>
dod: <met? evidence path>
skipped: <what>
residual risk: <what could be wrong>
concerns: <numbered, or none>
```

NEEDS_CONTEXT questions go in `concerns:`; the controller answers as a brief
addendum file and resumes the same worker.

## Ledger lines (`.scratch/<slug>/ledger.md`, append-only)

- Ticket close: `NN: done (commits <base7>..<head7>, evidence <path>)`
- Deviation: `Ruling: <what> — <why> — <cost if wrong>`
- Deferred finding: `NN deferred: <concern> (for review-change)`
