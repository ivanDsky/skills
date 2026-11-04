# ivandsky-skills

My personal skillset for AI coding agents — one flow, 24 small composable
skills in the open [Agent Skills](https://agentskills.io/specification)
format. Install it, run `/start`, and the right stages fire: intake asks the
few questions worth asking, specs get drafted with marked assumptions, tickets
carry checkable definitions of done, implementation runs per-ticket subagents,
review is tiered by effort, and delivery produces build/deploy evidence.

## The flow

```
/start ──> intake ──> spec (+ one checkpoint) ──> tickets ──> [research]
       ──> implement ──> review ──> deliver (build | deploy)
conditional: map-codebase (unmapped repo) · prototype mode · teardown gate
```

Stages are conditional and effort-scaled: the effort level (fast / standard /
thorough, set per project in `PROFILE.md`, overridable per session) maps to
subagent thinking, review depth, and which gates block. Prototypes are a flag
on the same flow, not a second process. When a module fails its second fix
round, an independent architect decides fix-forward vs teardown.

## Skills

**Flow (fresh, authored):**
`start` · `run-intake` · `draft-spec` · `write-tickets` · `implement` ·
`review-change` · `deliver` · `map-codebase` · `fan-out-research` ·
`graduate-prototype` · `assess-teardown` · `init-profile` · `integrate-skill` ·
`diagnose-bug` (bug reports: evidence ladder, user-time-last) ·
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
`micro-architecture` (feature-level file split: parallel-safe waves, open/closed one-file extension, single responsibility per file) ·
`senior-dev` (judgment defaults: verify before trusting, smallest correct change, reproduce before fixing, own mistakes) ·
`adopt-tool` (one-pass capability adoption checklist: verify → route → wire → mandate → navigate → eval → demo → ship from repo) ·
`goldfish-review` (fresh-context lenses on a concept or design before code: reuse, persona flows, data, failure, best version, verifiability; architecture, patterns, file structure — you choose none / up to 3 / all) ·
`structure-checks` (Konsist suite for Kotlin: one public type per file, layer dependencies, shrink-only allowlist — the mechanical backstop for file structure)

**Adapted (owned text, credited sources):**
`ponytail` (smallest-change governor) · `run-intake` core mechanics from
mattpocock/skills · `tdd` (fakes-over-mocks payload) from obra/superpowers ·
`scope-creep-detector` from awesome-llm-apps · `goldfish-review` from
google/elephant-goldfish-model (Apache-2.0)

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

Precedence: session > project > global user > skill defaults.
Vocabulary: [GLOSSARY.md](GLOSSARY.md).

## Layout

```
skills/<name>/          # one directory per skill
├── SKILL.md            # required: YAML frontmatter + instructions
├── references/         # optional: detail docs, loaded only when needed
└── scripts/            # optional: helper scripts the instructions call
evals/<name>.json       # routing trigger cases (>=3 positive, >=2 near-miss)
docs/skill-template/    # copy to skills/<name>/ to start a new skill
scripts/lint_skills.py  # ported from awesome-llm-apps (Apache-2.0)
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

## Distribution

```bash
npx skills add ivanDsky/skills
```

## Planning

This repo plans its own evolution with the **wayfinder** skill: a shared map
plus decision tickets on a private local markdown tracker (`.scratch/`, kept
out of the repo). Conventions: `docs/agents/issue-tracker.md`.
