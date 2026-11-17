---
name: write-tickets
description: >-
  Break an approved spec into tracer-bullet tickets in the shared backlog —
  walking-skeleton ticket 01 first, one end-to-end capability per ticket
  (≤ ~12 per milestone, a count gate for unvalidated designs), a mandatory
  checkable DoD + evidence on every ticket, one ticket per fresh subagent
  context, declared Unknowns fanned out to research, parallel-safe only on
  disjoint file scopes. Use when a spec has passed its checkpoint, or when a
  plan or spec must become dependency-ordered, trackable tickets.
interaction: afk
requires: []
---

> **TL;DR** Breaks an approved spec into few, bigger dependency-ordered tracer-bullet tickets with DoD and evidence in the shared backlog; fires after a spec passes checkpoint.
> **Related**: skill://draft-spec (upstream spec), skill://implement (downstream execution), skill://fan-out-research (Unknowns research), skill://structure-checks (file-map evidence), skill://goldfish-review (stage B design review), skill://user-check (re-gate fires this for hardening tickets: DoD includes "approved behavior unchanged", tests only for the bug each fixes), skill://tdd (§ What to test, what not to: the test policy every ticket's tests follow), skill://ship-to-trunk (`changes: trunk`: every ticket merges to main alone and dark)

# Write tickets

Turn the spec into tracer-bullet tickets in the shared backlog, each
closable only by evidence. The spec has passed its checkpoint — do not re-open
its decisions; fold new corrections in as ticket edits, never a re-interview.

1. Read first: `.scratch/<slug>/spec.md` (Solution, numbered Assumptions,
   Success criteria, Out of scope), PROFILE.md, the epic's open backlog tickets, and the
   code around the change. Assumption numbers are decisions — reference them
   (A1, A2) in the tickets that rely on them; never drop one silently.
2. Order tracer bullets: ticket 01 is the thinnest end-to-end walking
   skeleton — every layer touched, demoable on its own. Then narrow complete
   slices, blockers first, numbered `NN` in dependency order. A horizontal
   slice (all schema, then all API, then all UI) is never a ticket set — thin
   the slices instead. Prefactoring goes before ticket 01.
   **`trunk` runs** (PROFILE `changes: trunk`): every ticket must merge to
   main alone and dark. Ticket 01 is the flag ticket (release flag, off in
   release) and the walking skeleton follows behind it; then slices; a
   shared-file edit (registry, DI module, nav graph, `when` entry) is its
   own ticket merged first; the flip ticket and the cleanup ticket are
   written up front, last. Rules: `ship-to-trunk`/references/slicing.md.
3. Size: one ticket = one fresh subagent context, one sitting, and by default
   one user-visible capability end to end (data → domain → ViewModel → UI),
   never one layer. Merge mechanical pieces (DI/nav registration, strings,
   the slice's own call-site migration) into the slice that needs them;
   target ≤ ~12 tickets per milestone, ceiling ~600 changed production lines
   per ticket, split above it into a thinner capability, never by layer.
   `trunk` runs keep the hard cap ≤ ~400 changed lines, one concern, split
   before publishing, never after. A repo-wide migration over the ceiling →
   expand–contract batches, each `tier: mechanical`, old form deleted last.
   A plan over ~25 tickets for a design the user has not validated is split:
   prototype/contract milestone first, tickets after freeze. Rules, exceptions
   and the gate: references/slicing.md — read it before sizing.
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
     say so in the ticket). Tests a ticket asks for follow `tdd` § What to
     test, what not to. No DoD → not a ticket: thin or split until one exists.
   - **Contract lines** — tickets under a frozen UI contract only:
     `Contract: .scratch/<slug>/contract/` and one
     `Reference: <golden or test> = reference/<file>.png` line per pair
     (references/slicing.md § UI contract lines). Absent otherwise.
   - **flag** (`trunk` runs) — `flag: <Key> | none`; plus
     `live: <what> — <why backward compatible>` for a change no flag can hide
     (migration, persisted format, manifest/permission, dependency bump),
     which becomes its own user-approved ticket.
   - **tier** — `tier: mechanical | standard | deep`: how much judgment the
     work needs; it picks agent, model and spawn effort
     (`start`/references/effort-mapping.md, *Tier → agent and model*).
     `mechanical` only when *What to build* plus the brief leave zero design
     decisions (exact names, signatures and target files known). In doubt →
     `standard`.
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
6. Publish to the shared backlog (`work-tickets`/references/backlog.md).
   Draft each body at `.scratch/<slug>/drafts/NN-<slug>.md` with every
   item-4 field plus `effort:` and `tier:` lines. Then publish in `NN`
   order, so `--blocked-by` can name ids that already exist:
   `backlog.py new --title "NN — <title>" --type enhancement --area <area>
   --epic <slug> [--blocked-by <ids>] --body-file <draft>`. Hardening
   tickets for a bug use `--type bug`; the device-acceptance ticket gets
   `--hands-on`. Ledger `ticket: NN → <id>`. From here the backlog is the
   source of truth and drafts are never edited again. Claims, the frontier
   and closing belong to `implement`; `trunk` blockers count as done once
   their PR merged.
7. Prototype sets: DoD = the question answered or the thing demoable; the
   last ticket carries the `deploy:` flag (`main | standalone | none`).
8. Confirm: each ticket carries `effort:` (`fast | standard | thorough`) and
   `tier:` lines — effort per the per-task rules in `start`'s
   effort mapping (thorough only for architecture/planning/big-view tickets),
   tier per item 4. Downgrades below the run default follow the Downgrade ask
   (`start`/references/effort-mapping.md § Rules). Post the numbered list
   (title, effort / tier, blocked-by, what
   it delivers) and proceed at every effort level. Ask about granularity only
   when the ticket count gate fires or the user asked to see the list first
   (references/slicing.md § Ticket count gate, § Ticket confirm).
9. Design review (stage B, `goldfish-review`): before publishing, when the
   set adds a module or boundary or the run is thorough, ask the user whether
   they want a blind design review — none / up to 3 / all lenses (recommended:
   all at thorough, up to 3 otherwise), one question, in the gate's form when
   it fires. fast, or nothing architectural → skip silently. Findings land as
   ticket edits or file-map changes, never a second interview.

Adapted from mattpocock/skills (`to-tickets`) and obra/superpowers
(`writing-plans`), MIT.
