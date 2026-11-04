# Architecture rules — mini payload

The user's swappable rules payload (GLOSSARY: rules payload): replace per
user or project; the `design-architecture` procedure stays generic. Built on
the five-part rule template from ciembor/agent-rules-books (MIT): modal
strength MUST / SHOULD / MUST NOT, every rule cited to its source book. The
books themselves are the full-class reference; the bias list below is the
nano-class core.

## When to use

Designing or changing modules, placing a seam, choosing an interface, or
grading a diff's dependency direction — draft-spec's architecture section,
implement's architecture-heavy tickets, review-change's thorough tier.

## Primary bias to correct

Defaults this payload exists to kill (nano bias list from
ciembor/agent-rules-books, plus the books cited below):

- Shallow wrappers mistaken for good abstraction: interface as complex as
  the implementation.
- Framework-first design: layers shaped around the framework, not the policy.
- Fake layering: clean-architecture diagram in the README, imports ignoring
  it.
- Speculative seams: interfaces with a single production adapter and no test
  fake.
- Hidden consistency contracts: invariants no interface states.

## Decision rules

1. The dependency rule: source dependencies point inward, toward policy —
   UI, database, network, and framework code depend on business rules;
   business rules never name them. MUST. (Clean Architecture)
2. High-level modules MUST NOT import low-level details; both depend on
   abstractions, and the high level owns the abstraction (DIP). Cross every
   seam with an interface owned by the caller side. MUST. (Clean Architecture)
3. One module, one reason to change, one stakeholder who would ask for that
   change (SRP). A reason to change is about policy, not file size — a deep
   module serving one stakeholder is fine. MUST. (Clean Architecture)
4. Subtypes MUST be substitutable without the caller checking what it got
   (LSP): a test fake honors the same invariants and error modes as the real
   adapter. MUST. (Clean Architecture)
5. Callers MUST NOT depend on methods they never use (ISP): split a wide
   interface only where real caller needs diverge. SHOULD. (Clean Architecture)
6. Extension points only where variation is real (OCP as aim, not ceremony):
   open for extension where two adapters exist; closed elsewhere. SHOULD.
   (Clean Architecture)
7. Every added module, layer, helper, wrapper, facade, pattern, option, or
   argument MUST hide more complexity than it adds. (A Philosophy of
   Software Design)
8. MUST NOT add pass-through modules or methods — an interface that merely
   repeats its implementation. (A Philosophy of Software Design)
9. Decompose to hide what is likely to change; the interface MUST NOT leak
   implementation choices (information hiding). (A Philosophy of Software
   Design)
10. Frameworks, databases, and I/O stay at the outer ring behind adapters;
    business rules MUST NOT import framework types. (Clean Architecture)
11. Module names come from the ubiquitous language; each bounded context owns
    its model, and models are translated — never shared — across contexts
    (anti-corruption layer at the seam). MUST. (Domain-Driven Design)
12. Keep behavior changes, structural refactoring, and cleanup separate;
    before redesigning a touched seam, control it with characterization
    tests. MUST. (Working Effectively with Legacy Code)
13. Separate data, domain, and UI. The domain layer holds business rules and
    models and MUST NOT import data-source or UI types; data sources implement
    domain-owned interfaces; UI renders state and delegates operations. MUST.
    (Clean Architecture)
14. Non-trivial business operations become use cases: one operation each,
    thin, dependencies injected as interfaces — so each tests with fakes
    alone, no UI, no framework. A use case is born when orchestration (two or
    more sources/policies) appears inside a ViewModel or Composable. MUST.
    (Clean Architecture interactors)
15. Non-trivial interactive UI (multi-step flows, gestures, async-driven
    screens) is modeled as an explicit state machine: states, events,
    transitions in a plain testable class; the Composable renders state and
    never owns transition logic; every transition is unit-tested without
    composing UI. MUST. (GoF State; user bar)
16. Use a named pattern (repository, use case, state machine, adapter, factory)
    only when its forcing function is present; when it fits, follow its
    canonical shape instead of inventing a variant. MUST NOT pattern-drop.
    (Patterns of Enterprise Application Architecture)
17. File discipline (user bar, overrides rule 3's scope note where they
    conflict): a file holds one task or one abstraction and stays short; a
    second responsibility or a growing symbol table is the split signal —
    split by responsibility, not by line count alone. MUST. (user bar,
    2026-10-29; SRP per Clean Code)
18. Dispatchers, clocks, and scopes are injected, never hardcoded: classes
    take a DispatcherProvider (or injected `Dispatchers` values) so tests run
    virtual time deterministically. `Dispatchers.IO` / `Dispatchers.Default`
    appear only in the composition root that builds the provider. MUST.
    (kotlinx-coroutines-test guidance; user bar)
19. ViewModels expose read-only state: a private `MutableStateFlow`/field per
    concern, exposed as `StateFlow`/`State`; no public mutable fields, no raw
    `var` state. One exposed stream per concern, combined in one data class
    when the screen needs several. MUST. (Android state-holders guidance;
    user bar)
20. One public top-level type per file, in every layer: a file holds ONE
    public class/interface/object/composable (plus private helpers, its own
    extensions, typealiases, and previews). Several public top-level types
    sharing a file — however idiomatic the language — is the split signal;
    split before stacking a second. A sealed hierarchy either nests its
    variants inside the parent (one type) or gives each top-level variant its
    own file (`micro-architecture`). MUST. Mechanical check:
    `structure-checks`. (user bar; sharpens rule 17)

## Trigger rules

- Adding a module, layer, helper, wrapper, facade, pattern, option, callback,
  or argument → prove rule 7 first, in the decision note. (APoSD)
- A diff adds an import from an inner ring to an outer one → stop: invert at
  the caller's seam (rules 1–2) before any other fix. (Clean Architecture)
- Two call sites need different implementations at one point → real seam:
  introduce the interface at the caller side, one adapter per side. (DIP)
- Adding a variant of an existing behavior (new card type, new source, new
  payment flow) → extend by adding a subtype/adapter behind the existing
  interface; editing the dispatcher or the sibling implementations to accept
  the variant is an OCP violation. (Clean Architecture)
- A test must reach past an interface → shape problem, not test problem:
  deepen or re-place the seam (rules 8–9). (APoSD)
- Naming a module Manager, Helper, Util, ServiceImpl → language gap: name it
  from the project glossary (rule 11). (DDD)
- Touching a legacy module → rule 12 first: characterization tests before
  redesign; structure in its own commit. (WELC)

## Final checklist

- Every changed import edge points inward: policy ← details.
- Every new module hides more complexity than it adds; none is pass-through.
- Every seam has two adapters (production + test fake) or a recorded reason
  for one.
- Each interface carries only what callers must know: types, invariants,
  ordering, error modes.
- No caller type-checks its dependency; fakes honor invariants and error
  modes.
- No business rule imports a framework type.
- Module names speak the domain glossary; context edges translate, not share.
- Load-bearing decisions live in a spec contract or an ADR.
- data / domain / UI edges hold: domain imports none of them.
- Orchestrations are use cases; each tests against fakes only.
- Interactive screens have an explicit state machine; transitions tested headless.
- Patterns in the diff carry their forcing function in the decision note.
- No file serves two responsibilities; the split signal was acted on.
