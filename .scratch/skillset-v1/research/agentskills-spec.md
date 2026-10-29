---
title: "T003 — The Agent Skills standard (agentskills.io) + anthropics/skills: portable contract"
ticket: T003
status: findings
researched: 2026-10-29
sources:
  - https://agentskills.io/specification                      # S1 spec
  - https://agentskills.io/client-implementation/adding-skills-support  # S2 client guide
  - https://agentskills.io/skill-creation/best-practices      # S3 best practices
  - https://agentskills.io/skill-creation/quickstart          # S4 quickstart
  - https://agentskills.io/skill-creation/using-scripts       # S5 scripts
  - https://agentskills.io/skill-creation/optimizing-descriptions # S6 descriptions
  - https://raw.githubusercontent.com/agentskills/agentskills/main/skills-ref/src/skills_ref/validator.py  # S7 reference validator
  - https://raw.githubusercontent.com/agentskills/agentskills/main/skills-ref/src/skills_ref/parser.py     # S8 reference parser
  - https://raw.githubusercontent.com/anthropics/skills/main/skills/skill-creator/scripts/quick_validate.py # S9 Anthropic validator
  - https://raw.githubusercontent.com/anthropics/skills/main/skills/skill-creator/SKILL.md                 # S10 Anthropic skill-creator
  - https://raw.githubusercontent.com/anthropics/skills/main/README.md    # S11 repo README
  - https://raw.githubusercontent.com/anthropics/skills/main/template/SKILL.md # S12 template
  - https://raw.githubusercontent.com/anthropics/skills/main/spec/agent-skills-spec.md # S13 spec pointer
  - ~/.local/share/prime-agent/skills/skill-creator/SKILL.md              # S14 Prime Agent skill-creator
  - ~/.local/share/prime-agent/skills/skill-creator/references/python-skills.md # S15 Prime Agent python-skills
  - https://raw.githubusercontent.com/anthropics/skills/main/skills/pdf/SKILL.md  # S16 pdf example skill
---

# Agent Skills standard (agentskills.io) + anthropics/skills

## What it is

An open, vendor-neutral file format for agent "skills": a directory whose `SKILL.md` (YAML frontmatter + markdown body) tells an agent what to do and when, with optional `scripts/`, `references/`, `assets/` subdirs [S1]. Loading is three-tier progressive disclosure: every session loads only name+description for all skills (~50–100 tokens each), the full body on activation (<5k tokens recommended), and bundled resources only when referenced [S1, S2]. Anthropic created the pattern and moved the standard to agentskills.io; their repo now ships examples + a template and points at the spec (`spec/agent-skills-spec.md` is literally: "The spec is now located at <https://agentskills.io/specification>") [S11, S13].

## How it works

### Directory structure & discovery
- A skill = any directory containing `SKILL.md`; all other content is freeform, with three *recommended* subdirs: `scripts/` (executable code), `references/` (on-demand docs), `assets/` (templates/images/data) [S1].
- The spec does NOT mandate where skills live. The client guide documents the de-facto convention: scan `<project>/.<client>/skills/` plus cross-client `<project>/.agents/skills/` (and user-level `~/.agents/skills/`); "The `.agents/skills/` paths have emerged as a widely-adopted convention for cross-client skill sharing" [S2]. VS Code's quickstart uses `.agents/skills/roll-dice/SKILL.md` as the default location [S4]. Claude Code also scans `.claude/skills/` for compatibility [S2].
- Discovery scans for "subdirectories containing a file named exactly `SKILL.md`", skipping `.git/`/`node_modules/` [S2]. The reference parser additionally accepts lowercase `skill.md` ("Prefers SKILL.md (uppercase) but accepts skill.md (lowercase)") [S8].
- Name collisions: "project-level skills override user-level skills"; within a scope, first-found or last-found is fine but be deterministic and log a warning [S2]. Prime Agent does exactly this (explicit paths → project → global → package → built-in) [S14].

