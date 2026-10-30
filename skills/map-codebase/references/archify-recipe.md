# Archify recipe for the project map

Read before authoring the diagram candidate. archify is the installed
`skills/archify` package; its own SKILL.md and
`references/repository-authoring.md` are the deep authorities — this recipe
only fixes our posture.

1. **Posture**: export `ARCHIFY_UPDATE_CHECK_DISABLED=1` in the shell before
   any archify command (offline-first, T016 — the update check phones home by
   default; we consciously disable it).
2. **Freeze identity**: `git rev-parse HEAD` (full 40-char sha),
   `git remote get-url origin` with any userinfo stripped, `git status
   --short`. The candidate pins the credential-free origin + revision; a
   dirty worktree is noted in the report, never silently ignored.
3. **Author the candidate**: architecture type, from the recon slice (step 2
   of SKILL.md), not a full inventory. Every component carries source-linked
   references (`path` + `line`/`end_line`); boundaries only when they answer
   a real reader question. Follow archify's repository-backed authoring rules
   for evidence and identity fields.
4. **Stable paths**: candidate and receipts under `.archify/project-map/`,
   HTML at `docs/agents/project-map.html` — the map links that path, so
   refreshes overwrite instead of littering timestamped folders.
5. **Finalize** (one command, same as archify prescribes):
   `node <archify-path>/bin/archify.mjs finalize architecture <candidate.json>
   docs/agents/project-map.html --repo-root <repo-root> --quality showcase
   --json`. Non-zero exit is never success — repair per archify's delivery
   contract, bounded.
6. **Link it**: the map's diagram section points at
   `docs/agents/project-map.html`.

Fallback (archify absent): one mermaid `flowchart` block, ≤30 lines, main
journey + stores only, labelled "approximate — archify unavailable". Do not
hand-maintain a fake archify candidate.
