# Effort mapping

The one table: effort level → gates and knobs. `start` reads it to build the
run plan; `implement` enforces the subagent knobs at dispatch.

| effort | subagent thinking | reviewer model | research fan-out | intake gear | spec checkpoint | ticket confirm | review tier |
|---|---|---|---|---|---|---|---|
| fast | low | same tier as implementer | skip (only when a ticket is blocked) | focused | post-and-proceed | none | lint + screenshots |
| standard | medium | stronger tier | 1 per unknown, cap 3 | focused | blocking | none | + code review |
| thorough | high | most capable | full parallel fan-out | deep if high stakes, else focused | blocking | blocking (edges + sizing) | + dual-verdict |

Rules:

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
  development, it asks the user instead of silently deciding.
- Per-session override (`/start fast|standard|thorough`) still wins for the run
  default; per-ticket effort overrides the run default unless the user set the
  override explicitly.
- A prototype flag caps gates at the fast tier at any effort (subagent
  thinking still follows the table).
- The quality-vs-speed knob is the effort level.
- `implement` reads the same table at dispatch time; `start` does not
  re-derive it per stage.
