# GLOSSARY

Motion effects are named with canonical animation terms — `animation-vocabulary` resolves vague descriptions to names; do not invent adjectives.

Canonical vocabulary for this skillset. Use these terms in tickets, specs, and replies; the Avoid column lists words NOT to use (they mean something else or blur distinctions). Source: T006 spec §6.

Repo-root GLOSSARY.md (T008: yes), format per term: one-line definition + `_Avoid:_` synonyms. Seed:

| Term | Definition | Avoid |
|---|---|---|
| Stage | One named step of the /start flow (intake, orientation, spec, tickets, research, implement, user check, review, deliver). | phase |
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
| Ruling | Autonomous decision recorded as `Ruling: what — why — cost if wrong`. | decision log |
| HITL / AFK | Human-in-the-loop vs autonomous stage marking; declared in `interaction` frontmatter. | interactive / automatic |
| Prototype flag | Big-prototype triage outcome; same flow, reduced gates, DoD = question answered/demoable, carries `deploy: main/standalone/none`. | spike |
| Quick prototype | `prototype` skill output: one question → one throwaway self-contained HTML page in `.scratch/<slug>/prototype/`; no intake/spec/tickets; ends in a handoff file and a direct port or `graduate-prototype`. | mockup, spike |
| Handoff | `<NN>-<task>.handoff.md`: verdict, chosen variant, tokens → theme, states, motion, copy, what was faked; the port's spec. | notes |
| Deploy target | build-only (default), firebase, tailscale, or local; ordered list in PROFILE.md. | environment |
| Build identity | Per-install versionCode/versionName/APK name from deliver's allocator: one ledger in the git common dir shared by all worktrees, code never below the device's, no name ever reused. versionName `<semver>-<slug>.<n>` (plain `<semver>` only for a release); APK `<app>-<version_name>-<code>-<variant>.apk`. Semver bumps only on a release. | build number |
| Rules payload | Swappable `references/rules-*.md` carrying style/architecture rules; procedures stay generic (T008). | config |
| Component tier | Requirement level of the UI component rules for one module: `library` (design-system, shared by ≥2 features, or published; MUST) or `app` (feature-local; SHOULD). Inferred per module; ambiguous → `start` asks once, ledgered as `Ruling: ui-tier`. | strictness, mode |
| State holder (plain) | `@Stable class XxxState` + `rememberXxxState()` owning a component's UI state and UI logic; lives in composition, unit-tested headless. Not a ViewModel. | controller, presenter |
| Slot | A `@Composable` lambda parameter for a caller-varying region (`label`, `leadingIcon`); nullable with a `null` default when optional. | render prop, content param |
| `XxxDefaults` | The public object holding a component's default values and `colors()` factories, so wrappers can reproduce them. | style class, config |
| Goldfish | Fresh-context subagent that has not seen the conversation; gets a brief file (hypothesis + hard constraints, or spec + file maps) and reviews one angle. | reviewer (reviewer = diff grader) |
| Lens | One goldfish angle with its own objective and evidence (reuse, persona flows, data & migration, failure & resources, best version, verifiability; architecture, patterns, file structure). User picks the count: none / up to 3 / all. | persona, checklist |
| Tension | Two lenses pulling opposite ways, kept visible with the parent's pick and why; never averaged. | conflict |
| Not run | A lens that produced no findings file; reported as missing coverage, never as clean. | skipped, passed |
| Standards block | ≤5 lines in an implementer brief naming the rules this ticket must satisfy, picked by care-axes rank and ticket shape. | rules dump |
| File map | Per-ticket list of path — one-sentence responsibility; "and" in a line means two files. | file list |
