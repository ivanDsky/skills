---
name: map-codebase
description: >-
  Maps an unmapped codebase into docs/agents/project-map.md (layout, entry
  points, seams, working test commands, pinned commit, archify diagram) so
  every later stage reads the map, not guesses. Use when /start triage hits an
  unfamiliar codebase, when entering a repo with no map, or when the map is
  missing or stale.
interaction: afk
requires: [archify]
---

# Map the codebase

Turn an unmapped codebase into `docs/agents/project-map.md`: layout, entry
points, seams, test commands, pinned commit. AFK by design — the map is cheap
to redo and the user corrects it by editing the file, never in conversation.

## 1. Freshness check first

Compare any existing map against HEAD (`git rev-parse HEAD`) before any recon:

- Map exists and its `pinned:` commit == HEAD → skip the stage; hand the map
  path back and stop.
- Map exists, pin != HEAD → cheap refresh, not a re-run: `git diff --stat
  <pin>..HEAD`, re-check only the sections the touched paths hit (layout,
  entry points, seams, tests), update what drifted, bump `pinned:`.
- Map exists but carries no `pinned:` line → treat as unmapped; full run.
- No map → full run.

## 2. Recon

Read in order: `docs/agents/*.md`, GLOSSARY.md, README, build and manifest
files; then walk the tree. Extract, each with evidence:

1. **Purpose** — one line, from README or code, not invented.
2. **Layout** — top-level dirs and what actually lives there.
3. **Entry points** — mains, route tables, CLI registrations, handlers.
4. **Candidate seams** — where tests attach: interfaces, DI registrations,
   test dirs mirroring source.
5. **Working test commands** — run the suite once; record the commands that
   actually work with their pass/fail counts, not what the README claims.

Manifest and test discovery per language:
[recon-checklist.md](references/recon-checklist.md).

## 3. Diagram — soft step

`requires: [archify]` is soft: `/start` checks presence; absence never
blocks this stage.

- archify present → author an architecture candidate from the recon evidence:
  pinned to HEAD, credential-free origin, source-linked nodes; `finalize` it;
  link the HTML from the map. Run with `ARCHIFY_UPDATE_CHECK_DISABLED=1`
  (offline-first posture, T016). Recipe:
  [archify-recipe.md](references/archify-recipe.md).
- archify absent → inline a small mermaid block in the map instead, log the
  skip, continue. The map text is load-bearing; the diagram is not.

## 4. Write the map

Write `docs/agents/project-map.md`, exactly these sections: purpose; layout;
entry points; seams; working test commands; `pinned: <sha>`; diagram path (or
the inline mermaid); the drift rule from step 1, restated in one line.

- Durability rule: behavior and names only — no code snippets, no line
  numbers; they rot before the map is read again.
- PROFILE.md exists with empty care-axes → fill them from the map: the ranked
  quality priorities the recon supports. Say so in the report.

## 5. Report

≤15 lines to the user: map path, headline findings, test status, diagram link
or skip note, care-axes filled or not. Corrections land as map edits, never as
conversation. Debug on → append the ≤4-line `.scratch/run-log.md` entry.

Read [recon-checklist.md](references/recon-checklist.md) when the manifest or
test runner is not obvious from the tree. Read
[archify-recipe.md](references/archify-recipe.md) before authoring the
diagram candidate.

Ours; recon discipline adapted from mattpocock/skills (`research`), MIT.
Diagram step delegates to `archify` (tt-a1i/archify), Apache-2.0.
