# Skills under Claude Code (ivanDsky/skills, bots branch)

Only some skills are installed in a session (`~/.claude/skills` holds a small shared set; an Orca
bot adds its own role skills in `.claude/skills`). The skills were written for the omp harness.
Read their omp terms this way:

- `skill://<name>/<path>` is the file `~/.local/share/ivandsky-skills/skills/<name>/<path>`;
  `skill://<name>` alone is `~/.local/share/ivandsky-skills/skills/<name>/SKILL.md`. That dir holds
  every skill, installed or not: read the file with the Read tool, or invoke the skill by name when
  it is installed.
- `task` tool / "spawn a subagent" → the `Agent` tool. `agent: task` → `subagent_type: general-purpose`;
  `agent: scout|sonic|reviewer|security-reviewer` and goldfish lenses → the custom subagent of that name
  (`~/.claude/agents/`). `model: anthropic/claude-<family>-…` → `model: <family>` (`opus`, `sonnet`,
  `haiku`, `fable`). A spawn `effort` has no per-call equivalent; leave it out.
- "resume the same worker" → `SendMessage` to that subagent.
- `todo` → `TodoWrite`. `ask` tool / `ask` form → `AskUserQuestion` (batch the questions in one call,
  recommended option first).
- `eval` → run the code with Bash (`python3 -c …`, `bun -e …`, or a script file).
- Background jobs and `wait` on them → Bash with `run_in_background`. `wait` in ship-to-trunk is the
  `merge_lane.py wait` command, not a tool.
- `local://<name>.md` → a file under the worktree's `.scratch/`; `agent://<id>` → that subagent's
  result; `out://` → your reply; `xd://…`, `history://`, `proc://` → no equivalent, use the nearest
  native tool or skip the step and say so.

Guard hooks (`hooks/claude/` in the skills repo) run on every Bash call, in subagents too: they put
`./gradlew` and `ship_apk.py` behind `~/.local/bin/build-slot` (that prefix is expected; never cancel,
kill or script around it) and refuse pkill/killall of Gradle or build-slot, `gradlew --stop`, blind
`git add`, deleting shared caches, `yes` pipelines, non-canonical `adb install`, raw Taildrop, and commits carrying
tailnet addresses.
