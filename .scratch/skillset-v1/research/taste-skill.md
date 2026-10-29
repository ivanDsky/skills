---
repo: Leonxlnx/taste-skill
ticket: T014
date: 2026-10-29
mode: adoption survey
---

# taste-skill — adoption survey

## What it is

A single-skill repo: **one Agent Skill, `design-taste-frontend`**, described as "tasteskill v2, the anti-slop frontend skill". It makes a coding agent art-direct websites, landing pages, marketing sites, portfolios, product pages and (since v2.1) app screens (dashboards, admin views, settings) instead of assembling "the average landing page" — a centred headline, eyebrow label, three icon cards, soft gradient. [README](https://raw.githubusercontent.com/Leonxlnx/taste-skill/main/README.md), [SKILL.md](https://raw.githubusercontent.com/Leonxlnx/taste-skill/main/skills/taste-skill/SKILL.md)

Verified repo facts (GitHub API, 2026-10-29): **105,510 stars** (ticket's "105k" confirmed), 7,125 forks, 7 open issues, MIT, created 2026-02-19, pushed 2026-10-29 (today), v2.1.5 released 2026-10-25. [repo API](https://api.github.com/repos/Leonxlnx/taste-skill), [CHANGELOG](https://raw.githubusercontent.com/Leonxlnx/taste-skill/main/CHANGELOG.md)

It is not a style guide. It is a **build pipeline + measurement harness**: a script deals art directions so the model cannot default to the category average, open-archive imagery is sourced and credited, and a zero-dependency Chrome driver measures the built page and fails it on slop.

Note on scope: the repo used to hold many skills (high-end-visual-design, minimalist-ui, redesign-existing-projects, imagegen skills...). As of v2.1.3 everything consolidated into this one skill; the classics moved to [Leonxlnx/taste-skill-classics](https://github.com/Leonxlnx/taste-skill-classics), imagegen skills to [Leonxlnx/imagegen-skills](https://github.com/Leonxlnx/imagegen-skills), and `full-output-enforcement` was removed (pointer to Leonxlnx/unlazy). [README "Moved skills"](https://raw.githubusercontent.com/Leonxlnx/taste-skill/main/README.md)

## How it works

The SKILL.md (39.5 KB) prescribes a 10-step run. [SKILL.md](https://raw.githubusercontent.com/Leonxlnx/taste-skill/main/skills/taste-skill/SKILL.md)

1. **Brief + inventory** — list 8–12 things only this client has (street, materials, rituals, numbers); the idea must come from this list, not the category.
2. **Argument** — page as claims-with-proof, one line per section; sections without a claim are deleted.
3. **Draw the direction** — `node scripts/draw.mjs --sector <s> --brief "..." --sections <roles> --options 3` deals 3 of 20 researched directions (`name-as-monument`, `colour-chapters`, `specimen-catalogue`, `dark-room`, `type-only-statement`, ...); the agent picks one and the script deals the full sheet: type system, palette proportions, hero + section blueprints, imagery rules, motion, scroll scenes. Redraws are allowed only for stated reasons and must be reported. [draw.mjs](https://raw.githubusercontent.com/Leonxlnx/taste-skill/main/skills/taste-skill/scripts/draw.mjs), [directions.json](https://raw.githubusercontent.com/Leonxlnx/taste-skill/main/skills/taste-skill/library/directions.json)
4. **Find the idea** — fill "On this page, [subject's own thing] becomes [the direction's device]"; plus one "live thing" the visitor can do.
5. **Copy deck before markup** — headlines ≤ 2 lines at every width (~32 chars), full content in every section, proof never invented.
6. **Build** — tokens → hero → sections from blueprints → imagery (own > generated > open-archive found & credited > drawn in code > generic) → live thing → scroll scenes → fullness → frame → states/a11y. A hard "imagery floor": ≥4 real pictures, usually 6–12; SVG drawings don't count. `scripts/assets.mjs` searches Openverse, Wikimedia Commons, Art Institute of Chicago, the Met with no API keys, commercial-safe licences only (CC0/PD/CC BY/CC BY-SA), downloads and records credits. [assets.mjs](https://raw.githubusercontent.com/Leonxlnx/taste-skill/main/skills/taste-skill/scripts/assets.mjs), example credits in [examples/v2/CREDITS.md](https://raw.githubusercontent.com/Leonxlnx/taste-skill/main/examples/v2/CREDITS.md)
7. **Gate (the browser check)** — `lint.mjs` greps source for banned patterns/stock phrases; **`inspect.mjs`** opens the page in a real Chrome at 1440/768/390, measures (headline line counts, font sizes, fonts actually loaded, colours, shadows, gradients, contrast, overflow, equal margins, blank stretches, title, untitled sections) and screenshots to `.taste-skill/inspect/`; exit 1 on any FAIL. `scenes.mjs` films scroll scenes at 0–100% of their hold, desktop + phone + reduced motion. [inspect.mjs](https://raw.githubusercontent.com/Leonxlnx/taste-skill/main/skills/taste-skill/scripts/inspect.mjs)
8. **Look** — critique the screenshots (never the code) with `references/critique.md`: fourteen passes, an Awwwards-weighted score (design 40 / usability 30 / creativity 20 / content 10), fix top 3, re-inspect, max 3 rounds. [critique.md](https://raw.githubusercontent.com/Leonxlnx/taste-skill/main/skills/taste-skill/references/critique.md)
9. **Move** — a required motion layer (entrance staggers 60–90 ms, feedback on every control, one signature move, one moving picture); inspector fails under 8 moving elements; everything with `prefers-reduced-motion` fallbacks. [SKILL.md step 9](https://raw.githubusercontent.com/Leonxlnx/taste-skill/main/skills/taste-skill/SKILL.md)
10. **Report** — direction dealt, redraws, idea, scores, every image credit, sample content flagged. "Do not claim a check you did not run."

House style: a large table of measured bans (no eyebrows, no gradients, no shadows at rest, no glass/backdrop blur, no monospace outside code, no icon-card rows, no violet/indigo "assistant palette"), each justified with study numbers (icon cards on 1% of top sites vs 28% of weak ones; gradients 22% vs 52%) and an honest note that some bans contradict gallery fashion. [SKILL.md "House rules"](https://raw.githubusercontent.com/Leonxlnx/taste-skill/main/skills/taste-skill/SKILL.md)

**The browser check at runtime** — `scripts/lib/cdp.mjs` is a zero-dependency Chrome DevTools Protocol client over Node's built-in WebSocket (**Node 22+ required**; it throws otherwise). It finds an installed Chrome/Edge/Chromium/Brave via well-known paths or `CHROME_PATH`/`PUPPETEER_EXECUTABLE_PATH`, launches `--headless=new` with a throwaway `ad-chrome-*` temp profile carrying an owner file (machine + pids) so abandoned profiles get swept safely (a 2.1.4 regression fix with its own test), and kills Chrome + deletes the profile on exit. `inspect.mjs` serves local files over a throwaway local HTTP server and warns if it detects a dev server (tells you to gate the production build). No npm install, no API keys, network only for image search. [cdp.mjs](https://raw.githubusercontent.com/Leonxlnx/taste-skill/main/skills/taste-skill/scripts/lib/cdp.mjs)

**Does it evaluate its own skills?** Yes, two layers:
- `tests/` is repo hygiene in CI ([check-skills.yml](https://raw.githubusercontent.com/Leonxlnx/taste-skill/main/.github/workflows/check-skills.yml)): frontmatter parses as Claude Code and Codex parse it (strict YAML, kebab name, ≤1024-char description), clean UTF-8, all scripts `node --check`, browser-profile-cleanup + screenshot-naming unit tests (node:test). **CI does not run design evals.**
- `evals/evals.json` is a **manual blind A/B protocol**: 10 eval prompts (6 pages incl. SaaS/restaurant/portfolio, 4 app screens per the `--app` rules); run each on a fresh agent with the skill and one without, render both with `inspect.mjs`, have a blind judge score screenshots with critique.md, record FAIL counts for both. [evals.json](https://raw.githubusercontent.com/Leonxlnx/taste-skill/main/skills/taste-skill/evals/evals.json)
- The library itself is backed by a disclosed methodology: 247 sites (One Page Love + Awwwards SOTD), headless-Chrome captures, **21 model reviewers** scoring Awwwards-style — honestly labelled as model judgments from still frames, not human jurors; plus an October 2026 study of 100 fresh Sites of the Day and an app-screen study. [research.md](https://raw.githubusercontent.com/Leonxlnx/taste-skill/main/skills/taste-skill/references/research.md)

## Install & footprint

Exact commands ([README Install](https://raw.githubusercontent.com/Leonxlnx/taste-skill/main/README.md)):

```bash
# npx skills (the CLI we already standardised on, T004):
npx skills add https://github.com/Leonxlnx/taste-skill --skill "design-taste-frontend"

# or Claude Code plugin (namespaced taste-skill:, no collision):
/plugin marketplace add Leonxlnx/taste-skill
/plugin install taste-skill@taste-skill

# or from a clone, symlinked so git pull updates in place:
./install.sh            # ~/.claude/skills   (default)
./install.sh --codex    # ~/.codex/skills
./install.sh --all-agents
```

`install.sh` reads the install name from SKILL.md frontmatter and symlinks `skills/taste-skill/` → `~/.claude/skills/design-taste-frontend` (refuses to touch real files or foreign symlinks; `--uninstall` removes only links owned by this repo). [install.sh](https://raw.githubusercontent.com/Leonxlnx/taste-skill/main/install.sh) Under `npx skills` the same skill folder is copied into the agent skills dir under the install name `design-taste-frontend` (vercel-labs/skills mechanics per T004).

What lands on disk — the skill subtree is **~2.4 MB** ([git tree sizes](https://api.github.com/repos/Leonxlnx/taste-skill/git/trees/main?recursive=1)):

| Part | Size | Note |
| --- | --- | --- |
| `SKILL.md` | 39.5 KB (~10k tokens) | loaded into context on invocation |
| `library/*.json` | 1.68 MB | 20 directions, sections, type, palettes, photos, sites.json 869 KB — read via script, never whole |
| `scripts/` | 315 KB | draw/inspect/assets/lint/scenes + cdp/probe/rules libs |
| `references/*.md` | 288 KB | progressive disclosure: app-screens 85 KB, motion 55 KB, imagery 51 KB... |
| `assets/` | 92 KB | optional base.css/base.js, scenes, app.css, charts.js |

Per-session context cost: ~1 KB description always in routing; ~10k tokens for SKILL.md when the skill fires; big references read on demand only (app-screens.md alone is ~21k tokens — the dashboard route is expensive). Working files land in the **target project's** `.taste-skill/` (direction sheet, inspect screenshots, downloads). Build cost per page: "roughly 30 to 45 minutes and a few hundred thousand tokens" ([README How v2 works](https://raw.githubusercontent.com/Leonxlnx/taste-skill/main/README.md)). Runtime needs: Node 22+, an installed Chrome/Edge/Chromium/Brave, network for image search only.

## Overlap with installed design skills

Compared against `~/.agents/skills/` (read locally, 2026-10-29):

| Installed skill | What it actually does | Relation to taste-skill |
| --- | --- | --- |
| `emil-design-eng` (27 KB) | Emil Kowalski philosophy: component polish, interaction/animation judgment for product UI | **Complementary, mild motion overlap.** Emil = how interactions feel; taste-skill = what a page/screen looks like + measured gate. Both prescribe motion values (stagger, reduced-motion) — duplicate guidance possible in step 9, and both descriptions claim "design/UI" broadly, so routing can double-fire. |
| `apple-design` (22 KB) | Fluid interfaces, springs, gestures, **translucent materials/depth** | **Partial conflict.** taste-skill's house rules ban glass/backdrop-blur panels, gradients, floating pill nav on pages; apple-design teaches those materials. Fine when only one fires; contradictory when both fire on the same page. |
| `animation-vocabulary` (13 KB) | naming glossary | None. |
| `find-animation-opportunities` (9 KB) | read-only motion proposals on existing UI | Complementary: taste-skill covers greenfield page builds; this covers existing codebases. taste-skill's redesign mode (inspect before/after) covers some of the same ground for pages. |
| `improve-animations` (8 KB) | read-only motion audit + plans | Same as above. |
| `prototype` (3 KB) | throwaway prototypes | None. |

No installed skill does art direction, imagery sourcing, copy discipline, or browser-measured page checks — that gap is exactly what this fills.

## Adoption verdict

Per skill — the repo ships exactly one:

- **`design-taste-frontend` — install-as-is.** Best-in-class, actively maintained (v2.1.5 four days ago), zero-dependency runtime we already meet (Node 22, Chrome), MIT, fills a real gap (art-directed marketing/landing/portfolio pages + app screens with a measurable gate), installs under the same `npx skills` flow we standardised on.

Component-level notes (if we ever want to go beyond install-as-is):

- **`scripts/inspect.mjs` + `lib/{cdp,probe,rules}.mjs` as a standalone "browser design check" — integrate-adapt candidate, second step.** The zero-dep CDP driver + FAIL/WARN judge is a reusable completion gate we could point at our own pages or embed in a future own skill; but while it's maintained upstream, install-as-is gets us the same tool for free.
- **`references/critique.md` (14-pass rubric) and the copy.md two-line arithmetic — integrate-adapt later.** Small, framework-agnostic judgment aids that could be quoted into our own skills with MIT attribution; not a reason to hold off the install.
- **taste-skill-classics / imagegen-skills (moved skills) — skip for now.** Older v1 aesthetics and imagegen variants; revisit only if v2 proves insufficient.

Caveats to accept with the install: a full run is heavyweight (30–45 min, hundreds of thousands of tokens per page — use for real builds, not tweaks); the opinionated bans (no gradients/glass/monospace) will sometimes fight the user's or Apple-flavored preferences (mitigation: `--allow <rule>` escape hatch and `--keep palette,type` for existing brands); CI verifies hygiene, not design quality — the evals are a manual protocol.

## License & attribution

- **MIT**, "Copyright (c) 2026 Leonxlnx". [LICENSE](https://raw.githubusercontent.com/Leonxlnx/taste-skill/main/LICENSE), confirmed by [repo API](https://api.github.com/repos/Leonxlnx/taste-skill). Vendoring/adaptation explicitly allowed with the license notice kept.
- The repo models good attribution itself: found images are CC0/PD/CC BY/CC BY-SA only, credits auto-recorded and printed (`assets.mjs --credits`), example pages ship a full CREDITS.md. If we vendor any file, keep the MIT notice; if we quote study numbers, cite research.md.
- Sponsorware-free, no API keys, no accounts. README explicitly disclaims any crypto token using the project's name.

## Surprises & open questions

1. **The star count is real.** 105,510 stars on a 8-month-old repo with 7 open issues — unusual maintenance hygiene for that scale; every changelog entry links issues/PRs and names contributors.
2. **Only one skill remains.** Anyone adopting "the 105k-star taste repo" expecting a suite gets a single skill; the old ones (including `high-end-visual-design`) moved to a separate classics repo. Install name must be `design-taste-frontend`.
3. **The anti-Apple stance is explicit.** Glass, gradients, shadows-at-rest and the violet "assistant palette" are banned on pages — worth a note in our skillset docs so users running apple-design alongside know which skill wins where (taste-skill governs public-facing pages; apple-design governs interaction/motion physics).
4. **Study numbers are model judgments.** research.md is refreshingly honest: 21 *model* reviewers, still frames, one capture per site — not human jurors. Fine as design priors; not hard science.
5. **Open: context budget interplay.** app-screens.md (~21k tokens) + SKILL.md (~10k) + motion.md (~14k) on a dashboard task is heavy; unknown whether we want a policy ("prefer taste-skill for pages, emil-design-eng for component-level polish") — worth raising at the disposition step.
6. **Open: does `npx skills add` handle the 1.7 MB library folder fine?** It's plain file copying per T004, so presumably yes; not separately verified here.
