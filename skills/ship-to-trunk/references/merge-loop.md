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
gh pr merge <n> --squash --match-head-commit <sha>   # authority: SKILL.md table; never --delete-branch (below)
git push origin --delete <slug>/<NN>-<ticket>
git worktree remove ../<repo>-wt/<NN>
```

- Branch name `<slug>/<NN>-<ticket>`: the last segment stays the build
  identity slug (`deliver`).
- `--match-head-commit` pins the reviewed sha: a push after review blocks
  the merge instead of slipping in.
- `--auto` instead of waiting: only when branch protection requires the
  check (otherwise it merges immediately). Never `--admin`.
- Never `--delete-branch` from a worktree: after merging, gh checks out
  main locally, fails with "'main' is already checked out at …" and exits
  non-zero although the PR merged. Any non-zero merge exit → `gh pr view
  <n> --json state` decides before anything is retried.
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
a chance for main to move under it). Two owners split the sequence.

**Worker** (worktree from `origin/main`): 1. TDD with touched-module tests,
local gates (runner, `structure:`, lint) green. 2. `review-change` fast
tier over `git diff origin/main...HEAD`, fix rounds until clean. 3. Write
the PR body (`open-pr` slice template) with a `**check:**` line the lane
fills. 4. `git push -u origin HEAD` (branch only), report `ready`, stop.
The worker never runs the full suite, never rebases onto main, never opens
the PR, never merges and never polls.

**Orchestrator — the merge lane**: a queue of ready tickets, landed in
batches by `merge_lane.py land` as one async background bash job (no turns
spent), so the orchestrator keeps dispatching and answering while the
suite runs.

```bash
ML=~/.agents/skills/ship-to-trunk/scripts/merge_lane.py   # python3 $ML -h: queue fields, results, exit codes
Q=.scratch/<slug>/lane/queue.jsonl
python3 $ML enqueue --queue $Q --nn <NN> --worktree ../<repo>-wt/<NN> --title "<conventional title>" \
  --body-file .scratch/<slug>/pr-<NN>.md [--no-merge] [--red-fix <culprit>]   # when a worker reports ready
python3 $ML land --queue $Q --who <run slug> [--max 4]   # async; start whenever the queue is non-empty; a second land exits 4 (lane busy)
```

One `land` run: stack up to `--max` tickets (ticket 1 on `origin/main`,
ticket k on the rebased head of k-1; a rebase conflict drops that ticket),
run one suite on the top, then merge each ticket in order. The
instant-merge order per ticket, after the suite:

```bash
git fetch origin && git rebase --onto origin/main <tested head of k-1>   # lands the ticket on the main the squash of k-1 produced
python3 ~/.agents/skills/ship-to-trunk/scripts/main_health.py status   # red (exit 3) → the rest stay queued, no PR opened
git push -u --force-with-lease origin HEAD
gh pr create --base main --title "<conventional title>" --body-file <body>   # an OPEN PR for the branch is reused (gh pr view <branch>)
gh pr merge <n> --squash --match-head-commit <sha>   # immediately; <n> always passed, never --delete-branch; non-zero exit → gh pr view <n> decides (MERGED = merged); <sha> = the head the suite ran on
# never watch main after the merge (no gh run watch/view/list): the orchestrator's watcher does
git push origin --delete <branch> && git worktree remove ../<repo>-wt/<NN> && git branch -D <branch>
```

The PR exists only right before its merge: open about a minute, never a
waiting room.

Results (one JSON line per ticket) and what the orchestrator does next:

- **merged** (`slice: <NN> PR #<n> merged @ <sha7>`, plus the `merge: …`
  ledger lines): close the ticket, start the `main_health.py watch` job
  when none is running.
- **red** (log path in the line): the ticket turned the batch suite red;
  dispatch a fix worker into the same worktree with the log path (prompt as
  `implement`/references/dispatch.md, hard-rules block included), then
  `enqueue` again when it reports ready. Tickets stacked after it come
  back `requeued`.
- **conflict**: a worker rebases onto `origin/main` and resolves per
  Conflicts below, with the fast review of the resolution diff, then the
  ticket is enqueued again. Two tickets of one batch conflicting means they
  touch the same lines: the >~50 lines re-slice rule applies.
- **waiting_user** (`--no-merge`: unflaggable live change, flip PR): the PR
  is open after a green suite and is never merged by the lane. Ask the user
  through the ask tool (`start` § Waiting on the user). On approval:
  `main_health.py status`; green → apply the main-moved verdicts below, `gh pr
  merge <n> --squash --match-head-commit <sha>`; red →
  `main_health.py hold --pr <n> --who <id>` (Red main).
- **claim_refused**: another orchestrator holds the red-main claim; report
  it, nothing merged.
- **requeued**: nothing, the ticket is still queued and the next `land`
  takes it. A ticket stays `claimed` from `ready` until merged.
