# Format notes (example reference file)

This file is deliberately separate from `SKILL.md`: it is detail that
only some runs need. The skill body points here with a relative path
(`references/format-notes.md`), and the agent loads it only when that
step is relevant.

Rules that make routing work:

- The `description` is the only text the agent sees before deciding to
  load the skill, so it must name the concrete tasks, tools, and phrases
  that should trigger it.
- One trigger idea per clause; duplicated phrasings just cost context.
- If a skill should only ever fire when the user types
  `/skill:<name>`, set `disable-model-invocation: true` — its
  description then disappears from the agent's context entirely.
