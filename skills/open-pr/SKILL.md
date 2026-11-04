---
name: open-pr
description: >-
  Land a finished run as a pull request a human reads in two minutes: short
  summary, before/after screenshots for UI changes, the major changes, the top
  three things a reviewer must check with line links, and a small diagram when
  structure changed. Use when deliver reaches its land step with delivery =
  pr, when the user says "open a PR", "make a pull request" or "PR this", or
  when a finished branch needs a PR description.
interaction: afk
requires: [gh CLI logged in to the project's remote]
---

> **TL;DR** Opens the run's PR as a 2-minute read — summary, before/after screenshots, major changes, top-3 review checks with line links, optional diagram — and merges only on green review; fires from `deliver` when delivery is `pr`.
> **Related**: skill://deliver (fires it), skill://review-change (verdict the merge depends on; findings feed the top 3), skill://preview-compose (screenshot captures), skill://tdd (screenshot-test ladder), skill://archify (diagram when structure changed), skill://implement (commits on the run branch), skill://start (asks pr vs main), skill://init-profile (seeds `delivery:`)

# Open PR

The PR is a view over artifacts the run already produced, built for a reader
with two minutes. Screenshots come first because they are the fastest proof;
everything else is short. Template and budgets:
[references/pr-body.md](references/pr-body.md).

## 1. Gate and branch

1. `deliver` step 1 (green tree) must have passed. Review not green or not run
   → open as **draft**, never merge.
2. Branch = the run slug (kebab-case), cut before the run's first commit so
   `implement` commits on it. Run already committed on local `main`,
   unpushed → `git switch -c <slug>` and reset local `main` to `origin/main`.
   Pushed `main` is never rewritten unless the user says so; push own run
   branches with `--force-with-lease` only.
3. Over ~800 changed lines, or two unrelated concerns → propose a split in a
   `Ruling:` line before opening. A PR that cannot be read in two minutes is
   too big.

## 2. Gather (before writing a word)

- **Top 3 checks**: rank by what a reviewer could get wrong — review findings
  and `Ruling:` lines first, then one-way doors (migration, deletion, public
  API), shared contracts, and the densest logic in the diff. Exactly three or
  fewer; each is one line: what to check, why, a line link.
- **Line links**: permalinks on the pushed head sha —
  `https://github.com/<owner>/<repo>/blob/<head-sha>/<path>#L<a>-L<b>`. Take
  the ranges from `git diff -U0 <base>..<head>`. Push first; re-link if more
  commits land. No stable line (deleted code, whole-file) → link the file.
- **Screenshots** (UI diff only): pair each changed screen/state by capture
  name. Source is the screenshot test suite (`preview-compose`, Roborazzi / AGP
  captures) — never a device. *Before* = the committed golden at the base ref
  (`git show <base>:<path>`) or, with no golden, a capture run in a base-ref
  worktree. *After* = the capture at head. New screen → after only, labelled
  "new". Changed UI with no capture on either side → say so in one line
  and open as draft; do not substitute a device screenshot.
- **Diagram**: only when modules, dependencies or a flow changed. One
  `mermaid` block, ≤8 nodes, changed parts marked; use `archify` for anything
  bigger and link it. No structural change → no diagram.

## 3. Host the images

GitHub has no API for PR image upload. Commit the PNGs to an orphan branch
`pr-assets` (created once) under `<slug>/before/` and `<slug>/after/`; link by
sha: `https://github.com/<owner>/<repo>/blob/<assets-sha>/<slug>/after/<name>.png?raw=true`.
`main` stays free of binaries and the links survive branch deletion. Never
commit screenshots to the run branch.

## 4. Write and create

1. Title: imperative, ≤70 chars, behavior not files.
2. Body to `.scratch/<slug>/pr.md` from the template. Budget: **≤~350 words
   of prose**; images and the diagram are not counted. Over budget → cut the
   Changes list first, never the screenshots or the top 3.
3. `gh pr create --base main --head <slug> --title "<t>"
   --body-file .scratch/<slug>/pr.md` (add `--draft` per step 1; use the
   repo's default branch if it is not `main`). Print the URL.

## 5. Merge

Only when the PROFILE consent ledger pre-approves merge-to-main AND review is
green AND, if checks exist, `gh pr checks` is green (no CI → say "no CI";
it is not a pass). Then `gh pr merge --squash --delete-branch`; the squash
body is the Summary. Pending/red checks → leave open and report. After merge:
`git switch main && git pull`, then any post-merge step in PROFILE
`Environment facts` (skills repo: re-install with `npx skills add`).

## 6. Report

One line for `deliver`: `PR: <url> — merged | open (<why>) | draft (<why>)`.

## Anti-patterns

- Prose where a before/after pair would show it.
- More than three "must check" items — that is a list nobody follows.
- Device screenshots, or "after" images with no "before".
- A diagram of something that did not change.
- Implying verification that did not run (see the one-line Not verified rule
  in the template).