- **invalid**: the worktree is gone, holds uncommitted changes, or its HEAD
  moved after `enqueue` (a worker still running). Nothing touched; the
  worker finishes, then the ticket is enqueued again.
- **exit 3** (`main red; lane paused`): wait for the watcher to record
  green; only a `--red-fix` ticket lands meanwhile.
- **exit 4** (`lane busy`): another `land` holds the lane; nothing touched.
  Start no second job; the running one reports when it ends.

- `<suite>`: the first backticked command in the `pr-check: none` comment
  that starts with a script in the repo (`./gradlew …`); none written →
  assemble debug + unit `runner:` + `structure:` (when set).
- **Batch guarantee.** The suite tests only the batch top. The intermediate
  main states (after the 1st, 2nd, … merge of a batch) are never tested on
  their own. Accepted, because tickets in one queue are independent (the
  frontier dispatches only tickets whose parents are merged), main's
  post-merge workflow tests the newest push, and a red main still stops
  everything.
- **Throughput.** One suite covers up to `--max` tickets; at a ~5 min suite
  and batches of 4 the ceiling is about 48 merges an hour per
  orchestrator, minus about log2(batch) extra suites per red batch.
- Main moved during the suite or between merges → judge `git diff
  --name-only <base>..origin/main` (`<base>` = the main sha the suite ran
  on) against the batch's changes, mapped to build modules
  (`./gradlew <module>:dependencies` lists them as `project :x`):
  - **rerun** (restack + suite again): main changed a module the batch
    changed, the shared build setup (`build-logic/`, `gradle/`, root
    build/settings/properties files) or the `structure:` rules module. No
    module graph (single-module repo, build files unreadable) → rerun.
  - **compile** (main changed a dependency or dependent of a batch module,
    nothing else): restack, compile
    `:<m>:compileDebugKotlin :<m>:compileDebugUnitTestKotlin` for each
    batch module and each main-changed module depending on one. This
    catches an API break in a module the ticket never touched. Green →
    push; red → `red`, as a suite. No `./gradlew`, or `--dry-run` rejects a
    task → rerun.
  - **push** otherwise, without rebasing. Two modules that only share a
    consumer (both feed `:app`) are unrelated. The squash merge lands on
    the newer main; main's post-merge workflow is the net, and a red main
    stops merges (Red main below).
  - A textual conflict at merge (`gh pr merge` refuses) → rebase,
    Conflicts below, suite again.
  Ledger the call: `merge: <NN> main moved <k> commits —
  rerun|compile|push (<modules>)`.
- Merging needs the authority table to let the agent do it (dark /
  non-behavioral slice + consent line). Otherwise the orchestrator
  enqueues with `--no-merge` and the ticket ends `waiting_user`.
- `merge_lane.py` applies this mechanically: modules come from
  `include(...)` in `settings.gradle.kts`, project dependencies from
  `project(":x")` and `projects.x` in each module's build file. After 3
  full reruns of main moving the batch is requeued ("main keeps moving")
  and the lane exits 1; compile checks never count.
- The PR body is written once by the worker, after the fast review
  (`open-pr` slice template). The lane fills its `**check:**` line:
  `local suite green on batch top <sha7> (tickets <NN,NN>)[, then compile
  green after main moved]; no PR CI by design`.

## Lane events

