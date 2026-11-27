# Effort mapping

The one table: effort level → gates and knobs. `start` reads it to build the
run plan; `implement` enforces the subagent knobs at dispatch. *Tier → agent
and model* below is the only place model IDs appear; every other skill points
here.

| effort | subagent thinking (spawn `effort`) | reviewer model | research fan-out | intake gear | blind review (`goldfish-review`) | spec checkpoint | ticket confirm | review tier |
|---|---|---|---|---|---|---|---|---|
| fast | low | see *Tier → agent and model* | skip (only when a ticket is blocked) | focused | none (not asked) | post-and-proceed | post-and-proceed | lint + screenshots + design-only reviewer |
| standard | medium | see *Tier → agent and model* | 1 per unknown, cap 3 | focused | stage A: 0–2 lenses by risk after the checkpoint, not asked; stage B asked, recommend up to 3, only if architecture-heavy | blocking | post-and-proceed | one code reviewer (also fills the design rows), not two |
| thorough | high | see *Tier → agent and model* | full parallel fan-out | deep if high stakes, else focused | stage A: 0–2 lenses by risk after the checkpoint, not asked; stage B asked, recommend all | blocking | post-and-proceed | + dual-verdict + visual reviewer, once per feature range before the release (`pr`/`main`: once per change), never per slice |

Ticket confirm blocks at no effort: the list is posted and the run proceeds;
`write-tickets` asks about granularity only when its ticket count gate fires
or the user asked to see the list first (`write-tickets`/references/slicing.md
§ Ticket confirm).

## Tier → agent and model

Two independent axes per ticket: `effort:` decides gates and quality work
(table above, unchanged); `tier:` decides how much judgment the work needs,
and so the agent and model. A thorough run can hold a mechanical ticket and a
fast fix can need judgment: never derive one from the other.

| tier | work | implementer dispatch | spawn `effort` |
|---|---|---|---|
| `mechanical` | fully specified edits: renames, DI/nav registration, strings/resources, gradle deps, fixtures, moving code with no behavior change, call-site migration batches | `agent: sonic`, no `model` | `lo` |
| `standard` | ordinary feature/fix work with local decisions | ticket `effort: fast` → `agent: task`, `model: anthropic/claude-haiku-5-5:high` (cheap, so high thinking: a weak implementer costs more in fix loops than in tokens); `effort: standard`/`thorough` → `agent: task`, no `model` (Sonnet medium) | fast → omit (the `:high` model suffix sets thinking); standard → omit, thorough → `hi` |
| `deep` | the ticket names an open design for a new module or boundary, concurrency, or a state machine | `agent: task`, `model: anthropic/claude-opus-5-5:xhigh` | `hi` |
| `open` | a big open question the spec left open on purpose: the design itself is unresolved (competing architectures, no prior art in the repo, the choice reshapes several modules), or a `deep` worker failed twice | `agent: task`, `model: anthropic/claude-fable-5-2:high` | `hi` |

Defaults when write-tickets did not set `tier:`: `effort: fast` → `standard`;
`standard` → `standard`; `thorough` → `deep` only if the ticket is
architecture-heavy (`implement` §3: new module, new boundary, dependency
direction in play), else `standard`.

`open` is rare: a run plan holding more than one `open` ticket names each
one's open question in a line, or downgrades it to `deep`. A new module,
boundary, state machine or concurrency is `deep`, not `open`, when the spec
or contract already decides its shape.

Never `deep` or `open`: test-only tickets (pins, characterization,
coverage), behaviour-preserving refactors whose target shape is given, and
work against an API the ticket already specifies. "Expensive if wrong" is
not a tier: a `standard` worker that fails escalates (below).

Work outside tickets:

| work | dispatch |
|---|---|
| `user-check` fast fixes (`mode: fast-fix`) | `standard` tier at most: `agent: task`, no `model`; spawn `effort` omitted |
| hardening tickets from the re-gate | their own `tier:` per the table above; never `open` |
| `user-check` re-gate (designer hat, fresh context) | `agent: task`, `model: anthropic/claude-opus-5-5:xhigh`, `hi` |
| `assess-teardown` architect | `agent: task`, `model: anthropic/claude-fable-5-2:high`, `hi`: fix-forward vs redesign is an open question by definition |

Reviewer and research dispatch:

| use | dispatch |
|---|---|
| fast review tier, design-only reviewer (every per-slice review, at any run effort: exactly one reviewer per slice) | `agent: reviewer`, spawn `effort: lo`; `model: anthropic/claude-haiku-5-5:low` when every reviewed ticket is `mechanical` or `effort: fast`, else no `model` (Sonnet) |
| standard review tier, the one code reviewer (design rows + code review) | `agent: reviewer`, no `model` (Sonnet high, a stronger tier than the Sonnet-medium implementer) |
| thorough dual-verdict / fresh visual reviewer (once per feature range, never per slice; the code reviewer above runs with them) | `agent: reviewer`, `model: anthropic/claude-opus-5-5:xhigh` |
| fan-out-research, code/repo questions | `agent: scout` (Haiku), no `model` |
| fan-out-research, web/primary-source questions | ticket `effort: fast` → `agent: task`, `model: anthropic/claude-haiku-5-5:low`, spawn `effort: lo`; standard → `agent: task`, no `model`, omit `effort`; thorough → `agent: task`, no `model`, `hi` |
| brief context gathering (neighbor interfaces, file-scope facts) | `agent: scout` |

