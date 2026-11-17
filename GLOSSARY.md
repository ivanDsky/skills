# GLOSSARY

Motion effects are named with canonical animation terms — `animation-vocabulary` resolves vague descriptions to names; do not invent adjectives.

Canonical vocabulary for this skillset. Use these terms in tickets, specs, and replies; the Avoid column lists words NOT to use (they mean something else or blur distinctions). Source: T006 spec §6.

Repo-root GLOSSARY.md (T008: yes), format per term: one-line definition + `_Avoid:_` synonyms. Seed:

| Term | Definition | Avoid |
|---|---|---|
| Stage | One named step of the /start flow (intake, orientation, spec, tickets, research, implement, user check, review, deliver). | phase |
| Effort level | fast / standard / thorough; quality-vs-speed setting. Per task by default (`thorough` = architecture/planning/big-view only); run default comes from PROFILE.md, per-session override wins for the default. | dial (retired, T005), mode |
| Tier | Per-ticket `tier: mechanical / standard / deep`: how much judgment the work needs; picks implementer agent, model and spawn effort (`start`/references/effort-mapping.md, *Tier → agent and model*). Independent of effort level. | model tier, difficulty, size |
| Caveman voice | Terse register for chat, briefs, agent reports, ledgers and findings files: answer first, no ceremony, every negation and code/path/number verbatim (`start` § Voice, upstream `caveman` skill). Questions, warnings and persisted human docs stay plain prose. | brief mode, compressed style |
| Gear | Intake batch size: focused (5–8) or deep (20–30). | mode |
| Care-axes | Ranked quality priorities in PROFILE.md; drive review order + rules-payload selection. | preferences |
| Run plan | start's output: stages × fires/skips × HITL/AFK × gates for one run. | agenda |
| Frontier | Backlog tickets in `ready-for-agent` whose `blocked-by` tickets are all `done` (`backlog.py list --frontier`); claims take only from it. | queue, todo list |
| Backlog | The one shared ticket store per repo, GitHub Issues or `<git-common-dir>/backlog/` (PROFILE `## Tracker`), read and written only through `work-tickets`' `backlog.py`; every worktree and session sees the same tickets. | tracker folder, `.scratch` tickets, issue list |
| Feedback session | A `file-tickets` session: the user talks, the agent files deduplicated tickets and runs the check batch; it never implements. | triage session, inbox |
| Worker session | A `work-tickets` session in a worktree: claims packs matching a filter and lands each ticket as its own PR; never asks the user. | ralph loop, AFK agent |
| Claim | Atomic move of a frontier ticket to `claimed` with `claimed-by`, made only by `backlog.py claim` under the backlog lock; released by `unclaim` or a state change. | assign, grab, take |
| Pack | Up to 5 tickets one `claim` call returns for a worker's filter; the next pack is claimed only when every ticket of the current one has an outcome. | batch (batch = the check batch), sprint |
| Agent brief | The body of a ticket filed by `file-tickets`: the user's words, expected behavior, acceptance, out of scope; behavior and contracts only, never file paths (epic tickets from `write-tickets` keep their file scope and map). | description, spec |
| needs-check | Backlog state of a merged hands-on ticket that waits for the user's check batch; ends in `done` or back to `ready-for-agent`. | in review, QA, awaiting verification |
| Check batch | One build from `main` covering every `needs-check` ticket, handed over in one message by the feedback session (`file-tickets` § 3). | UAT round, test build |
| Area | A ticket's kebab-case product surface label (`area:<name>`) that workers filter on. | component, module, epic |
| Tracer bullet | Ticket cutting a narrow but complete path through every layer; demoable alone; 01 = thinnest walking path. | spike (spike = throwaway, different thing) |
| DoD | Per-ticket checkable completion condition; no DoD, no ticket. | acceptance criteria |
| Evidence | Artifact proving a DoD: command output, screenshot path, deploy output. | proof |
| Unknown | A declared open question on a ticket/spec that triggers research fan-out. | risk |
| Assumption | Unresolved point the agent decided, numbered (A1…) in the spec for review. | guess |
| Checkpoint | The single "correct me or I go" spec message; the only standing blocking gate besides intake and the user check. | approval |
| User check | `user-check` stage after implement and before review: the user tries the whole change (installed build, LAN URL or demo output) and answers `ok` or feedback by id. One per run, never per ticket. | UAT, manual QA, demo |
| F-id | One numbered point of user-check feedback (`F1`…), quoted in the user's words; outranks the spec and amends it at the re-gate. | comment, note |
| Fast fix | A feedback-round change made with the quality bar off (no tests, no refactor), committed `fast(F<n>): …`; never cuts validation, security, accessibility or data-loss handling. | hotfix, quick fix |
| Re-gate | user-check's step after OK: reconcile spec vs feedback vs code, design-check the diff, emit hardening tickets. Written to `regate.md`. | retro, cleanup |
| Hardening ticket | Re-gate output that pays fast-fix debt (tests, structure, design) while keeping the approved behavior unchanged. | tech-debt ticket |
| Stack layer | One branch + PR in a `gh stack` (one per ticket, tracer bullet at the bottom); fixes land in the layer that owns the code, then `gh stack rebase --upstack`. | sub-PR, child PR |
| Teardown gate | 2 failed fix rounds or reviewer discretion → independent architect decides fix-forward vs redesign; carries only root cause, contracts, surviving tests. | rewrite, pivot |
| Dual-verdict review | Reviewer returns two separate verdicts: spec compliance + code quality; never merged. | sign-off |
| Ledger | Append-only run log (`.scratch/<slug>/ledger.md`): rulings, ticket closes; beats memory after compaction. | progress file |
| Captain | One fresh Sonnet subagent per execution milestone after spec freeze: dispatches tickets, runs the merge lane and fix loop from the resume file, returns one digest; never talks to the user (`start`/references/lifecycle.md). | sub-orchestrator, manager agent |
| Resume file | `.scratch/<slug>/resume.md`, overwritten at each milestone boundary: ledger pointer, live `Decision:` lines, open tickets, next step, how to resume. Feeds each captain and a fresh session. | checkpoint file (Checkpoint is the spec message), handoff (omp `/handoff` compacts in place) |
| Ruling | Autonomous decision recorded as `Ruling: what — why — cost if wrong`. | decision log |
| HITL / AFK | Human-in-the-loop vs autonomous stage marking; declared in `interaction` frontmatter. | interactive / automatic |
| Prototype flag | Big-prototype triage outcome; same flow, reduced gates, DoD = question answered/demoable, carries `deploy: main/standalone/none`. | spike |
| Quick prototype | `prototype` skill output: one question → one throwaway self-contained HTML page in `.scratch/<slug>/prototype/`; no intake/spec/tickets; ends in a handoff file and a direct port or `graduate-prototype`. | mockup, spike |
| Handoff | `<NN>-<task>.handoff.md`: verdict, chosen variant, tokens → theme, states, motion, copy, what was faked; the port's spec. | notes |
| UI contract | Frozen `.scratch/<slug>/contract/` of a UI feature: reference PNGs per screen × state × phone/tablet × theme, `acceptance.md`, `motion.md`, rulings in `contract.md`; UI tickets carry `Contract:` and `Reference:` lines and the build implements to it (`prototype`/references/contract.md). | mockup, design spec, golden |
| Contract sitting | The one up-front session where the user marks every contract page frame OK or annotates it once; ends in the freeze. Only for features adding or redesigning screens or motion. | design review, re-gate |
| Deploy target | build-only (default), firebase, tailscale, or local; ordered list in PROFILE.md. | environment |
| Build identity | Per-install versionCode/versionName/APK name from deliver's allocator: one ledger in the git common dir shared by all worktrees, code never below the device's, no name ever reused. versionName `<semver>-<slug>.<n>` (plain `<semver>` only for a release); APK `<app>-<version_name>-<code>-<variant>.apk`. Semver bumps only on a release. | build number |
| Rules payload | Swappable `references/rules-*.md` carrying style/architecture rules; procedures stay generic (T008). | config |
| Component tier | Requirement level of the UI component rules for one module: `library` (design-system, shared by ≥2 features, or published; MUST) or `app` (feature-local; SHOULD). Inferred per module; ambiguous → `start` asks once, ledgered as `Ruling: ui-tier`. | strictness, mode |
| State holder (plain) | `@Stable class XxxState` + `rememberXxxState()` owning a component's UI state and UI logic; lives in composition, unit-tested headless. Not a ViewModel. | controller, presenter |
| Slot | A `@Composable` lambda parameter for a caller-varying region (`label`, `leadingIcon`); nullable with a `null` default when optional. | render prop, content param |
| `XxxDefaults` | The public object holding a component's default values and `colors()` factories, so wrappers can reproduce them. | style class, config |
| Development style | Per-project choice in `init-profile` question 9, recorded as PROFILE `changes:`: `default` (= `pr`: one PR or `gh stack` per run) or `trunk` (`ship-to-trunk`). Only the user switches it. | workflow mode, branching strategy |
| Trunk | `main`, kept releasable after every merge; in `changes: trunk` runs every ticket merges into it as its own PR within hours (`ship-to-trunk`). | integration branch, develop |
| PR check | The CI workflow on `pull_request` that main's branch protection requires; the merge judge in trunk runs. PROFILE `pr-check: none` (opt-in, `init-profile` answer `trunk-local`) replaces it with the local suite on the branch rebased onto fresh `origin/main`; main's post-merge workflow is then the safety net. Absent → the required check. | CI gate, status check |
| Slice PR | One ticket's small PR (one concern, ≤ ~400 changed lines) branched from fresh `origin/main` and merged on a green check; never bumps the release version. | stack layer, partial PR |
| Release flag | Typed flag that keeps unfinished behavior dark: off in release builds, forced-on toggle in debug; added by the feature's first ticket, flipped by the flip PR, deleted by the cleanup ticket. Owned by `wire-dev-settings`. | feature toggle (ambiguous), kill switch (= ops flag) |
| Flip PR | The PR that turns a release flag's release default on and bumps the version; the release of a trunk feature, merged only with user approval after user-check OK and thorough review. | launch PR, release branch |
| Live change | A change no flag can hide (schema migration, persisted format, manifest/permission, dependency bump); ships backward compatible in its own PR with user approval. | breaking change |
| Goldfish | Fresh-context subagent that has not seen the conversation; gets a brief file (hypothesis + hard constraints, or spec + file maps) and reviews one angle. | reviewer (reviewer = diff grader) |
| Lens | One goldfish angle with its own objective and evidence (reuse, persona flows, data & migration, failure & resources, best version, verifiability; architecture, patterns, file structure). Stage A: the orchestrator picks 0–2 by risk after scope is confirmed; stage B: the user picks none / up to 3 / all. | persona, checklist |
| Tension | Two lenses pulling opposite ways, kept visible with the parent's pick and why; never averaged. | conflict |
| Not run | A lens that produced no findings file; reported as missing coverage, never as clean. | skipped, passed |
| Standards block | ≤5 lines in an implementer brief naming the rules this ticket must satisfy, picked by care-axes rank and ticket shape. | rules dump |
| File map | Per-ticket list of path — one-sentence responsibility; "and" in a line means two files. | file list |
| Session audit | A `skill-doctor` run: one window of omp session transcripts turned into metrics, graded scores, verified findings and proposals. | retro (= one run's `retrospect`), review |
| Condensed transcript | The per-session digest `skill-doctor` writes for graders: user turns, asks, spawns, errors, compactions and replies kept, routine tool calls folded into counts, every line addressed by its JSONL line `#n`. | summary, log |
| Change unit | One delivered change inside a session (a merged ticket or a quick-task fix); the denominator for per-change cost and ask rates. | task, PR |
| Skills hash | Hash of the skills dir recorded per audit run; two runs with the same hash measure drift, not a skill change. | version |
| Proposal | A ranked, verified skill change from a session audit with `token_delta` and `success_metric`; lands only through `integrate-skill` path B after the user picks it. | suggestion, fix |
