# Deep modules

Full vocabulary and deepening patterns behind `design-architecture`. Adapted
from mattpocock/skills (`codebase-design`, `DEEPENING.md`,
`DESIGN-IT-TWICE.md`), MIT. Read when deepening a module, testing past an
interface, or designing a load-bearing interface.

## Vocabulary

Use these terms exactly; don't substitute "component", "service", "API", or
"boundary".

- **Module**: anything with an interface and an implementation — a function,
  class, package, or tier-spanning slice. _Avoid:_ unit, component, service.
- **Interface**: everything a caller must know to use the module correctly:
  the type signature plus invariants, ordering constraints, error modes,
  required configuration, performance characteristics. _Avoid:_ API,
  signature (type-level surface only).
- **Implementation**: what's inside. A thing can be a small adapter with a
  large implementation (Postgres repo) or a large adapter with a small one
  (in-memory fake); say "adapter" when the seam is the topic.
- **Depth**: leverage at the interface — behavior per unit of interface the
  caller must learn. Deep = lots of behavior behind a small interface;
  shallow = interface nearly as complex as the implementation.
- **Seam** (Feathers): a place where behavior can change without editing that
  place; where a module's interface lives. _Avoid:_ boundary (collides with
  DDD's bounded context).
- **Adapter**: a concrete thing satisfying an interface at a seam — role, not
  substance.
- **Leverage** / **locality**: what callers get (capability per interface
  learned) / what maintainers get (change, bugs, and verification concentrate
  in one place).

## Tests of a module

- **Deletion test**: imagine deleting the module. Complexity vanishes → it
  was a pass-through. Complexity reappears across N callers → it was earning
  its keep.
- **The interface is the test surface**: callers and tests cross the same
  seam. A test that must reach past the interface means the module is the
  wrong shape.
- **One adapter = hypothetical seam; two = real.** Don't introduce a seam
  unless something actually varies across it. Production adapter + in-memory
  test fake = two.
- Depth is a property of the interface, not the implementation: a deep module
  may be composed of small swappable parts internally — they are just not
  part of the interface (internal seams stay private to the implementation
  and its own tests).

## Deepening a cluster

Classify the dependencies first; the category decides how the deepened module
is tested across its seam:

1. **In-process** (pure computation, in-memory state): always deepenable —
   merge and test through the new interface; no adapter needed.
2. **Local-substitutable** (a local test stand-in exists, e.g. in-memory DB
   or filesystem): deepenable if the stand-in exists; test with it; the seam
   stays internal.
3. **Remote but owned** (your own services across the network): define a
   port at the seam; the deep module owns the logic; transport is injected as
   an adapter (HTTP/gRPC in production, in-memory in tests).
4. **True external** (third-party services you don't control): the deepened
   module takes the dependency as an injected port; tests provide a mock
   adapter.

Replace, don't layer: once tests exist at the deepened module's interface,
the old unit tests on the shallow parts are waste — delete them. New tests
assert observable outcomes through the interface and survive internal
refactors; a test that changes when the implementation changes is testing
past the interface.

## Design-it-twice

For a load-bearing interface: spawn 3+ parallel subagents, each producing a
radically different interface under a different constraint — minimize entry
points (1–3) / maximize flexibility / make the common caller trivial /
ports-and-adapters. Compare on depth, locality, and seam placement; recommend
one opinionatedly, or propose a hybrid. First ideas are rarely best
(Ousterhout).