Orchestrator by stage (who runs each stage: lifecycle.md):

| stage | orchestrator | model |
|---|---|---|
| triage, intake, spec, UI contract, goldfish gates, ticketing | main session | the session's launch model: `anthropic/claude-opus-5-5` (`anthropic/claude-fable-5-2` when the user launches it for thorough design); the agent never switches it |
| user-check F-id triage, taste rulings, asks, approvals, release, milestone digests | main session | same launch model; taste stays off Sonnet |
| execution milestone after spec freeze: slices, user-check build, one fix round, hardening + review, deliver | captain, one fresh spawn per milestone | `agent: task`, no `model` (Sonnet); spawn `effort` omitted, `hi` at run effort `thorough` |
| quick task, quick prototype, bug diagnosis | main session, no captain | launch model |

- Fable (`anthropic/claude-fable-5-2`) runs only where these tables name it:
  the `open` tier, the `assess-teardown` architect, and a main session the
  user launched on it. Any other Fable spawn, per-slice reviewers and
  fast fixes included, is a defect: dispatch per the table instead, or ask.
- Never pass `model` to `scout` or `sonic`: the harness pins them to Haiku,
  and a per-call `model` on a pinned agent is a preflight conflict error.
- Spawn `effort` is `lo`, omitted or `hi`. Never pass `med`: measured
  2026-11-07, `med` ran at high thinking, same as `hi`; omitting it keeps
  the agent's default (medium for `task`). Never request above `hi`.
- Spawn `effort` is the real thinking budget. The dispatch voice line's
  "think in short notes" half (start § Voice) is best effort: the model may
  not follow it, and the displayed thinking may be a harness summary.
- Escalation (cheap first, pay only on failure): a `mechanical` worker or a
  Haiku `effort: fast` worker that returns BLOCKED or NEEDS_CONTEXT twice,
  or fails its DoD after one fix round, is re-dispatched one tier up
  (`mechanical` → `standard`; Haiku fast → Sonnet: `agent: task`, no
  `model`; then `deep`; a `deep` worker that fails twice → `open`). Ledger:
  `Ruling: NN escalated <from>→<to> — <why> — <cost if wrong>` (Haiku step:
  `escalated haiku→standard`). Never escalate pre-emptively.
- `:xhigh` needs omp `task.maxEffort: xhigh` and the model approved through
  a `modelRoles` entry (`deep: anthropic/claude-opus-5-5:xhigh`). A spawn
  rejected for the model → re-dispatch with `anthropic/claude-opus-5-5:high`
  and say so once in the run plan.

## Rules

- **The main session plans, splits and routes.** It never implements a
  ticket itself and never reads files to build a brief that a `scout` could
  gather.
- **Per-task effort is the rule; run-wide effort is the default.** Every task
  and ticket gets its own effort level, chosen at triage/ticketing from task
  shape — not inherited from the run default.
  - `thorough` only for big-view work: architecture, new module design,
    cross-cutting refactors, planning, irreversible or data-loss-risk changes.
  - `standard` for ordinary feature tickets.
  - `fast` for contained fixes, config, copy, single-file changes, quick tasks.
- Downgrade ask: when the agent picks a lower level than the run default for a
  task, it says so in the run plan / ticket list in one line ("ticket 3 downgraded
  to fast: single-file fix") — if it believes a different level would accelerate
  development, it asks the user instead of silently deciding. The run plan
  states each ticket's tier next to its effort
  (`ticket 3: fast / mechanical → sonic`).
- Per-session override (`/start fast|standard|thorough`) still wins for the run
  default; per-ticket effort overrides the run default unless the user set the
  override explicitly.
- A prototype flag caps gates at the fast tier at any effort (subagent
  thinking still follows the table).
- The quality-vs-speed knob is the effort level — except inside the
  `user-check` feedback loop, where fast fixes ignore code quality at every
  effort and the re-gate pays it down. `user-check` itself runs at every
  effort; only its check doc scales.
- Tests: ticket cycles and fix rounds run touched-module tests; once per
  run, in `review-change` after the fix loop converges, the tests the
  change can break (PROFILE `affected-check:`, else the full suite), at
  every effort. The full suite otherwise runs only on main's post-merge CI
  and when a red main nobody expected escalates (`ship-to-trunk` § Red
  main).
- Review-site publish: `thorough` defaults to yes (the `user-check` check
  doc is the primary hands-on surface); fast/standard follow the run's decision
  (PROFILE `Review site publish:` or the session answer in start's plan).
  An explicit user no always wins.
- `implement` reads the same table at dispatch time; `start` does not
  re-derive it per stage.
