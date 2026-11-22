# ivandsky-skills

My personal skillset for AI coding agents — one flow, 26 small composable
skills in the open [Agent Skills](https://agentskills.io/specification)
format. Install it, run `/start`, and the right stages fire: intake asks the
few questions worth asking, specs get drafted with marked assumptions, tickets
carry checkable definitions of done, implementation runs per-ticket subagents,
review is tiered by effort, and delivery produces build/deploy evidence.

## The flow

```
/start ──> intake ──> spec (+ one checkpoint) ──> tickets ──> [research]
       ──> implement ──> user check ──> review ──> deliver (build | deploy)
                         ↺ feedback → fast fix
                         ok → re-gate → hardening tickets
conditional: map-codebase (unmapped repo) · prototype mode · teardown gate
```

The user tries the whole change before any review, test suite or PR body:
feedback rounds are fast fixes that ignore code quality, and on OK the run
goes back to design level (spec vs feedback vs code, senior-dev and
architecture checks) and pays the debt down as hardening tickets. The full
suite runs once, in review. The user reads code last, in the PR.

Stages are conditional and effort-scaled: the effort level (fast / standard /
thorough, set per project in `PROFILE.md`, overridable per session) maps to
subagent thinking, review depth, and which gates block. Prototypes are a flag
on the same flow, not a second process. When a module fails its second fix
round, an independent architect decides fix-forward vs teardown.

**Shared backlog.** Features take the chain above. Bugs and one-shot fixes go
through a shared backlog instead: GitHub Issues, or files in the clone's git
dir, chosen per project at `init-profile`. A feedback session
(`file-tickets`) turns whatever you say into deduplicated tickets and never
implements. Worker sessions (`work-tickets`) in any worktree claim packs of up
to 5 matching tickets atomically and land each as its own small PR, merged
dark. Tickets that need your eyes wait in `needs-check` until one batched
build. A release cuts `main` as it stands, and unfinished tickets roll over.

```
feedback session ──file──> backlog ──claim pack──> worker (any worktree) ──PR merged──> done | needs-check
     └────────── check batch: one build, your replies ──────────────────────────────────────┘
```

## Skills

**Flow (fresh, authored):**
`start` · `run-intake` · `draft-spec` · `write-tickets` · `implement` ·
`user-check` · `review-change` · `deliver` · `map-codebase` · `fan-out-research` ·
`graduate-prototype` · `assess-teardown` · `init-profile` · `integrate-skill` ·
`diagnose-bug` (bug reports: evidence ladder, user-time-last) ·
`file-tickets` (feedback session: deduplicated backlog tickets, batched hands-on checks; never implements) ·
`work-tickets` (worker session: atomic pack claims, one dark PR per ticket; GitHub Issues or local backend) ·
`design-architecture` (SOLID payload, wired into spec/implement/review) ·
`preview-compose` (previews + animation preview verification) ·
`deploy-firebase` (test users + APK distribution) ·
`deploy-tailscale` (device registry + APK sharing)
`wire-dev-settings` (reactive Firebase flags, dev menu, Showkase playground) ·
`review-site` (one-file localhost review dashboard: changes, screenshots, diagrams, test report) ·
`android-cli` (Android CLI routing: device-free preview renders, Studio analysis, docs, emulator/device control, Journeys, Crashlytics signals) ·
`android-env` (session bootstrap: PATH, local.properties, worktree git, device connect, Gradle triage, Studio modal handling) ·
`web-env` (web/Node session bootstrap: runtime + package-manager resolution, env files, ports, lockfiles, dev-server triage, Playwright evidence) ·
`senior-ux` (UX engineering method: framework-judged pixels, measured references, A/B on user hardware, tokens with computed floors, walk-every-state) ·
`micro-architecture` (feature-level file split: parallel-safe waves, open/closed one-file extension, single responsibility per file; reusable Compose component API — library/app tier, slots vs params, Modifier vs component, state owner ladder, `XxxDefaults`, with a compiled sample) ·
`senior-dev` (judgment defaults: verify before trusting, smallest correct change, reproduce before fixing, own mistakes) ·
`adopt-tool` (one-pass capability adoption checklist: verify → route → wire → mandate → navigate → eval → demo → ship from repo) ·
`goldfish-review` (fresh-context lenses on a concept or design before code: reuse, persona flows, data, failure, best version, verifiability; architecture, patterns, file structure — concept lenses run only after you confirm scope, at most 2 picked by risk; design lenses: you choose none / up to 3 / all) ·
`structure-checks` (Konsist suite for Kotlin: one public type per file, layer dependencies, shrink-only allowlist, opt-in component-API check — the mechanical backstop for file structure) ·
`open-pr` (PR as a 2-minute read: summary, before/after screenshot-test captures, major changes, top-3 review checks with line links, optional diagram; big runs as a per-ticket `gh stack` with fixes landing in the owning layer; start asks trunk, one PR, or straight to main) ·
`ship-to-trunk` (trunk-based delivery: every ticket a small slice PR merged into main within hours behind a release flag, live changes backward compatible and user-approved, one release PR per epic turns the flags on, removes them and bumps the version on one explicit owner Yes to "Release <X.Y.Z>?"; a leftover ticket removes any the release left) ·
`prototype` (quick throwaway prototype: one task → one self-contained HTML page, 2-3 switchable variants judged with senior-ux on your phone, one subagent per task + an index page; small picks ported straight into the app, big ones through graduate-prototype)

**Adapted (owned text, credited sources):**
`ponytail` (smallest-change governor) · `run-intake` core mechanics from
mattpocock/skills · `tdd` (fakes-over-mocks payload) from obra/superpowers ·
`scope-creep-detector` from awesome-llm-apps · `goldfish-review` from
google/elephant-goldfish-model (Apache-2.0) · `prototype` from
mattpocock/skills (MIT) · `skill-doctor` (session audit: omp transcript
metrics, graded scores, verified skill-line findings, ranked change proposals
it never applies) from warpdotdev/common-skills skill-doctor (MIT)

**Installed as-is (vendored, attributed — see skills/ATTRIBUTION.md):**
`design-taste-frontend` · `archify` · `ponytail-review` / `-audit` / `-debt` ·
`ui-ux-pro-max`

Design knowledge ships here too — `apple-design`, `emil-design-eng`,
`animation-vocabulary` (vendored from emilkowalski/skills, MIT), plus
`ui-ux-pro-max` for stack-specific guidelines. Every skill carries routing
trigger cases in `evals/` (one file per skill). Flow skills name the moment to
reach for expertise and descriptions route the rest; the repo is
self-sufficient — no other skills need to be installed.

## Configuration

- **Global user layer** (`~/.agents/AGENTS.md`): preferred stack, default
  platform, UI taste, hard style rules — written once, checked by `init-profile`.
- **Project** (`PROFILE.md` + `docs/agents/*.md`): deltas only — deploy
  targets, testing style, effort default, tracker config.
- **Feedback loop**: corrections end with `Save this? [p]roject config |
  [s]kill update | [n]o` — project-local exceptions or durable skill fixes
  (which land only through `integrate-skill`'s lint + trigger-case gate).
- **Debug run log**: `debug: on` makes every skill append a ≤4-line entry to
  `.scratch/run-log.md` — what fired, what it contributed, what went too deep
  and why.
- **Voice**: chat, briefs, worker/reviewer reports, ledgers and findings
  files use the caveman voice (`start` § Voice; install upstream once:
  `npx skills add JuliusBrussee/caveman --skill caveman -g`). Questions,
  warnings and persisted human docs (PRs, specs, tickets) stay plain prose.
- **Model routing**: each ticket's `tier:` picks agent, model and spawn
  effort from one table (`start`/references/effort-mapping.md).

Precedence: session > project > global user > skill defaults.
Vocabulary: [GLOSSARY.md](GLOSSARY.md).

## Layout

```
skills/<name>/          # one directory per skill
├── SKILL.md            # required: YAML frontmatter + instructions
├── references/         # optional: detail docs, loaded only when needed
└── scripts/            # optional: helper scripts the instructions call
    └── tests/          # pytest suites + fixtures from real inputs; lint runs them
evals/<name>.json       # routing trigger cases (>=3 positive, >=2 near-miss)
hooks/pre/*.ts          # versioned omp guard hooks (install: § Hooks)
hooks/claude/*.ts       # Claude Code PreToolUse entries running the same hooks (§ Claude Code)
hooks/test/             # bun tests for the hooks
claude/agents/*.md      # Claude Code subagents: reviewer, goldfish, scout, security-reviewer, sonic
claude/CLAUDE.md        # omp → Claude Code term map, installed into ~/.claude/CLAUDE.md
claude/bots.json        # Orca bot manifest: shared skills, per-bot skills + settings (§ Claude Code)
claude/bots/<bot>/SOUL.md # each bot's SOUL.md, installed into ~/.orca/bots/<bot>/
docs/skill-template/    # copy to skills/<name>/ to start a new skill
scripts/lint_skills.py  # ported from awesome-llm-apps (Apache-2.0); no argument = every skill
scripts/test_skills.py  # runs every skills/*/scripts/tests with pytest (lint calls it)
scripts/claude_install.py # installs the Claude Code pieces and the bots (tests: scripts/tests/)
scripts/update.sh        # one command after git pull: omp skills, Claude Code and every bot
```

## Writing a skill

1. `cp -r docs/skill-template skills/my-skill` — the `name` must match the directory.
2. Frontmatter rules:

   | Field | Rules |
   |---|---|
   | `name` | required; lowercase `a-z`, `0-9`, hyphens; matches the directory |
   | `description` | required; say what it does **and** when to use it ("Use when..."). Empty description = the skill silently never loads. |
   | `interaction` | our extension: `hitl` (stops for the human), `afk` (runs alone), `mixed` |
   | `requires` | our extension: external tools the skill needs; `/start` checks before routing |

3. Keep `SKILL.md` small (≤ ~1.5k tokens): decision rules, not prose. Push
   detail into `references/*.md` behind "read X when Y" pointers.
4. Every skill gets `evals/<name>.json` trigger cases; routing failures are
   fixed by editing the description, never the eval.
5. New and changed skills land through `integrate-skill` — lint PASS required.
6. Every script ships with pytest tests under `scripts/tests/`, with fixtures
   captured from real inputs (real PROFILE wording, real `gh`/`adb` output;
   identifiers scrubbed). `python3 scripts/lint_skills.py [skills/<name>]`
   runs them, so a failing script test fails lint. Uses `pytest` when
   importable, else `uv run --with pytest`; neither available fails lint.

## Distribution

```bash
npx skills add ivanDsky/skills
```

## Hooks

Rules an agent broke twice in prose are enforced by a hook, and the hook is
versioned here instead of living only in `~/.omp`. `hooks/pre/worker-guard.ts`
blocks the mechanically detectable worker hard rules in bash commands
(`skills/implement/references/hard-rules.md`): `pkill`/`killall` of
Gradle/Java/build-slot, `gradlew --stop`, `git add -A`/`--all`/`.`, and `rm` of
`~/.gradle`, `~/Library` or `~/.android`. `hooks/pre/tailnet-leak-guard.ts`
refuses a `git commit` or `git push` whose added lines carry a Tailscale
address (100.64.0.0/10) or a `*.ts.net` name; device data belongs in the
gitignored `PROFILE.local.md` (deploy-tailscale § 2). `hooks/pre/build-queue.ts`
prefixes agent `gradlew` and `ship_apk.py` calls, and `bash <abs path>.sh` scripts
that run gradlew, with `~/.local/bin/build-slot` (a machine-wide build queue that
lives outside this repo; without it the hook does nothing). `hooks/pre/apk-ship-guard.ts`
refuses raw Taildrop copies and `adb install` of APKs without a canonical
build-identity name (deliver). Install (omp loads every `.ts` in that directory) and test:

```bash
mkdir -p ~/.omp/agent/hooks/pre && cp hooks/pre/*.ts ~/.omp/agent/hooks/pre/
bun test hooks/
```

Re-run the `cp` after every change under `hooks/pre/`; the installed copy is
not a symlink. Limits are listed at the top of each hook.

## Claude Code (Orca bots)

The skills are written for omp; the same checkout also runs under plain
Claude Code, where the 8 Orca bots (intake, planner, designer, builder, fixer,
lander, tester, coach) run. `scripts/claude_install.py` writes only `~/.claude`,
`~/.orca/bots/<bot>/` and its store; omp never reads those, and `~/.agents/skills`
stays the omp install.

Each bot sees a small shared set plus its own role skills, nothing else. A skill
list costs context at every session start, so scoping matters: a builder session
went from 28.2k to 21.5k input tokens.

- Manifest: `claude/bots.json` holds the `shared` set (what worker sessions in
  PuzzleBox worktrees need: they only get user-level skills), the per-bot
  `skills`, and each bot's `settings` (model, effortLevel, permissions). The
  bot's `SOUL.md` lives in `claude/bots/<bot>/`. Change a bot here, not in its
  folder.
- Store: `install` copies `skills/`, `hooks/` and `claude/` to
  `~/.local/share/ivandsky-skills`, and links every other skill in
  `~/.agents/skills` (caveman, mattpocock, orchestration, …) into its `skills/`.
  All links and hook commands point there, so deleting or moving this checkout
  breaks nothing, and `skill://<name>` resolves there for every skill, installed
  or not.
- `~/.claude/skills`: the shared set only. Other symlinks are removed (their
  original targets are kept in `~/.claude/.skills-bots-install.json`); real
  directories are reported and left.
- Bots: each existing `~/.orca/bots/<bot>/` gets `.claude/skills/<skill>` links
  for its role set, plus `.claude/settings.json` and `SOUL.md` from the manifest.
  A bot missing in Orca is reported, never created. Anything else in the bot
  folder is kept. A `settings.json` or `SOUL.md` edited by hand is shown as a
  diff and overwritten only with `install --force` (after a backup).
- Settings: one `PreToolUse` group (matcher `Bash`) in `~/.claude/settings.json`
  runs `hooks/claude/<hook>.ts` with bun. Each entry imports the omp hook from
  `hooks/pre/` unchanged through `hooks/claude/adapter.ts`: a block becomes
  `permissionDecision: "deny"`, a rewrite becomes `updatedInput`. The manifest's
  `user_settings` turn off claude.ai synced skills (`syncClaudeAiSkills`),
  bundled skills (`disableBundledSkills`) and the built-in `plugin-authoring`
  skill (`skillOverrides`). Other keys and hook groups (Orca, Superset) are left
  as they are, and every write backs the file up to
  `settings.json.pre-bots-<timestamp>`.
- Subagents: `claude/agents/*.md` symlinked into `~/.claude/agents/`.
- Note: `claude/CLAUDE.md` goes into a marked block of `~/.claude/CLAUDE.md`. It
  maps `skill://` paths and the omp tools (`task`, `todo`, `ask`, `eval`,
  `local://`, …) to their Claude Code equivalents, so the skill text keeps one
  wording for both harnesses.

Update everything after a `git pull` (idempotent):

```bash
scripts/update.sh            # npx skills update -g (omp), then claude_install.py install + status
SKIP_OMP=1 scripts/update.sh # Claude Code and bots only
```

New machine:

1. Install Orca (it provides the `orchestration` and `orca-cli` skills in
   `~/.agents/skills`), Claude Code and bun, and clone this repo.
2. Install omp's skills once; `install` refuses a manifest skill that exists
   neither here nor in `~/.agents/skills`:

   ```bash
   for s in ivanDsky/skills mattpocock/skills JuliusBrussee/caveman emilkowalski/skill vercel-labs/skills tw93/Mole; do
     npx skills add "$s" -g
   done
   ```

3. Run `scripts/update.sh`.
4. Create the 8 bots in the Orca GUI (a bot can't be created from outside Orca),
   then run `scripts/update.sh` again so the bots get their skills, settings and
   SOUL.md.

```bash
python3 scripts/claude_install.py install [--force]
python3 scripts/claude_install.py status      # drift per bot: missing/extra skills, edited files
python3 scripts/claude_install.py uninstall   # restores settings, links and CLAUDE.md; removes the store
python3 -m pytest scripts/tests/test_claude_install.py
```

The store is a copy: changes in this checkout reach Claude Code and the bots
only after `install`. Limits: the hooks see Bash calls only; skills with
`disable-model-invocation: true` (pick-ui-library, review-animations, handoff)
are installed but only typable as `/name`, never listed to the model; a
subagent always gets Claude Code's git status snapshot (goldfish lenses are
told not to use it).

## Planning

This repo plans its own evolution with the **wayfinder** skill: a shared map
plus decision tickets on a private local markdown tracker (`.scratch/`, kept
out of the repo). Conventions: `docs/agents/issue-tracker.md`.
