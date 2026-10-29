# Reference map — what every analyzed repo brings

Orientation doc for designing **ivanDsky/skills**: one paragraph per source (why it's popular, its novelty, why it's organized that way, what we take), then the state-of-the-art synthesis (agent management, human↔agent communication, waiting-vs-delivering). Full notes with citations live in [`research/`](research/); adoption decisions are indexed on the [map](MAP.md).

## The repos at a glance

| Source | Essence | Novelty (why popular) | We take |
|---|---|---|---|
| **obra/superpowers** (308k★) | A complete auto-triggered SD methodology as 15 skills + 1 bootstrap | The process owns you: brainstorm→spec→plan→subagent-execution→review runs for hours without drift | Artifact spine w/ backlinks, bootstrap+router pattern, dual-verdict review, fix-round caps |
| **mattpocock/skills** (260k★) | ~20 small, composable, mostly user-invoked skills | Anti-framework stance: "GSD/BMAD/Spec-Kit own your process; these adapt to you" | `docs/agents/*.md` config contract, tracer-bullet tickets, expand–contract, two-axis review, scope/glossary hygiene |
| **anthropics/skills + agentskills.io** | The open standard itself | One file format every major agent can load | 13-rule linter checklist, progressive disclosure, size budgets |
| **vercel-labs/skills + skills.sh** | The de-facto package manager + leaderboard | `npx skills add <repo>` — skills became installable | Flat `skills/<name>/` layout, frontmatter contract, discovery rules, badge/listing |
| **affaan-m/ECC** (292k★) | "Harness performance optimization system" — 313 skills, 71 agents, instincts, memory | Maximality + a learning loop: instincts (confidence-scored lessons) auto-injected in a budget | Instinct YAML microformat, memory trust vocabulary, injection budgets — as patterns, never install |
| **Shubhamsaboo/awesome-llm-apps** (143k★) | Gallery of 100+ agent apps; `agent_skills/` is the gold corner | Breadth; but the skill corner ships evals + lint per skill | `skill_lint.py` (near-verbatim), trigger-cases.json eval pattern |
| **ciembor/agent-rules-books** (3.1k★) | 14 classic software books distilled into 3-size rule sets + a workbench | Books as swappable "decision pressure" payloads, byte-metered (full/mini/nano) | The sizing discipline, 5-part rule template, pattern: skill = procedure + rule payload |
| **addyosmani/agent-skills** (111k★) | 25-skill SDLC pack, "production-grade" | Every skill ships evals: 3-tier framework (lint → routing → behavioral) | The eval ladder + "fix routing by editing the description, not the eval" |
| **DietrichGebert/ponytail** (180k★) | One prompt: "laziest senior dev" — smallest change that fully solves | Radical minimalism + honest endings ("here's what I skipped, here's the risk") | The mode prompt (adapted as ours), skip/risk reporting convention; skip the always-on hooks |
| **Leonxlnx/taste-skill** (105k★) | One skill: art-direct pages instead of "average AI landing page" | Names the pain (generic AI slop) and fixes it with direction + a measurable browser gate | `design-taste-frontend` install-as-is; the reference-image → browser-check loop |
| **pbakaus/impeccable** (95k★) | Design vocabulary: 24 commands + 62-rule Rust slop detector | Vocabulary-as-interface (polish/bolder/critique/audit) + deterministic detector | Install-as-is external tool; vocabulary-driven steering as a UX idea |
| **tt-a1i/archify** (91k★) | Idea/plan/codebase → validated interactive HTML diagram | Typed JSON IR: agent authors, CLI renders+validates — diagrams you can trust | Install-as-is; brownfield orientation + spec viz; disable update-check |

---

## Why each repo is organized the way it is

