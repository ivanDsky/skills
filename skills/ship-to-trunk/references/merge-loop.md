# Merge loop — one ticket, one PR

Read when dispatching a ticket in a `trunk` run, when a slice PR conflicts,
when the repo has no PR check, or when PROFILE says `pr-check: none`.
Flags verified against `gh` 2.96.0 `--help` (2026-11-07): `pr merge
--squash --delete-branch --auto --match-head-commit`, `pr checks --watch
--fail-fast --required`, `pr update-branch --rebase`.

## Per ticket (`pr-check: <workflow>` or no `pr-check:` key)

```bash
git fetch origin
git worktree add -b <slug>/<NN>-<ticket> ../<repo>-wt/<NN> origin/main
# ... TDD, local gates (runner, structure:, lint) green ...
git fetch origin && git rebase origin/main      # re-run the gates if main moved
git push -u origin HEAD
gh pr create --base main --title "<conventional title>" --body-file .scratch/<slug>/pr-<NN>.md
gh pr checks <n> --watch --fail-fast --required   # skip when PROFILE says pr-check: none (see below)
gh pr merge <n> --squash --delete-branch --match-head-commit <sha>   # authority: SKILL.md table
git worktree remove ../<repo>-wt/<NN>
```

- Branch name `<slug>/<NN>-<ticket>`: the last segment stays the build
  identity slug (`deliver`).
- `--match-head-commit` pins the reviewed sha: a push after review blocks
  the merge instead of slipping in.
- `--auto` instead of waiting: only when branch protection requires the
  check (otherwise it merges immediately). Never `--admin`.
- Squash title = the PR title in conventional-commit form
  (`feat(play): …`, `fix: …`, `refactor: …`); `caveman-commit` rules apply.
  The title is the changelog line.
- Body: `open-pr` slice template (≤ ~120 words).

## `pr-check: none` — local merge gate, instant merge

Opt-in, read from PROFILE `## Delivery`: the repo runs no PR CI and main's
post-merge workflow is the safety net. `pr-check:` absent or naming a
workflow → the loop above, unchanged (its CI needs the PR to exist). With
`none`, never call `gh pr checks` (it errors "no checks reported"), and
every gate runs **before** the PR exists: the PR is a readable diff and
description, open about a minute, not a waiting room (every open minute is
a chance for main to move under it). Whole sequence:

```bash
git fetch origin
git worktree add -b <slug>/<NN>-<ticket> ../<repo>-wt/<NN> origin/main
# 1. TDD, local gates (runner, structure:, lint) green
# 2. review-change fast tier over `git diff origin/main...HEAD`, fix rounds until clean
git fetch origin && git rebase origin/main       # 3.
<suite>                                          # 4. PROFILE's pr-check comment command, e.g. ./gradlew assembleDebug test
git fetch origin                                 # 5. origin/main moved → rebase + suite again
git push -u --force-with-lease origin HEAD       # 6.
gh pr create --base main --title "<conventional title>" --body-file .scratch/<slug>/pr-<NN>.md   # 7.
gh pr merge <n> --squash --delete-branch --match-head-commit <sha>   # 8. immediately; <sha> = the head the suite ran on
git worktree remove ../<repo>-wt/<NN>
```

- `<suite>`: the command in the `pr-check: none` comment; none written →
  assemble debug + unit `runner:` + `structure:` (when set).
- A rebase that pulled in new commits always re-runs the suite — the build
  tool's incremental cache keeps that cheap, and it catches API breaks
  between modules that touch no shared file. Never skip it because the
  changed files do not overlap. Merge only on a green suite over exactly
  `<sha>` rebased onto the current `origin/main`.
- Step 8 runs right after step 7 only when the authority table lets the
  agent merge (dark/non-behavioral slice + consent line). Otherwise
  (unflaggable live change, flip PR) the PR opens after review and suite
  passed and waits only for the user.
- Write the PR body once, after step 2 (`open-pr` slice template); its
  check line reads `local suite green on <sha>; no PR CI by design`.

## Main moved while the PR waits

`gh pr update-branch <n> --rebase`, wait for the check again, then merge
with the new head sha. `pr-check: none`: applies only to a PR waiting for
user approval — rebase locally and re-run the suite (steps 3–6 above).
Rebasing is the slice author's job, never the next ticket's.

## Conflicts

1. Rebase locally, resolve, re-run the gates, force-push with
   `--force-with-lease` (the slice branch only — never main).
2. Resolution keeps both intents. Unsure which side wins → stop and ask;
   never drop the other ticket's change to get green.
3. Conflict > ~50 lines, or in a file another in-flight ticket owns → the
   tickets were mis-sliced: pause the later ticket, report, re-slice
   (shared file edit becomes its own ticket merged first).
4. A conflict resolved by hand gets a `review-change` fast-tier review of
   the resolution diff only (the conflicted hunks as resolved) before
   merge. A clean rebase gets no review.

## No required PR check — trunk precondition

Trunk mode does not start without CI as the judge, unless PROFILE says
`pr-check: none` (the local gate above is then the judge; skip this
section). Detect: no workflow in
`.github/workflows/` with an `on: pull_request` trigger, or `gh api
repos/{owner}/{repo}/branches/main/protection` shows no required status
check. Then:

1. The run's first ticket is the check setup: one workflow on
   `pull_request` running assemble debug + PROFILE's unit `runner:` +
   `structure:` (when set), landed as one ordinary PR the user approves.
2. The user enables branch protection on main requiring that check (a repo
   setting; ask, never change it from the agent).
3. Slices start after both. Until then the run is blocked on the setup,
   not downgraded: local gates never stand in for the check, and no slice
   merges on local evidence.

## Red main

A merge turned the main check red → stop merging. Next PR = `git revert`
of the culprit squash commit (agent may merge it on green), then the
ticket is reopened. Fix forward only for a one-line obvious fix.

## Release workflows on push

Repos whose workflow publishes on every push to main (tag per version,
skipped when the tag exists): slices never bump the version, so they
publish nothing. The flip PR bumps the version and is the release.
