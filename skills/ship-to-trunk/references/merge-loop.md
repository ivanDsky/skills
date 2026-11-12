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
git fetch origin                                 # 5. origin/main moved → rerun rule below: related → rebase + suite again; unrelated → push the green head as is
git push -u --force-with-lease origin HEAD       # 6.
gh pr create --base main --title "<conventional title>" --body-file .scratch/<slug>/pr-<NN>.md   # 7.
python3 ~/.agents/skills/ship-to-trunk/scripts/main_health.py status   # red (exit 3) → `main_health.py hold --pr <n> --who <id>`, PR and worktree stay, skip the rest (Red main)
gh pr merge <n> --squash --delete-branch --match-head-commit <sha>   # 8. immediately; <sha> = the head the suite ran on
# never watch main after the merge (no gh run watch/view/list): report and stop; the orchestrator's watcher does
git worktree remove ../<repo>-wt/<NN>
```

- `<suite>`: the command in the `pr-check: none` comment; none written →
  assemble debug + unit `runner:` + `structure:` (when set).
- Main moved during the suite (step 5) → rerun only when it matters,
  judged over the new commits `git diff --name-only <base>..origin/main`
  (`<base>` = the main sha the suite ran on) against the ticket's own
  `git diff --name-only <base>...HEAD`, mapped to build modules:
  - **Rerun** (rebase + suite again) when a module main changed and a
    module the ticket changed are the same, or either depends on the other
    transitively (project dependencies in the build files;
    `./gradlew <module>:dependencies` lists them as `project :x`) — this is
    what catches an API break in a module the ticket never touched; or when
    main touched the shared build setup (`build-logic/`, `gradle/`, root
    build/settings/properties files, the `structure:` rules module).
  - **Otherwise push the green head without rebasing.** Two modules that
    only share a consumer (both feed `:app`) are unrelated.
    The squash merge lands on the newer main; main's post-merge workflow is
    the net, and a red main stops merges (Red main below).
  - No module graph (single-module repo, build files unreadable) → rerun.
  - A textual conflict at merge (`gh pr merge` refuses) → rebase,
    Conflicts below, suite again.
  Ledger the call either way: `merge: <NN> main moved <k> commits —
  rerun|push (<modules>)`.
- Step 8 runs right after step 7 only when the authority table lets the
  agent merge (dark/non-behavioral slice + consent line). Otherwise
  (unflaggable live change, flip PR) the PR opens after review and suite
  passed and waits only for the user.
- Write the PR body once, after step 2 (`open-pr` slice template); its
  check line reads `local suite green on <sha>; no PR CI by design`.

## Main moved while the PR waits

`gh pr update-branch <n> --rebase`, wait for the check again, then merge
with the new head sha. `pr-check: none`: applies only to a PR waiting for
user approval — same rerun rule as step 5 (related → rebase and re-run the
suite; unrelated → merge as is). Rebasing is the slice author's job, never
the next ticket's.

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

`pr-check: <workflow>` or no key: a merge turned the main check red →
stop merging. Next PR = `git revert` of the culprit squash commit (agent
may merge it on green), then the ticket is reopened. Fix forward only for
a one-line obvious fix.

`pr-check: none`: main's verdict lives in a shared ledger,
`<git-common-dir>/agent-builds/main-health.jsonl` (every worktree sees
it, next to the build ledger), read and written only by
`MH=~/.agents/skills/ship-to-trunk/scripts/main_health.py` (workflow:
PROFILE `- main-check:`, else the `- release:` workflow; `python3 $MH -h`).

- **Workers never wait on main.** A main run takes up to half an hour and
  ends green almost every time; a worker that waits idles. After step 8 the
  worker reports and stops: no `gh run watch`, `gh run view` or `gh run
  list`.
- **One watcher per orchestrator** (each runs its own; the ledger dedupes
  runs): `python3 $MH watch --who <run slug>` as one background bash job
  (async, costs no turns), started after the run's first merge and again
  after any later merge, the fix PR included, when none is running. It
  exits once no main run is pending: 0 green, 3 red, printing `main red at
  <sha> (run <id>), range <last green>..<red sha>`. `status` reads only the
  ledger, so it stays red until a watcher records the next green run.
- **Red → every merge stops except the fix.** `status` exits 3: the worker
  still runs review, suite, push and `gh pr create`, then `main_health.py
  hold --pr <n> --who <id>`, keeps its worktree, reports `held, main red`
  and stops with the PR open.
- **Culprit**: `gh run view <id> --log-failed` → failing Gradle task →
  module; each commit in the range → `git diff --name-only <sha>^ <sha>`
  → modules. One match is the culprit. Several (cancelled runs make one red
  run cover many merges) → the most likely first, the next if main stays
  red. Never bisect on CI.
- **Owner**: the orchestrator whose merge is the culprit runs
  `main_health.py claim --who <id> --culprit <sha|#PR>`, then opens the fix
  PR: `git revert` of the culprit squash commit (the ticket reopens), or a
  fix forward when it is one obvious line; record it with `claim … --fix-pr
  <n>`. The fix PR merges despite `status` exit 3, never skipping the local
  suite or fast review.
  Everyone else reads the claim in `status` and opens no second fix. A
  claim idle for 30 min with no merged fix → `claim --takeover` (refused
  while a merged fix has no red run after it yet).
- **Green again**: the watcher records the green run, which closes the
  incident. `main_health.py held` lists the held PRs still open; the
  orchestrator merges each from its kept worktree after `status` is green,
  under the step-5 rerun rule (main moved: related → rebase + suite again,
  force-push; unrelated → merge as is), then removes the worktree.

## Release workflows on push

Repos whose workflow publishes on every push to main (tag per version,
skipped when the tag exists): slices never bump the version, so they
publish nothing. The flip PR bumps the version and is the release.
