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

> **TL;DR** Breaks an approved spec into dependency-ordered tracer-bullet tickets with DoD and evidence in the local tracker; fires after a spec passes checkpoint.
> **Related**: skill://draft-spec (upstream spec), skill://implement (downstream execution), skill://fan-out-research (Unknowns research), skill://structure-checks (file-map evidence), skill://goldfish-review (stage B design review), skill://user-check (re-gate fires this for hardening tickets: DoD includes "approved behavior unchanged", one ticket pins the baseline as tests)

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
   - **File map** — only when the ticket adds or moves files: one line per new
     or moved file, `path — one-sentence responsibility`. A line that needs
     "and" to state its responsibility is two files. Reviewers diff the real
     files against this map; paths belong here and in the brief, never in the
     spec.
   - **Unknowns** — one open question per line; each line becomes one
     `fan-out-research` subagent before coding starts. If an answer could
     change the build, either write a DoD that survives both answers or block
     the ticket on a research ticket.
   - **DoD** — ONE checkable condition. **Evidence** — a re-runnable command
     with an exit code (test task, `structure:` command from PROFILE.md,
     preview render task). Screenshot paths and deploy output are Evidence only
     on the single device-acceptance ticket (item 5). A ticket that adds or
     moves files also carries the DoD line "structure checks green" with the
     `structure:` command as Evidence (`structure-checks`; not configured →
     say so in the ticket). No DoD → not a ticket: thin or split until one
     exists.
5. Parallel-safe, and make it the DEFAULT: tickets are designed to run in
   parallel with minimal overlap — serialization is the exception that needs
   a reason, not the norm. Mark a ticket parallel-safe only when its file
   scope is
   disjoint from every other open ticket's scope (the split itself comes
   from `micro-architecture` — engine seam, one file per variant, exact
   signatures across tickets); when scopes collide, re-split along
   `micro-architecture`'s seams first, and only fall back to a blocking
   edge if the shared surface is genuinely inseparable. An interface crossing
   tickets is written once as an exact signature in both the producing and the
   consuming ticket.
   **Device/emulator checks are pulled OUT of implementation tickets.** A
   ticket whose DoD needs a device either (a) loses that DoD to a
   device-free equivalent (JVM screenshot suite, `android preview render`,
   unit test — the testing ladder), or (b) becomes ONE separate aggregate
   ticket at the end of the set that batches every remaining on-device
   acceptance check into a single sitting. Never spread device checks
   across tickets — each one serializes its ticket behind a device and
   multiplies emulator boots. (b) is the fallback; (a) is the goal, and a
   set with no device-dependent ticket at all is the win.
6. Publish: one file per ticket, `.scratch/<slug>/tickets/NN-<slug>.md`, with
   the tracker frontmatter from docs/agents/issue-tracker.md (`id`, `title`,
   `labels`, `status`, `assignee`, `blocked-by`). Claim = set `assignee:`
   before any work; the frontier = `status: open`, `assignee: none`, every
   `blocked-by` id done; close = `status: done` + Evidence under
   `## Resolution`. PROFILE.md may point at another tracker — publish there
   natively and use its real blocking links.
7. Prototype sets: DoD = the question answered or the thing demoable; the
   last ticket carries the `deploy:` flag (`main | standalone | none`).
8. Confirm by effort: each ticket carries an `effort:` frontmatter field
   (`fast | standard | thorough`) per the per-task rules in `start`'s effort
   mapping — thorough only for architecture/planning/big-view tickets. List
   every downgrade below the run default with a reason; if a different level
   would likely accelerate development, ask the user. fast/standard — publish
   and report the numbered list (title, effort, blocked-by, what it delivers).
   Thorough — show the list and wait: confirm granularity, blocking edges, and
   split/merge before publishing.
9. Design review (stage B, `goldfish-review`): before publishing, when the
   set adds a module or boundary or the run is thorough, ask the user in the
   same confirm message whether they want a blind design review — none / up
   to 3 / all lenses (recommended: all at thorough, up to 3 otherwise). fast,
   or nothing architectural → skip silently. Findings land as ticket edits
   or file-map changes, never a second interview.

Adapted from mattpocock/skills (`to-tickets`) and obra/superpowers
(`writing-plans`), MIT.
