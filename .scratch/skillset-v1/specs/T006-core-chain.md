# T006 — Spec: the /start core chain

Inputs locked upstream: flow constitution **T005** (resolution section), authoring standards **T008** (resolution section).
Sources cited as `research/*.md` (see §9). Consumers: T007 (orientation internals), T017 (external installs), T018 (inventory + rules payloads).

## 0. Scope

1. Specs the happy path exactly as locked in T005: `/start` entry + 7 chain skills, plus the two conditional stages — orientation (hook, T007-owned) and research (micro-skill).
2. Does NOT spec: brownfield orientation body (T007), external skill installs (T017), rules-payload contents (T018).
3. Every skill obeys T008: flat `skills/<name>/`, kebab-case verb-first ASCII, frontmatter `name` + `description` + `interaction` + `requires`, body ≤ ~1.5k tokens, depth in `references/` one level deep, dual access (routes standalone AND composes in the chain).

## 1. Flow at a glance

Locked stage sequence (T005): `intake -> [orientation] -> spec -> tickets -> [research] -> implement -> review -> deliver`.

T008 locks verb-first skill names; T005's stage terms stay the chain vocabulary. Mapping:

| # | Stage (locked term) | Skill name | Fires when | Consumes | Produces (fixed paths) | Mode |
|---|---|---|---|---|---|---|
| 0 | setup | `init-profile` | no PROFILE.md | repo + user answers | PROFILE.md, `.scratch/` seed, harness entry line | hitl (once/project) |
| 1 | entry | `start` | every run | PROFILE.md + tracker frontier + the ask | run plan (stages, effort, HITL/AFK) | hitl |
| 2 | intake | `run-intake` | feature, prototype | ask + repo context | one batch of answers + numbered assumption list | hitl |
| 3 | orientation | `orient` *(T007)* | unmapped codebase + chain work | repo | orientation map, PROFILE care-axes fill | afk |
| 4 | spec | `draft-spec` | feature, prototype | intake answers | `.scratch/<slug>/spec.md` + checkpoint message | mixed |
| 5 | tickets | `write-tickets` | feature, prototype | spec | `.scratch/<slug>/tickets/NN-*.md` | afk (confirm at thorough) |
| 6 | research | `fan-out-research` | ticket/spec declares Unknowns | one unknown statement | `.scratch/<slug>/research/<topic>.md` | afk, parallel |
| 7 | implement | `implement` | ready frontier ticket | ticket brief + spec backlink + ledger | code + commits, ledger line, DoD evidence | afk |
| 8 | review | `review-change` | implement done | diff vs base + spec + PROFILE | verdicts + findings; fixes; teardown if stuck | afk |
| 9 | deliver | `deliver` | review passes | green change + PROFILE targets | build/deploy output, closed tickets | afk |

**Handoff rule**: every stage hands forward a FILE, never chat memory. The run ledger `.scratch/<slug>/ledger.md` is append-only and records every autonomous decision as `Ruling: <what> — <why> — <cost if wrong>`. After compaction or interruption: trust the ledger + git log over recollection (`research/superpowers.md`).

## 2. Skill specs

### 2.1 `start` — entry, triage, run plan

- **Purpose**: classify the ask, read project state, print the run plan (stages × effort × HITL/AFK), fire the chain.
- **Frontmatter**:

```yaml
name: start
description: >-
  Triage an ask (quick task / prototype / feature / unmapped codebase) and run the
  matching flow with effort-tiered gates. Use when the user says /start or /build,
  or when work starts in a project that has PROFILE.md.
interaction: hitl
requires: []
```

