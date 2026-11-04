---
name: micro-architecture
description: >-
  Feature- and task-level architecture — not app architecture. Splits work
  into files/classes so agents can run them in parallel: file-disjoint
  scopes, open/closed extension (new behavior = new file, not edits to
  existing ones), single responsibility at the smallest useful grain (one
  interaction, one decision per file). Use when designing a feature, before
  writing tickets, or when parallel dispatch keeps colliding on shared
  files.
interaction: afk
requires: [design-architecture for cross-app structure]
---

> **TL;DR** Design the feature so that adding part N+1 is a new file and part N is untouched; every file owns one small thing; disjoint files = parallel agents with zero merge conflicts.
> **Related**: skill://write-tickets (file-disjoint tickets are the output contract), skill://implement (parallel dispatch), skill://design-architecture (cross-app structure — this skill stops where that one starts), skill://senior-dev (the judgment defaults), skill://structure-checks (mechanical enforcement of one responsibility per file), skill://goldfish-review (patterns and file-structure lenses at stage B)

# Micro-architecture — the shape of one feature

App architecture decides where modules live and how they talk. Micro-
architecture decides how ONE feature (or one ticket) decomposes into
files — optimized for three goals in order: parallel agent execution,
extension without modification, and the smallest honest responsibility
per file.

## 1. Parallel-first file split

The unit of parallelism is the file. Before any code exists, draw the file
map:

- **File-disjoint waves**: list the files each unit of work touches; if two
  units touch the same file, they are one unit (or get a blocking edge).
  Two agents editing one file = serialized anyway, plus conflict risk
  (audited: five tickets serialized on one shared screen file — 107 minutes
  of pure wait that a different split would have parallelized).
- **Interfaces cross tickets only as exact signatures**: written once,
  verbatim, in both the producing and consuming ticket. The producer owns
  the file; the consumer codes against the signature and stubs the rest.
- **Shared surface is designed BEFORE fan-out**: the one file everyone
  would touch (a screen, a registry, DI wiring) is either built first in a
  tracer-bullet ticket, or split so each agent owns a distinct slice
  (extension point + their own file).

## 2. Open/closed at file granularity

Adding part N+1 must mean: new file + at most one-line registration. Never
modifying part N's logic.

- Prefer **registries, maps, and sealed hierarchies with per-entry files**
  over `when`/`if` ladders inside shared files. A new variant, provider,
  tool, or screen = a new class/file implementing the interface; the engine
  (the dispatcher that iterates the registry) does not change.
- The **engine/plugin seam**: common, stable core owns iteration and
  dispatch; each variant is a self-contained validating/behaving unit.
  Rules-as-self-contained-classes is the canonical shape — swappable,
  testable in isolation, O(n) to verify.
- If adding a feature requires editing two existing files, the split is
  wrong: extract the variation point first (that refactor is its own
  ticket, done before the fan-out).

### Patterns that buy this (reach for these first)

| Pattern | Use it when | Why it simplifies agent work |
|---|---|---|
| **Strategy** | one behavior, many interchangeable implementations (validators, sorters, pricing rules) | each strategy is one file, parallel-writable; swap without touching callers |
| **Factory / Abstract Factory** | object creation scatters `if`-branches by type or platform | creation lives in one file; adding a type touches only the factory's registry |
| **Registry (plugin map)** | many self-contained units discovered by key | the canonical OCP shape: part N+1 = new file + one registration line |
| **Command** | user actions / undoable operations / queued work | each command is one file with one `execute`; history, undo, queue come free |
| **Facade** | a subsystem with many parts behind one call site | consumers code to the facade; you can rewrite the subsystem without breaking agents working on consumers |
| **Adapter** | third-party or legacy API doesn't match your interface | the mismatch is quarantined in one file; swapping the dependency = new adapter |
| **Observer / Flow** | state changes must reach several unrelated listeners | producers and consumers are file-disjoint; new listener = new file, zero producer edits |
| **Template Method** | several variants share a skeleton but differ in steps | skeleton owned once; each variant overrides only its steps in its own file |
| **Chain of Responsibility** | a request passes through optional stages (middleware, interceptors, validation steps) | each stage is one file; insert/reorder without touching stages |
| **Specification** | business rules as composable predicates | rules are one-line-testable files; combine instead of nesting ifs |
| **Repository** | data access behind an interface | UI/domain code never touches the data source; fakes for tests are one file |

Rules of use: pick the **simplest pattern that makes part N+1 a new file** —
a registry beats Abstract Factory when one map line suffices; don't stack
patterns (Facade over Repository is common and fine; Factory inside
Strategy inside Command is a smell). In Kotlin, sealed classes + enums often
replace Factory/Registry entirely — one file, compiler-checked coverage.

## 3. Single responsibility — small enough to state as one sentence

Every file/class gets a one-sentence job description. If the sentence
contains "and", split it. The right grain is usually smaller than feels
natural:

- one **interaction** (drag-to-dismiss) per handler,
- one **decision** (which variant applies) per resolver,
- one **state machine** per owner — never two state enums in one file.

Why it matters beyond taste: small files are (a) trivially reviewable, so
the reviewer's diff read is real reading; (b) merge-trivial under parallel
agents; (c) testable without scaffolding for unrelated concerns.

## 4. Design order for a feature

1. Name the stable core (what part N+1 will NOT touch) — this is the
   engine/seam.
2. Define the extension interface (exact signatures, in one file).
3. List the variants/units; one file each; check they are mutually
   file-disjoint.
4. Build the core + one variant as a tracer bullet — end-to-end, tested —
   before fanning out the rest.
5. Hand the remaining variants to parallel agents; each adds files only.
6. Registration/wiring lands in one closing ticket (or was a one-line slot
   from step 2).

## Anti-patterns

- **Hot file**: every ticket touches the same screen/viewmodel — split the
  screen into per-feature composable files or serialize honestly.
- **Breadth-first prototypes**: many variants of every axis built before a
  narrow-down gate (audited: ~7 tickets of churn, user kept two). Build
  one variant per axis, let the user pick, then fill.
- **Interface by conversation**: signatures negotiated in agent messages
  instead of written in a file both tickets cite — the audited source of
  merge conflicts and stale handoffs.
- **expect/actual by reflex** (KMP): platform-gating chosen without
  checking the KMP constraint actually applies — cost a dead-end detour.
  Check the constraint first, then choose the mechanism.
