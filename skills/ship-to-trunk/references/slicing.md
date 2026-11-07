# Slicing — tickets that can merge before the feature is done

Read when writing tickets for a `trunk` run, when a ticket looks too big for
one PR, or when a change cannot hide behind a flag.

## Shape of a feature

| Ticket | Lands | Flag |
|---|---|---|
| 01 flag | release flag, off in release, debug toggle | adds `<Key>` |
| 02..N slices | domain, data, UI pieces behind the flag; each builds and passes alone | gated |
| shared-file edits | registry / DI module / nav graph / `when` entry, alone and first | gated or inert |
| hardening (after user-check) | tests pinning approved behavior, fixes | gated |
| flip | release default on, version bump, changelog | flips `<Key>` |
| cleanup | remove flag, dead branch, override | removes `<Key>` |

Every ticket names `flag: <Key> | none` and, for invariant-7 changes,
`live: <what> — <why it is backward compatible>`.

## Making a slice mergeable

- **Gate at the entry, not everywhere**: one check at the route, menu item,
  use-case binding or DI choice. Code below the gate is ordinary, testable
  code that nothing reaches in release.
- **Additive first**: new class, new function, new module beside the old
  one; switch callers in a later slice behind the flag.
- **Branch by abstraction** for replacements: introduce the seam (interface
  over the old implementation, no behavior change) → add the new
  implementation behind the seam → flag selects → flip → delete the old
  implementation in the cleanup ticket.
- **Tests travel with the slice**: both flag states are covered where
  behavior differs (JVM test per state; screenshot per state for UI).
- **Inert wiring is fine**: an unused API, an empty screen behind a gated
  route, a repository nothing calls yet.

## Unflaggable — ship live, backward compatible

| Change | Rule |
|---|---|
| Room/SQL schema | expand/contract: additive migration (new table/column, nullable or defaulted) ships first; the code stops reading the old shape only after the flip; destructive migration only in the cleanup ticket. Migration test per version. |
| Persisted formats (DataStore, files, Firestore docs) | readers accept old and new before any writer writes new; new fields optional; never rename in place. |
| Manifest, permissions, exported components | own ticket, user approves; a new permission prompt is user-visible even if the feature is dark. |
| Dependency / SDK / Gradle bumps | own ticket, no feature code in the same PR. |
| Public API of a published module | additive only until the flip; removal follows the module's deprecation cycle. |

Old installed versions keep running against shared data (Firestore,
backend): anything they read must stay readable until the minimum supported
version moves.

## Too big for one PR

Split by layer seam (domain → data → UI), by variant (one file per variant,
`micro-architecture`), or by scaffold then fill (inert route first, content
next). A ticket whose diff is mostly one new file of > ~400 lines is a
structure problem, not a slicing problem (`structure-checks` S2).