- **Body outline**:
  1. Read PROFILE.md (care-axes, effort, deploy targets, testing style) + tracker frontier (open, unblocked, unclaimed). Missing PROFILE.md → run `init-profile` first, then continue.
  2. Frontier non-empty → run plan lists in-flight tickets and offers resume (resume = jump straight to `implement`); the new ask is still classified normally.
  3. Triage tree, in order: **quick task** — ALL true: ≤3 files touched, no new public interface, no irreversible op, no deploy → inline ponytail run, zero artifacts, reply ends with skipped + residual risk. **Unmapped codebase** — chain work ahead + no orientation artifacts → run `orient` (T007), update PROFILE care-axes, re-triage. **Prototype** — user flag or the ask is really a question → chain + prototype flag. **Feature** — default → full chain.
  4. Map effort (PROFILE.md value; command override `/start fast|standard|thorough` wins) through the §3 table; prototype caps gates at the fast tier.
  5. Print the run plan: per stage — fires/skips, HITL or AFK (read from each skill's `interaction` frontmatter, effort overrides applied), gate, artifact path. Ask at most one question (only if triage is genuinely ambiguous), then fire.
- **References**: `references/triage-cases.md` (worked examples per branch).
- **Est**: ~1.2k tokens.

### 2.2 `run-intake` — two-gear batched questions

- **Purpose**: extract the load-bearing decisions in ONE batch; park everything else as marked assumptions.
- **Frontmatter**:

```yaml
name: run-intake
description: >-
  Ask one batch of the highest-impact questions with recommended one-word answers,
  then stop asking — the rest becomes marked assumptions in the spec. Use before
  drafting a spec for feature or prototype work.
interaction: hitl
requires: []
```

- **Body outline**:
  1. Gear: **focused** = 5–8 questions (default) | **deep** = 20–30 (user requests it, or high stakes = an irreversible fork is on the table: production deploy, data migration, money, deletions). The `grilling` skill stays reserved for irreversible forks discovered mid-flight (T005).
  2. One batch, frontier order: number every question, give the recommended answer, word each so "yes" accepts it; one-word answers expected (`research/mattpocock-skills.md`). Send the batch, then wait.
  3. Never ask what the repo or PROFILE.md already answers — look it up, or let it become an assumption.
  4. Everything unasked → numbered assumption list (A1, A2, …) handed to `draft-spec`. No silent gaps.
  5. Prototype runs: the batch must include the deploy question (`deploy: main | standalone | none`).
- **Est**: ~0.8k tokens.

### 2.3 `draft-spec` — spec + single checkpoint

- **Purpose**: write the working spec with an explicit Assumptions section; run the one correct-me-or-I-go checkpoint.
- **Frontmatter**:

```yaml
name: draft-spec
description: >-
  Write the working spec with an explicit numbered Assumptions section and post the
  single "correct me or I go" checkpoint before autonomous execution. Use after
  intake answers exist.
interaction: mixed
requires: []
```

- **Body outline**:
  1. Synthesize; do not re-interview. Sections: Problem / Solution / **Assumptions (numbered)** / Success criteria / Out of scope / Deploy (prototypes only).
  2. Durability rule: no file paths, no line numbers — behavior and decisions only (`research/mattpocock-skills.md`; confirmed in three independent skills there).
  3. Checkpoint (the flow's only standing blocking gate besides intake): post digest ≤30 lines + full assumption list + "correct me or I go."
  4. Blocking per effort: fast = post and proceed immediately (later corrections become ticket edits); standard/thorough = wait for any reply. Prototype never blocks.
  5. Corrections are folded in by editing the spec — never a second interview. A newly surfaced irreversible fork escalates to `grilling`.
- **Est**: ~0.7k tokens.

### 2.4 `write-tickets` — tracker tickets with DoD

- **Purpose**: turn the spec into tracer-bullet tickets in the local wayfinder tracker, each closable only by evidence.
- **Frontmatter**:

```yaml
name: write-tickets
description: >-
  Break an approved spec into tracer-bullet tickets in the local tracker with
  mandatory checkable DoD + evidence, each sized to one fresh subagent context.
  Use after a spec passes its checkpoint.
interaction: afk
requires: []
```

- **Body outline**:
  1. Ordering: tracer bullets — ticket 01 is the thinnest end-to-end walking path (already demoable), then narrow complete slices; blockers first, numbered `NN` in dependency order (`research/mattpocock-skills.md`).
  2. Sizing rule: one ticket = one fresh subagent context, one sitting. Checkable proxy: ≤5 files touched + exactly one demoable/verifiable outcome. Over budget → split vertically; wide refactor → expand–contract batches.
  3. Mandatory fields per ticket: **What to build** (behavioral) / **Blocked by** / **Unknowns** (each line declares one research fan-out) / **DoD**: one checkable condition / **Evidence**: command, screenshot path, or deploy output. No DoD → not a ticket (T005).
  4. Publish: default local markdown `.scratch/<slug>/tickets/NN-<slug>.md` with `status: open | claimed | done`; PROFILE.md may point at another tracker. Claim = set `status: claimed` before any work.
  5. Prototype ticket sets: DoD = question answered or demoable; the last ticket carries the `deploy:` flag.
- **Est**: ~1.2k tokens.

### 2.5 `implement` — per-ticket subagent execution

- **Purpose**: execute ready tickets — one fresh subagent each, ponytail ordering, ledger bookkeeping, research fan-out for declared unknowns.
- **Frontmatter**:

```yaml
name: implement
description: >-
  Execute tracker tickets one fresh subagent per ticket in tracer-bullet order with
  ponytail ordering and an append-only ledger; fan out research subagents for
  declared unknowns first. Use when the frontier has ready tickets.
interaction: afk
requires: []
```

- **Body outline**:
  1. Step 0 — unknowns: each ticket with `Unknowns` gets research subagents in parallel (AFK, count per §3); findings files are linked into the ticket before coding starts.
  2. Dispatch: one subagent per ticket, fresh context, brief handed as a FILE (ticket + spec backlink + neighbor interfaces) — never paste session history into a dispatch prompt; report file + ≤15-line status contract `DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT` (`research/superpowers.md`).
  3. Ordering inside a ticket (ponytail, adapted): **understand → reuse → adapt → extend → new code last**; smallest change that fully solves; never cut validation, security, accessibility, or data-loss handling; non-trivial logic leaves one small test behind. Every reply ends with "skipped: … / residual risk: …" (`research/ponytail.md`).
  4. Subagent knobs per §3: implementer on the cheapest capable tier, reviewers on the strongest; workers never spawn reviewers or any subagents; never run parallel implementers on one tree.
  5. Close per ticket: DoD evidence must exist or the ticket stays open; append the ledger line; take the next frontier ticket. Interruption/compaction recovery = trust the ledger + git log.
- **References**: `references/dispatch.md` (brief + report templates).
- **Est**: ~1.5k tokens.

### 2.6 `review-change` — tiered gates + teardown

- **Purpose**: run the effort's review gate over the whole change; own findings, fix rounds, and the teardown escalation.
- **Frontmatter**:

```yaml
name: review-change
description: >-
  Run the effort-tiered review gate over the change — scripted checks + screenshots,
  then code review, then dual-verdict subagent review — and own the teardown
  escalation. Use after implementation, before deliver.
interaction: afk
requires: []
```

- **Body outline**:
  1. Tier gates (exact, per effort): **fast** = lint + typecheck/compile + screenshots of touched UI; **standard** = + code review (one reviewer subagent, stronger tier); **thorough** = + dual-verdict subagent review on the most capable model. Prototype caps at fast tier + the demo.
  2. Review inputs: diff vs base, the spec (numbered assumptions count as decisions), PROFILE care-axes set the priority order. UI work is checked against `design-taste-frontend` when installed (T014); screenshots via the harness browser (taste-skill's zero-dep CDP loop).
  3. Dual verdict (thorough): spec-compliance verdict ✅/❌/⚠️ cannot-verify + quality verdict Approved/Needs-fixes; findings graded Critical/Important/Minor; the two axes are reported separately and never merged (`research/superpowers.md`, `research/mattpocock-skills.md`).
  4. Fix loop: findings go back to the same implementer (resumed), re-review is scoped to the fix diff; Minors are ledgered as deferred, never silently fixed.
  5. **Teardown gate** (T005): trigger = 2 failed fix rounds or reviewer discretion → invoke `assess-teardown` (T007; independent architect skill — fresh context, high effort, minimal brief, never the transcript; Tier-3 eval target and directly user-invocable) which decides fix-forward vs clean redesign; a teardown carries forward only root cause, interface contracts, and surviving tests. Verdict is reported to the user.
- **References**: `references/review-prompts.md` (verdict templates, ≤400-word axes), `references/fix-loop.md` (rounds, scoped re-review, teardown prompt).
- **Est**: ~1.2k tokens.

### 2.7 `deliver` — build + deploy evidence

- **Purpose**: produce the build (and, when targeted, the deploy) output that closes the run.
- **Frontmatter**:

```yaml
name: deliver
description: >-
  Build the change and deploy to the PROFILE.md targets — build-only, firebase,
  tailscale, or local — attaching the build/deploy output as evidence. Use after
  review passes.
interaction: afk
requires: [firebase CLI when target=firebase, tailscale CLI when target=tailscale]
```

- **Body outline**:
  1. Default = build-only. Deploy targets come from PROFILE.md (in listed order); a prototype uses its ticket's `deploy:` flag (`main | standalone | none`).
  2. One short checklist per target in `references/deploy-targets.md`: firebase (project id, hosting rules), tailscale (serve/funnel + host), local (run command straight from PROFILE.md).
  3. Target CLI missing → stop with the install pointer; never improvise a deploy path.
  4. Evidence = build log path or deploy URL, appended to the final ticket + ledger; tickets close only with evidence attached (T005 DoD rule).
  5. Final message = honest endings: what shipped, what was skipped, residual risk.
- **Est**: ~0.6k tokens.

### 2.8 `fan-out-research` — micro-skill, conditional stage

- **Purpose**: answer one declared unknown against primary sources with a cited findings file.
- **Frontmatter**:

```yaml
name: fan-out-research
description: >-
  Answer one declared unknown with a subagent that reads primary sources and writes
  a cited findings file. Use when a spec or ticket declares an Unknown.
interaction: afk
requires: [websearch]
```

- **Body outline**:
  1. One unknown = one subagent = one file `.scratch/<slug>/research/<topic>.md`.
  2. Every claim cites the source that owns it.
  3. The file ends with "so what": the blocked decision this resolves.
  4. Findings feed the ticket's approach — the spec is never edited silently by research.
  5. Parallel-safe (read-only); fan-out is capped by effort (§3).
- **Est**: ~0.4k tokens.

### 2.9 `init-profile` — setup ritual owner

- **Purpose**: one-time per-project setup: write PROFILE.md, seed the tracker, wire the entry line.
- **Frontmatter**:

```yaml
name: init-profile
description: >-
  Interview with recommended one-word defaults, then write PROFILE.md, seed the
  tracker, and add the /start entry line to the harness config. Use on the first
  /start in a project, after installing the skillset, or via /setup.
interaction: hitl
requires: []
```

- **Body outline**:
  1. One intake-style batch (recommended defaults, one-word answers): care-axes rank, effort level, deploy targets, testing style, tracker location.
  2. Write PROFILE.md (§5) at the project root; create `.scratch/` if absent.
  3. Add ONE entry line to the project's harness config (CLAUDE.md / AGENTS.md / prime-agent prompt note): "Work in this repo starts with /start." `npx skills` places files but fires no hooks, so this line is the entire bootstrap (`research/skills-ecosystem.md`, `research/superpowers.md`).
  4. Hard-vs-soft dependency rule: only `init-profile` gets an explicit "run /setup" pointer; every chain skill reads PROFILE.md and degrades silently when a section is missing (`research/mattpocock-skills.md`, ADR 0001 pattern).
  5. Idempotent: existing PROFILE.md → show a diff and offer edits; never overwrite care-axes silently.
- **Alias**: `/setup`.
- **Est**: ~0.8k tokens.

## 3. Effort mapping (the one table)

`start` and `implement` both read this table; `implement` enforces the subagent knobs at dispatch time.

| effort | subagent thinking | reviewer model | research fan-out | intake gear | spec checkpoint | ticket confirm | review tier |
|---|---|---|---|---|---|---|---|
| fast | low | same tier as implementer | skip (only when a ticket is blocked) | focused | post-and-proceed | none | lint + screenshots |
| standard | medium | stronger tier | 1 per unknown, cap 3 | focused | blocking | none | + code review |
| thorough | high | most capable | full parallel fan-out | deep if high stakes, else focused | blocking | blocking (edges + sizing) | + dual-verdict |

Rules: the per-session override (`/start <level>`) wins over PROFILE.md; default is standard; a prototype flag caps gates at the fast tier at any effort (thinking still follows the table). The quality-vs-speed knob is called the **effort level** — "dial" stays retired (T005).

## 4. Gates summary

Gates exist only where artifacts persist or money is spent:

1. Intake batch — always HITL; this is the alignment purchase that buys the autonomous run.
2. Spec checkpoint — the single "correct me or I go" message.
3. Ticket confirm — thorough effort only (blocking edges + sizing).
4. Review tier gates — per §3.
5. Teardown verdict — reported to the user; the independent architect decides (T005 wording).

Everything else is AFK. Interruption and steering stay harness responsibilities; no skill invents its own polling or approval loops.

## 5. PROFILE.md shape

Project root, written by `init-profile`, read by `start` (and every chain skill, degrading silently):

```markdown
# PROFILE.md — written by init-profile, read by /start

## Care-axes (ranked: what quality means here)
1. architecture/SOLID        # <free text or rules-payload pointer>
2. UI/UX                     # premium | standard
3. readability               # comment-free preferred, small units

## Effort
- level: standard            # fast | standard | thorough; per-session override: /start <level>

## Platform & stack (global-first)

Preferred stack and default platform are USER-level and stored once globally in `~/.agents/AGENTS.md` (AGENTS.md global convention) — e.g., mobile-first, Kotlin / Jetpack Compose. `init-profile` checks and offers to create it. Project `PROFILE.md` holds only deltas: deploy targets, testing style, effort default, and a platform override only when the project differs from the user default. Platform routes: the UI rules payload (`references/rules-ui-<platform>.md`, seedable from ui-ux-pro-max's design-system generation), the platform review axes (mobile: touch targets, density, safe areas, state restoration, offline), and the screenshot source for fast-tier review (emulator/device for mobile, browser for web).

## Deploy targets (in order; empty list = build-only)
- local: <run command>
# - firebase: <project id>
# - tailscale: <host>

## Testing style
- runner: <command>
- approach: tdd-fakes        # tdd-fakes | tdd-real | smoke-only
- seams: <where tests attach>
```

Rules: care-axes are **ranked** — the order is the review priority order and selects which `references/rules-*.md` payloads load (T008 rules-payload pattern); a missing section = `start` asks once, writes the answer back, moves on; effort default standard; the four sections above are the contract — extra sections are allowed but never required.

## 6. GLOSSARY.md seed terms

Repo-root GLOSSARY.md (T008: yes), format per term: one-line definition + `_Avoid:_` synonyms. Seed:

| Term | Definition | Avoid |
|---|---|---|
| Stage | One named step of the /start flow (intake, orientation, spec, tickets, research, implement, review, deliver). | phase |
| Effort level | fast / standard / thorough; quality-vs-speed setting, per-session override wins. | dial (retired, T005), mode |
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

## 7. Setup ritual triggers

| Trigger | What happens | Actor |
|---|---|---|
| Install (`npx skills add ivanDsky/skills`) | Skill files placed; nothing fires — the skills CLI has no hooks. | user |
| First `/start` in a project (no PROFILE.md) | `start` delegates to `init-profile`: one batch → PROFILE.md + `.scratch/` seed + entry line → re-triage the actual ask. | agent |
| New session in a configured project | The entry line ("Work in this repo starts with /start.") routes the session to `start`; it reads PROFILE.md + frontier and offers resume. | agent |
| `/setup` (manual) | `init-profile` re-run; idempotent, diff-first. | user |

Bootstrap rule: one entry line, written once by `init-profile` — superpowers' lesson ("the bootstrap is the entire integration") at skills-CLI cost: no hooks, no injection budget, ~0 tokens until `/start` is invoked.

## 8. Validation hooks (per T008)

1. Tier 1 lint: all 9 skills (13-rule checklist + `interaction`/`requires` extension checks).
2. Tier 2 routing evals: all 9; the hardest near-miss pairs are `start` (quick vs feature vs prototype) and `run-intake` vs `grilling` (batch vs irreversible fork).
3. Tier 3 behavioral evals, opt-in on chain-critical skills per T008: `run-intake`, `review-change`, and the teardown-gate path.

## 10. Feedback capture (two-way rule)

When the user corrects or complains about how a skill or step behaved, the acting skill ends with a one-line offer:
`Save this? [p]roject config (docs/agents/AGENTS.md) | [s]kill update (ivanDsky/skills) | [n]o`
- **project**: append the decision to `docs/agents/AGENTS.md` (per-project override; `start` reads it at triage). Fast, no versioning.
- **skill**: file an update against the named skill; it lands only through `integrate-skill` (trigger cases + routing check + size report) so the eval ladder catches regressions.
Applies at every HITL gate and to in-flight corrections; never applied silently.

## 11. Debug toggle & run log

`PROFILE.md` key `debug: off | on` plus per-session override ("debug on"). When on, `start` creates `.scratch/run-log.md` and every chain skill appends one bounded entry (<=4 lines):

`<skill> | fired by <trigger> | contributed: <what changed, one line> | depth: ok | skipped: <none | what + why>`

`depth != ok` when: body/references exceeded the size estimate, >2 fix rounds, research fan-out exceeded 3 subagents, or a gate re-ran — always with the cause. Off = no log. Purpose: single-user explainability (what was used, what it brought, what went too deep and why).

## 9. Sources

- `research/superpowers.md` — per-ticket fresh subagents, brief/report files instead of pasted history, ≤15-line status contract, ledger + `Ruling:` lines, dual-verdict review, fix-round cap → teardown, model ladder (cheapest implementer / strongest reviewer), workers never spawn reviewers, "the bootstrap is the entire integration".
- `research/mattpocock-skills.md` — tracer-bullet tickets sized to one fresh context, durability rule (no paths/line numbers), two-axis ≤400-word review reported separately, frontier batch questioning with yes-accepts-default wording, config-as-files, glossary Avoid-lists, hard-vs-soft dependency pointers.
- `research/ponytail.md` — ordering ladder (understand → reuse → adapt → extend → new last), smallest-change-that-fully-solves, never-cut list, honest endings (skipped + residual risk).
- `research/skills-ecosystem.md` — `npx skills` = file placement only, no hooks → entry-line bootstrap.
- Tickets: T005 resolution (flow, gears, prototype flag, teardown gate, effort level, ponytail ordering, DoD mandate), T008 resolution (standards, rules payloads, eval ladder), T013 (ponytail adoption verdict), T014 (taste-skill as the UI check).

## 10. Handed off

- **T007**: the `orient` skill body (archify-based), expand–contract details, how orientation updates PROFILE care-axes.
- **T018**: rules-payload contents (architecture/SOLID, code style), external installs wiring (taste-skill, impeccable, archify, ponytail-review), teardown-architect prompt text.
- **Open, flagged not resolved**: multi-harness manifests beyond the entry line (MAP fog item); resume across machines (ledger lives in `.scratch/`, git-ignored by default).
## 12. Composition, precedence, parallelism, conflicts

**How skills compose.** Skills are not function calls; they apply on different axes and are selected by `start` + their `Use when` descriptions. Two composition kinds: (a) *sequenced* — chain stages hand artifacts to each other; (b) *layered* — skills governing different axes apply inside the same stage. Example: `implement` runs the `tdd` procedure (process axis: red-green-refactor, fakes) while `ponytail` governs scope (how much to build, new code last). When they tension (tests want scaffolding, ponytail wants minimal), ponytail's own never-cut list keeps validation — scope shrinks, tests never.

**Precedence** (same everywhere): session override > project config (`docs/agents/AGENTS.md`, `PROFILE.md`) > global user layer (`~/.agents/AGENTS.md`: preferred stack, default platform, UI taste, hard style rules) > skill body > skill defaults. Feedback-capture writes are dated, newest wins; the two-way capture decides project-local exception vs global fix. `references/rules-*.md` payloads are the shared layer multiple skills read.

**UX review axis.** `review-change` references include `review-ux.md`: platform-agnostic principles via the knowledge layer (apple-design, emil-design-eng) + stack-specific guidelines via ui-ux-pro-max (22 stacks incl. Jetpack Compose/SwiftUI — the mobile source; T022) + the platform rules payload + impeccable/taste gates *when the surface is web*. No separate reviewer skills in the roster (smallness); the axis is a reference any review tier can load.

**Parallelism.** Research: fan-out parallel by design (one subagent per unknown; effort mapping caps the count; >3 flags depth). Implementation: tickets run in order by default; `write-tickets` may mark independent tickets (declared disjoint file scopes) as parallel-safe, each getting its own fresh subagent. Shared-surface work gets blocking edges instead.

**Conflicts, three classes.**
1. *Code* (parallel implementers): prevented by disjoint-scope tickets; when unavoidable, isolated branches/worktrees, serial merge, scoped re-review of the merge diff.
2. *Verdicts* (reviewer vs implementer, dual-verdict disagreement): verdicts are ✅/❌/⚠️ with mandatory evidence; unresolved disagreement escalates by fix-round cap to `assess-teardown`'s architect; the user arbitrates any ❌ dispute. Every ruling lands as a `Ruling:` line in the tracker ledger.
3. *Policy* (rules payload vs procedure, project vs global): the precedence order above; the feedback two-way capture (§10) decides where a correction lives — project-local exception or global skill fix.
