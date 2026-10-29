# Adoption survey: pbakaus/impeccable (T015)

Surveyed 2026-10-29 from primary sources: repo README, git tree (5,059 entries), `skill/SKILL.src.md`, `reference/routing.md`, `reference/craft-floor.md`, `reference/bolder.md`, `reference/hooks.md`, `NOTICE.md`, `LICENSE`, `package.json`, `README.npm.md`, `.claude/settings.json`, repo metadata. Repo: 95,254 stars, Apache-2.0, created 2025-11-16, v4.8.0, pushed 2026-10-29 (https://api.github.com/repos/pbakaus/impeccable, https://github.com/pbakaus/impeccable).

## What it is

A single Agent Skill (`impeccable`) that gives a coding agent a **design vocabulary**: 24 named sub-commands invoked as `/impeccable <command> [target]`, plus a deterministic slop detector and live browser iteration. Tagline: steer with `polish`/`bolder`, review with `critique`/`audit`, catch AI slop before it ships (https://raw.githubusercontent.com/pbakaus/impeccable/main/README.md).

One skill, four artifact families (tree: https://api.github.com/repos/pbakaus/impeccable/git/trees/main?recursive=1):

1. **The skill itself** — `skill/` (canonical; 65 files, ~2.18 MB) with one `SKILL.md` router and per-command playbooks in `reference/`. Mirrored into ~20 per-harness adapter dirs committed at repo root (`.claude/`, `.agents/`, `.cursor/`, `.agent/`, `.devin/`, `.gemini/`, `.github/`, `.grok/`, `.hermes/`, `.opencode/`, `.kiro/`, `.pi/`, `.qoder/`, `.rovodev/`, `.trae/`, `.trae-cn/`, `.vibe/`, `.dsh/`, `.omp/`, `.veto/`), each ~65 entries — same skill, packaged per tool.
2. **A Rust detector engine** — `crates/` (564 files) compiled to self-contained per-platform binaries shipped as optional npm deps `@impeccable/cli-<os>-<arch>` v0.1.18 (https://raw.githubusercontent.com/pbakaus/impeccable/main/package.json). 62 deterministic rules, no LLM, no API key: AI-slop tells (gradient text, purple gradients, nested cards, side-stripe borders, eyebrow labels), WCAG contrast, typography, motion, spacing (https://raw.githubusercontent.com/pbakaus/impeccable/main/README.npm.md).
3. **A CLI/installer** — `cli/` published to npm as `impeccable`; a thin launcher that installs the skill into detected harnesses and runs `detect` against files, dirs, or live URLs (exit 2 = findings), with `--json` and `--github` CI modes (README.md; README.npm.md).
4. **Extras** — Chrome extension (overlay findings on any page), VS Code/Copilot extension, Claude Code plugin marketplace (`.claude-plugin/marketplace.json`), and `live` mode: an overlay on your dev server (Vite/Next/SvelteKit/Astro/Nuxt/plain HTML) where you pick an element and hot-swap variants written back to source (README.md).

The 24 commands group as: **Steer** (`bolder quieter distill colorize typeset layout animate delight overdrive`), **Review** (`critique` scored UX review, `audit` technical P0–P3 report), **Finish** (`polish harden clarify adapt optimize onboard`), **Iterate** (`live generate`), **Plan/setup** (`shape init document extract`) (README.md commands table).

## How it works

- **Context files, not memory.** `/impeccable init` interviews only what it can't infer and writes `PRODUCT.md`; `/impeccable document` distills the existing visual system into `DESIGN.md`. Every later command reads them (README.md, https://impeccable.style/docs).
- **Per session, the skill runs `scripts/impeccable context`** once: the engine binary reads PRODUCT.md, DESIGN.md, matching surface brief, and native-platform guidance, then emits directives the model follows (SKILL.md Setup step 1, https://raw.githubusercontent.com/pbakaus/impeccable/main/skill/SKILL.src.md).
- **Progressive disclosure is explicit.** SKILL.md is a ~12 KB router (modes Persuade/Operate/Read/Experience, command table, routing rules). Each invocation loads exactly one playbook from `reference/` (3.5–64 KB), and `craft-floor.md` (7.2 KB) is required reading immediately before *any* UI edit: the quality floor, the absolute bans (gradient text, eyebrow/kickers, numbered sections, glassmorphism-by-default, glyph icons…), and a `<codex>` block of Codex-specific failure patterns (craft-floor.md).
- **No-argument invocation** reads `routing.md`, runs `impeccable signals`, and presents a context-aware menu (2–3 recommended next commands with reasons, optionally seeded by a `detect` run over dirty files) — never auto-runs (https://raw.githubusercontent.com/pbakaus/impeccable/main/skill/reference/routing.md).
- **The design hook is two-tier and mechanical.** `PostToolUse` (Edit/Write on UI files) runs the engine and pushes a short system reminder with immediate-tier findings (broken images, overflow, contrast, gradient text, glow shadows, design-system drift); the `Stop` hook runs the full 62-rule deep pass over every UI file touched in the session, deduplicated against per-edit findings. Wired natively for Claude Code, Codex, Cursor, GitHub Copilot, Grok Build, Hermes (hooks.md, https://raw.githubusercontent.com/pbakaus/impeccable/main/skill/reference/hooks.md; `.claude/settings.json` shows the three hook entries with 5s/30s timeouts).
- **Modes guard scope.** Steer commands are refinement-only: `bolder` "amplifies what the system already owns… touch only the named target", preserves existing copy, and ends with a skeleton test (bolder.md). Redesign vs refinement is an explicit gate (`new-work.md` decides preserve/expand/replace).
- **Native mobile**: `reference/ios.md` and `android.md` cover iOS/Android surfaces; `live`/`generate`/`detect` are web-only and routing skips them on native platforms (routing.md).

## Install & footprint

Exact commands (README.md; README.npm.md):

```bash
npx impeccable install                    # detects tools, asks project|global, offers the hook
npx impeccable install -y --providers=claude,codex --scope=project   # scripted
npx impeccable update                     # refresh existing install
npx impeccable install --no-hooks         # skills only
# Claude Code plugin alternative:
/plugin marketplace add pbakaus/impeccable
# detector without any agent:
npx impeccable detect src/ ; npx impeccable detect --json . ; npx impeccable detect --list-rules
```

What lands where: the skill folder is copied into the harness's skills dir (project: `.claude/skills/impeccable/`, `.agents/skills/impeccable/`, etc.; global: `~/.claude/skills/`, `~/.agents/skills/`, `~/.qoder/skills/`, …) plus hook manifests in each tool's settings and Claude Code subagents (`.claude/agents/` README.md manual-copy table). The engine binary ships beside the skill or downloads once into `~/.impeccable/bin/`; Node is only needed for `npx` (README.md). Working files live in `.impeccable/` — shared artifacts (`config.json`, `design.json`, `surfaces/*.md`, `critique/*.md`) belong in the repo; screenshots/caches/session state are gitignored (README.md gitignore block). Manual copy is supported with no Node at all: clone, copy one `skills/impeccable` folder (README.md).

Footprint numbers (tree blob sizes):

- Skill folder on disk: ~2.18 MB, of which `data/font-index.json` 1.10 MB and `live-browser.js` 563 KB are machinery, not prose; the text content (SKILL.md + 30-odd references) is roughly 500 KB.
- Always in context: only the frontmatter description (~110 words ≈ 150 tokens) in skills-enabled harnesses.
- On invocation: SKILL.md 12,009 bytes ≈ 3,000 tokens; `craft-floor.md` 7,158 bytes ≈ 1,800 tokens before UI edits; playbooks 3.5 KB (`bolder`) to 64 KB (`new-work`, the big one ≈ 16k tokens) on demand; `impeccable context` emits bounded directives.
- Hook cost: short system reminders per UI edit (immediate tier) + one dedup'd Stop-time report; silent when clean (hooks.md).

## Adoption verdict

It's one skill, so verdicts are per artifact. Existing design skills in `~/.agents/skills/` for the overlap check: apple-design, emil-design-eng, animation-vocabulary, find-animation-opportunities, improve-animations, review-animations, pick-ui-library.

| Artifact | Verdict | Why |
|---|---|---|
| Core skill (24 commands, modes, craft floor) | **install-as-is** | Nothing in our set does steer/review/critique as an executable loop; apple-design and emil-design-eng are knowledge, this is workflow + engine — complementary, not duplicate. |
| Detector + design hook | **install-as-is** | 62 deterministic rules, no LLM tokens, CI-able; nothing comparable exists in our skillset. |
| `craft-floor.md` alone | **integrate-adapt** | Standalone slop ban-list; worth mining into our own design skills even if the workflow is rejected. |
| ios.md / android.md platform refs | **integrate-adapt** | Useful, but overlaps apple-design's turf; keep only if apple-design doesn't already cover the same HIG ground. |
| `live` / `generate` browser mode | **skip** | Needs a running dev server + browser tooling; heavy, niche, and the 563 KB `live-browser.js` is most of the skill folder's weight. |
| Whole-repo vendoring (20 adapter dirs) | **skip** | 5,059 paths incl. Rust sources and 2,716 test files; vendor only `skill/impeccable` (or let its own installer manage it). |

Two adoption paths, pick one: **(a)** run `npx impeccable install` and keep it as a self-updating external tool (`npx impeccable update`) — simplest, respects its own versioning (4 releases to 4.8.0 in under a year); **(b)** vendor `skill/impeccable` into our repo for `npx skills add` distribution — works (Apache-2.0), but we take on sync duty against a fast-moving upstream. Recommendation: (a) now, revisit vendoring only if we want it in the distributed skillset.

## License & attribution

- Apache-2.0 (`LICENSE`, 10,766 bytes; confirmed via repo API `license.spdx_id = apache-2.0`). Vendoring and redistribution permitted; retain the LICENSE file.
- `NOTICE.md` (503 bytes) declares derived content: `reference/ios.md` and `android.md` are distilled from ehmo/platform-design-skills (MIT) — that attribution must be preserved when vendoring (https://raw.githubusercontent.com/pbakaus/impeccable/main/NOTICE.md).
- SKILL.md frontmatter carries `license: Apache 2.0`.

## Surprises & open questions

- **Star count is real**: 95,254 (API metadata), matching the ticket's 95k claim.
- **Scale mismatch**: the repo is a product (Rust engine, 2,716 test files, extensions, CI), not a skill collection — "adopt the repo" really means "adopt one skill folder + optionally a hook".
- `skills-lock.json` at repo root is `{ "skills": {} }` — vestigial (https://raw.githubusercontent.com/pbakaus/impeccable/main/skills-lock.json).
- `CLAUDE.md` (59.5 KB) and `AGENTS.md` (17.7 KB) are repo-dev instructions, an order of magnitude larger than the shipped SKILL.md — don't confuse them with the artifact.
- The skill assumes a *project* with rendered UI to verify against ("verify by looking at the rendered result"); fits web/frontend work, less so library/backend tasks.
- Open: does `npx skills add ivanDsky/skills` conflict with impeccable's own `install/update` manager if we vendor (double bookkeeping of the same folder)?
- Open: hook consent UX — Claude Code requires approving project hooks; does the user want per-edit context interruptions during normal coding sessions?
- Open: `new-work.md` is 64 KB ≈ 16k tokens when loaded; acceptable on demand, but worth noting against any per-session context budget we set.
