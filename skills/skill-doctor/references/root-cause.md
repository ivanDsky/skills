# Tracing findings to skill text

Read this before step 7. It says how to turn graded failures into verified findings, which findings become proposals, and how to rank them.

## Steps

1. **Cluster.** Group grader reasons, static flags and metric outliers by cause across sessions. A cluster lists every session key and `#n` it rests on.
2. **Locate.** For each cluster, read the skill files those sessions loaded (`skills_used`) and find the line whose wording produced the behaviour. Use `span` to read the raw lines around each cited `#n`.
3. **Classify** with the category table below.
4. **Write `RUN_DIR/findings.json`**: `{"findings": [ … ]}`, one object per cluster:

```json
{"id":"F3","skill":"start","file":"start/SKILL.md","line_start":212,"line_end":214,
 "quote":"verbatim skill text","category":"wrong_guidance","subtype":null,
 "sessions":["KEY1","KEY2"],
 "transcript_quotes":[{"session":"KEY1","agent":"T01Gap","line":431,"quote":"verbatim transcript text"}],
 "protective":false,
 "existing_rule":null,
 "counterfactual_rule":"one sentence the skill should have said",
 "competent_agent_still_fails":true}
```

`file` resolves against `--skills-dir`. `agent` is the subagent file stem; omit it for the orchestrator. Omit `line` only when the quote's line is unknown; the check then searches the whole file.

5. **Verify.** `python3 scripts/omp_sessions.py verify "$RUN_DIR"` writes `findings.verified.json` and exits 1 if any finding fails. It rejects a finding when:
   - `category` is not in the enum;
   - the quote is not in the skill file at the cited lines (it reports the line where it is, or that the text is gone, which means already fixed);
   - a transcript quote is not in the cited JSONL line;
   - the skill was not loaded in any cited session, unless the category is `discovery_failure` or `context_decay`;
   - only one session shows it and `protective` is not true.

   Fix or drop rejected findings and re-run until exit 0. Only verified findings reach the report.

## Categories

| Category | Meaning | Proposal kinds |
|---|---|---|
| `discovery_failure` | trigger met, skill never loaded | `description_fix`, dispatch-table row |
| `missing_guidance` | no instruction covers the situation | `add` (net-token rule), `replace` |
| `instruction_ambiguity` | weak modal, unbounded quantity, undefined term | `replace` |
| `wrong_guidance` | the text asks for the costly behaviour | `replace`, `remove` |
| `conflicting_guidance` | two skills or sections disagree | `dedupe`, `remove` |
| `skill_hurts` | `subtype`: `heavyweight_ceremony` (cost exceeds what it caught), `displaces_default` (replaced a better default), `unsolvable_pointer` (points at a tool the agent cannot run) | `remove`, `move_to_reference`, `move_to_script`, `replace` |
| `context_decay` | loaded, then lost at compaction or not passed to subagents | dispatch template or re-injection change |
| `ignored_instruction` | clear text, in context, not followed | `move_to_script` or `dedupe`, only at ≥ 3 sessions; never new wording |
| `agent_error` | model variance | none |
| `harness_or_infra` | config, model routing, tooling | `config` note for the user |
| `project_specific` | true for one project only | `project` note for that project's `docs/agents/AGENTS.md` |
| `unknown` | evidence insufficient | none |

**Causation check.** Before filing, answer: did an existing rule already require the right behaviour (`existing_rule` non-null → `ignored_instruction`)? Would a competent agent with the current text still fail (`competent_agent_still_fails: false` → not filed)? Among sessions that loaded the same skill, did the failure happen in under a quarter of them with n ≥ 4 (→ `agent_error`)?

## Filing bar

Adapted from warpdotdev/common-skills (`.agents/skills/skill-doctor/references/skill-improvements.md`, commit 8792394), Copyright (c) 2026 Denver Technologies, Inc., MIT; see `../LICENSE-warp-skill-doctor`. Modified: categories, net-token rule, verify gate, `not_filed_reason` values.

Do not propose changes by default. File only when all of these hold:

- The cause is a missing, wrong, ambiguous or harmful instruction at a named `skill:file:line`.
- You can state the owning surface and one reusable rule in one sentence.
- Had that rule been present and followed, the failure would not have happened.
- The finding is verified.
- Net-token rule: the proposal states `token_delta`. An `add` to a SKILL.md already over ~1.5k tokens must pair with a removal or a move to `references/`.

Do not file when the instruction already required the right behaviour, the failure is variance, the only edit restates or hedges or adds examples from these runs, or the real fix is product, infra, grader or code.

Every cluster not filed gets one `not_filed_reason`: `ignored_instruction`, `variance`, `single_occurrence`, `not_loaded`, `quote_unverified`, `already_fixed`, `project_specific`, `infra`, `restating_only`. Filing nothing is a valid result; a speculative change is worse than none.

## Removals first

`static.json` produces removal candidates without a grader. Consider them before any addition:

| Candidate | Proposal |
|---|---|
| `never_loaded` skill | review; deletion candidate only after two consecutive runs with zero loads |
| `duplicated_lines` in ≥ 3 skills | `dedupe` to one canonical section |
| `over_budget` SKILL.md | `move_to_reference`; low priority unless a finding cites the file |
| A review or check step whose spend yielded no caught defects across ≥ 2 sessions | `remove` or reduce |
| `weak_modals` | lint note; a proposal only when a verified finding cites the line |
| `description_collisions` | `description_fix` |

A removal proposal states what was observed (zero loads, zero catches, cost), what could break, and which routing evals cover it.

## Proposal object

```json
{"id":"P3","rank":3,"kind":"remove","skill":"start","file":"start/SKILL.md","line_start":212,"line_end":214,
 "quote":"…","rule":"one sentence","category":"wrong_guidance","findings":["F3"],
 "evidence":{"sessions":["…"],"recurrence":7,"cost_share":0.12},
 "token_delta":-120,"effort":"S",
 "success_metric":{"metric":"asks.count","direction":"down","target":"-25%"},
 "risk":"what could break"}
```

- `kind`: `remove`, `replace`, `move_to_script`, `move_to_reference`, `description_fix`, `dedupe`, `add`, `config`, `project`.
- `success_metric.metric` is a `metrics.json` path, so the next run can measure it with `compare`.
- Rank = recurrence × severity (1–3) × cost share ÷ effort (S=1, M=2, L=3). Ties go to removals.
- A skill listed as install-as-is in `skills/ATTRIBUTION.md` gets an upstream note, not an edit.