- **superpowers** — one shared `skills/` tree, many thin per-harness plugin dirs. The methodology is harness-independent; only *injection* (the SessionStart hook) is harness-specific. Organization serves auto-trigger.
- **mattpocock** — `skills/engineering|productivity/<name>` with category READMEs, plus repo-level `SCOPE.md` (contribution bar: observed failure only), `GLOSSARY.md` (canonical vocabulary with avoid-lists), `.out-of-scope/` (one file per rejected idea). Organization serves curation and a public audience.
- **anthropics** — `template/` + `spec/` pointer + example skills. Organization serves the standard, not a workflow.
- **addyosmani** — `skills/` + `commands/` + `evals/` + `hooks/` + 11 host adapters. Organization serves testability; the adapters are the biggest maintenance chunk (their own docs admit it) — the cautionary tale for multi-host ambitions.
- **ECC** — 6,440 files: subagents, skills, commands, rules, hooks, memory. Organization serves a *platform with a paid tier*; KDnuggets: "overkill if you only need a better debugging prompt."
- **rules-books** — one dir per book × three sizes + `_rule-workbench/` that compresses with traceability (rules cite source line ranges) and a self-criticism doc. Organization serves trust in derived content.
- **ponytail** — one skill + a generator spraying ~20 host formats. Organization proves the "one prompt, many loaders" thesis; everything except `skills/ponytail/SKILL.md` is packaging.
- **taste-skill / archify / impeccable** — single-skill repos (archify ships its CLI inside the skill dir; impeccable hides a Rust binary behind one router SKILL.md). Organization serves install-and-go via `npx skills`.

## State of the art: managing agents

The pattern stack, from most to least adopted:

