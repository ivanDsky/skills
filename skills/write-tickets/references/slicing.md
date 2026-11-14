# Slicing — fewer, bigger tickets

Read when sizing or merging tickets (SKILL.md item 3), when the plan nears
~25 tickets, or when writing UI tickets under a frozen contract. Every ticket
pays a worker, a review and a merge; a week of audited runs spent 1,840
subagents, a 37-ticket plan was approved in a minute, and one plan grew from
39 to 74 tickets. The unit of cost is the ticket, so cut fewer.

## Default slice

One user-visible capability, end to end through one module chain (data →
domain → ViewModel → UI), demoable on its own. Never one layer. A capability
too big for one ticket splits into a thinner capability (one state, one
variant, one entry point), never into layers.

## Merge the mechanical pieces

DI and nav registration, strings and resources, a gradle dependency, and the
call-site migration of the slice's own callers belong to the slice that needs
them. They are not tickets. The merged ticket takes the tier of its judgment
core (`start`/references/effort-mapping.md, *Tier → agent and model*) and
keeps one checkable DoD.

Stay separate only when:

- a shared file is touched by parallel slices (registry, DI module, nav graph,
  `when` entry): one shared-wiring ticket first, or the extension slot from
  `micro-architecture`, so the slices stay file-disjoint; `trunk` runs always
  do this (SKILL.md item 2);
- a repo-wide migration would break the size ceiling: expand–contract batches,
  each `tier: mechanical`, old form deleted last;
- the change is a dependency or SDK bump, a persisted-format migration or a
  manifest/permission change: own ticket (`ship-to-trunk`/references/slicing.md).

## Size

- Target: ≤ ~12 tickets per milestone. More → group into milestones; the
  digest points are the milestones (`start` § Decisions and waiting).
- Ceiling: ~600 changed production lines per ticket. Tests, goldens,
  resources and generated files do not count. Split above it, before
  publishing. `trunk` runs keep their tighter ~400-line cap.
- Floor: a piece under ~100 lines with no DoD of its own merges into the
  neighboring slice.
- Parallelism still wins over size: two capabilities with disjoint file scopes
  stay two tickets even when small (SKILL.md item 5).

## Ticket count gate

A plan over ~25 tickets for a design the user has not validated is split.
Validated means one of: a frozen contract under `.scratch/<slug>/contract/`, an
approved and graduated prototype, or a change inside an existing shipped design.
When the gate fires:

1. Publish only the prototype or contract milestone (`prototype`; the
   contract it produces is the freeze); deferred slices stay an outline in the
   spec, not tickets.
2. Tickets for the rest are written after the freeze, against the frozen
   contract.
3. Ask the user once whether to split, through the ask tool (`start` § Waiting
   on the user); the reversible default is the split.

A validated design over ~25 tickets is not split by this gate; it is cut into
milestones of ≤ ~12.

## UI contract lines

A ticket that changes a screen under a frozen contract carries, in its body:

```
Contract: .scratch/<slug>/contract/
Reference: <golden png path or test name> = reference/<screen>__<state>__<phone|tablet>__<light|dark>.png
```

One `Reference:` line per golden and reference pair, paths relative to the
contract directory. The contract holds `contract.md` (prototype URL, freeze
date, rulings), `acceptance.md` (one line per screen × state), `motion.md`
(confirmed motion values) and the reference screenshots. Rules:

- Required for every ticket under a frozen contract that renders UI; absent
  otherwise, never an empty placeholder.
- The slice's per-screen `acceptance.md` lines become its DoD material; motion
  values come from `motion.md` and are never re-tuned in the ticket.
- A state with no reference screenshot has no `Reference:` line; say so in the
  ticket instead of inventing a pair.
- The reviewer and the visual gate diff the new goldens against these lines.

## Ticket confirm

Post the numbered list and proceed. Ask the user about granularity only when
the count gate above fires or the user asked to see it first. The effort level
does not turn the confirm into a blocking wait. Edges and sizing are the
agent's call; the downgrade line and the design-review question
(SKILL.md item 9) still apply.
