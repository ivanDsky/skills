# Lens catalog

Each lens is a fresh subagent with one objective. The dispatch prompt names
the lens and points here; the subagent reads only its own section, the brief
file, and the repo. Knowledge skill = the existing skill whose method the
lens follows (the subagent reads that skill's SKILL.md). Every finding needs
evidence; "no findings" must list what was checked.

Common ask for every lens: *find what is wrong, missing, or expensive from
your angle; cite evidence; propose one disposition; do not redesign the
feature.*

## Stage A — concept (input: hypothesis + hard constraints)

### reuse
- Objective: what already exists (in this repo, the platform, the stdlib, an
  installed library) that does part of this, and which part of the
  hypothesis can be cut without losing the point.
- Knowledge skill: `ponytail` (understand → reuse → adapt → extend → new code
  last). Evidence: repo search, project map, dependency list.
- Tension partner: best version (cut vs add).

### persona flows
- Objective: walk each persona through the first use, the happy path, and an
  interrupted path (back, kill, no network); name every point they stall,
  misread, or need something the hypothesis does not give.
- Personas come only from PROFILE.md's Product frame or ones the user named in
  the brief — never invented. At most 3; none available → lens is skipped and
  reported as not run (reason: no personas).
- Knowledge skill: `senior-ux`. Evidence: existing screens and flows in the
  repo the new flow must sit beside.

### data and migration
- Objective: what is stored, where, and what the change does to data that
  already exists — schema changes, migration and rollback, defaults for old
  rows, backup/restore, export/delete obligations, size growth.
- Knowledge skill: `senior-dev` (Room migrations are the usual case).
  Evidence: current schema, existing migrations, DAO/entity files.
- Skip-with-reason when the hypothesis stores nothing: report "no persistent
  data touched — checked: <where>", not silence.

### failure and resources
- Objective: how it behaves under process death, configuration change,
  permission denial, no/slow/flaky network, background limits, battery,
  rate limits or quotas, very large or empty inputs, and concurrent use.
- Knowledge skill: `senior-dev`; `android-env` for platform facts. Evidence:
  how comparable existing features in the repo handle the same failures.

### best version
- Objective: the generative counterweight. What would make this feel great
  rather than merely done — what small, adjacent additions give outsized
  clarity or delight, what the best comparable products do. Every suggestion
  carries a rough cost (cheap / moderate / costly) and is marked optional.
  It proposes; it never demands, and it never reopens a hard constraint.
- Knowledge skill: `apple-design`, `emil-design-eng`, `ui-ux-pro-max` for UI;
  `animation-vocabulary` to name any motion. Evidence: references the user
  gave in the brief, existing app style.
- Tension partner: reuse (add vs cut) — the parent records the tension; this
  lens does not self-censor to avoid it.

### verifiability
- Objective: for each likely success criterion, can it be proven without a
  device — JVM unit/semantic test, preview render, screenshot test — and what
  seam would make that possible (injectable clock/dispatcher, fake data
  source, stable test tags)? List what cannot, and the minimum human
  acceptance step for it.
- Knowledge skill: `tdd` (`references/android-testing.md` ladder). Evidence:
  existing test setup in the repo.

## Stage B — design (input: spec + module map + file maps)

### architecture
- Objective: module boundaries, dependency direction, and whether the file
  maps respect them; one-adapter seams with no forcing function; missing
  boundaries.
- Knowledge skill: `design-architecture` with
  `references/rules-architecture.md` (its scope gate: reusable UI components
  are graded against `micro-architecture`'s `ui-components.md` at the
  ledgered `ui-tier`, never handed a domain layer or ViewModel). Evidence:
  module map, imports in the files the tickets touch.

### patterns
- Objective: does the design make part N+1 a new file where the spec's
  **Extension points** assumption says it should, and no further? Is every
  introduced pattern one the repo already uses (consistency) or has a named
  forcing function? Is the simplest pattern chosen (sealed/enum before
  Factory, registry before Abstract Factory)?
- Knowledge skill: `micro-architecture` (its pattern table).
  Evidence: existing variation points in the repo, the Extension points
  assumption.
- Tension partner: reuse (seam vs YAGNI) — the parent records it.

### file structure
- Objective: read each ticket's file map: any line whose responsibility
  needs "and"; several public types in one file (rules-architecture 20,
  `structure-checks` exceptions list); a shared `when`/registry that tickets
  must edit in parallel; file scopes that overlap between parallel tickets;
  files that will exceed the size tripwire. In `trunk` runs: can each
  ticket merge alone and dark — `flag:` named, live changes identified
  (`live:`), shared-file edits first-merged (`ship-to-trunk`/references/slicing.md)?
- Knowledge skill: `micro-architecture`, `structure-checks`
  (`references/rules-structure.md`). Evidence: the file maps and the files
  that exist today.
