---
id: R004
title: npx skills ecosystem mechanics (vercel-labs/skills, vercel-labs/agent-skills, skills.sh)
source-tickets: [T004]
date: 2026-10-29
---

# The npx skills ecosystem: what makes a repo a first-class citizen

## What it is

`npx skills` (npm package `skills`, repo `vercel-labs/skills`) is the de-facto package manager for agent skills: it discovers `SKILL.md` files in any git repo, lets the user pick skills + target agents, and symlinks (or copies) them into per-agent skill directories. [skills.sh](https://skills.sh) is its discovery surface — a leaderboard ranked by anonymous install telemetry from the CLI, with one page per repo/skill. A repo is a "first-class citizen" when `npx skills add <owner>/<repo>` finds its skills in standard locations, each skill has clean frontmatter, and the skills.sh page reads well (groupings, badge).

## How it works

### Discovery — what `add` scans in a source repo

Priority search, in order, then a fallback ([docs/creating-skills.md](https://raw.githubusercontent.com/vercel-labs/skills/main/docs/creating-skills.md), [src/skills.ts](https://raw.githubusercontent.com/vercel-labs/skills/main/src/skills.ts)):

1. **Repo-root `SKILL.md`** — if present, it is the repo (returns early; "If pointing directly at a skill, add it (and return early unless fullDepth is set)"). Exception: a root skill that matches the repo's own `skills-lock.json` is treated as an *installed copy* and skipped so source skills are surfaced ([src/skills.ts](https://raw.githubusercontent.com/vercel-labs/skills/main/src/skills.ts): `isInstalledProjectSkill`).
2. **Known container dirs, walked 3 levels deep** ("flat layouts (`skills/<name>/SKILL.md`) and catalog layouts with one or two category levels"). The list ([src/skills.ts](https://raw.githubusercontent.com/vercel-labs/skills/main/src/skills.ts) `AGENT_PROJECT_SKILL_DIRS` + [docs/creating-skills.md](https://raw.githubusercontent.com/vercel-labs/skills/main/docs/creating-skills.md) skill-discovery block): `skills/` (plus `skills/.curated/`, `skills/.experimental/`, `skills/.system/`), `.agents/skills/`, `.claude/skills/`, `.codex/skills/`, `.pi/skills/`, `.cursor/skills/` (~30 agent dirs — all share the same walk). Constant: `DEFAULT_SKILL_CONTAINER_DEPTH = 3` ([src/constants.ts](https://raw.githubusercontent.com/vercel-labs/skills/main/src/constants.ts)).
3. **Repo root at depth 1** — any *immediate* subdirectory containing `SKILL.md` is found even outside `skills/`. Verified live: `npx skills add ivanDsky/skills --list` found our `_template/SKILL.md` as skill `template` alongside `skills/example-skill`. Deeper strays (e.g. `examples/foo/SKILL.md`) are only found with `--full-depth` or the recursive fallback.
4. **`skills.sh.json` `paths` field** — repo-root JSON with `"paths": ["./tools/skills"]` adds custom container dirs ("Each entry is a container directory… searched the same way as `skills/`, up to three levels deep. Entries must start with `./`… If two skills have the same name, only the first one found is kept") ([docs/creating-skills.md](https://raw.githubusercontent.com/vercel-labs/skills/main/docs/creating-skills.md), [src/skills-sh-config.ts](https://raw.githubusercontent.com/vercel-labs/skills/main/src/skills-sh-config.ts)). Invalid entries are silently ignored.
5. **Plugin manifests** — `.claude-plugin/marketplace.json` / `plugin.json` skill paths are discovered at their declared depth (Claude Code marketplace compat) ([docs/creating-skills.md](https://raw.githubusercontent.com/vercel-labs/skills/main/docs/creating-skills.md)).
6. **Fallback** — full recursive walk (depth ≤ 5, skipping `node_modules/.git/dist/build/__pycache__`) "if nothing found, or if fullDepth is set" ([src/skills.ts](https://raw.githubusercontent.com/vercel-labs/skills/main/src/skills.ts)).

A discovered `SKILL.md` is a skill only if its YAML frontmatter has non-empty string `name` **and** `description`; otherwise it is skipped with a warning ("missing required frontmatter field(s): …") ([src/skills.ts](https://raw.githubusercontent.com/vercel-labs/skills/main/src/skills.ts) `parseSkillMd`). The parser is a minimal YAML-only `---` block parser ([src/frontmatter.ts](https://raw.githubusercontent.com/vercel-labs/skills/main/src/frontmatter.ts)). **The CLI never checks that `name` matches the directory name** — the skill's identity is frontmatter `name` (dedup: "If two skills have the same name, only the first one found is kept"). `metadata.internal: true` hides a skill from discovery unless `INSTALL_INTERNAL_SKILLS=1` or the user names it explicitly ([docs/creating-skills.md](https://raw.githubusercontent.com/vercel-labs/skills/main/docs/creating-skills.md)).

### Install — picking skills and agents

Interactive flow: choose skills (name + description is *all* the user sees — verified via `add --list` output), choose agents, choose symlink vs copy ([docs/commands.md](https://raw.githubusercontent.com/vercel-labs/skills/main/docs/commands.md)). Non-interactive: `--skill <names>` / `--skill '*'`, `-a <agents>` / `-a '*'`, `-y`, `--all` ("Install all skills to all agents without prompts"). Sources: `owner/repo`, full URLs (GitHub/GitLab/Azure/any git), direct skill-dir URL, direct download URL (single SKILL.md or archive), or local path ([docs/commands.md](https://raw.githubusercontent.com/vercel-labs/skills/main/docs/commands.md)). Private repos work with the user's existing git credentials / `gh` / SSH; `GITHUB_TOKEN`/`GH_TOKEN` optional ([docs/commands.md](https://raw.githubusercontent.com/vercel-labs/skills/main/docs/commands.md)) — our private repo cloned fine in the live `--list` test.

Destinations per agent ([docs/agents.md](https://raw.githubusercontent.com/vercel-labs/skills/main/docs/agents.md)): project `./<agent-dir>/skills/`, global `~/<agent-dir>/skills/` with `-g`. Many agents share `.agents/skills/` (codex, pi, cursor, amp, opencode, gemini-cli, copilot…); Claude Code gets `.claude/skills/`. Symlink mode copies into "the canonical dir" and symlinks each agent dir to it — single source of truth, easy `update`/`check` ([src/installer.ts](https://raw.githubusercontent.com/vercel-labs/skills/main/src/installer.ts): "`symlink`: copy into the canonical dir, symlink agent dirs to it"). Installed skills are tracked in a project `skills-lock.json` (full support in the experimental `sync`/`install` commands) ([docs/commands.md](https://raw.githubusercontent.com/vercel-labs/skills/main/docs/commands.md)).

**Targeting prime-agent/pi:** `pi` (badlogic/pi-mono) is a first-class target: `-a pi` → project `.agents/skills/`, global `~/.agents/skills/` ([docs/agents.md](https://raw.githubusercontent.com/vercel-labs/skills/main/docs/agents.md)). prime-agent itself is not in the CLI's agent table, but it reads skills from `~/.agents/skills/` and `.agents/skills/` (its own installed skills live there), so `pi`/`codex`/`amp`-style installs land exactly where prime-agent looks. Compatibility extensions (`allowed-tools`, `context: fork`, hooks) vary by agent; plain frontmatter skills are universal ("Skills are generally compatible across agents since they follow a shared Agent Skills specification") ([docs/agents.md](https://raw.githubusercontent.com/vercel-labs/skills/main/docs/agents.md)).

### skills.sh — listing, search, badges, skills.sh.json

- **Listing:** a repo page exists once the CLI has seen installs of it — the leaderboard is "ranked based on anonymous telemetry data collected from the skills CLI" ([docs](https://skills.sh/docs)); telemetry posts `event: 'install'` with source + skills to `www.skills.sh/tele/t` ([src/telemetry.ts](https://raw.githubusercontent.com/vercel-labs/skills/main/src/telemetry.ts)); opt-out via `DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1` per [README](https://raw.githubusercontent.com/vercel-labs/skills/main/README.md). `npx skills find` searches skills.sh's API and prints `owner/repo@skill` + install counts ([src/find.ts](https://raw.githubusercontent.com/vercel-labs/skills/main/src/find.ts): `GET /api/search?q=…&owner=…`).
- **skills.sh.json (display only):** repo-root file "to control how its repository page appears… available to every public GitHub repository listed on skills.sh, with no approval or allowlist required" ([docs](https://skills.sh/docs/customize)). Fields: `groupings: [{title, description, skills: [slugs]}]`, `notGrouped: "top"|"bottom"` (default bottom → "Other skills"). Caveat: "skills.sh picks up skills.sh.json after the repository is installed with the skills CLI with telemetry enabled" — page is cached; the CLI ignores everything except `paths` ([src/skills-sh-config.ts](https://raw.githubusercontent.com/vercel-labs/skills/main/src/skills-sh-config.ts): "The CLI reads its optional `paths` field"). Live example: [vercel-labs/agent-skills/skills.sh.json](https://raw.githubusercontent.com/vercel-labs/agent-skills/main/skills.sh.json) groups React / Vercel / Design; rendered at [skills.sh/vercel-labs/agent-skills](https://skills.sh/vercel-labs/agent-skills) with per-skill install counts.
- **Badge:** `[![skills.sh](https://skills.sh/b/owner/repo)](https://skills.sh/owner/repo)` ([docs](https://skills.sh/docs)); the endpoint returns an SVG with the install count (`aria-label="Skills: 3.1M"`, verified via GET; `?style=for-the-badge` variant used in [vercel-labs/skills README](https://raw.githubusercontent.com/vercel-labs/skills/main/README.md)).
- **Vercel's own repo conventions** ([vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills)): flat `skills/<name>/` with `SKILL.md` + optional `scripts/`, `references/`, `README.md`, `AGENTS.md`, `metadata.json` (version/organization/abstract); zips committed next to skill dirs; README documents every skill with "Use when:" trigger lists; a GitHub Actions workflow ([agent-skills-discovery.yml](https://raw.githubusercontent.com/vercel-labs/agent-skills/main/.github/workflows/agent-skills-discovery.yml)) validates on PR and publishes "an immutable GitHub release with an Agent Skills discovery index and one artifact per skill" per push to main ([scripts/build-discovery-index.mjs](https://raw.githubusercontent.com/vercel-labs/agent-skills/main/scripts/build-discovery-index.mjs)).

## What to steal

Mapped to our goal: greenfield/brownfield chains installed via `npx skills add ivanDsky/skills`, usable by prime-agent/pi and friends.

1. **Keep the flat `skills/<name>/SKILL.md` layout** — it is the first-class container; catalog nesting (`skills/<category>/<name>/`) also works (3-level walk) if we later want chain-grouped folders. Avoid exotic top-level dirs for real skills (our `_template/` is currently *installable* — see surprises).
2. **Frontmatter contract per skill: `name` + `description`, both strings** — that is all the CLI requires; but follow the agentskills.io name-matches-dir convention anyway (other agents + the spec expect it; T003). Write `description` as a routing-oriented trigger ("Use when …") — it is literally the only text shown in the interactive picker, `find` results, and the skills.sh page.
3. **`skills.sh.json` at repo root with `paths` + `groupings`** — `paths` only if we keep skills outside `skills/`; `groupings` to present our repo page as "Greenfield chain / Brownfield chain / Authoring / Meta" instead of an install-count-sorted pile. Cost: ~15 lines of JSON.
4. **Badge in README** (`skills.sh/b/ivanDsky/skills`) once first installs happen — the count only moves with telemetry-on installs.
5. **README per skill with "Use when" triggers** (agent-skills pattern) and a repo README that documents the one-liner `npx skills add ivanDsky/skills` plus per-chain install examples (`--skill <name>`, `-a pi`, `-g`) — this is what makes the repo legible on skills.sh and in search.
6. **`metadata.internal: true`** for anything not meant for public consumption (templates, WIP) — officially supported way to keep `_template` invisible without moving it.
7. **Optional CI mirroring agent-skills' validate-on-PR** for frontmatter lint (ties into MAP.md's planned frontmatter lint tooling); their discovery-index release machinery is overkill for us now.

## What to skip

- **Plugin manifests (`.claude-plugin/marketplace.json`)** — only needed for Claude Code marketplace distribution; superpowers-style multi-harness plugin story is a separate MAP decision, and plain skills already install to `.claude/skills/`.
- **`experimental_sync` / `experimental_install` / npm `skills` field** — that's for npm packages shipping skills, not for a skills repo like ours.
- **Discovery-index releases + committed zips** (agent-skills) — build artifacts for Vercel-scale distribution; skills.sh serves straight from the git source.
- **`--full-depth` reliance** — design the layout so standard discovery finds everything; full-depth is a debugging escape hatch.
- **Topics/"Official" pages** — curated by Vercel, not self-serve (no doc'd application path).

## Surprises & open questions

- **Our `_template/` already leaks into the public surface**: any top-level dir with a `SKILL.md` is discovered at root depth-1, so `npx skills add ivanDsky/skills` currently offers a skill literally named `template` with the placeholder description. Fix: `metadata.internal: true`, or rename `name:` to something clearly not-for-install, or move it under a non-container path deeper than depth-1 (root walk stops at depth 1).
- **No name↔dir check in the CLI** — contradicts the common assumption (and MAP.md's "name matches dir" bar, which comes from agentskills.io/Claude, not from `skills`). We keep the stricter bar, but validation must be our own tooling (T008), the CLI won't do it.
- **Root-`SKILL.md` repos collapse to a single skill** unless `--full-depth` — never put a `SKILL.md` at our repo root.
- **skills.sh.json display updates are lazy**: they only apply "after the repository is installed with the skills CLI with telemetry enabled" and pages are cached — don't expect instant reflection after committing.
- **Open: does prime-agent read project-level `.agents/skills/` too, or only `~/.agents/skills/`?** Verified global (`~/.agents/skills/` is where this session's skills live); project-level path untested here. If project-level works, per-project skill bundles for brownfield flow become possible.
- **Open: is there a way to claim/verify ownership on skills.sh beyond telemetry?** Docs show no allowlist for repo pages, but "Official" curation and the API's auth are Vercel-side; not needed for v1.

## Checklist: What github.com/ivanDsky/skills needs so `npx skills add ivanDsky/skills` just works

- [ ] **Layout**: every installable skill at `skills/<name>/SKILL.md` (optionally `skills/<category>/<name>/SKILL.md` later); no `SKILL.md` at repo root. *(discovery: [docs/creating-skills.md](https://raw.githubusercontent.com/vercel-labs/skills/main/docs/creating-skills.md))*
- [ ] **Frontmatter**: each SKILL.md has string `name` (lowercase-hyphen, matches dir name per agentskills.io) and non-empty `description` phrased as triggers ("Use when …"). *(required by [src/skills.ts](https://raw.githubusercontent.com/vercel-labs/skills/main/src/skills.ts); shown verbatim in the picker)*
- [ ] **`_template/` neutralized**: add `metadata:
  internal: true` (or rename/move) so `template` stops appearing as an installable skill. *([docs/creating-skills.md](https://raw.githubusercontent.com/vercel-labs/skills/main/docs/creating-skills.md))*
- [ ] **skills.sh.json** at repo root: `$schema`, `groupings` (e.g. Greenfield chain / Brownfield chain / Authoring), `notGrouped: "bottom"`; `paths` only if skills live outside `skills/`. *([docs/customize](https://skills.sh/docs/customize))*
- [ ] **README**: install one-liner + badge `[![skills.sh](https://skills.sh/b/ivanDsky/skills)](https://skills.sh/ivanDsky/skills)`; per-skill "Use when" sections. *([badge docs](https://skills.sh/docs))*
- [ ] **Listing**: do at least one telemetry-on install after going public (or from any machine) so skills.sh creates the repo page; expect leaderboard ranking to accrue with installs. *([docs](https://skills.sh/docs))*
- [ ] **Agent targeting**: document `npx skills add ivanDsky/skills -a pi` (project `.agents/skills/`, global `~/.agents/skills/` with `-g`) for prime-agent/pi users; note `-a '*'`/`--all` and `--skill <name>` for scripted installs. *([docs/agents.md](https://raw.githubusercontent.com/vercel-labs/skills/main/docs/agents.md))*
- [ ] **(optional) CI frontmatter lint** — name/dir match, non-empty description — since the CLI itself won't reject mismatches.
