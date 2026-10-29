# awesome-llm-apps / agent_skills (Shubhamsaboo) — research notes

Repo: <https://github.com/Shubhamsaboo/awesome-llm-apps> — 143,439 stars; scope here is ONLY `agent_skills/` (126 files) (GitHub API, 2026-10-29).
Article framing: KDnuggets, "5 Best GitHub Repositories for AI Agent Skills" (Abid Ali Awan, 2026-10-21) — <https://www.kdnuggets.com/5-best-github-repositories-for-ai-agent-skills>

## What it is

The repo is a gallery of "100+ AI Agents, Agent Skills and RAG Apps - Free and Open Source" (GitHub API description) — 100+ standalone apps that are a different artifact class and out of scope. `agent_skills/` is the exception: 8 hand-made, agentskills.io-spec skills (SKILL.md + references/ + scripts/) plus a per-skill eval suite and a machine-readable registry, installed with the same `npx skills` CLI we chose: `npx skills add https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/agent_skills/<skill>` (https://raw.githubusercontent.com/Shubhamsaboo/awesome-llm-apps/main/agent_skills/README.md). KDnuggets frames the repo's value as breadth, not the skills: "Instead of focusing only on skills, it contains 100+ open-source AI agents, agent skills, and RAG applications … You can see how agents, tools, retrieval, multiple models, and skills are actually combined into working applications."

## How it works

### Catalog (`agent_skills/README.md`, `agent_skills/registry.json`)

8 skills: advisor-orchestrator-worker, commit-archaeologist, dependency-doctor, first-reader, project-graveyard, scope-creep-detector, thinking-out-loud (all real skills), and self-improving-agent-skills (actually a FastAPI + Next.js web app, not a portable skill). Each registry entry carries `name, path, description, license: Apache-2.0, metadata{author,version,source}, install, evals_dir`. The README states the authoring bar verbatim:

> Most "skills" on registries are text-only prompt dumps: advice the model already knows, wrapped in frontmatter. Skills here have to earn their place: **Real scripts.** … **Researched references.** … **Evidence over vibes.** … **Local and private by default.** No network calls unless declared. … **Tested before shipped.**

And the safety stance: "Read the `SKILL.md` and every script before installing, from us or anyone. … Nothing asks your agent to `curl | bash` anything, ever." Network use is declared in the `compatibility:` frontmatter field (advisor-orchestrator-worker: "Makes network calls: workers via the Antigravity CLI (agy) … Needs jq").

### Skill anatomy (examples read in full)

- `project-graveyard/SKILL.md`: scans local repos for dead side projects, autopsies each from git history ("deploy fear, payments wall, killed by a newer project"), then reports "census, the dead (with cause of death), patterns, and the top 3 by 'pulse' (resurrectability score)". Notable mechanics: causes are "evidence-based guesses, not verdicts — each comes with the evidence line"; low-confidence verdicts trigger a 2–3 question "autopsy interview"; verdicts must be labeled "(forensic)" vs "(confirmed)"; "Necromancer mode" — when the user starts a new project, check the graveyard for a prior attempt first, but "never blocks the new project". Script is "read-only. It never writes inside a scanned repo."
- `scope-creep-detector/SKILL.md`: diffs a change against "stated intent" (user's one-liner, or branch name; "If that name is generic, detached, or unrelated … ask for one line of intent"), Python script outputs JSON, model maps signals to "keep, split, or justify decisions". Thresholds: "Do not tune the threshold merely to make a warning disappear."
- `thinking-out-loud/SKILL.md`: for voice-dictation rambles, "act on nothing until the echo brief is approved" — an echo "with the model's own additions quarantined from the user's words"; rationale: "questions alone cannot secure a transfer … the user verifies what it believes, not just what it doubts."
- `advisor-orchestrator-worker/SKILL.md`: three-tier model team — "the advisor is the strongest reasoning model you can reach, workers the cheapest that pass verification"; dispatches workers from "its own EMPTY temp dir" with written brief files to avoid shell-injection via briefs.
- Common shape: "When to use" + "When not to use" sections with explicit near-misses (graveyard: "that's `kondo`/`npkill`, not this"); references/ files hold the deep content; scripts are stdlib-only and emit JSON for the model to interpret.

### The eval suite (`agent_skills/evals/`) — the real find

Per skill, two files:

1. `evals/<skill>/trigger-cases.json` — a trigger spec: positives, negatives, and near-misses with `should_trigger: bool` plus an `assert` string per case. Its `purpose` field says: "CI runs tools/run_trigger_evals.py against these cases lexically — positives must clear near-misses on description vocabulary alone; … Cases with lexical:false trigger via reasoning, not vocabulary, and are covered by the behavioral tier."
2. `evals/<skill>/evals.json` — behavioral evals: prompt, `expected_output`, and 3–4 checkable `expectations` (e.g. graveyard #2: "No shaming language; epitaphs punch at the pattern, not the person"; "One resurrection candidate offered, not a list").

Tools (`agent_skills/evals/tools/`):

- `run_trigger_evals.py` — "Tier 2 — trigger & routing. Deterministic, CI-safe, no model." Docstring credits the pattern: "Pattern from addyosmani/agent-skills (evals/README.md there): a skill's description is its entire trigger surface, so check it lexically — positive prompts must score against their skill's description clearly above the near-miss negatives, and … must rank their own skill first, with no two descriptions near-colliding." Margin constant `MARGIN = 1.15`. Punchline: "A failure here usually means *fix the description*."
- `skill_lint.py` — "[vendored] Repo-side CI copy. Origin: the skill-builder skill" — validates a skill dir against the agentskills.io spec: name regex + "must equal the directory name", description ≤1024 chars + "triggering heuristics" (regexes for "use when/when the user/triggers on…" and against first-person "I/we/you should"), body warnings at 400/500 lines (~5k-token budget), relative file references must exist, forward-slash paths only, TODO markers, and "text-only skills (no scripts/ AND no references/) are warned — the awesome-llm-apps quality bar expects bundled tools and references". Exit codes 0/1/2; "Python 3 stdlib only … pyyaml is NOT required."

## What to steal (mapped to our greenfield/brownfield flow)

1. **skill_lint.py, near-verbatim** (Apache-2.0) — fills our MAP gap "Frontmatter lint tooling … hangs on T008". It already encodes: name==dir, non-empty description, trigger-signal heuristics, body-length budget (~5k tokens), reference-exists checks. Stdlib-only means zero install cost in CI or a pre-ship skill.
2. **Two-tier evals as our T008 authoring standard**: every skill we ship gets a `trigger-cases.json` (positives + near-miss negatives + asserts) and optionally `evals.json` (behavioral expectations). The lexical router (`run_trigger_evals.py`) is ~100 lines and could gate our repo CI: catches "a description missing the vocabulary users actually say" and "an over-broad description that outranks the right skill".
3. **Description-writing discipline**: near-miss negatives belong in the description itself ("Not for single-file edits or tasks one model handles in one pass") — this is exactly the routing-oriented-description bar from `writing-great-skills`, with a checkable enforcement mechanism attached.
4. **`When not to use` as a required section** in our skill template (T008): every AWLA skill pairs "When to use" with explicit near-misses; it's the cheapest way to prevent misrouting without hurting predictability.
5. **compatibility frontmatter for declared side effects**: "Makes network calls: …", "Runs entirely locally." — adopt for any of our skills that shell out or touch the network; aligns with our "local and private by default" preference.
6. **Specific skills to consider porting** (Apache-2.0, vendored with attribution): scope-creep-detector (brownfield review gate: diff vs stated intent → keep/split/justify), commit-archaeologist (brownfield archaeology before risky edits), thinking-out-loud (greenfield intake: echo-before-act on rambling briefs). These complement, not overlap, our planned chain.
7. **registry.json pattern** for our own repo: one machine-readable index (name, path, description, license, install, evals_dir) that CI lints and future multi-harness manifests can be generated from.

## What to skip

- **Everything outside `agent_skills/`** (per ticket): 100+ app examples (RAG, chatbots, voice) are runnable apps, not agent-loadable artifacts; nothing to install into a skillset. KDnuggets' praise is for that breadth — "how agents, tools, retrieval, multiple models, and skills are actually combined into working applications" — which is inspiration, not cargo.
- **self-improving-agent-skills**: a hosted web app (FastAPI backend, Next.js frontend, Gemini/ADK agents: Executor/Analyst/Mutator loop that mutates a skill prompt and keeps changes if score improves). Interesting idea (auto-tuning descriptions against evals) but wrong artifact class and heavy deps; revisit only if we ever automate eval-driven description tuning — the same loop could run on our trigger-cases without the web app.
- **advisor-orchestrator-worker's implementation**: shells out to Antigravity CLI + Gemini API + claude CLI with `--dangerously-skip-permissions`; our harness has native subagents and model routing, so the machinery is redundant. The one transferable rule: "briefs carry quotes and arbitrary text, so that is a shell-injection bug. Write each brief to a temp file."
- **first-reader**: pleasant but niche (simulated readers for drafts); not a flow skill.

## Surprises & open questions

- **Only 8 skills in a 143k-star repo** — the stars come from the app gallery; the skills dir is young and "released one at a time" (README). Quality-per-skill is unusually high for an "awesome" list because of the eval gate.
- **The eval tooling is cross-repo borrowed**: `run_trigger_evals.py` explicitly credits addyosmani/agent-skills (T012's repo) and `skill_lint.py` is "vendored … Origin: the skill-builder skill (revamp branch)" with a note to make the skill the single source of truth when it ships. The pattern to copy is *vendoring linters into the repo* rather than depending on an external CLI.
- **Honest verification ladder** in trigger-cases.json's own `purpose` field: lexical CI is an approximation; "after any description change, also verify by hand in a fresh agent session." Good model for what we automate vs manually check.
- Open: the `self-improving-agent-skills` "ONE targeted change per round, keep if score improves" loop is unvalidated here (web app, not run); if we later automate description tuning, that one-change-per-round rule is the part worth keeping.
- Open: `npx skills add <github-tree-url>` works per the README (KDnuggets repeats it) — worth one live test before we rely on tree-URL installs for our own repo docs.
