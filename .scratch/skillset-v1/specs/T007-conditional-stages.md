# T007 — Spec: conditional stages of the one flow

Draft · 2026-10-30 · Tracker ticket: `tickets/T007-define-brownfield-chain.md`
Sources: T005 resolution (locked flow decisions), T008 (authoring standards), `REFERENCE-MAP.md` §"managing agents" + §"waiting vs delivering", `research/superpowers.md` (fix-loop round caps, fresh implementers, status contracts), `research/mattpocock-skills.md` (tracer bullets, research skill, wayfinder frontier), `research/archify.md` (repo-backed diagrams), `research/impeccable.md` (detect/critique tiers).

## 0. Where the conditionals sit

One flow (T005): `intake → [orientation] → spec → tickets → [research] → implement → review → deliver`.

| # | Mechanism | Fires when | Stage slot | Skill |
|---|---|---|---|---|
| 1 | Orientation | codebase not yet mapped, or map stale | between intake and spec | `map-codebase` |
| 2 | Research fan-out | a ticket declares `Unknowns:` | between tickets and implement | `fan-out-research` |
| 3 | Prototype mode | `/start` triage sets the prototype flag | flag bends spec/tickets/review/deliver | `graduate-prototype` (exit step) |
| 4 | Teardown gate | 2 failed fix rounds on one module, or reviewer discretion | inside the implement/review loop | `adjudicate-teardown` |

Shared rules, all four mechanisms:

1. **Verify-on-disk**: a subagent's output counts only when its file exists at the absolute path given in the brief. Chat replies are status, never findings.
2. **Absolute paths**: every subagent brief carries absolute artifact paths (children may run in a different cwd; same disk).
3. **Minimal briefs**: fresh-context subagents get artifacts + pointers (spec excerpt, ledger lines, findings files) — never pasted session history.

## 1. Orientation — `map-codebase`

Purpose: turn an unmapped codebase into `docs/agents/project-map.md` so every later stage reads the map, not guesses.

```yaml
name: map-codebase
description: >-
  Maps an unmapped codebase into docs/agents/project-map.md (layout, entry
  points, seams, test commands, pinned commit, archify diagram). Use when
  /start triage hits an unfamiliar codebase or the map is missing or stale.
interaction: afk
requires: [archify]
```

Body:

1. **Skip condition first**: map exists AND its `pinned:` commit == HEAD → skip stage. Pin != HEAD → cheap refresh: re-check only map sections the `git diff --stat pin..HEAD` touches. No pin → treat as unmapped.
2. **Recon**: read `docs/agents/*.md`, GLOSSARY, README, build/manifest files; walk the tree; find entry points and candidate seams (where tests attach); run the test suite once; record the commands that work.
3. **Diagram**: author an archify architecture JSON pinned to `git rev-parse HEAD`, credential-free origin, source-linked nodes; `finalize` it; link the HTML from the map. archify absent → inline mermaid in the map, log the skip, continue (map text is load-bearing, the diagram is not).
4. **Write the map**: purpose, layout, entry points, seams, working test commands, `pinned: <sha>`, diagram path, drift rule (step 1). No code snippets (durability rule).
5. **Report ≤ 15 lines** to the user; corrections land as map edits, not conversation.

Est: ~900 tok body. Depth → `references/recon-checklist.md` (per-language manifest/test discovery) + `references/archify-recipe.md`.

Decisions: orientation is AFK — the map is cheap to redo and the user corrects by editing; seam agreement stays in the spec stage (T006) where it is load-bearing. archify posture per T016: update-check off (`ARCHIFY_UPDATE_CHECK_DISABLED=1`). `requires: [archify]` is soft: `/start` checks presence; absence degrades to mermaid, it never blocks.

## 2. Research fan-out — `fan-out-research`

Purpose: resolve ticket unknowns with parallel fresh-context subagents; findings land as cited files.

```yaml
name: fan-out-research
description: >-
  Spawns one research subagent per declared unknown and clears the ticket
  blocker only when the findings file exists on disk with citations. Use when
  a ticket carries an Unknowns: block.
interaction: afk
```

No `requires`: subagents are harness-native; web access is the child's business.

Body:

1. **Ticket contract**: tickets may declare an `Unknowns:` block — each entry must be answerable from code, docs, or primary sources. Answerable only by user preference → it is an intake question instead, not an unknown.
2. **Fan-out**: one subagent per unknown, no shared state. Brief = the question + absolute findings path `.scratch/<effort>/research/<NN>-<slug>.md` + citation rule (primary sources; every claim traces to its owner).
3. **Verify-on-disk** (shared rule 1): no file → unknown still open. Never accept a chat reply as a finding.
4. **Feed back**: finding answers the unknown → edit the ticket (resolution line + file link), clear the blocker. Finding forks the design → it graduates into an intake question / decision ticket (grilling stays reserved for irreversible forks). Finding kills the ticket → close it with the reason.
5. **Don't block the frontier**: dispatch all unknowns at once; unblocked tickets keep implementing; blockers are re-checked at each frontier scan, not by polling.

