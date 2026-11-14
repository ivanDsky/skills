# Report template

Read this at step 8. Write the report to `RUN_DIR/report.md` first; publish only after the user confirms.

## Sections

1. **Scope and method.** Projects, window, session and subagent counts, depth (`metrics` or `full`), grader models, `skills_hash` from `inventory.json`, sessions excluded and why.
2. **Headline numbers.** From `metrics.json` `totals`: cost and its input/output/cache split, cost by model, orchestrator vs subagents, subagent medians, builds, asks and ask wait, compactions, spawns missing `model`. Then one row per session: cost, asks, ask wait, compactions, subagents.
3. **Scores.** Label distribution per axis, discrimination flags, failed sessions, then `warp_compat` once, labelled "for comparison with earlier audits only".
4. **Findings.** One block per verified finding:
   - **Evidence**: metrics and quoted transcript lines with session key and `#n`.
   - **Root cause**: `skill:file:line`, the quoted skill text, the category.
   - **Proposal**: its id, or the `not_filed_reason`.
5. **What works and should stay.** Sessions or steps that ran cheapest per delivered change, and the skills loaded there. This keeps good text from churning.
6. **Routing and config.** Model split, `spawns.missing_model_resolved` (what unset spawns really ran on), `never_loaded` skills, description collisions. `config` and `project` notes live here, not in the change list.
7. **Ranked change list.** Table: rank, change, kind, file:line, evidence, token delta, success metric.
8. **Not filed, and why.** One line per cluster with its `not_filed_reason`.
9. **Compared with the previous run.** Output of `compare`. If both runs share a `skills_hash`, say the deltas are drift, not a skill change. Every delta is observational: never write that a change caused it.
10. **What to measure next run.** Each proposal's `success_metric`, plus the standing metrics.
11. **Caveats.** Abstention counts, non-discriminating axes, sample size, model or task-mix differences, and `[INFERENCE]` on every expected effect.

## Publishing

Ask before publishing. On yes, write `docs/audits/<YYYY-MM-DD>-skill-doctor.md` in the skills repo, never in a project repo, with these rules applied:

- Quotes ≤ 240 characters.
- Replace key-like tokens, emails and URLs with credentials with `[redacted]`.
- Write home paths as `~`.
- Copy no raw spans, condensed transcripts or grader prompts.

Keep `metrics.json`, `scores.json` and `findings.verified.json` in `RUN_DIR`; the next run's `compare` reads that directory.