### SKILL.md frontmatter (the whole contract)
Exactly six fields are defined [S1, S7]:
- `name` (required): 1–64 chars; lowercase alphanumeric + hyphens; no leading/trailing hyphen; no `--`; **must match the parent directory name** [S1].
- `description` (required): 1–1024 chars, non-empty; "Should describe both what the skill does and when to use it… Should include specific keywords" [S1]. It is the only routing signal: "the description carries the entire burden of triggering" [S6].
- `license` (optional): short name or pointer to a bundled file, e.g. `license: Proprietary. LICENSE.txt has complete terms` (pdf skill) [S1, S16].
- `compatibility` (optional): 1–500 chars, only if the skill has environment requirements ("Requires git, docker, jq, and access to the internet") [S1].
- `metadata` (optional): "a map from string keys to string values" for client-specific extras; the reference parser coerces every value to `str` [S1, S8].
- `allowed-tools` (optional, experimental): "A space-separated string of tools that are pre-approved to run", Claude-Code-style patterns (`Bash(git:*) Bash(jq:*) Read`); "Support for this field may vary" [S1].
- Body: "There are no format restrictions" [S1].

### Loading lifecycle — what every compliant client does (S2, the guarantees our files can rely on)
1. Discover → parse frontmatter only; store name/description/location [S2].
2. Disclose a catalog (name + description + path) in system prompt or a tool description, plus a short behavioral instruction [S2].
3. Activate by model decision (file-read or activation tool), or user-explicit slash command [S2].
4. Malformed-YAML fallback: wrap unquoted colons and retry — skills from other clients often have technically-invalid YAML that still parses [S2].
5. **Lenient validation is the client-side norm**: "Name doesn't match the parent directory name → warn, load anyway. Name exceeds 64 characters → warn, load anyway. Description is missing or empty → skip the skill… log the error. YAML is completely unparseable → skip" [S2]. So: a bad name still loads; a missing/empty description silently never loads.
6. Filtered skills (disabled, permission-denied, or opted out "via a `disable-model-invocation` flag") are hidden from the catalog entirely [S2]. Prime Agent implements this exact field: "`true` hides the skill from the system prompt; only explicit `/skill:<name>` invokes it" [S14].
7. Clients should exempt skill content from context compaction and dedupe repeat activations [S2].

### Validation — two reference implementations
- Official `skills-ref` CLI (`skills-ref validate ./my-skill`, from agentskills/agentskills) checks, per `validator.py`: frontmatter is a mapping; **only the six allowed fields** (unknown field = error); `name` present, non-empty, NFKC-normalized, ≤64, lowercase (`!= name.lower()` errors), no leading/trailing hyphen, no consecutive hyphens, `all(c.isalnum() or c == '-')` (**Unicode alnum — i18n letters allowed**), dir-name match (NFKC); `description` non-empty ≤1024; `compatibility` ≤500 [S7]. Parser uses `strictyaml` (schema-locked YAML), requires file to start with `---` and close with `---` [S8].
- Anthropic's own `skills/skill-creator/scripts/quick_validate.py` (S9): same six-field allowlist, ASCII-only name regex `^[a-z0-9-]+$`, ≤64, hyphen rules, dir-match not enforced by the script but warned by clients, description ≤1024 **plus "Description cannot contain angle brackets (< or >)"** (not in the spec), compatibility ≤500.
- anthropics/skills layout: 19 example skills, each `skills/<name>/` with `SKILL.md` + `LICENSE.txt` + optional `scripts/ references/ assets/` (e.g. pdf: `SKILL.md`, `LICENSE.txt`, `forms.md`, `reference.md`, `scripts/*.py`; skill-creator even has `agents/*.md` + `eval-viewer/`) [S11]. `template/SKILL.md` is just frontmatter (`name: template-skill`, description placeholder) + "# Insert instructions below" [S12]. Repo doubles as a Claude Code plugin marketplace (`/plugin marketplace add anthropics/skills`) and carries a skills.sh badge [S11].

