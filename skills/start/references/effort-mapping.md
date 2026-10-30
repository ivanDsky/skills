# Effort mapping

The one table: effort level → gates and knobs. `start` reads it to build the
run plan; `implement` enforces the subagent knobs at dispatch.

| effort | subagent thinking | reviewer model | research fan-out | intake gear | spec checkpoint | ticket confirm | review tier |
|---|---|---|---|---|---|---|---|
| fast | low | same tier as implementer | skip (only when a ticket is blocked) | focused | post-and-proceed | none | lint + screenshots |
| standard | medium | stronger tier | 1 per unknown, cap 3 | focused | blocking | none | + code review |
| thorough | high | most capable | full parallel fan-out | deep if high stakes, else focused | blocking | blocking (edges + sizing) | + dual-verdict |

Rules:

- Per-session override (`/start fast|standard|thorough`) wins over PROFILE.md;
  default is `standard`.
- A prototype flag caps gates at the fast tier at any effort (subagent
  thinking still follows the table).
- The quality-vs-speed knob is the effort level.
- `implement` reads the same table at dispatch time; `start` does not
  re-derive it per stage.