`merge_lane.py land` appends one JSON line per event to
`<git-common-dir>/agent-builds/lane-events.jsonl` (next to
`main-health.jsonl`, shared by every worktree, never committed, written
under a mkdir lock like main_health's ledger). It answers how often main
moving forces a rerun, how many tickets one suite covers, and which
module's tests cost the suite time. Logging never changes a decision or
the exit code: an IO error prints `merge_lane: event log: …` on stderr
and the lane goes on.
Every line has `ts` (UTC), `who` (the `--who` run slug) and `event`.

- `suite` / `compile`: one per suite run or compile check. `batch` (ticket
  NNs of the stack it ran on), `batch_size`, `round` (restack round of this
  `land`, 1 first; compile rounds count), `phase` (`stack`, `bisect` for a
  red batch's binary search, `merge` for a check between merges),
  `modules` (modules the batch's commits touch; `[]` without a module
  graph), `base` and `top` (sha7 of the main it stacked on and of the
  head it ran on), `result` (`green`|`red`), `wall_s`, `module_test_s`
  (`{module: seconds}`: JUnit `testsuite@time` summed per module from
  `<module>/build/test-results/**/*.xml` written since the run started,
  so earlier runs' files are ignored; `{}` when none).
- `ticket`: one per result line. `nn`, `result` (the names above),
  `reason` (the requeue or invalid reason verbatim, else null), `pr`
  (null before a PR exists).
- `main_moved`: one per main-moved verdict. `batch`, `phase` (`stack`|
  `merge`), `commits`, `decision` (`rerun`|`compile`|`push`, or `requeue`
  where a rerun verdict requeues instead: past the 3 full rounds, or
  between merges), `reason` (the modules label of the ledger line,
  `+shared build setup` etc. included).

Rerun rate: `main_moved` lines with `decision: rerun` per `land`.
Tickets per suite: `batch_size` of `suite` lines with `phase: stack`.

## Main moved while the PR waits

`gh pr update-branch <n> --rebase`, wait for the check again, then merge
with the new head sha. `pr-check: none`: applies only to a `waiting_user`
PR — same verdicts (rerun → rebase + suite; compile → rebase + compile;
push → merge as is), by hand. Rebasing is the slice author's job (under
`pr-check: none` the lane's), never the next ticket's.

## Conflicts

1. Rebase locally, resolve, re-run the gates, force-push with
   `--force-with-lease` (the slice branch only — never main).
2. Resolution keeps both intents. Unsure which side wins → stop; a worker
   reports BLOCKED, the orchestrator asks the user (ask tool);
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
  ends green almost every time; a worker that waits idles. Workers push
  the branch, report `ready` and stop; the lane's last step is the last
  step anyone takes on a merge: no `gh run watch`, `gh run view` or `gh run
  list`.
- **One watcher per orchestrator** (each runs its own; the ledger dedupes
  runs): `python3 $MH watch --who <run slug>` as one background bash job
  (async, costs no turns), started after the run's first merge and again
  after any later merge, the fix PR included, when none is running. It
  exits once no main run is pending: 0 green, 3 red, printing `main red at
  <sha> (run <id>), range <last green>..<red sha>; cause <hint>: <first
  failing tests>`. `status` reads only the ledger, so it stays red until a
  watcher records the next green run.
- **Red → every merge stops except the fix.** `merge_lane.py land` sees
  `status` exit 3 and exits 3 (`main red; lane paused`): ready tickets wait
  in the queue with no PR open, so no `hold` is needed, and the lane stays
  paused until the watcher records green. Workers are not involved in red
  main at all. `main_health.py hold`/`held` stay for PRs that wait outside
  the lane: a `waiting_user` PR whose approval arrives while main is red is
  held (`hold --pr <n> --who <id>`) instead of merged.
- **Cause**: each red run's ledger record carries `failed_tests`
  (`Class.method`, else the failed Gradle task paths; at most 50) and
  `cause_hint`, both read from `gh run view <id> --log-failed`: `test`,
  `compile`, `download` (Robolectric android-all or a Gradle artifact
  fetch), `infra` (no job started, runner lost) or `unknown` (no log; read
  it yourself). `download` and `infra` name no commit: rerun the failed
  jobs (`gh run rerun <id> --failed`) and start a watcher.
- **Culprit** (`test`, `compile`, `unknown`): failing test or task →
  module; each commit in the range → `git diff --name-only <sha>^ <sha>`
  → modules. One match is the culprit. Several (cancelled runs make one red
  run cover many merges) → the most likely first, the next if main stays
  red. Never bisect on CI.
- **Flaky test → quarantine in the same incident.** A test that fails on
  main and passes on rerun with no code change is flaky, not a culprit.
  Measure it first with `tdd`'s `flake_rate.py` (`tdd` § Flakes). The fix
  PR marks it `@Ignore("quarantine #<ticket> until <YYYY-MM-DD>")`, at
  most 48 h out, with a filed ticket and a named owner who fixes or deletes
  the test. `status` and `watch` print `quarantine expired: <Class> #<N>
  since <date>` for each past date in `src/test` or `src/androidTest`
  Kotlin; exit codes stay unchanged.
- **Owner**: the orchestrator whose merge is the culprit prepares the fix
  in its own worktree: `git revert` of the culprit squash commit (the
  ticket reopens), or a fix forward when it is one obvious line, then the
  fast review of the revert or fix. It enqueues the ticket with
  `merge_lane.py enqueue … --red-fix <culprit>` and starts `land`: a
  `red_fix` ticket lands alone even on a red main, local suite included.
  After its PR exists the lane records `main_health.py claim --who <id>
  --culprit <culprit> --fix-pr <n>` (a refused claim → result
  `claim_refused`, nothing merged) and merges despite `status` exit 3.
  Everyone else reads the claim in `status` and opens no second fix. A
  claim idle for 30 min with no merged fix → `claim --takeover` (refused
  while a merged fix has no red run after it yet).
- **Green again**: the watcher records the green run, which closes the
  incident. The lane resumes by itself: the next `land` takes the queued
  tickets (nothing was held, so nothing to release). `main_health.py held`
  lists PRs still held outside the lane (`waiting_user` PRs held on red):
  the orchestrator merges each after `status` is green, under the
  main-moved verdicts.

## Release workflows on push

Repos whose workflow publishes on every push to main (tag per version,
skipped when the tag exists): slices never bump the version, so they
publish nothing. The flip PR bumps the version and is the release.