### Authoring guidance that rises to near-contract level
- Size budgets: metadata ~100 tokens; "Keep your main SKILL.md under 500 lines" and body "< 5000 tokens recommended"; reference files ">300 lines: include a table of contents"; "Keep file references one level deep from SKILL.md" [S1, S3, S10].
- Every reference gets a load condition: "'Read references/api-errors.md if the API returns a non-200 status code' is more useful than a generic 'see references/ for details'" [S3].
- Description style: imperative "Use this skill when…", focus on user intent, "Err on the side of being pushy… even if they don't explicitly mention 'CSV'", and agents under-trigger, so push [S6, S10]. Note: agents skip skills for trivial tasks they can do alone [S6].
- Scripts: relative paths from the skill root; list available scripts in SKILL.md; self-contained via PEP 723 inline deps run with `uv run scripts/x.py`; pin versions for one-off commands (`npx eslint@9`); no interactive prompts; `--help`; structured output [S5].
- Instruction patterns worth copying into our skills: gotchas sections (highest-value content), output templates, checklists with `- [ ]` progress, validation loops, plan-validate-execute for destructive ops [S3].

## THE DELIVERABLE — Linter checklist (exact rules our repo enforces)

**ERROR level (spec-mandatory; skill is broken without it):**
1. `SKILL.md` exists at skill-dir root (we can also accept `skill.md`, like skills-ref [S8] — recommend NO: require uppercase, matches every client's primary path).
2. File starts with `---` and frontmatter closes with a second `---` [S8].
3. Frontmatter parses as a YAML mapping (reject lists/scalars) [S8].
4. `name` present, non-empty string [S7].
5. `name` ≤ 64 chars [S1, S7].
6. `name` is all `[a-z0-9-]` (decide: ASCII per spec table + Anthropic validator + Prime Agent [S1, S9, S14], or Unicode alnum per skills-ref `isalnum()` [S7] — see Open Questions).
7. `name` not starting/ending with `-`; no `--` anywhere [S1, S7].
8. `name` == parent directory basename (exact, after NFKC + strip) [S1, S7].
9. `description` present, non-empty after strip [S7]. (Client behavior: silent non-load [S2] — this is the #1 failure mode, hence ERROR.)
10. `description` ≤ 1024 chars [S1].
11. No angle brackets `<` `>` in `description` (Anthropic's stricter rule [S9]; spec-optional but cheap injection-safety) — recommend WARN not ERROR.
12. `compatibility` if present is a string ≤ 500 chars [S1, S7].
13. `metadata` if present is a mapping of string→string [S1, S8].

**WARN level (cosmetic per client-side lenient norm [S2]):**
14. Unknown frontmatter keys (unless we define our own extensions — see below; then they're checked against OUR allowlist).
15. Body > 500 lines or > ~5000 tokens [S1, S3].
16. Reference file > 300 lines without a table of contents [S10].
17. Relative links/paths in body that don't resolve from the skill root; reference chains deeper than one level from SKILL.md [S1, S3].
18. `scripts/*` mentioning unpinned versions in one-off commands (`npx x` without `@version`) [S5].
19. Description missing "use when"-style trigger language (style lint; Anthropic marks descriptions as "the primary triggering mechanism" [S10]).

**Repo-level (CI over the whole skillset):**
20. Skill names unique across the repo (collision = shadowing warning at load [S2]).
21. Each dir under `skills/` is a valid skill (no stray dirs) or explicitly ignored.
22. Optional: run `skills-ref validate` (official CLI, `agentskills/agentskills`) in CI as an oracle alongside our linter [S1, S7].

## What the standard does NOT cover (we must decide)

- **Where skills live**: spec defines content, not location; only the `.agents/skills/` cross-client convention exists [S2]. Our repo layout under `skills/` is ours; installs go wherever `npx skills` puts them (T004).
- **Chaining between skills**: nothing in spec/examples defines skill→skill invocation or flow-chaining; skill-creator's `agents/*.md` subagent files are an Anthropic-internal pattern, not standard [S10]. Our greenfield/brownfield chains are our own convention.
- **HITL/AFK marking**: no field exists. Closest: `disable-model-invocation` (Claude Code + Prime Agent) = user-explicit-only [S2, S14] — usable as an "AFK-unsafe" marker, but approval gates must be prose (checklists/validation-loop pattern [S3]) or our own metadata key.
- **Per-project configuration**: no config file in the standard; project-vs-user precedence is client behavior [S2]. Our "configurable per project" goal needs our own mechanism (e.g., a metadata key or a sibling config file).
- **Python-backed extensions**: Prime Agent's contract (skill-root `pyproject.toml`, `src/<import_name>/__init__.py`, import name = name with `-`→`_`, optional `run()` + `rlm.skill:cli`) is entirely a Prime Agent extension, NOT portable; a compliant client just sees a markdown skill [S14, S15]. Fine to ship, but skills relying on it degrade to instructions-only elsewhere.
- Also uncovered, worth a decision: versioning (no `version` field — put it in `metadata` [S1]); evals (`evals/evals.json` is skill-creator convention, not spec [S10]); trust gating for repo-supplied skills (client-side concern [S2]); permissions beyond experimental `allowed-tools` [S1].

## What to steal (mapped to our flow)

1. **The ERROR checklist above as `scripts/lint_skills.py`** — our repo's hard gate; mirror skills-ref rules so `npx skills add ivanDsky/skills` installs cleanly everywhere [S1, S7, S9].
2. **Template skill** (`template/SKILL.md` pattern: minimal frontmatter + section stubs) extended with our chain/HITL conventions [S12].
3. **Size budgets + progressive disclosure as review criteria**: <500-line SKILL.md, references pushed down with explicit "read X when Y" pointers, one-level-deep references [S1, S3, S10].
4. **Description style rules** (imperative, intent-focused, pushy, keyword-rich) as a lint hint + authoring doc — this is what makes greenfield chains actually fire [S6, S10].
5. **Scripts conventions**: PEP 723 + `uv run` self-contained scripts, pinned one-off versions, relative paths, structured output [S5] — fits brownfield flow steps that call validators.
6. **Validation-loop / plan-validate-execute patterns** as the backbone of our brownfield chain's edit steps [S3].
7. **`disable-model-invocation` semantics** for AFK-unsafe skills [S2, S14].
8. **Gotchas sections**: corrections from real runs get appended to the skill's Gotchas — matches our "refine with real execution" loop [S3].

## What to skip

- **docx/pptx/xlsx/pdf production skills** — source-available proprietary, reference-only [S11].
- **skills-ref as a hard dependency** — strict unknown-field errors conflict with the ecosystem's leniency and our future extension fields; implement rules ourselves, optionally run it in CI as a second opinion [S2, S7].
- **`allowed-tools`** — experimental, Claude-Code-pattern syntax, variable support [S1].
- **skill-creator's eval-viewer/benchmark machinery** — heavy, Claude-Code-subagent-specific; a checklist + a few test prompts is enough for v1 [S10].
- **Cloud/sandbox discovery provisioning** — irrelevant to a git-distributed skillset [S2].

## Surprises & open questions

- **"spec/" in anthropics/skills is a stub** — the standard lives entirely on agentskills.io (github.com/agentskills/agentskills holds only docs + skills-ref) [S13]. Anthropic gave the format away.
- **Charset contradiction inside the spec itself**: the page says "unicode lowercase alphanumeric characters (`a-z`, `0-9`)" — Unicode in prose, ASCII in parens; skills-ref validates Unicode (`isalnum()`), Anthropic's validator is ASCII-only [S1, S7, S9]. **Open Q: enforce ASCII?** Recommend YES: every named harness we target (Prime Agent docs, Anthropic validator) is ASCII, and npx-installable names should be.
- **Strictness splits by role**: author-side `skills-ref` errors on unknown fields; client-side guide says warn-and-load; Prime Agent ignores unknown fields [S2, S7, S14]. Since we WILL add extension fields (chaining, HITL), our linter needs an explicit allowlist = 6 spec fields + our extensions.
- **A bad `name` still loads in most clients (warn), but a missing description never loads (silent)** [S2] — matches the MAP's warning; lint the description hardest.
- **"Pushy" descriptions are official advice** because models under-trigger — not just mattpocock folk wisdom [S6, S10].
- **Open Q:** does `npx skills` (vercel-labs) add extra frontmatter requirements or its own metadata keys? → T004.
- **Open Q:** where do our chain-marker fields live — `metadata` (string→string, future-proof, spec-clean) vs top-level custom keys (breaks skills-ref validation)? Recommend `metadata` keys.
