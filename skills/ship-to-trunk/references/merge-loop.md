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

**Orchestrator — the merge lane**: one lane per repository, shared by
every session that works in it. Each orchestrator enqueues its ready
tickets and follows them with `merge_lane.py wait` as one async
background bash job (no turns spent), so it keeps dispatching and
answering while suites run. The lane lives in
`<git-common-dir>/agent-builds/lane/` (queue, rewritten under a flock
on `queue.jsonl.flock` so concurrent `enqueue`s never drop an entry,
lock, two scratch worktrees, check logs, PR bodies, `land.log`), so
every worktree of the repository finds the same one. The scratch
worktrees sit in
`.git/agent-builds/lane/wt` of the main checkout: exclude that path from
IDE indexing and backups. Each check gets the main checkout's
`local.properties` copied into its scratch worktree, so the lane's
environment needs that file or `ANDROID_HOME` for the Android SDK.

```bash
ML=~/.agents/skills/ship-to-trunk/scripts/merge_lane.py   # python3 $ML -h: queue fields, results, exit codes
python3 $ML enqueue --who <run slug> --nn <NN> --worktree ../<repo>-wt/<NN> --title "<conventional title>" \
  --body-file .scratch/<slug>/pr-<NN>.md [--no-merge] [--red-fix <culprit>]   # when a worker reports ready
python3 $ML wait --who <run slug> --nn <NN>   # right after, async: one wait per ready ticket, to its final result
```