Est: ~800 tok. Depth → `references/finding-format.md` (file template, citation rules).

Decision: one file per unknown, not one mega-report — parallel subagents never share state, and a failed unknown costs one file, not the batch.

## 3. Prototype mode — flag contract + `graduate-prototype`

### 3.1 Flag contract (defined here; honored by the T006 chain skills)

1. `/start` triage sets `mode: prototype` in the effort's flow state; any stage may propose the flag, the user confirms once. Same flow, not a second chain.
2. Spec: one page max, assumptions marked inline; deep intake off; grilling only for irreversible forks.
3. Tickets: every ticket a tracer bullet — narrow complete slice, demoable or question-answering, sized for one fresh context window.
4. Review = fast tier: verification-before-completion checks (tests ran, output read) plus, for UI changes, an impeccable `detect`/`critique` pass with a screenshot from the deploy target. No dual-verdict full review; heavy audit / art-direction stays full-tier (post-graduation).
5. DoD: question answered / demo runs. No DoD, no close — same as the main flow.
6. Deliver: each prototype carries one line, `deploy: main | standalone | none` — `main` = merge to main like a feature; `standalone` = its own branch deployed to a test target the user tries; `none` = throwaway, findings only.
7. Exit: every prototype ends in graduate or discard, never in limbo.

### 3.2 Skill: `graduate-prototype`

Purpose: cherry-pick the prototype modules worth keeping into real tickets that pass full gates.

```yaml
name: graduate-prototype
description: >-
  Cherry-picks working prototype modules into real tickets that enter the
  standard flow at implement. Use when a prototype answered its question and
  some of its code should ship.
interaction: hitl
```

Body:

1. **Trigger**: user answers the prototype's question or approves the demo; flag stays on until graduate/discard is decided.
2. **Inventory**: list prototype modules; classify keep / rewrite / discard. Passing tests are evidence; a running demo is not.
3. **Cherry-pick**: one real ticket per keep module, `Blocked by:` ordered, each referencing the prototype branch + commit; rewrite modules carry design notes from prototype findings.
4. **Handoff**: tickets enter the standard flow at implement — full gates, dual-verdict review. The prototype branch merges only via these tickets, never directly.
5. **Discard path**: `deploy: none` prototypes end with a findings file (what was learned, what to reuse) and the branch archived.

Est: ~700 tok.

## 4. Teardown gate — trigger contract + `adjudicate-teardown`

### 4.1 Trigger contract (lives in the implement/review loop)

1. Per-module fix-round counter in the ledger. 2 failed fix rounds on the same module → gate fires before round 3.
2. Reviewer discretion: any reviewer may fire the gate once, with a logged reason. Discretion verdicts go through the same architect, so the architect is the check against abuse.
3. Every trigger is a ledger line (`Ruling:` format).

### 4.2 Skill: `adjudicate-teardown`

Purpose: decide fix-forward vs clean redesign for a failing module with an independent architect; on redesign, rebuild carries only extracted findings.

```yaml
name: adjudicate-teardown
description: >-
  Decides fix-forward vs clean redesign for a twice-failed module using an
  independent fresh-context architect, then extracts findings before any
  rebuild. Use when a module fails its second fix round or a reviewer fires
  the teardown gate.
interaction: mixed
```

No `requires`: the architect is a harness-native high-effort subagent; PROFILE effort level does not inherit (forced high).

Body:

1. **Independent architect**: fresh context, effort forced to high. Brief = module path, spec excerpt, fix-round history, review findings. Never the session transcript, never the full fix diffs.
2. **Binary verdict**: `fix-forward` (bounded plan: what changes, how verified) or `clean-redesign` (rationale). Recorded as a Ruling; user informed, may veto once.
3. **Findings extraction (on redesign)**: memo file with exactly three sections — root cause (why the attempts failed), interface contracts worth keeping (Consumes/Produces signatures), surviving tests (passing tests that encode required behavior). Memo path goes in the ledger.
4. **Rebuild**: fresh-context implementer receives only the memo + spec excerpt. Old branch archived (kept for reference), never merged. New work re-enters the normal gates.
5. **No recursion**: the architect does not implement; the rebuild implementer does not spawn reviewers.

Est: ~900 tok. Depth → `references/architect-brief.md` (dispatch template + verdict format).

Decisions: fresh context means the architect grades the module as a stranger would — same pattern as superpowers' fresh implementers/reviewers, and their fix-loop research is why the trigger is a hard counter, not a feeling. Our cap is 2 rounds (superpowers caps at 3) because the gate itself is cheap and teardown preserves the value: memo + surviving tests + archived branch.

## 5. Boundaries

- Chain slots, gates per effort level, artifact handoffs between core stages: T006. This spec defines only the conditional mechanisms and their contracts.
- Naming, lint, routing evals: T008. Skill disposition and install plan: T017/T018.
- Open question (deferred to T006): whether `map-codebase` also refreshes the map at deliver time — cheap, probably yes, but it belongs with the gate definitions.
