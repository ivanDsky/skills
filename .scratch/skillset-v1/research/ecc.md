# ECC (affaan-m/ECC) — research notes

Repo: <https://github.com/affaan-m/ECC> — MIT. 292,683 stars, default branch `main` (GitHub API, 2026-10-29).
Article framing: KDnuggets, "5 Best GitHub Repositories for AI Agent Skills" (Abid Ali Awan, 2026-10-21) — <https://www.kdnuggets.com/5-best-github-repositories-for-ai-agent-skills>

## What it is

A 6,440-file "agent harness performance optimization system" for Claude Code (best), Codex, Qoder, plus adapters for Cursor/OpenCode/Gemini/Zed/Copilot: 71 subagent definitions, 313 skills, 98 command shims, 122 rules, a hook runtime, a cross-harness Markdown memory store, a hook-driven "instincts" learning loop, and AgentShield config scanning. README workflow: `plan -> test -> implement -> review -> verify -> remember -> improve` and motto "Optimize the context window. Persist everything else." (https://raw.githubusercontent.com/affaan-m/ECC/main/README.md). KDnuggets calls it "the biggest collection in this list in terms of raw capabilities" and "probably overkill if you only need a better debugging prompt."

## How it works

### The five artifact classes (README "Key Concepts", same URL as above)

| Concept | What it does | Context behavior |
|---|---|---|
| Skills | Reusable workflows such as TDD, security review, or deep research | Loaded when the task needs them |
| Agents | Scoped workers with their own context and tool permissions | Isolate planning, implementation, and review |
| Rules | Durable project or language standards | Always loaded, so install them selectively |
| Hooks | Scripts triggered by harness events | Run outside the model context |
| Instincts | Patterns learned from real sessions with confidence scores | Recalled when relevant |

### Instincts vs skills (`skills/continuous-learning-v2/SKILL.md`, https://raw.githubusercontent.com/affaan-m/ECC/main/skills/continuous-learning-v2/SKILL.md)

An instinct is "a small learned behavior" — an atomic YAML file with frontmatter `id / trigger / confidence / domain / source / scope / project_id` and a two-section body (`## Action`, `## Evidence`). One trigger, one action; confidence 0.3 ("tentative") to 0.9 ("near-certain"); ≥0.7 means "auto-approved for application". A skill is a full workflow document; instincts are the raw material skills evolve from: `/evolve` "Cluster related instincts into skills/commands, suggest promotions". The loop:

- Hooks (`PreToolUse`/`PostToolUse`, `hooks/hooks.json`) append every prompt/tool call to `observations.jsonl`. Rationale, verbatim: "v1 relied on skills to observe. Skills are probabilistic -- they fire ~50-80% of the time based on Claude's judgment." / "Hooks fire 100% of the time, deterministically."
- An optional background observer agent (Haiku; `observer.enabled` defaults to **false**, every 5 min, needs ≥20 observations) reads observations and writes instincts: "User corrections -> instinct", "Error resolutions -> instinct", "Repeated workflows -> instinct".
- v2.1 scopes instincts per project (hash of git remote URL) under `${XDG_DATA_HOME:-~/.local/share}/ecc-homunculus/projects/<hash>/`; promotion to global is rule-based: "Same instinct ID in 2+ projects, Average confidence >= 0.8".
- Shipped example of curated instincts: `.claude/homunculus/instincts/inherited/ecc-instincts.yaml` — 8 instincts with `source: repo-curation`, confidence 0.8–0.9 (conventional commits 0.9, test runner 0.9, "cross-platform sync" 0.9…), including the meta-instinct "Prefer a small set of accurate instincts over bulk-generated, duplicated, or contradictory instincts."

Note: the confidence numbers are curation with dressing — the "confidence increases/decreases when…" rules are prose in the SKILL.md; the shipped instincts are hand-curated from repo history, not machine-learned.

### Memory (`docs/design/ecc-memory-vault.md`, https://raw.githubusercontent.com/affaan-m/ECC/main/docs/design/ecc-memory-vault.md; skill: `skills/unified-memory/SKILL.md`)

- Format: portable `ecc.memory.v1` Markdown files with strict JSON-valued YAML frontmatter (`schema, id, title, kind, scope, trust, status, source_harness, target_harnesses, tags, links, timestamps`). "Markdown files are the source of truth. SQLite context graphs, embeddings, and hosted systems are indexes or adapters, never the only copy."
- Scopes: `project` at `<repo>/.ecc/memory/` ("protected by a fail-closed `.gitignore`"), `team` (human-inspected, committed), `user` at `~/.ecc/memory/` ("recalled only when explicitly requested"). Kinds: contexts, decisions, facts, handoffs, lessons, notes, preferences, runbooks.
- Trust model: "A memory is context, not an instruction. Every first-release vault entry is `trust: "unreviewed"` and cannot silently become rules, skills, or policy." Writes are **create-only**; supersession is a new linked document; "Human review does not change a vault entry's `trust` field; accepted knowledge is promoted into a governed repository artifact. … a shell-capable agent cannot be treated as an independent human approval boundary."
- Hardening: known secret shapes rejected pre-write; readers don't follow symlinks; bounded lexical search; truncated/incomplete scans fail closed with `ECC_MEMORY_INCOMPLETE` rather than returning partial "not found" answers.
- Access: `ecc memory init|save|handoff|search|read|doctor` CLI (needs separate `npm i -g ecc-universal`; "Skill-only, minimal, manual, and Claude plugin installs do not put the Memory Vault runtime on `PATH`") plus an opt-in MCP server with a server-side harness identity (`ECC_MEMORY_HARNESS`) clients can't override. `handoff --from claude --target codex` is the cross-harness transfer primitive.

### "Research-first development" (repo description, GitHub API)

Two concrete artifacts, not a philosophy doc:

- `contexts/research.md` (https://raw.githubusercontent.com/affaan-m/ECC/main/contexts/research.md): one of three injectable mode contexts (dev/review/research). Verbatim: "Focus: Understanding before acting … Findings first, recommendations second", with a 5-step process and a favored-tools list.
- `skills/search-first/SKILL.md` (https://raw.githubusercontent.com/affaan-m/ECC/main/skills/search-first/SKILL.md): "Research-before-coding workflow: search npm/PyPI, MCP servers, skills, and GitHub for existing tools before writing custom code, then adopt, extend, or build." Step 0 is a "TOOL AVAILABILITY PREFLIGHT" that reports skipped channels "honestly"; decision matrix: Exact match → **Adopt**; partial match → **Extend**; multiple weak matches → **Compose**; nothing → **Build**.
- `manifests/install-profiles.json` ships a `research` install profile (rules+hooks+`research-apis`+`business-content`+`social-distribution` modules).

### Security (`the-security-guide.md`, https://raw.githubusercontent.com/affaan-m/ECC/main/the-security-guide.md; AgentShield)

Cites the Feb 2026 Claude Code CVEs: CVE-2025-59536 (CVSS 8.7) "allowed project-contained code to execute before the user accepted the trust dialog"; CVE-2026-21852 redirected API traffic via attacker-controlled `ANTHROPIC_BASE_URL`, "leaking the API key before trust was confirmed". On memory: "Persistent memory is useful. It is also gasoline." — keep memory narrow, never store secrets, separate project from user-global, reset after untrusted runs. AgentShield "scans the harness itself as an attack surface" — prompts, hooks, MCP config, permissions, secrets (README; KDnuggets).

### Install footprint & what gets injected every session

- The plugin's `hooks/hooks.json` registers 27 hook bindings: PreToolUse ×10 (Bash, PowerShell, Write, Edit|Write, `.*`, `Bash|PowerShell|Write|Edit|MultiEdit`, `^mcp__`), UserPromptSubmit ×1, PreCompact ×1, SessionStart ×2, PostToolUse ×2, PostToolUseFailure ×2, **Stop ×8**, SessionEnd ×1. Hook commands are inline `node -e` blobs that resolve the plugin root by probing several install paths (`ecc`, `everything-claude-code`, …).
- `scripts/hooks/session-start.js` (https://raw.githubusercontent.com/affaan-m/ECC/main/scripts/hooks/session-start.js) injects into every session: the latest session summary + up to **6 instincts** above the 0.7 confidence threshold, stack-relevance-ranked ("`ECC_MAX_INJECTED_INSTINCTS=6`", "`ECC_INSTINCT_CONFIDENCE_THRESHOLD=0.7`") + up to 6 learned skills as 220-char summaries — all capped at **8000 chars** ("Cap SessionStart additional context (default: 8000 chars)", README; `ECC_SESSION_START_CONTEXT=off` to disable).
- Install profiles (`manifests/install-profiles.json`): `minimal` ("no hook runtime"), `core`, `developer` (default; adds framework-language/database/orchestration), `security`, `research`, `full`.
- Repo weight: `docs/` alone is 2,181 files across 8+ languages; `.kiro/` 204, `.opencode/` 91, `.cursor/` 85 mirrored files; docker/ 561, tests/ 550, scripts/ 399. The maintainer's own instinct: "Treat the root repo as the source of truth, then mirror shipped changes to `.cursor/`, `.codex/`, `.opencode/`, and `.agents/` only where the feature actually exists." (`ecc-instincts.yaml`)

KDnuggets framing to keep: ECC's differentiators are "the last two steps" of its pipeline — "remember" and "improve" — i.e. memory + continuous learning, and "if you want your coding agent setup to behave more like a complete engineering platform with memory, security, and specialized workers, it is one of the most ambitious options available."

## What to steal (mapped to our greenfield/brownfield flow)

1. **Instinct YAML as a "lessons" microformat** (T006/T007 capture step): `id/trigger/confidence/domain` + `## Action` / `## Evidence` bodies are a minimal, checkable format for per-project lessons — better than prose memories for things we want re-surfaced. Adopt the promotion rule verbatim: promote to global only when "seen in 2+ projects" with high confidence. Fits our harness's refine/memory layer; no hooks needed.
2. **Memory trust vocabulary** (T008 standards): "Memory is unreviewed context, not executable policy" + create-only writes + supersession links + human promotion into governed docs. This is exactly our `.scratch/` research files vs shipped-skills distinction, stated as a rule. Also steal the fail-closed idea: never answer "does not exist" from an incomplete scan.
3. **`search-first` skill** (port, Apache-2.0-compatible with MIT attribution): the Adopt/Extend/Compose/Build matrix is a brownfield gate and also governs our own porting decisions (adopt a repo's skill vs adapt vs write ours). Small enough to adapt in <100 lines.
4. **Explicit injection budgets**: 8000-char SessionStart cap, ≤6 instincts, ≤6 learned skills, 220-char summaries. Concrete numbers to copy into any prompt note/memory policy we write so our own injected context stays predictable.
5. **The evidence-trail sentence** for greenfield completion criteria: "A result is not just code. It's a trail of evidence: the plan, the failing test, the passing test, the review findings, and the final verification." (README) — maps 1:1 to our chain's checkable-completion bar.
6. **The five-class context-behavior table** as a positioning test (T005): every artifact class we ship must answer "when does this load?" — never (rules), on demand (skills), on event (hooks), on recall (memory/instincts). If a candidate skill can't state its context behavior, it doesn't ship.
7. **Research context mode**: "Findings first, recommendations second" (contexts/research.md) — a one-line policy worth putting in our research skill/note template.

## What to skip

- **Installing ECC itself.** 313 skills + 71 agents + 98 commands + 27 hook bindings is an engineering platform with a paid Pro tier, not a predictable personal skillset; we want a curated handful under `npx skills add ivanDsky/skills`. KDnuggets says the quiet part: "overkill if you only need a better debugging prompt."
- **The hook runtime / continuous-learning observer.** Off by default even upstream, Claude-Code-specific, and broken on native Windows (the SKILL.md itself: the observer "starts and reports success, but the process is killed when the spawning hook exits" — issue #2489). Our harness already has refinement + memory machinery; a second, shell-hook-based one is duplicated sources of truth.
- **The rules layer (122 always-loaded files).** ECC's own table admits rules are "Always loaded, so install them selectively" — permanent context cost per file. Our predictable-flow bar prefers progressive disclosure via skills.
- **The commands layer.** ECC is migrating "to a skills-first surface" and keeps 98 command shims for compatibility (README; `legacy-command-shims/`). Confirms our skills-only decision; no need to invent a command surface.
- **Multi-harness mirroring.** 8-language docs and six mirrored `.cursor/.opencode/.kiro/...` trees are maintenance debt we shouldn't copy; distribution is already decided (`npx skills`).
- **Memory Vault runtime (npm `ecc-universal`).** Good design doc, but it's a separate CLI/MCP platform; our harness scopes (local/global memories + files under `.scratch/`) already cover it. Steal the document contract, not the runtime.

## Surprises & open questions

- **ECC was renamed from "everything-claude-code"** — the hook bootstrap still probes install dirs named `everything-claude-code` and `everything-claude-code@everything-claude-code` (`hooks/hooks.json`).
- **The star magnet is marketing surface as much as code**: 100k+ lines of README with sponsors, a Pro GitHub App ("Private repos from $19/seat/mo"), and a 292k-star count vs KDnuggets' 256.7k three weeks earlier. The mechanisms underneath are simpler than the pitch: curated YAML + hooks + Markdown files.
- **"Learning" is mostly curation**: the flagship shipped instincts are hand-written with `source: repo-curation`; the auto-observer defaults to off; confidence decay/raise rules are prose. Open question: does `skills/continuous-learning-v2/scripts/instinct-cli.py` actually implement confidence updates, or only promotion/export? (Not read — next session can check before adopting the format.)
- **Their security posture is unusually good for a skills repo**: fail-closed memory reads, secret-shape rejection pre-write, no auto-promotion from memory to policy. Worth citing in T008 as the bar for our own memory/refinement policies.
- Open: KDnuggets counts (292 skills / 68 agents / 94 shims) already lag the tree (313 / 71 / 98) — weekly churn; anything we borrow should be vendored, not linked.
