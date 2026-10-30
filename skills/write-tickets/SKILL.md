---
name: write-tickets
description: >-
  Break an approved spec into tracer-bullet tickets in the local tracker —
  walking-skeleton ticket 01 first, a mandatory checkable DoD + evidence on
  every ticket, one ticket per fresh subagent context, declared Unknowns fanned
  out to research, parallel-safe only on disjoint file scopes. Use after a spec
  passes its checkpoint, or when a plan or spec must become dependency-ordered,
  trackable tickets.
interaction: afk
requires: []
---

# Write tickets

Turn the spec into tracer-bullet tickets in the wayfinder tracker, each
closable only by evidence. The spec has passed its checkpoint — do not re-open
its decisions; fold new corrections in as ticket edits, never a re-interview.

1. Read first: `.scratch/<slug>/spec.md` (Solution, numbered Assumptions,
   Success criteria, Out of scope), PROFILE.md, the tracker frontier, and the
   code around the change. Assumption numbers are decisions — reference them
   (A1, A2) in the tickets that rely on them; never drop one silently.
2. Order tracer bullets: ticket 01 is the thinnest end-to-end walking
   skeleton — every layer touched, demoable on its own. Then narrow complete
   slices, blockers first, numbered `NN` in dependency order. A horizontal
   slice (all schema, then all API, then all UI) is never a ticket set — thin
   the slices instead. Prefactoring goes before ticket 01.
3. Size: one ticket = one fresh subagent context, one sitting. The budget is
   a single context window: ticket + spec backlink + neighbor interfaces in,
   code + evidence out. Checkable proxy: ≤5 files touched and exactly one
   demoable or verifiable outcome. Over budget → split vertically (a thinner
   slice), never by layer. One mechanical change with a wide blast radius →
   expand–contract batches: add the new form beside the old, migrate call
   sites in batches, delete the old form last.
4. Every ticket carries ALL mandatory fields:
   - **What to build** — end-to-end behavior from the user's perspective, not
     a layer list. No file paths or line numbers; they go stale. Exception: a
     prototype snippet encoding a decision (state machine, schema, type) may
     be inlined, trimmed to the decision.
   - **Blocked by** — ticket ids that must close first, or "none".
   - **File scope** — the files/dirs this ticket may touch.
   - **Unknowns** — one open question per line; each line becomes one
     `fan-out-research` subagent before coding starts. If an answer could
     change the build, either write a DoD that survives both answers or block
     the ticket on a research ticket.
   - **DoD** — ONE checkable condition. **Evidence** — the command, screenshot
     path, or deploy output that will prove it. No DoD → not a ticket: thin or
     split until one exists.
5. Parallel-safe: mark a ticket parallel-safe only when its file scope is
   disjoint from every other open ticket's scope. Shared surface — same files
   or shared interfaces — gets a blocking edge instead. An interface crossing
   tickets is written once as an exact signature in both the producing and the
   consuming ticket.
6. Publish: one file per ticket, `.scratch/<slug>/tickets/NN-<slug>.md`, with
   the tracker frontmatter from docs/agents/issue-tracker.md (`id`, `title`,
   `labels`, `status`, `assignee`, `blocked-by`). Claim = set `assignee:`
   before any work; the frontier = `status: open`, `assignee: none`, every
   `blocked-by` id done; close = `status: done` + Evidence under
   `## Resolution`. PROFILE.md may point at another tracker — publish there
   natively and use its real blocking links.
7. Prototype sets: DoD = the question answered or the thing demoable; the
   last ticket carries the `deploy:` flag (`main | standalone | none`).
8. Confirm by effort: fast/standard — publish and report the numbered list
   (title, blocked-by, what it delivers). Thorough — show the list and wait:
   confirm granularity, blocking edges, and split/merge before publishing.

Adapted from mattpocock/skills (`to-tickets`) and obra/superpowers
(`writing-plans`), MIT.