`wait` starts `land` whenever no `land` holds the lane (one `land` lands
every session's tickets), prints each result line of its own tickets and
the ledger lines that name them, and exits 0 when all merged, 1 when any
ended otherwise, 3 when main is red (`main red; lane paused` plus
`main_health.py status`). Start one `wait` per ticket that reports ready;
several at once are fine: each follows only its tickets, and the lane
runs one `land` at a time. `land --who <run slug> [--max 5]` runs the
lane once in the foreground (exit 4 `lane busy` while another `land`
holds it). A `land` holds a flock on `lane/land.lock`, which the kernel
drops however the `land` dies; SIGTERM also stops the checks it started
and logs them `discarded`. The process group of every running check is
recorded in `lane/check-groups` (leader pid and start time): a `land`
killed outright (SIGKILL) leaves its checks running, and the next `land`
kills them right after it takes the lock, skipping any pid whose start
time differs (a reused pid names another process).
`--queue` is gone: it exits 2 with the commands above and asks to
re-enqueue anything left in the old `.scratch/<slug>/lane/queue.jsonl`.

One `land` run takes two batches off the queue, oldest first: A (up to
`--max` tickets, default 5) and B (the next up to 5). A stacks on
`origin/main` (ticket 1 on main, ticket k on the rebased head of k-1; a
rebase conflict drops that ticket), B stacks the same way on A's top, and
both suites start at once, each in its own scratch worktree
(`lane/wt/0`, `lane/wt/1`, reset between checks, ignored build output
kept) through `build-slot`, so the two remote build slots run them side
by side. A merges first, then B (Two batches below). The instant-merge
order per ticket, after its suite:

```bash
git fetch origin && git rebase --onto origin/main <tested head of k-1>   # lands the ticket on the main the squash of k-1 produced
python3 ~/.agents/skills/ship-to-trunk/scripts/main_health.py status   # red (exit 3) → the rest stay queued, no PR opened
git push -u --force-with-lease origin HEAD
gh pr create --base main --title "<conventional title>" --body-file <body>   # an OPEN PR for the branch is reused (gh pr view <branch>, read before the push: the ticket's own CLOSED PR → result closed, nothing pushed; a CLOSED PR closed before the enqueue and not on the ticket's head is an older PR of a reused branch name → ignored, a new PR is opened)
gh pr merge <n> --squash --match-head-commit <sha>   # immediately; <n> always passed, never --delete-branch; a transient refusal (not mergeable yet; HTTP 5xx; network) is retried up to 3 times 5 s apart; "Base branch was modified" → fetch: origin/main still has the tree the ticket was rebased on (GitHub settling after the batch's previous squash) → the same retry, else main moved under the merge → rebase, rerun rule, push and merge again for this ticket and the rest (up to 3 times; never a blind retry); "Head branch was modified" (the PR head is not the pushed sha) is never retried; non-zero exit → gh pr view <n> decides (MERGED = merged; else a sha race left over → requeued, anything else → refused); <sha> = the head just pushed: the ticket rebased onto main with the previous squash, the tree the suite ran on
# never watch main after the merge (no gh run watch/view/list): the orchestrator's watcher does
git push origin --delete <branch> && git worktree remove ../<repo>-wt/<NN> && git branch -D <branch>
```

The PR exists only right before its merge: open about a minute, never a
waiting room.

Results (one JSON line per ticket, `{"who", "nn", "result", …}`) and what
the orchestrator does next:

- **merged** (`slice: <NN> PR #<n> merged @ <sha7>` with the squash commit
  on main, or `merged (main sha unresolved; tested @ <sha7>)` when gh
  reports no merge commit; plus the `merge: … suite green tested @ <sha7>`
  ledger lines, which name the tested stack, never a main commit; the result
  line carries both as `sha` (null when unresolved) and `tested`): close the
  ticket, start the `main_health.py watch` job when none is running.
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
- **requeued**: transient only (main moved, main red, a merge race on
  GitHub, stacked after a ticket that did not merge, `stacked on a red
  batch`: it was in B when A went red). Nothing to do: the ticket is
  still queued and `wait` starts the next `land` for it. A ticket stays
  `claimed` from `ready` until merged.
- **refused** (+ `reason`, gh's stderr; `pr` when it exists): `gh pr
  create` failed or `gh pr merge` refused the PR (a required review, a
  ruleset, or a transient refusal that outlived 3 retries 5 s apart).
  Final: fix the cause the reason names, then `enqueue` again; the open PR
  is reused. Tickets stacked after it come back `requeued`.
- **closed** (+ `pr`, `url`): the user closed the ticket's PR. Final: the
  lane never pushes to it or opens another. Ask the user, then drop the
  ticket, or reopen the PR and `enqueue` again. The ticket's PR is one
  closed at or after the `enqueue`, or one whose head is the ticket's
  head; an older CLOSED PR of a reused branch name is ignored and a new
  PR is opened. A PR the user closed before the enqueue, on another head,
  gets a new PR too: an enqueue after a close is a new request.
- **stuck**: the ticket itself caused 6 requeues already (`requeues` in
  the queue entry: main moved under its check, the head/base race on
  GitHub, main red); the 7th ends it. A `stacked on …` requeue (a ticket
  below it or batch A went red, conflicted or was refused) never counts.
  Read the reason (the last requeue's), fix what keeps it moving, then
  `enqueue` again (the count starts over).
- **invalid**: the worktree is gone, holds uncommitted changes, or its HEAD
  moved after `enqueue` (a worker still running). Nothing touched; the
  worker finishes, then the ticket is enqueued again. Known risk: a `land`
  killed or crashed between rebasing a ticket and logging its result
  leaves the worktree HEAD moved, so the next run reports it `invalid`;
  `enqueue` it again.
- **exit 3** (`main red; lane paused`): wait for the watcher to record
  green, then `wait` again; only a `--red-fix` ticket lands meanwhile.

### Two batches, two slots

| State | A | B (stacked on A's top) |
|---|---|---|
| Both suites running | runs in `wt/0` | runs in `wt/1` |
| A red (any round, or a red compile between merges) | bisects as alone; its green prefix merges | check killed, logged `discarded`; every ticket `requeued` ("stacked on a red batch"); no round counted |
| A done, nothing red | merged, refused, closed, or requeued by its own rules | its check finishes (red → bisect within B); then `tree(origin/main) == tree(A's top)` → B's green run stands and merges; else the rerun rule below over `git diff --name-only <A's top> origin/main`: rerun = restack on main + suite (B's own 3 rounds), compile = restack + compile, push = merge |
| A requeued ("main keeps moving") | requeued | the same tree compare: main lacks A, so the diff names A's changes too |
| Main red at a merge | `main_health.py status` before each merge: the rest `requeued` ("main red") | the same |

A `--no-merge` or `--red-fix` ticket is a batch of its own; B never
stacks on a `--no-merge` A (it never merges), and on red main only the
`--red-fix` ticket runs.

- `<suite>`: the first backticked command in the `pr-check: none` comment
  that starts with a script in the repo (`./gradlew …`); none written →
  assemble debug + unit `runner:` + `structure:` (when set).
- `<e2e>` (optional): PROFILE `- e2e: <command>   # when: <module
  globs>`, for a slow end-to-end tier the user took off the every-merge
  path. `when:` is a comma-separated list (`app, feature:*:api`; globs may
  be backticked, prose after the list is ignored); `none` or `off` as the
  command means no key. When the batch's commits touch a module that
  matches a glob (`fnmatch` on names like `feature:play`), or the shared
  build setup (root build and settings scripts, `gradle.properties`,
  `gradle/`, `build-logic/`), the lane runs `<suite> && <e2e>` as one check
  in the same build slot: a red e2e is a red suite, bisect included (each
  half reuses the batch's `due` and `trigger`). Only modules the batch
  touches directly count, not their dependents: the module that runs the
  tier depends on everything. No `when:` or no module graph → every suite.
  Each suite round recomputes it on its own stack (a rerun after main moved
  may differ); compile checks never run it. Main's post-merge workflow
  keeps running the tier on every push, so it still covers the batches
  that skip it.
- **Batch guarantee.** Each suite tests only its batch top; B's tests A's
  top plus B. The intermediate main states (after the 1st, 2nd, … merge)
  are never tested on their own. Accepted, because tickets in the queue
  are independent (the frontier dispatches only tickets whose parents are
  merged), main's post-merge workflow tests the newest push, and a red
  main still stops everything. A requeued A ticket can land after B's:
  independent tickets, so order across batches does not matter.
- **Throughput.** At the 4.0 min suite median one slot runs about 15
  suites an hour; two pipelined batches about 30, each covering up to 5
  tickets, for every session of the repository together. A red batch
  costs about log2(batch) extra suites, plus B's suite when B sat on it.
- Main moved during the suite or between merges → judge `git diff
  --name-only <base>..origin/main` (`<base>` = the main sha the suite ran
  on, or A's top for B) against the batch's changes, mapped to build modules
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
  Ledger the call: `merge: <who>/<NN>,… main moved <k> commits —
  rerun|compile|push (<modules>)` (`<k>`: commits neither batch merged).
- Merging needs the authority table to let the agent do it (dark /
  non-behavioral slice + consent line). Otherwise the orchestrator
  enqueues with `--no-merge` and the ticket ends `waiting_user`.
- `merge_lane.py` applies this mechanically: modules come from
  `include(...)` in `settings.gradle.kts`, project dependencies from
  `project(":x")` and `projects.x` in each module's build file. After 3
  full reruns of main moving a batch is requeued ("main keeps moving");
  compile checks never count, and B counts its own rounds.
- The PR body is written once by the worker, after the fast review
  (`open-pr` slice template). The lane fills its `**check:**` line:
  `local suite green on batch top <sha7> (tickets <who>/<NN>,<who>/<NN>)[,
  then compile green after main moved]; no PR CI by design`.

## Lane events

`merge_lane.py` appends one JSON line per event to
`<git-common-dir>/agent-builds/lane-events.jsonl` (next to
`main-health.jsonl`, shared by every worktree, never committed, written
under a flock on `lane-events.flock`). It answers how often main
moving forces a rerun, how many tickets one suite covers, and which
module's tests cost the suite time; `wait` reads its results from it.
Logging never changes a decision or the exit code: an IO error prints
`merge_lane: event log: …` on stderr and the lane goes on (a `wait`
whose ticket left the queue without a logged result then exits 1).
Every line has `ts` (UTC), `who` (the run slug of the `land` or
`enqueue` that wrote it; a `ticket` line names the ticket's own) and
`event`. Tickets are labelled `<who>/<NN>`.

- `enqueue`: one per enqueue. `nn`, `id` (the queue entry's; `wait`
  finds its tickets by it).
- `suite` / `compile`: one per suite run or compile check. `pipe` (`A`|
  `B`), `batch` (labels of the stack it ran on), `batch_size`, `round`
  (restack round of this batch, 1 first; compile rounds count), `phase`
  (`stack`, `bisect` for a red batch's binary search, `merge` for a check
  between merges), `modules` (modules the batch's commits touch; `[]`
  without a module graph), `base` and `top` (sha7 of the commit it stacked
  on, main or A's top, and of the head it ran on), `result`
  (`green`|`red`|`discarded`: B dropped because A went red), `wall_s`,
  `module_test_s` (`{module: seconds}`: JUnit `testsuite@time` summed per
  module from `<module>/build/test-results/**/*.xml` written since the
  run started, so earlier runs' files are ignored; `{}` when none; on a
  run where e2e is due, the tier's module includes the e2e XML), `e2e`
  (null without an `e2e:` key and on compile checks; else `due` (the step
  was appended to this round's suite), `trigger` (the batch modules that
  matched `when:`, all of them without one, plus `shared build setup` when
  the batch touched it), `ran` (the log has the `merge_lane: e2e start`
  marker; false when the suite went red first) and `wall_s` (from the
  `merge_lane: e2e rc=<n> wall_s=<s>` marker, else null)).
- `ticket`: one per result line. `nn`, `id`, `pipe` (null for `invalid`),
  `result` (the names above), `reason` (the requeued, refused, stuck or
  invalid reason verbatim, else null), `pr` (null before a PR exists), `line` (the
  result line as printed).
- `main_moved`: one per main-moved verdict. `pipe`, `batch`, `phase`
  (`stack`|`merge`), `commits`, `decision` (`rerun`|`compile`|`push`, or
  `requeue` where a rerun verdict requeues instead: past the 3 full
  rounds, or between merges), `reason` (the modules label of the ledger
  line, `+shared build setup` etc. included).
- `ledger`: one per `merge:`, `slice:` or claim line `land` prints.
  `line`, `ids` (the tickets it names).

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
  `status` exit 3 and exits 3 (`main red; lane paused`), and every `wait`
  following queued tickets exits 3 with it: ready tickets wait in the
  queue with no PR open, so no `hold` is needed, and the lane stays
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
  `merge_lane.py enqueue … --red-fix <culprit>` and follows it with
  `wait`: a `red_fix` ticket lands alone even on a red main, local suite
  included. After its PR exists the lane records `main_health.py claim
  --who <id> --culprit <culprit> --fix-pr <n>` (a refused claim → result
  `claim_refused`, nothing merged) and merges despite `status` exit 3.
  A fix that does not merge (any other result) ends that `land` with
  exit 3 too, so the owner's `wait` stops on its result line instead of
  looping: act on that result as above (a `requeued` fix is still queued:
  `wait` again).
  Everyone else reads the claim in `status` and opens no second fix. A
  claim idle for 30 min with no merged fix → `claim --takeover` (refused
  while a merged fix has no red run after it yet).
- **Green again**: the watcher records the green run, which closes the
  incident. The lane resumes on the next `wait`: each orchestrator whose
  `wait` exited 3 starts it again for its queued tickets, and the first
  one starts `land`, which takes every session's queued tickets (nothing
  was held, so nothing to release). `main_health.py held`
  lists PRs still held outside the lane (`waiting_user` PRs held on red):
  the orchestrator merges each after `status` is green, under the
  main-moved verdicts.

## Release workflows on push

Repos whose workflow publishes on every push to main (tag per version,
skipped when the tag exists): slices never bump the version, so they
publish nothing. The flip PR bumps the version and is the release.
