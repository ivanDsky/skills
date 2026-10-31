# GLOSSARY

Motion effects are named with canonical animation terms — `animation-vocabulary` resolves vague descriptions to names; do not invent adjectives.

Canonical vocabulary for this skillset. Use these terms in tickets, specs, and replies; the Avoid column lists words NOT to use (they mean something else or blur distinctions). Source: T006 spec §6.

Repo-root GLOSSARY.md (T008: yes), format per term: one-line definition + `_Avoid:_` synonyms. Seed:

| Term | Definition | Avoid |
|---|---|---|
| Stage | One named step of the /start flow (intake, orientation, spec, tickets, research, implement, review, deliver). | phase |
| Effort level | fast / standard / thorough; quality-vs-speed setting. Per task by default (`thorough` = architecture/planning/big-view only); run default comes from PROFILE.md, per-session override wins for the default. | dial (retired, T005), mode |
| Gear | Intake batch size: focused (5–8) or deep (20–30). | mode |
| Care-axes | Ranked quality priorities in PROFILE.md; drive review order + rules-payload selection. | preferences |
| Run plan | start's output: stages × fires/skips × HITL/AFK × gates for one run. | agenda |
| Frontier | Tracker tickets that are open, unblocked, unclaimed. | backlog |
| Tracer bullet | Ticket cutting a narrow but complete path through every layer; demoable alone; 01 = thinnest walking path. | spike (spike = throwaway, different thing) |
| DoD | Per-ticket checkable completion condition; no DoD, no ticket. | acceptance criteria |
| Evidence | Artifact proving a DoD: command output, screenshot path, deploy output. | proof |
| Unknown | A declared open question on a ticket/spec that triggers research fan-out. | risk |
| Assumption | Unresolved point the agent decided, numbered (A1…) in the spec for review. | guess |
| Checkpoint | The single "correct me or I go" spec message; the only standing blocking gate besides intake. | approval |
| Teardown gate | 2 failed fix rounds or reviewer discretion → independent architect decides fix-forward vs redesign; carries only root cause, contracts, surviving tests. | rewrite, pivot |
| Dual-verdict review | Reviewer returns two separate verdicts: spec compliance + code quality; never merged. | sign-off |
| Ledger | Append-only run log (`.scratch/<slug>/ledger.md`): rulings, ticket closes; beats memory after compaction. | progress file |
| Ruling | Autonomous decision recorded as `Ruling: what — why — cost if wrong`. | decision log |
| HITL / AFK | Human-in-the-loop vs autonomous stage marking; declared in `interaction` frontmatter. | interactive / automatic |
| Prototype flag | Triage outcome; same flow, reduced gates, DoD = question answered/demoable, carries `deploy: main/standalone/none`. | spike |
| Deploy target | build-only (default), firebase, tailscale, or local; ordered list in PROFILE.md. | environment |
| Rules payload | Swappable `references/rules-*.md` carrying style/architecture rules; procedures stay generic (T008). | config |
