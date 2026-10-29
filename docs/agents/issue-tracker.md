# Issue tracker

Tracker for this repo: **local markdown**. Issues are files in the repo, under
`.scratch/` — no external service. Commit them like code; concurrent sessions
are expected to edit concurrently.

## Layout

```
.scratch/<effort>/
├── MAP.md                      # wayfinder map (labels: [wayfinder:map])
└── tickets/
    └── TNNN-<slug>.md          # one file per ticket
```

## Issue file format

YAML frontmatter + markdown body:

```markdown
---
id: T001
title: Human-readable ticket title
labels: [wayfinder:research]     # wayfinder:map | wayfinder:research |
                                 # wayfinder:prototype | wayfinder:grilling | wayfinder:task
status: open                     # open | closed
assignee: none                   # session/agent name that claimed it
blocked-by: []                   # ids of tickets that must close first
---

## Question

<for wayfinder tickets: the decision this ticket resolves>

## Resolution

<appended on close: the answer, links to findings/assets>
```

## Wayfinding operations

- **Create** a ticket: add `tickets/TNNN-<slug>.md` (next free number), commit.
- **Claim**: set `assignee:` to your name **before** working. An open ticket
  with `assignee: none` is unclaimed.
- **Block**: list blocker ids in `blocked-by:`. A ticket is unblocked when
  every blocker is `closed`. (Local tracker has no native dependency UI —
  this frontmatter list is the convention.)
- **Frontier**: all tickets that are `status: open`, `assignee: none`, and
  have no unclosed `blocked-by` ids.
- **Close**: set `status: closed`, append `## Resolution`, commit. Reference
  tickets by **title**, linking the file — never by bare id.
- **Map**: `.scratch/<effort>/MAP.md` is the index; decisions live in tickets,
  the map only gists and links.
