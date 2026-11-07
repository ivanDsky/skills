# Effort mapping

The one table: effort level → gates and knobs. `start` reads it to build the
run plan; `implement` enforces the subagent knobs at dispatch. *Tier → agent
and model* below is the only place model IDs appear; every other skill points
here.

| effort | subagent thinking (spawn `effort`) | reviewer model | research fan-out | intake gear | blind review (`goldfish-review`) | spec checkpoint | ticket confirm | review tier |
|---|---|---|---|---|---|---|---|---|
| fast | low | see *Tier → agent and model* | skip (only when a ticket is blocked) | focused | none (not asked) | post-and-proceed | none | lint + screenshots + design-only reviewer |
| standard | medium | see *Tier → agent and model* | 1 per unknown, cap 3 | focused | asked; recommend up to 3 (stage B only if architecture-heavy) | blocking | none | + code review |
| thorough | high | see *Tier → agent and model* | full parallel fan-out | deep if high stakes, else focused | asked; recommend all, stages A and B | blocking | blocking (edges + sizing) | + dual-verdict |

## Tier → agent and model

Two independent axes per ticket: `effort:` decides gates and quality work
(table above, unchanged); `tier:` decides how much judgment the work needs,
and so the agent and model. A thorough run can hold a mechanical ticket and a
fast fix can need judgment: never derive one from the other.

| tier | work | implementer dispatch | spawn `effort` |
|---|---|---|---|
| `mechanical` | fully specified edits: renames, DI/nav registration, strings/resources, gradle deps, fixtures, moving code with no behavior change, call-site migration batches | `agent: sonic`, no `model` | `lo` |
| `standard` | ordinary feature/fix work with local decisions | `agent: task`, no `model` (Sonnet medium) | from ticket `effort:` (fast → `lo`, standard → `med`, thorough → `hi`) |
| `deep` | new module/boundary, concurrency/state-machine logic, cross-cutting refactor design, anything where a wrong call is expensive to unwind | `agent: task`, `model: anthropic/claude-opus-5-5:high` | `hi` |

Defaults when write-tickets did not set `tier:`: `effort: fast` → `standard`;
`standard` → `standard`; `thorough` → `deep` only if the ticket is
architecture-heavy (`implement` §3: new module, new boundary, dependency
direction in play), else `standard`.

Reviewer and research dispatch:

| use | dispatch |
|---|---|
| fast review tier, design-only reviewer | `agent: reviewer`, `model: anthropic/claude-haiku-5-5:low` when every reviewed ticket was `mechanical`, else no `model` (Sonnet high) |
| standard review tier, code reviewer | `agent: reviewer`, no `model` (Sonnet high, a stronger tier than the Sonnet-medium implementer) |
| thorough dual-verdict / fresh visual reviewer | `agent: reviewer`, `model: anthropic/claude-opus-5-5:high` |
| fan-out-research, code/repo questions | `agent: scout` (Haiku), no `model` |
| fan-out-research, web/primary-source questions | `agent: task`, no `model`; spawn `effort` per the effort table (low/med/hi) |
| brief context gathering (neighbor interfaces, file-scope facts) | `agent: scout` |

- Never pass `model` to `scout` or `sonic`: the harness pins them to Haiku,
  and a per-call `model` on a pinned agent is a preflight conflict error.
- Spawn `effort` is `lo | med | hi` only; never request higher.
- Escalation (cheap first, pay only on failure): a `mechanical` worker that
  returns BLOCKED or NEEDS_CONTEXT twice, or fails its DoD after one fix
  round, is re-dispatched one tier up (`standard`, then `deep`). Ledger:
  `Ruling: NN escalated <from>→<to> — <why> — <cost if wrong>`. Never
  escalate pre-emptively.

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
- Full suite: once per run, in `review-change` after the fix loop converges,
  at every effort. Ticket cycles and fix rounds run touched-module tests.
- Review-site publish: `thorough` defaults to yes (the `user-check` check
  doc is the primary hands-on surface); fast/standard follow the run's decision
  (PROFILE `Review site publish:` or the session answer in start's plan).
  An explicit user no always wins.
- `implement` reads the same table at dispatch time; `start` does not
  re-derive it per stage.