1. **Externalized state over chat memory.** Every serious repo treats the *repo* as the agent's memory: specs, plans, per-task workspaces with ledgers, decisions on trackers (superpowers' artifact spine, Matt's tracker-based chain, our wayfinder map). Chat is ephemeral; artifacts are load-bearing. Superpowers goes furthest: per-plan git-ignored workspaces whose "Ruling:" and "deferred-minors" conventions survive compaction.
2. **Chains of small skills with artifact handoffs.** The unit of composition is skill → artifact → skill (grilling → spec → tickets → implement → review). Two philosophies coexist: *auto-triggered* (superpowers: one bootstrap skill + SessionStart hook makes the methodology fire itself) vs *user-invoked* (Matt: you summon each stage; the skill set stays out of the way). This is exactly our T005 decision.
3. **Config-as-files, not config-as-prompts.** Per-repo behavior lives in `docs/agents/*.md` (tracker location, labels, domain docs) that skills read at runtime (Matt's setup skill writes them; consumers read them). This is what makes one skillset work across many projects — our "configure to use" requirement.
4. **Subagent-driven execution with adversarial review.** Superpowers: fresh implementer + dual-verdict reviewer per task (spec-compliance ✅/❌/⚠️ + quality), scoped re-reviews, fix-round caps, a model ladder (cheap workers, stronger reviewers), workers forbidden to spawn their own reviewers.
5. **Learning loops with trust levels.** ECC's instincts: atomic YAML lessons (trigger/confidence/evidence), injected only above a confidence threshold inside a hard byte budget; promote to global only after seen in 2+ projects. Memory is create-only; "memory is context, not instruction"; humans promote. Nothing else in the ecosystem does measured lesson-persistence this carefully.
6. **Evals as the quality gate.** Three tiers now exist in the wild: structural lint in CI (frontmatter, name==dir, size caps — free), routing evals (per-skill case files: ≥3 positive + ≥2 near-miss negatives, TF-IDF rank check with a rank-1 ratchet — still free), behavioral evals (headless agent runs against fixture repos, evidence-mandatory grading — expensive, opt-in). Addyosmani's key lesson: **routing failures get fixed by editing the description, not the eval** (one clause took fires 7/27 → 21/27).
7. **Injection budgets.** ECC hard-caps always-on injection (≤6 instincts, 8000-char budget); ponytail measures the delta (full plugin ≈760 tok/session vs ≈400 via skills-CLI). Always-on is a cost you pay every turn; the SOTA treats context as a budget line, not a dumping ground.

## State of the art: human ↔ agent communication

- **Grilling before building.** The highest-leverage pattern in the ecosystem (Matt's most popular skills): the agent asks detailed questions one at a time *before* writing anything — breadth phase (fan out across the whole problem) then depth phase (commit to decisions). Answer-in-a-word defaults keep the human fast.
- **Specs in digestible chunks with sign-off gates.** Superpowers shows the spec in sections short enough to actually read; nothing gets built before explicit approval. Front-loading human attention is what buys later autonomy.
- **Vocabulary discipline.** GLOSSARY.md with canonical terms *and avoid-lists* (Matt); "refer by name, never bare ids" (wayfinder); ubiquitous language so human, agent, and code use one vocabulary (DDD, via domain-modeling).
- **Honest endings.** Ponytail's convention — every reply ends with "what was skipped, what risk remains" — is the cheapest trust mechanism found anywhere in the research.
- **Status contracts.** Superpowers caps worker status reports at ≤15 lines; our own harness does the same with progress notes. Bounded status = readable oversight.
- **READMEs organized by failure mode.** Matt's README names the pain ("agent didn't do what I want", "agent is way too verbose") then the fix. Humans route by problem, not feature list; taste-skill does the same ("generic AI pages").

## The core trade-off: waiting for the agent vs delivering

Think of it as a ladder of **verification buy-in** — each rung costs latency now to save rework later:

| Rung | Cost | Catches | Used by |
|---|---|---|---|
| Nothing — ship on vibes | 0 | nothing | the failure mode everyone's README opens with |
| Structural lint (frontmatter, sizes, links) | seconds in CI | broken skills that silently never load | addyosmani T1, awesome-llm-apps lint |
| Routing evals (does the right skill fire?) | minutes in CI | mis-routed work — the "agent didn't do what I want" class | addyosmani T2 |
| Behavioral evals (does it *behave* right?) | headless runs, expensive | wrong behavior despite right routing | addyosmani T3 |
| Human gates (grill → approve spec → review) | minutes of your attention | misalignment itself — wrong goals, not wrong code | superpowers, Matt's chain |

The empirical claim from superpowers: **minutes of upfront grilling buy hours of autonomous execution** ("not uncommon for your agent to work autonomously for a couple of hours without deviating"). Alignment is the cheapest latency investment there is; rework is the most expensive. Matt's counterweight: gates *per skill invocation* would strangle small tasks — hence his chain is user-invoked and lightweight, gates only where artifacts are durable (spec, tickets).

Practical synthesis for us:

- **Spend human attention where artifacts persist** (destination, spec, ticket set, review of the change) and let agents run ungated where output is cheap to redo (research fan-out, prototypes, drafts).
- **Parallelize the waiting.** Research tickets run as concurrent subagents while the human lives their life (this map session proved it: 11 findings produced while the user did other things). Blocking edges + claim/frontier let independent work start without coordination.
- **Defer precision deliberately (fog of war).** Don't pre-slice decisions that hang on open questions; ticket only what's sharp. Waiting to specify is often cheaper than specifying early and rewriting.
- **Let cheap verification run constantly, expensive verification run opt-in.** Lint + routing evals belong in CI on every commit; behavioral evals and human review attach to the chain gates.
- **Always-on context is a rent, artifacts are a purchase.** Every always-on token is paid every turn (ECC budgets instincts; ponytail counts sessions); reference files are paid once when reached (progressive disclosure).

## Queued for the next session

Your inputs (what matters to you in skills, how skills should drive projects, your ideal workflow) + two unblocked HITL tickets: **Position the flow** (T005 — auto-triggered vs user-invoked, greenfield/brownfield entry points) and **Set authoring standards** (T008 — naming, HITL/AFK marking, linter, evals). The research side of this map is complete; nothing left to read before deciding.
