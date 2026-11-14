# Metrics and transcript layout

Read this when a metric looks wrong, when you cite a transcript line, or when omp changes its session format.

## Where omp keeps sessions

| Path under `~/.omp/agent/sessions/` | What it is |
|---|---|
| `<slug>/<ts>_<uuid>.jsonl` | orchestrator session (header has no `parentSession`) |
| `<slug>/<ts>_<uuid>/<Name>.jsonl` | subagent spawned by that session |
| `<slug>/<ts>_<uuid>/<Name>/<Name>.<Child>.jsonl` | nested subagent |
| `<slug>/<ts>_<uuid>/local/` | the session's scratch artifacts; skipped |

`<slug>` is the working directory with `/` replaced by `-`, so `--project '*PuzzleBox*'` matches every worktree of that repo. A file counts as a transcript when it has a `type: session` line. A child whose header has `seanceSource` is a consult replaying another session: its cost counts, its replayed spawns do not.

Entry shapes the script relies on:

- `message` with `message.role` `user` | `assistant` | `toolResult`. Assistant messages carry `provider`, `model`, `usage.cost.{input,output,cacheRead,cacheWrite,total}`, `stopReason`, and `content[]` with `toolCall {id, name, arguments}`.
- `toolResult` carries `toolCallId`, `toolName`, `isError`, and for `task` the spawned agents in `details.progress[]`.
- `compaction {tokensBefore, tokensAfter, summary}`.
- `custom_message` with `customType: skill-prompt` and `details.name`: the user invoked a skill.
- `model_usage`: a side call (title, summary) billed to the session.
- `session_init.data.{agent, resolvedModel}` in subagent files.

## Addresses

`#n` in a condensed transcript is the 1-based line number in the JSONL file. `span RUN KEY --lines A-B [--agent STEM]` prints those raw lines. Findings cite `#n`; `verify` re-reads the line to check every quote.

## Metric definitions (`metrics.json`)

Per session (`sessions[]`); `totals` sums them across the window.

| Path | Definition |
|---|---|
| `cost.total`, `side_cost` | assistant `usage.cost.total` in the orchestrator file; `model_usage` cost |
| `subagents.cost` | the same, summed over every subagent file in the tree |
| `total_cost` | orchestrator + side + subagents |
| `by_model` | assistant turns and cost per `provider/model` |
| `asks.count`, `asks.questions` | `ask` calls; distinct form-control `name=` values (or `questions[]` items) |
| `asks.wait_h`, `asks.max_wait_h` | ask result timestamp − ask call timestamp, in hours |
| `asks.cancelled` | ask results that errored or say cancelled |
| `compactions` | `compaction` entries |
| `builds` | bash commands matching `gradlew` |
| `hazards` | bash commands matching `kill_build_daemon` (`pkill … gradle`, `gradlew --stop`), `git_add_all` (`git add -A`, `--all`, `.`), `cache_delete` (`rm -r…` on `.gradle` or `Library/Caches`) |
| `repeated_calls` | extra calls beyond the first for each identical (tool, arguments) pair |
| `tool_errors` | tool results with `isError` |
| `spawns.count`, `spawns.without_model` | agents in `task` calls; those with no `model` key |
| `spawns.missing_model_resolved` | for spawns without `model`: the model the child transcript actually ran, joined by spawn name = child file stem |
| `skills.model_invoked`, `skills.user_invoked` | reads of `skill://<name>` or `skills/<name>/SKILL.md`; `skill-prompt` entries |
| `skills_used` | union of the above across the orchestrator and its subagents |
| `replies.count`, `median_chars`, `long` | assistant turns ending with `stopReason: stop` and text; `long` = over 1,500 chars |
| `user_status_probes` | user messages like "are you done", "are you stuck", "what are you waiting for" |
| `subagents.by_role` | count and cost by spawn-name prefix: the leading capital run before a digit (`T01Gap` → `T`) or the first word (`Consult`) |
| `subagents.median_first_turn_context` | median input + cache tokens of each subagent's first turn |
| `subagents.idle_over_5m` | subagents with a gap over five minutes between entries |

Skill detection is structural only: a skill name in prose is not a load.

Sessions that load `skill-doctor` itself are dropped, so the audit never grades its own runs.

## Static checks (`static.json`)

| Key | Rule |
|---|---|
| `never_loaded` | skills in `--skills-dir` absent from every session's `skills_used` |
| `over_budget` | SKILL.md body over ~1,500 tokens (chars ÷ 4) |
| `skills.<name>.weak_modals` | lines containing optional, consider, if possible, where appropriate, as needed, try to |
| `description_collisions` | description word sets with Jaccard overlap > 0.5 |
| `duplicated_lines` | a normalized line of ≥ 60 chars present in ≥ 3 skills |

## Known limits

- Cost is what omp logged. Cached-token prices follow the provider's billing at the time.
- `builds` only sees Gradle. Other build tools need a pattern in `BUILD_RE`.
- A spawn whose child transcript is missing resolves to `no_transcript`.
- Ask wait includes the time the user was away. It measures blocking, not effort.
