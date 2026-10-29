# ivandsky-skills

My personal skillset for AI coding agents — small, composable skills in the
open [Agent Skills](https://agentskills.io/specification) format, written to
give greenfield and brownfield work a predictable, reliable flow.

> **Status:** v1 is being charted. The plan of record lives in
> [`.scratch/skillset-v1/MAP.md`](.scratch/skillset-v1/MAP.md) (wayfinder map,
> local markdown tracker).

## Layout

```
skills/<name>/          # one directory per skill
├── SKILL.md            # required: YAML frontmatter + instructions
├── references/         # optional: detail docs, loaded only when needed
└── scripts/            # optional: helper scripts the instructions call
_template/              # copy to skills/<name>/ to start a new skill
```

## Writing a skill

1. `cp -r _template skills/my-skill` — the `name` must match the directory.
2. Frontmatter rules:

   | Field | Rules |
   |---|---|
   | `name` | required; lowercase `a-z`, `0-9`, hyphens; matches the directory |
   | `description` | required; say what it does **and** when to use it ("Use when..."). Empty description = the skill silently never loads. |
   | `disable-model-invocation` | `true` hides it from the agent — only explicit invocation fires it. Use for skills only you summon. |

3. Keep `SKILL.md` short: decision flow, common commands, contract. Push long
   detail into `references/*.md` behind context pointers. Steps end in
   checkable completion criteria.
4. Say whether a skill is **HITL** (needs a live human) or **AFK** (agent
   drives alone) — in the body, explicitly.

Python-backed skills (agent calls `await my_skill(...)` directly) follow the
Prime Agent contract: `pyproject.toml` at the skill root, `src/<import_name>/`
layout, a documented `run()`. Decide per skill; see Prime Agent's
`skill-creator` docs for the full contract.

## Distribution

Once v1 lands, install from any project:

```bash
npx skills add ivanDsky/skills
```

Until then, skills are installed by hand (copy a skill directory into the
agent's skills location, e.g. `~/.agents/skills/`).

## Planning process

This repo plans its own evolution with the **wayfinder** skill: a shared map
plus decision tickets on a **local markdown tracker** — issues live as files
under `.scratch/<effort>/`. See `docs/agents/issue-tracker.md` for the
conventions.
