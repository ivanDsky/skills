#!/usr/bin/env python3
"""Merge lane for trunk runs with `pr-check: none`: land ready tickets in batches.

One lane per repository, shared by every session and worktree of it, in
`<git-common-dir>/agent-builds/lane/`. Orchestrators enqueue their ready
tickets, then wait for them; whichever `wait` finds the lane idle starts one
`land`. A `land` holds an exclusive flock on `lane/land.lock` for its whole
run (the kernel releases it however the land dies; the file names the
holder's pid for messages only); a second `land` exits 4 without touching
anything. SIGTERM stops a `land` and every check it started (each logged
`discarded`). Each check runs in its own process group, recorded in
`lane/check-groups` (leader pid and start time) while it runs; a `land` that
takes the lock first kills the groups on that record whose leader still has
the recorded start time (the checks of a SIGKILLed land; a reused pid is
spared), then clears it. Workers never run the lane: they push the branch and
report ready; the orchestrator enqueues the ticket.

After a merge a `land` starts `main_health.py watch` detached (`watch: started
pid <n>, log <lane>/main-health-watch.log`) unless the pidfile in agent-builds/
names a live one (`watch: running pid <n>`). The watcher outlives the `land`:
no SIGTERM, stop or kill_orphans touches it.

  merge_lane.py enqueue --who <run slug> --nn <NN> --worktree <path>
                        --title "<conventional title>" --body-file <f>
                        [--no-merge] [--red-fix <sha|#PR>]
  merge_lane.py wait    --who <run slug> --nn <NN>... [--max 5]
  merge_lane.py land    --who <run slug> [--max 5]

Queue: `lane/queue.jsonl`, one JSON object per ready ticket, edited only under
an exclusive flock on `queue.jsonl.flock` (written to a tmp file, then renamed
over it). A ticket is (who, nn): `who` is the run slug of the session that
owns it. `enqueue` fills the rest from the worktree, gives the entry a fresh
`id`, and replaces an entry with the same who and nn (a ticket that re-enters
after a fix):
  {"who","nn","id","enqueued","worktree","branch","head","base","title",
   "body_file","no_merge":false,"red_fix":null,"full":false,"lane_head"?,
   "requeues"?}
`enqueued` is the UTC time of the enqueue (`2026-01-31T12:00:00Z`). `base` is
the ticket's merge-base with origin/main; `base..head` is its own commits,
restacked from scratch on every lane run. `no_merge: true` marks a PR only
the user may merge (unflaggable live change, flip PR). `red_fix` (culprit
sha|#PR) marks the fix PR of a red main. `full: true` (`--full`) makes its
batch run the full suite instead of the affected check (release PRs, a fix
after an unexpected red main). `lane_head` is the worktree HEAD the
lane left after rebasing a requeued ticket; `requeues` counts the requeues
the ticket caused itself (main moved or red, main keeps moving, GitHub's sha
race), not those for a ticket or batch it was stacked on ("stacked on ...").
`enqueue` logs an `enqueue` event (nn, id) before it writes the queue.

`wait` maps each NN to the id of the last `enqueue` event of <who> for it and
reads the lane events from the start of the file. It prints the result line
of each of its tickets and every ledger line that names one of them. While a
ticket of its own is still queued and no `land` holds the lane, it starts
one, detached (output appended to `lane/land.log`). It returns once every
ticket has a final result: exit 0 when all merged, 1 otherwise, 3 when a
`land` found main red (`main red; lane paused` and `main_health.py status`).
A ticket that left the queue without a logged result, or a `land` that exits
without any ticket result while a ticket of its own is still queued, fails
the wait (exit 1, one stderr line).

`land` output: one JSON line per ticket touched, {"who","nn","result",...},
plus plain ledger lines (`merge: ...`, `slice: ...`; lines not starting with
`{`). result is one of
  merged        (+ pr, sha, tested): sha is the squash commit on main (sha7;
                null when gh reports no merge commit), tested the PR head
                the lane pushed and merged (sha7)
  conflict      (+ files): rebase conflict, rebase aborted
  red           (+ log): the ticket turned the suite red
  waiting_user  (+ url): `no_merge` ticket, PR open, suite green
  claim_refused (+ reason): `red_fix` claim refused, nothing merged
  refused       (+ reason[, pr]): `gh pr create` failed, or `gh pr merge`
                refused the PR (reason: gh's stderr) for any cause but a
                head or base sha that moved on GitHub (that one requeues);
                a transient refusal is retried first (step 7.5)
  closed        (+ pr, url): the ticket's PR was closed (by the user); the
                lane never pushes to it or opens another
  invalid       (+ reason): worktree missing, holding uncommitted changes, or
                its HEAD is neither `head` nor `lane_head` (moved since enqueue)
  requeued      (+ reason): stays in the queue, in order
  stuck         (+ reason): the ticket already caused REQUEUE_CAP (6)
                requeues; reason is the requeue reason it would have had
Finished tickets (everything but requeued) leave the queue. Tickets stacked
after a red, refused or closed ticket are requeued ("stacked on a red |
refused | closed ticket").
Exit 0 when every ticket of both batches merged, 1 otherwise, 3 when main was
red at the start and the queue holds no `red_fix` ticket (nothing touched) or
the `red_fix` ticket did not merge, 4 when another `land` holds the lane
(nothing touched).

Sequence:
 1. `main_health.py status`. Red -> `main red; lane paused`, exit 3: the
    queue is the hold, no PR is opened. Red with a `red_fix` ticket queued
    -> that ticket lands alone, no batch B (steps 3-7; 7.1 skipped; after its
    PR exists `main_health.py claim --who <its who> --culprit <x> --fix-pr
    <n>`, refused -> claim_refused; then it merges despite red). The fix not
    merged (any other result) -> `main red; lane paused`, exit 3.
 2. Batches: A is the queue head, up to --max (default 5), stopping before
    the first `no_merge` or `red_fix` ticket; such a ticket at the head lands
    alone (a `no_merge` one ends with its PR open: waiting_user, no merge).
    B is the next batch after A by the same rule.
 3. Stack: `git fetch origin`; ticket 1 of A is rebased onto origin/main,
    ticket k onto the rebased head of k-1; ticket 1 of B onto A's top (onto
    origin/main when A is a `no_merge` ticket). Conflict at k: abort, result
    conflict, the next ticket stacks on k-1.
 4. One check per batch, both started at once, each in its own scratch
    worktree (`lane/wt/0` for A, `lane/wt/1` for B) detached at the batch
    top and reset before every use (`checkout -f`, `clean -fd`; ignored
    build output stays), with the main checkout's `local.properties` copied
    in when it has one, through `build-slot` when on PATH. The check is the
    affected check when PROFILE has `- affected-check: <cmd>` (see "Affected
    check" below), else the suite: the command in PROFILE's `pr-check: none`
    comment, else debug + unit `runner:` + `structure:`; log
    `lane/logs/lane-<NN-NN>-<sha7>.log` (`...-compile.log` for a compile
    check, step 6). PROFILE `- e2e: <cmd>
    # when: <module globs>` (a comma-separated list, e.g. `app,
    feature:*:api`; `none`/`off` = no key): when the batch's commits touch a
    matching module directly (no dependency closure) or the shared build
    setup (no `when:`, or no module graph: every suite), the check is
    `<suite> && <cmd>` in the same run and slot, with the marker lines
    `merge_lane: e2e start` and `merge_lane: e2e rc=<n> wall_s=<s>` in the
    log. A red e2e is a red suite (bisect included); compile checks never
    run it.
 5. Red batch: binary search over prefix length (one suite or compile check
    per step on that prefix's top head, no extra rebases). The first ticket
    that turns the prefix red gets `red`; the green prefix proceeds; tickets
    after it are requeued ("stacked on a red ticket"). About 1 + log2(batch)
    runs. A red anywhere in A (a check or a compile between merges) -> B's
    check is killed and all of B is requeued ("stacked on a red batch").
 6. Main check once a batch is green: `git fetch origin`; main's tree equals
    the tree the batch was stacked on -> merge (for B: A merged all of its
    tickets and nothing else landed). Otherwise the rerun rule (below) over
    `git diff --name-only <stacked-on> origin/main`. `rerun` -> back to 3 on
    the new origin/main with the full suite, at most 3 such rounds per batch,
    then the batch is requeued ("main keeps moving"). `compile` -> back to 3
    on the new origin/main, but the check is the compile command (a red one
    bisects like a red suite); compile rounds never count toward the 3.
    `push` -> merge. A restack takes only the green tickets: a red ticket
    stays red, its followers stay requeued.
 7. Merge A in order, then B, k = 1..n: 7.1 `main_health.py status`, red ->
    the rest requeued ("main red"). 7.2 `git fetch origin`,
    `git rebase --onto origin/main <tested head of k-1>` (for k = 1 the
    commit the batch was stacked on); the new head's tree must equal k's
    tested tree. 7.3 Tree differs -> main moved under the batch: rerun rule
    over the outside commits against tickets k..n; `rerun` -> k..n requeued
    ("main moved: related"); `compile` -> compile check on k's rebased head,
    red -> k gets `red` and k+1..n are requeued ("stacked on a red ticket").
    7.4 `gh pr view <branch>`: CLOSED and the ticket's own (closed at or
    after `enqueued`, or its head is `head` or `lane_head`) -> `closed`,
    k+1..n requeued ("stacked on a closed ticket"), nothing pushed; any
    other CLOSED PR is an older one of a reused branch name and is ignored.
    Push `--force-with-lease`; reuse the OPEN PR, else `gh pr create` (body
    check line: `local suite|affected check green on batch top <sha7>
    (tickets <who>/<NN>,...)[, then compile green after main moved]; no PR CI by
    design`); create fails -> `refused`.
    7.5 `gh pr merge <n> --squash --match-head-commit <sha>` (always with the
    PR number, never `--delete-branch`: gh would check out main locally);
    non-zero exit -> `gh pr view <n>` decides: MERGED counts as merged. A
    transient refusal ("not mergeable", "mergeable state", "try again", HTTP
    5xx, a network error) is retried up to 3 times, 5 s apart. "Base branch
    was modified": fetch; origin/main still has the tree k was rebased on
    (GitHub settling after the batch's previous squash) -> the same retry;
    else main moved under the merge -> 7.2-7.5 again for k on the new main,
    up to 3 times, never a blind retry. "Head branch was modified" (the PR
    head is not the pushed sha) is never retried. A sha race left after that
    requeues k..n; anything else, or the last retry's error, is `refused`
    with k+1..n requeued ("stacked on a refused ticket"). 7.6 delete the remote
    branch, `git worktree remove`, delete the local branch.
 8. Ledger lines, tickets named <who>/<NN>: `merge: batch <labels> suite|affected
    green tested @ <sha7>[, compile green tested @ <sha7>] (<s> suites[,
    <c> compiles])` (the tested stack, not main), each rerun decision
    `merge: <labels> main moved <k> commits - rerun|compile|push (<modules>)`
    (k counts outside commits only), and one `slice: <NN> PR #<n> merged @
    <sha7>` per merge (the squash commit on main, from `gh pr view <n> --json
    mergeCommit`; `slice: <NN> PR #<n> merged (main sha unresolved; tested @
    <sha7>)` when gh reports none), before its result line.
 9. Lane events (`EventLog`): one JSON line per enqueue, suite or compile
    check, ticket result, main-moved decision and ledger line, appended to
    `<git-common-dir>/agent-builds/lane-events.jsonl` (main_health's ledger
    dir) under an exclusive flock on `lane-events.flock`. Fields:
    references/merge-loop.md § Lane events.
    Logging never changes a decision or the exit code: an IO error is one
    `merge_lane: event log: ...` line on stderr (`wait` reads this log, so a
    wait on a broken log ends in "left the queue without a result").

Docs-only batches skip the suite. When every file of a suite round's diff
(`git diff --name-only --no-renames <stacked-on> <batch top>`: both paths of
a rename, deletions included) matches PROFILE `- lane docs-only: <glob>, ...`
(default `docs/**, *.md, PROFILE*.md`; a glob without `/` matches the file
name at any depth, `**` spans directories; an empty value or `none` turns
skipping off), no suite runs: the tickets are still stacked and rebased
(conflicts still give `conflict`) and the per-merge tree check still runs, and
the ledger line is `merge: batch <labels> suite skipped (docs only) @ <sha7>`.
The PR check line then says `local suite skipped (docs only)`. A `no_merge`
ticket follows the rule (its PR opens untested, which only the user merges
anyway); a batch holding a `red_fix` ticket never skips (a fix of red main
must be proved green). Main moving under a docs-only batch (steps 6 and 7.3)
is always `push`: docs cannot break main's code, and nothing of the batch
needs a suite or compile check to be re-proved.

Affected check. PROFILE `- affected-check: <cmd>   # full when: <glob>, ...`
runs only the tests the batch can break, instead of the suite. Placeholders,
filled per check from `git diff <stacked-on> <prefix top>`:
  {files}           the changed files that exist at the top (renames: the new
                    path), shell-quoted, space-separated
  {modules:<task>}  `:<m>:<task>` for each module the commits touch and each
                    module depending on one, transitively (the module graph)
The suite runs instead (scope `full`) when the batch holds a `red_fix` or
`full` ticket, the key is absent or `none`, the commits touch the shared build
setup or a file matching a `full when:` glob (docs-glob syntax), `{modules:...}`
has no module graph, or a placeholder expands to nothing. Each check
(bisect steps included) recomputes this on its own prefix; the e2e step
appends to either. Ledger and PR check line name the scope that proved the
green top: `suite green` (full) or `affected green` / `local affected check
green`. Main's post-merge workflow runs the full suite on every push: it is
the net for what the affected check did not run.

Rerun rule (mechanical), judged over the files that differ between main and
the commit the batch was stacked on, mapped to modules (from `include(...)` in
settings.gradle.kts, dependencies from `project(":x")` and `projects.x` in
the build files):
  rerun    main changed a module the batch changed, `build-logic/`, `gradle/`,
           root build/settings/properties files or the `structure:` rules
           module (any `:a:b` prefix of a `structure:` path that is a module),
           or no module graph is readable.
  compile  dependency-only overlap (one module depends on the other,
           transitively): restack, then `./gradlew` `:<m>:compileDebugKotlin
           :<m>:compileDebugUnitTestKotlin` for each batch module and each
           main-changed module that depends on one. A missing `gradlew` or a
           `--dry-run` that rejects a task (JVM-only module, flavors) -> rerun.
  push     otherwise.

The check tests only the batch top. The intermediate main states (after the
1st, 2nd, ... merge of a batch) are not tested on their own. Batches merge in
queue order, but a ticket requeued from A goes back to the queue while B may
still merge: tickets are independent by construction.
"""
import argparse
import fcntl
import fnmatch
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import time
import uuid
import xml.etree.ElementTree as ET
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

MAX_ROUNDS = 3  # check reruns per batch (main moved); compile checks are not counted
MAX_BATCH = 5  # tickets per batch
REQUEUE_CAP = 6  # requeues of one queue entry; the next one ends it `stuck`
COMPILE_TASKS = ("compileDebugKotlin", "compileDebugUnitTestKotlin")
HERE = Path(__file__).resolve().parent
SHARED_ROOT_FILES = re.compile(
    r"^(build|settings)\.gradle(\.kts)?$|^gradle\.properties$|^gradle/|^build-logic/")


def run(*cmd, cwd, check=True):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=check)


def out(*cmd, cwd):
    return run(*cmd, cwd=cwd).stdout.strip()


def fail(msg, code=1):
    print(f"merge_lane: {msg}", file=sys.stderr)
    sys.exit(code)


def profile_line(wt, key):
    """Full `- <key>: <value>   # <comment>` as (value, comment) from PROFILE.md."""
    profile = Path(wt) / "PROFILE.md"
    if not profile.exists():
        return None, None
    m = re.search(rf"^-\s*{re.escape(key)}:[ \t]*([^#\n]*?)[ \t]*(?:#[ \t]*(.*))?$",
                  profile.read_text(), re.M)
    if not m or m.group(1).startswith("<"):
        return None, None
    return m.group(1) or None, m.group(2)


DOCS_ONLY_DEFAULT = ["docs/**", "*.md", "PROFILE*.md"]


def docs_globs(wt):
    """Globs of the files that are not build inputs (PROFILE `- lane docs-only:`); [] = skipping off."""
    v, _ = profile_line(wt, "lane docs-only")
    if v is None:
        profile = Path(wt) / "PROFILE.md"
        if profile.exists() and re.search(r"^-\s*lane docs-only:[ \t]*(?:#.*)?$", profile.read_text(), re.M):
            return []  # the key is there with an explicit empty value
        return DOCS_ONLY_DEFAULT
    if v.lower() == "none":
        return []
    return [g.strip("` ") for g in v.split(",") if g.strip("` ")]


def glob_re(g):
    """Regex of a docs glob: `**` spans directories, `*` and `?` stay inside one."""
    r, i = "", 0
    while i < len(g):
        if g.startswith("**/", i):
            r, i = r + "(?:.*/)?", i + 3
        elif g.startswith("**", i):
            r, i = r + ".*", i + 2
        else:
            r += "[^/]*" if g[i] == "*" else "[^/]" if g[i] == "?" else re.escape(g[i])
            i += 1
    return re.compile(r + r"\Z")


def docs_only(wt, tickets, base, head):
    """True when the suite can be skipped: no `red_fix` ticket, and every path base..head
    touches (both sides of a rename) matches the docs globs."""
    globs = [(glob_re(g), "/" not in g) for g in docs_globs(wt)]
    if not globs or any(t.get("red_fix") for t in tickets):
        return False
    files = out("git", "diff", "--name-only", "--no-renames", base, head, cwd=wt).splitlines()
    return bool(files) and all(
        any(rx.match(f.rsplit("/", 1)[-1] if flat else f) for rx, flat in globs) for f in files)


def suite_command(wt):
    """First backticked command in the `pr-check:` comment that starts with a
    script in the repo (`./gradlew …`); prose like `pr-check` or `gh pr checks`
    is skipped. None found -> assembled from PROFILE keys."""
    _, comment = profile_line(wt, "pr-check")
    for t in re.findall(r"`([^`]+)`", comment or ""):
        first = (t.split() or [""])[0]
        if "/" in first and (Path(wt) / first).is_file():
            return t
    parts = ["./gradlew assembleDebug"]
    for key in ("runner", "structure"):
        v, _ = profile_line(wt, key)
        if v:
            parts.append(v)
    return " && ".join(parts)


FULL_WHEN = re.compile(r"\bfull when:\s*(.*)")
MODULES_TASK = re.compile(r"\{modules:([^}\s]+)\}")


def full_when_globs(comment):
    """Globs of an `affected-check:` comment's `full when:` list (comma-separated, each
    optionally backticked); prose after the list is ignored."""
    m = FULL_WHEN.search(comment or "")
    globs = []
    for item in m.group(1).split(",") if m else []:
        words = item.split()
        if not words:
            break
        globs.append(words[0].strip("`"))
        if len(words) > 1:
            break
    return [g for g in globs if g]


def dependents(deps, mods):
    """`mods` plus every module that depends on one of them, transitively."""
    return {m for m in deps if m in mods or mods & closure(deps, m)}


def check_plan(wt, tickets, base, head):
    """(command, scope, why) of a check on base..head: scope `affected` is PROFILE
    `affected-check:` with its placeholders filled; `full` is the suite, and `why`
    names what forced it."""
    suite = suite_command(wt)
    cmd, comment = profile_line(wt, "affected-check")
    cmd = (cmd or "").strip("` ")
    if not cmd or cmd.lower() in ("none", "off"):
        return suite, "full", "no affected-check"
    if any(t.get("red_fix") or t.get("full") for t in tickets):
        return suite, "full", "red_fix or full ticket"
    changed = names(wt, "--no-renames", base, head)
    globs = [(glob_re(g), "/" not in g) for g in full_when_globs(comment)]
    hit = next((f for f in changed if SHARED_ROOT_FILES.match(f) or
                any(rx.match(f.rsplit("/", 1)[-1] if flat else f) for rx, flat in globs)), None)
    if hit:
        return suite, "full", f"full when: {hit}"
    if "{files}" in cmd:
        files = names(wt, "--diff-filter=d", base, head)
        if not files:
            return suite, "full", "no files"
        cmd = cmd.replace("{files}", shlex.join(files))
    if MODULES_TASK.search(cmd):
        graph = module_graph(wt)
        if not graph:
            return suite, "full", "no module graph"
        mods = sorted(dependents(graph[1], to_modules(graph[0], changed)[0]))
        if not mods:
            return suite, "full", "no modules"
        cmd = MODULES_TASK.sub(lambda m: " ".join(f":{x}:{m.group(1)}" for x in mods), cmd)
    return cmd, "affected", None


E2E_START = re.compile(r"^merge_lane: e2e start$", re.M)
E2E_END = re.compile(r"^merge_lane: e2e rc=\d+ wall_s=(\d+)$", re.M)
# `when: <glob>, <glob>, ...`: a comma-separated list, each glob optionally backticked; prose after it is ignored.
E2E_WHEN = re.compile(r"\bwhen:\s*(`?[\w:*?\[\]-]+`?(?:\s*,\s*`?[\w:*?\[\]-]+`?)*)")
SHARED_SETUP = "shared build setup"  # e2e trigger entry for a batch that touched SHARED_ROOT_FILES


def e2e_globs(comment):
    """Module globs of an `e2e:` comment's `when:` list (a leading `:` dropped), [] without one."""
    m = E2E_WHEN.search(comment or "")
    return [g.strip("` ").lstrip(":") for g in m.group(1).split(",")] if m else []


def e2e_plan(wt, base, head):
    """PROFILE `e2e:` step for a suite on base..head: (command or None, trigger), or
    (None, None) without the key (or with `none`/`off`). The `when:` globs name the
    modules whose change makes it due (fnmatch on `feature:play` style names); only
    modules the batch touches count, not their dependents (`app` depends on
    everything). trigger = the batch modules that matched (no `when:`: all of them),
    plus SHARED_SETUP when the batch touched the shared build setup, which makes it
    due too. No `when:` or no module graph -> due on every suite."""
    cmd, comment = profile_line(wt, "e2e")
    if not cmd or cmd.lower() in ("none", "off"):
        return None, None
    globs = e2e_globs(comment)
    graph = module_graph(wt)
    if not graph:
        return cmd, []
    mods, shared = to_modules(graph[0], names(wt, base, head))
    hit = [x for x in sorted(mods) if not globs or any(fnmatch.fnmatchcase(x, g) for g in globs)]
    hit += [SHARED_SETUP] if shared else []
    return (cmd if hit or not globs else None), hit


def with_e2e(suite, e2e):
    """The suite, then the e2e step between log markers (build-slot may run it
    remotely, so the log is the only way its timing comes back)."""
    return (f"{suite} && {{ echo 'merge_lane: e2e start'; s=$SECONDS; {e2e}; r=$?; "
            f'echo "merge_lane: e2e rc=$r wall_s=$((SECONDS - s))"; exit $r; }}')


def e2e_event(plan, log):
    """The suite event's `e2e` field: null without an e2e plan, else the plan plus
    `ran` (start marker in the log) and `wall_s` (from the end marker, else null)."""
    if plan is None:
        return None
    text = Path(log).read_text(errors="replace") if plan["due"] else ""
    end = E2E_END.search(text)
    return dict(plan, ran=bool(E2E_START.search(text)), wall_s=int(end.group(1)) if end else None)


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def module_graph(wt):
    """({module: dir}, {module: set(direct deps)}) or None when unreadable."""
    settings = next((Path(wt) / n for n in ("settings.gradle.kts", "settings.gradle")
                     if (Path(wt) / n).exists()), None)
    if not settings:
        return None
    text = settings.read_text()
    mods = {}
    for inc in re.findall(r"include\s*\(([^)]*)\)", text):
        for m in re.findall(r"""["']:?([^"']+)["']""", inc):
            mods[m] = m.replace(":", "/")
    if not mods:
        return None
    by_norm = {norm(m): m for m in mods}
    deps = {}
    for m, d in mods.items():
        bf = next((Path(wt) / d / n for n in ("build.gradle.kts", "build.gradle")
                   if (Path(wt) / d / n).exists()), None)
        if not bf:
            return None
        t = bf.read_text()
        found = set(re.findall(r"""project\(\s*["']:?([^"']+)["']""", t))
        found |= {by_norm[norm(x)] for x in re.findall(r"\bprojects\.([A-Za-z0-9_.]+)", t)
                  if norm(x) in by_norm}
        deps[m] = {f for f in found if f in mods}
    return mods, deps


def closure(deps, m):
    seen, todo = set(), [m]
    while todo:
        for d in deps.get(todo.pop(), ()):
            if d not in seen:
                seen.add(d)
                todo.append(d)
    return seen


def to_modules(mods, files):
    """(modules touched, touched shared build setup)."""
    hit, shared = set(), False
    for f in files:
        if SHARED_ROOT_FILES.match(f):
            shared = True
            continue
        best = max((m for m, d in mods.items() if f.startswith(d + "/")), key=lambda m: len(mods[m]),
                   default=None)
        if best:
            hit.add(best)
    return hit, shared


def judge(wt, main_files, ticket_files):
    """(kind, label, compile modules) per the rerun rule; kind is rerun | compile | push."""
    graph = module_graph(wt)
    if not graph:
        return "rerun", "no module graph", []
    mods, deps = graph
    theirs, shared = to_modules(mods, main_files)
    mine, _ = to_modules(mods, ticket_files)
    label = ",".join(sorted(theirs | mine)) or "-"
    if shared:
        return "rerun", label + " +shared build setup", []
    structure, _ = profile_line(wt, "structure")
    for m in re.findall(r":([A-Za-z0-9_.:-]+)", structure or ""):
        parts = m.split(":")
        if any(":".join(parts[:i]) in mods and ":".join(parts[:i]) in theirs
               for i in range(1, len(parts) + 1)):
            return "rerun", label + " +structure rules", []
    if theirs & mine:
        return "rerun", label, []
    above = {m for m in theirs if mine & closure(deps, m)}  # main changed a dependent of the batch
    below = any(m in closure(deps, t) for t in mine for m in theirs)  # ... or a dependency of it
    if above or below:
        return "compile", label, sorted(mine | above)
    return "push", label, []


def compile_command(wt, modules):
    """`./gradlew` compile tasks for the modules, None when they cannot be resolved here."""
    if not (Path(wt) / "gradlew").is_file():
        return None
    cmd = shlex.join(["./gradlew"] + [f":{m}:{t}" for m in modules for t in COMPILE_TASKS])
    dry = subprocess.run(["bash", "-c", cmd + " --dry-run"], cwd=wt, capture_output=True)
    return cmd if dry.returncode == 0 else None


def decide(wt, main_files, ticket_files):
    """(kind, label, compile command): `judge`, a compile verdict without a command -> rerun."""
    kind, label, mods = judge(wt, main_files, ticket_files)
    cmd = compile_command(wt, mods) if kind == "compile" else None
    if kind == "compile" and not cmd:
        return "rerun", label + " +no compile command", None
    return kind, label, cmd


def sha7(wt):
    return out("git", "rev-parse", "--short=7", "HEAD", cwd=wt)


def names(wt, *rng):
    return [l for l in out("git", "diff", "--name-only", *rng, cwd=wt).splitlines() if l]


LOCK_WAIT_S = 30
EVENTS = "lane-events.jsonl"
WATCH_PID = "main-health-watch.pid"  # in agent-builds/, written by `main_health.py watch` while it runs
WATCH_LOG = "main-health-watch.log"  # in the lane dir
CHECK_GROUPS = "check-groups"  # process groups of the running checks, one per line
WAIT_POLL_S = 0.5
KILL_GRACE_S = 30
BUSY_RETRY_S = 0.3  # a `wait` probing the lane lock holds it for microseconds; a real holder for minutes
# GitHub refuses a merge whose head or base moved since the request: a race, so the ticket is requeued
# once gh_merge gives up. A moved head (the PR head is not the pushed sha) is never retried; a moved
# base is retried only while origin/main keeps the tree the lane checked.
SHA_MOVED = re.compile(r"(Head|Base) branch was modified")
HEAD_MOVED = re.compile(r"Head branch was modified")
BASE_MOVED = re.compile(r"Base branch was modified")
# GitHub refusals that pass on their own (mergeability not computed yet, a 5xx, the network): retried.
MERGE_TRANSIENT = re.compile(r"not mergeable|mergeable state|try again|HTTP 5\d\d|error connecting|"
                             r"connection (reset|refused)|timeout|timed out|deadline exceeded|no such host|"
                             r"unexpected EOF", re.I)
MERGE_RETRIES = 3
MERGE_RETRY_S = 5
MOVED = ("--queue is gone: one lane per repository now (<git-common-dir>/agent-builds/lane/); use: "
         "merge_lane.py enqueue --who <run slug> --nn <NN> --worktree <path> --title <title> "
         "--body-file <f>, then merge_lane.py wait --who <run slug> --nn <NN>...; "
         "re-enqueue anything left in the old .scratch/<slug>/lane/queue.jsonl")


def flock_ex(fd, wait_s):
    """Take an exclusive flock on `fd`, retrying for `wait_s`: False while another holds it."""
    deadline = time.time() + wait_s
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except BlockingIOError:
            if time.time() > deadline:
                return False
            time.sleep(0.05)


@contextmanager
def file_lock(path):
    """Hold an exclusive flock on `path` (created when missing); the kernel drops it
    however the holder dies. TimeoutError after LOCK_WAIT_S."""
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        if not flock_ex(fd, LOCK_WAIT_S):
            raise TimeoutError(f"locked > {LOCK_WAIT_S}s: {path}")
        yield
    finally:
        os.close(fd)


def batch_modules(wt, base, head):
    """Modules the commits base..head touch, sorted; [] without a module graph."""
    graph = module_graph(wt)
    return sorted(to_modules(graph[0], names(wt, base, head))[0]) if graph else []


def module_test_seconds(wt, since):
    """{module: seconds}: `testsuite@time` summed over the JUnit XML in each
    module's build/test-results written at or after `since` (older files are
    an earlier run's). Modules from the module graph, else top-level dirs."""
    graph = module_graph(wt)
    mods = graph[0] if graph else {p.parent.name: p.parent.name for p in Path(wt).glob("*/build")}
    secs = {}
    for m, d in mods.items():
        for x in (Path(wt) / d / "build" / "test-results").glob("**/*.xml"):
            try:
                if x.stat().st_mtime < since:
                    continue
                t = sum(float(s.get("time") or 0) for s in ET.parse(x).getroot().iter("testsuite"))
            except (OSError, ET.ParseError, ValueError):
                continue
            secs[m] = secs.get(m, 0) + t
    return {m: round(s, 3) for m, s in sorted(secs.items())}


def lane_dir(cwd):
    """The repository's one merge lane: <git-common-dir>/agent-builds/lane (shared by every worktree)."""
    r = run("git", "rev-parse", "--path-format=absolute", "--git-common-dir", cwd=cwd, check=False)
    if r.returncode or not r.stdout.strip():
        fail(f"not in a git repository: {cwd}")
    return Path(r.stdout.strip()) / "agent-builds" / "lane"


def label(e):
    return f"{e['who']}/{e['nn']}"


def labels(entries):
    return ",".join(label(e) for e in entries)


def safe(s):
    return re.sub(r"[^A-Za-z0-9_.-]", "_", s)


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class EventLog:
    """Lane events for later analysis and for `wait`, one JSON line each, in
    <git-common-dir>/agent-builds/lane-events.jsonl (next to the lane dir, never
    committed). `who` is the run slug of the `land` or `enqueue`; a ticket's
    fields name the ticket's own. `log` never raises: a failure is one stderr
    line and the lane goes on."""

    def __init__(self, who, lane):
        self.who, self.path = who, Path(lane).parent / EVENTS

    def log(self, event, fields):
        """`fields`: a dict, or a callable returning one (evaluated under the same guard)."""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            rec = {"ts": utc_now(), "who": self.who, "event": event,
                   **(fields() if callable(fields) else fields)}
            with file_lock(self.path.with_suffix(".flock")):
                with self.path.open("a") as f:
                    f.write(json.dumps(rec) + "\n")
        except Exception as e:  # noqa: BLE001 - logging must never stop the lane
            print(f"merge_lane: event log: {e!r}", file=sys.stderr)


def read_events(path, off):
    """(events, new offset): the complete JSON lines of `path` from byte `off`;
    a partly written last line is left for the next read."""
    try:
        with open(path, "rb") as f:
            f.seek(off)
            data = f.read()
    except (FileNotFoundError, IsADirectoryError):
        return [], off
    end = data.rfind(b"\n") + 1
    evs = []
    for line in data[:end].splitlines():
        try:
            evs.append(json.loads(line))
        except ValueError:
            continue
    return evs, off + end


class Queue:
    """JSONL queue, edited only under an exclusive flock on `<queue>.flock`."""

    def __init__(self, path):
        self.path = Path(path)
        self.lock = Path(str(path) + ".flock")

    def read(self):
        if not self.path.exists():
            return []
        return [json.loads(l) for l in self.path.read_text().splitlines() if l.strip()]

    def update(self, fn):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with file_lock(self.lock):
                recs = fn(self.read())
                tmp = self.path.with_suffix(".tmp")
                tmp.write_text("".join(json.dumps(r) + "\n" for r in recs))
                tmp.replace(self.path)
        except TimeoutError as e:
            fail(f"queue {e}")


def cmd_enqueue(a):
    wt = str(Path(a.worktree).resolve())
    if not Path(wt).is_dir():
        fail(f"no worktree at {wt}")
    lane = lane_dir(wt)
    e = {"who": a.who, "nn": a.nn, "id": uuid.uuid4().hex[:12], "enqueued": utc_now(), "worktree": wt,
         "branch": out("git", "rev-parse", "--abbrev-ref", "HEAD", cwd=wt),
         "head": out("git", "rev-parse", "HEAD", cwd=wt),
         "base": out("git", "merge-base", "HEAD", "origin/main", cwd=wt),
         "title": a.title, "body_file": str(Path(a.body_file).resolve()),
         "no_merge": a.no_merge, "red_fix": a.red_fix, "full": a.full}
    # Logged first: in the log, a ticket's results always follow its enqueue.
    EventLog(a.who, lane).log("enqueue", {"nn": a.nn, "id": e["id"]})
    Queue(lane / "queue.jsonl").update(
        lambda recs: [r for r in recs if (r["who"], r["nn"]) != (a.who, a.nn)] + [e])
    print(f"queued {label(e)} @ {e['head'][:7]} ({e['branch']})")
    return 0


class LaneLock:
    """One `land` per repository: an exclusive flock on `<lane>/land.lock`. The
    kernel releases it when the holder exits, however it dies, so there is no
    stale lock to detect. The file holds the holder's pid, for messages only."""

    def __init__(self, lane):
        self.path = Path(lane) / "land.lock"
        self.fd = None

    def holder(self):
        """The holder's pid (-1 before it wrote it) while the lock is held, else None."""
        try:
            fd = os.open(self.path, os.O_RDONLY)
        except FileNotFoundError:
            return None
        try:
            fcntl.flock(fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
            return None
        except BlockingIOError:
            try:
                return int(os.read(fd, 32) or b"-1")
            except ValueError:
                return -1
        finally:
            os.close(fd)  # drops the probe's shared lock too

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(self.path, os.O_RDWR | os.O_CREAT, 0o644)  # not inherited by the checks
        if not flock_ex(fd, BUSY_RETRY_S):
            os.close(fd)
            fail(f"lane busy: land pid {self.holder() or '?'} holds {self.path}", 4)
        os.ftruncate(fd, 0)
        os.write(fd, str(os.getpid()).encode())
        self.fd = fd
        return self

    def __exit__(self, *exc):
        os.close(self.fd)


def scratch(lane, k, sha, repo):
    """Scratch worktree `lane/wt/<k>` detached at `sha`, reset from whatever an
    earlier (maybe killed) check left: tracked files restored, untracked ones
    removed, ignored build output kept for an incremental build. The main
    checkout's `local.properties` (Android SDK path, never committed) is copied in."""
    wt = Path(lane) / "wt" / str(k)
    if (wt / ".git").is_file() and run("git", "rev-parse", "--git-dir", cwd=wt, check=False).returncode == 0:
        run("git", "checkout", "-q", "-f", "--detach", sha, cwd=wt)
        run("git", "clean", "-fdq", cwd=wt)
    else:
        shutil.rmtree(wt, ignore_errors=True)
        run("git", "worktree", "prune", cwd=repo)
        wt.parent.mkdir(parents=True, exist_ok=True)
        run("git", "worktree", "add", "-q", "--detach", str(wt), sha, cwd=repo)
    props = Path(lane).parents[2] / "local.properties"  # <checkout>/.git/agent-builds/lane -> main checkout
    if props.is_file():
        shutil.copyfile(props, wt / "local.properties")
    return wt


def kill_group(p):
    """Stop a check: SIGTERM to its process group (it runs in its own session),
    SIGKILL after KILL_GRACE_S."""
    try:
        os.killpg(p.pid, signal.SIGTERM)
        p.wait(timeout=KILL_GRACE_S)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    except ProcessLookupError:
        pass


def proc_start(pid):
    """When process `pid` started, per `ps` ("" once it is gone): with the pid, one process."""
    return subprocess.run(["ps", "-o", "lstart=", "-p", str(pid)], capture_output=True, text=True).stdout.strip()


def watch_pid(agent_builds):
    """The pid of the live `main_health.py watch` (pidfile present, `kill -0` succeeds), else None."""
    try:
        pid = int((Path(agent_builds) / WATCH_PID).read_text())
        os.kill(pid, 0)
    except (OSError, ValueError) as e:
        return pid if isinstance(e, PermissionError) else None  # EPERM: alive, another user's
    return pid


def kill_orphans(lane):
    """Kill the checks a SIGKILLed `land` left running: each process group on the
    CHECK_GROUPS record whose leader still has the recorded start time (else the pid
    names another process now) gets SIGTERM, SIGKILL after KILL_GRACE_S; a group gone
    or all zombies (EPERM on macOS) counts as dead. Then clear the record. Only a
    `land` holding the lane lock reads or writes it."""
    rec = Path(lane) / CHECK_GROUPS
    try:
        lines = rec.read_text().splitlines()
    except FileNotFoundError:
        return
    try:
        for line in lines:
            pid, _, start = line.partition(" ")
            if not pid.isdigit() or not start or proc_start(pid) != start:
                continue
            g = int(pid)
            try:
                os.killpg(g, signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                continue
            deadline = time.time() + KILL_GRACE_S
            while time.time() < deadline:
                try:
                    os.killpg(g, 0)
                except (ProcessLookupError, PermissionError):
                    break
                time.sleep(0.1)
            else:
                try:
                    os.killpg(g, signal.SIGKILL)
                except (ProcessLookupError, PermissionError):
                    pass
    finally:
        rec.unlink(missing_ok=True)


def worktree_problem(r):
    """Why the lane must not touch this entry's worktree, or None."""
    wt = r["worktree"]
    if not Path(wt).is_dir():
        return f"no worktree at {wt}"
    if out("git", "status", "--porcelain", "--untracked-files=no", cwd=wt):
        return "uncommitted changes in the worktree (worker still running?); re-enqueue when ready"
    if out("git", "rev-parse", "HEAD", cwd=wt) not in (r["head"], r.get("lane_head")):
        return "worktree HEAD moved since enqueue; re-enqueue"
    return None


def pr_merged(wt, pr):
    v = run("gh", "pr", "view", pr, "--json", "state", "-q", ".state", cwd=wt, check=False)
    return v.returncode == 0 and v.stdout.strip() == "MERGED"


def merge_commit(wt, pr):
    """The squash commit GitHub put on main for merged PR `pr`, or None when gh reports none."""
    v = run("gh", "pr", "view", pr, "--json", "mergeCommit", "-q", ".mergeCommit.oid", cwd=wt, check=False)
    return (v.stdout.strip() if v.returncode == 0 else "") or None


def gh_merge(wt, pr, head, main):
    """Squash-merge PR `pr` at `head`, checked on origin/main `main`: (None, False) once
    merged, else (gh's error, main moved). A transient refusal (MERGE_TRANSIENT) is
    retried MERGE_RETRIES times, MERGE_RETRY_S apart, and so is a moved base while
    origin/main keeps `main`'s tree (GitHub settling after the batch's previous squash).
    A base that really moved returns at once with main moved True: the caller runs the
    main-moved step again, never a blind retry. A moved head (HEAD_MOVED) is never retried."""
    for attempt in range(MERGE_RETRIES + 1):
        # No --delete-branch: gh then checks out main locally, which fails with
        # "'main' is already checked out" in a worktree even after a good merge.
        m = run("gh", "pr", "merge", pr, "--squash", "--match-head-commit", head, cwd=wt, check=False)
        if not m.returncode or pr_merged(wt, pr):
            return None, False
        err = (m.stderr or m.stdout).strip()
        if BASE_MOVED.search(err):
            run("git", "fetch", "origin", cwd=wt)
            if tree(wt, "origin/main") != tree(wt, main):
                return err, True
        elif HEAD_MOVED.search(err) or not MERGE_TRANSIENT.search(err):
            return err, False
        if attempt == MERGE_RETRIES:
            return err, False
        time.sleep(MERGE_RETRY_S)


def own_closed_pr(info, e):
    """`info` (`gh pr view <branch>`) is this ticket's PR, closed by the user: closed at or
    after the enqueue, or on the ticket's head. Any other CLOSED PR is an older one of a
    reused branch name: the ticket gets a new PR. An entry without `enqueued` (queued by
    an older lane) owns any CLOSED PR of its branch."""
    head = info.get("headRefOid")
    return info.get("state") == "CLOSED" and (
        (info.get("closedAt") or "") >= e.get("enqueued", "")
        or bool(head) and head in (e["head"], e.get("lane_head")))


def tree(wt, rev):
    return out("git", "rev-parse", f"{rev}^{{tree}}", cwd=wt)


def take(recs, n):
    """The next batch: a `no_merge` or `red_fix` head alone, else up to n tickets
    before the first such one."""
    if recs and (recs[0].get("no_merge") or recs[0].get("red_fix")):
        return recs[:1]
    batch = []
    for r in recs:
        if len(batch) >= n or r.get("no_merge") or r.get("red_fix"):
            break
        batch.append(r)
    return batch


class Land:
    """One `land` run: batch A, and batch B stacked on A's top, checked at once."""

    def __init__(self, who, lane, max_):
        self.who, self.lane, self.max = who, Path(lane), max_
        self.git = str(self.lane.parent.parent)  # <common>/agent-builds/lane -> <common>: outlives every worktree
        self.repo = str(self.lane.parent.parent.parent)  # <common>/agent-builds/lane -> repo root
        self.q = Queue(self.lane / "queue.jsonl")
        self.events = EventLog(who, self.lane)
        self.results = {}  # entry id -> result
        self.checks = []  # (batch, check) for every check started; stop() ends the live ones
        self.groups = self.lane / CHECK_GROUPS
        self.mh = [sys.executable, str(HERE / "main_health.py")]
        self.watcher = None  # the watch this land started
        self.slot = ["build-slot"] if shutil.which("build-slot") else []

    def emit(self, e, result, pipe, **kw):
        # Only a requeue the ticket caused counts toward the cap, not one for a ticket or batch under it.
        counts = result == "requeued" and not kw["reason"].startswith("stacked on")
        n = 0
        if counts:
            n = next((r.get("requeues", 0) for r in self.q.read() if r.get("id") == e["id"]), 0)
            if n >= REQUEUE_CAP:
                result = "stuck"
        line = {"who": e["who"], "nn": e["nn"], "result": result, **kw}
        print(json.dumps(line), flush=True)
        self.events.log("ticket", {"who": e["who"], "nn": e["nn"], "id": e["id"], "pipe": pipe,
                                   "result": result, "reason": kw.get("reason"), "pr": kw.get("pr"),
                                   "line": line})
        if result == "merged" and "merged" not in self.results.values():
            self.watch()  # the first merge of this land; land() checks again on exit
        self.results[e["id"]] = result
        if result != "requeued":
            self.q.update(lambda recs: [r for r in recs if r.get("id") != e["id"]])
            return
        upd = {"requeues": n + 1} if counts else {}
        if Path(e["worktree"]).is_dir():  # the lane rebased it: its HEAD is still ours
            upd["lane_head"] = out("git", "rev-parse", "HEAD", cwd=e["worktree"])
        self.q.update(lambda recs: [dict(r, **upd) if r.get("id") == e["id"] else r for r in recs])

    def requeue(self, entries, reason, pipe):
        for e in entries:
            self.emit(e, "requeued", pipe, reason=reason)

    def track(self):
        """Record the process groups of the checks still running (kill_orphans reads it)."""
        self.groups.write_text("".join(f"{c['p'].pid} {c['lstart']}\n"
                                       for _, c in self.checks if c["p"].returncode is None))

    def stop(self):
        """The land is exiting: kill every check still running (logged `discarded`), clear the record."""
        for batch, c in self.checks:
            if c["p"].returncode is None:
                batch.finish(c, discard=True)
        self.groups.unlink(missing_ok=True)

    def watch(self):
        """Keep main-health fresh after a merge: start `main_health.py watch` detached unless one is
        alive. It outlives this land on purpose: neither stop() nor kill_orphans knows its pid."""
        pid = self.watcher.pid if self.watcher and self.watcher.poll() is None else watch_pid(self.lane.parent)
        if pid:
            print(f"watch: running pid {pid}", flush=True)
            return
        log = self.lane / WATCH_LOG
        try:
            with log.open("a") as f:
                self.watcher = subprocess.Popen(self.mh + ["watch", "--who", self.who], cwd=self.repo,
                                                stdin=subprocess.DEVNULL, stdout=f, stderr=subprocess.STDOUT,
                                                start_new_session=True)
        except OSError as e:
            print(f"watch: not started: {e}", flush=True)
            return
        print(f"watch: started pid {self.watcher.pid}, log {log}", flush=True)

    def ledger(self, line, entries):
        print(line, flush=True)
        self.events.log("ledger", {"line": line, "ids": [e["id"] for e in entries]})

    def status(self, wt):
        s = subprocess.run(self.mh + ["status"], cwd=wt, capture_output=True, text=True)
        if s.returncode not in (0, 3):
            fail(f"main_health status failed: {s.stderr.strip()}")
        return s

    def run(self):
        recs = []
        for r in self.q.read():
            problem = worktree_problem(r)
            if problem:
                self.emit(r, "invalid", None, reason=problem)
            else:
                recs.append(r)
        if not recs:
            return 0 if not self.results else 1
        st = self.status(recs[0]["worktree"])
        red = st.returncode == 3
        if red:
            fx = next((r for r in recs if r.get("red_fix")), None)
            if not fx:
                print("main red; lane paused")
                print(st.stdout.strip())
                return 3
            parts = [[fx], []]
        else:
            first = take(recs, self.max)
            parts = [first, take(recs[len(first):], self.max)]
        run("git", "fetch", "origin", cwd=recs[0]["worktree"])
        base = out("git", "rev-parse", "origin/main", cwd=recs[0]["worktree"])
        a = Batch(self, "A", parts[0], 0)
        a.round(base)
        b = None
        if parts[1]:
            b = Batch(self, "B", parts[1], 1)
            on_a = bool(a.top) and not parts[0][0].get("no_merge")  # a no_merge A never merges
            b.round(a.top if on_a else base, main0=base, under=a if on_a else None)
        a.settle(dependent=b if b and b.under else None)
        a.merge()
        if b and b.live:
            if a.red and b.under:
                b.discard("stacked on a red batch")
            else:
                b.settle()
                b.merge()
        if red and self.results.get(parts[0][0]["id"]) != "merged":
            print("main red; lane paused")
            print(st.stdout.strip())
            return 3
        return 0 if all(self.results.get(e["id"]) == "merged" for e in parts[0] + parts[1]) else 1


class Batch:
    """One batch on one scratch worktree (k): stack, check, main check, merge."""

    def __init__(self, land, pipe, cands, k):
        self.land, self.pipe, self.cands, self.k = land, pipe, cands, k
        self.rounds = self.full = self.suites = self.compiles = self.merged = 0
        self.kind, self.cc, self.tag, self.cmd, self.e2e, self.e2e_cmd = "rerun", None, "suite", None, None, None
        self.stack, self.green, self.pending, self.check = [], list(cands), [], None
        self.base = self.main0 = self.under = None
        self.suite7, self.red, self.live, self.docs, self.scope = "", False, True, False, None
        self.git = land.git

    @property
    def top(self):
        return self.stack[-1]["head_t"] if self.stack else None

    def round(self, base, main0=None, under=None):
        """Stack the green tickets (all of them at first) on `base` and start their
        check. `under`: the batch whose top `base` is; `main0`: then the origin/main
        that batch was stacked on. A ticket already red or requeued stays so."""
        self.rounds += 1
        self.base, self.main0, self.under = base, main0 or base, under
        self.stack, self.check, prev = [], None, base
        for e in self.green:
            wt = e["worktree"]
            run("git", "checkout", "-q", "-B", e["branch"], e["head"], cwd=wt)
            if run("git", "rebase", "--onto", prev, e["base"], cwd=wt, check=False).returncode:
                files = out("git", "diff", "--name-only", "--diff-filter=U", cwd=wt).splitlines()
                run("git", "rebase", "--abort", cwd=wt, check=False)
                self.pending.append((e, "conflict", {"files": files}))
                continue
            e = dict(e, head_t=out("git", "rev-parse", "HEAD", cwd=wt), tree=tree(wt, "HEAD"))
            self.stack.append(e)
            prev = e["head_t"]
        self.green = self.stack
        if self.stack:
            self.cmd, self.tag = (None, "suite") if self.kind == "rerun" else (self.cc, "compile")
            self.e2e = self.e2e_cmd = None
            if self.tag == "suite":
                self.full += 1
                top = self.stack[-1]
                self.docs = docs_only(top["worktree"], self.stack, base, top["head_t"])
                e2e, trigger = (None, None) if self.docs else e2e_plan(top["worktree"], base, top["head_t"])
                if trigger is not None:
                    self.e2e = {"due": bool(e2e), "trigger": trigger}
                self.e2e_cmd = e2e
            if not self.docs:
                self.check = self.start(self.stack, self.cmd, self.tag, base, "stack")

    def start(self, prefix, cmd, tag, base, phase):
        """Start one build command on the prefix's top in this batch's scratch worktree:
        `cmd` for a compile check; a suite check computes its own (`check_plan` on the
        prefix, then the batch's e2e step). `base`: the commit the prefix is stacked on;
        `phase`: stack | bisect | merge."""
        top = prefix[-1]
        scope = why = None
        if tag == "suite":
            self.suites += 1
            cmd, scope, why = check_plan(top["worktree"], prefix, base, top["head_t"])
            cmd = with_e2e(cmd, self.e2e_cmd) if self.e2e_cmd else cmd
        else:
            self.compiles += 1
        logdir = self.land.lane / "logs"
        logdir.mkdir(parents=True, exist_ok=True)
        log = logdir / (f"lane-{'-'.join(e['nn'] for e in prefix)}-{top['head_t'][:7]}"
                        f"{'' if tag == 'suite' else '-compile'}.log")
        wt = scratch(self.land.lane, self.k, top["head_t"], top["worktree"])
        t0 = time.time()
        with log.open("w") as f:
            p = subprocess.Popen(self.land.slot + ["bash", "-c", cmd], cwd=wt, stdin=subprocess.DEVNULL,
                                 stdout=f, stderr=subprocess.STDOUT, start_new_session=True)
        c = {"p": p, "lstart": proc_start(p.pid), "t0": t0, "log": str(log), "prefix": prefix, "tag": tag,
             "phase": phase, "base": base, "wt": wt, "round": self.rounds, "scope": scope, "why": why,
             "e2e": self.e2e if tag == "suite" else None}
        self.land.checks.append((self, c))
        self.land.track()
        return c

    def finish(self, c, discard=False):
        """Wait for a started check (killed first when discarding) and log it: (rc, log)."""
        p = c["p"]
        if discard and p.poll() is None:
            kill_group(p)
        rc = p.wait()
        self.land.track()
        wall = time.time() - c["t0"]
        prefix, top = c["prefix"], c["prefix"][-1]
        self.land.events.log(c["tag"], lambda: {
            "pipe": self.pipe, "batch": [label(e) for e in prefix], "batch_size": len(prefix),
            "round": c["round"], "phase": c["phase"],
            "modules": batch_modules(c["wt"], c["base"], top["head_t"]),
            "base": c["base"][:7], "top": top["head_t"][:7], "scope": c["scope"], "why": c["why"],
            "result": "discarded" if discard else "red" if rc else "green", "wall_s": round(wall, 1),
            # whole seconds: a coarse mtime clock must not hide a file this run wrote
            "module_test_s": module_test_seconds(c["wt"], int(c["t0"])),
            "e2e": e2e_event(c["e2e"], c["log"])})
        return rc, c["log"]

    def outside(self, main):
        """Commits on `main` since `main0` that neither batch merged."""
        k = int(out("git", "rev-list", "--count", f"{self.main0}..{main}", cwd=self.git))
        return k - (self.under.merged if self.under else 0) - self.merged

    def discard(self, reason):
        """The batch under this one went red: kill the check, requeue every ticket."""
        if self.check:
            self.finish(self.check, discard=True)
            self.check = None
        self.live, self.green = False, []
        self.land.requeue(self.cands, reason, self.pipe)

    def settle(self, dependent=None):
        """Finish the check (bisect a red one), then the main check of step 6,
        restacking until main holds still or the batch is requeued."""
        while self.stack:
            proof = self.check["scope"] if self.check else None  # the scope of the check proving the green top
            rc, log = self.finish(self.check) if self.check else (0, None)  # no check: docs only
            self.check = None
            if rc:
                self.red = True
                if dependent and dependent.live:
                    dependent.discard("stacked on a red batch")
                logs, lo, hi = {len(self.stack): log}, 0, len(self.stack)
                while hi - lo > 1:
                    mid = (lo + hi) // 2
                    c2 = self.start(self.stack[:mid], self.cmd, self.tag, self.base, "bisect")
                    rc2, log2 = self.finish(c2)
                    if rc2:
                        hi, logs[mid] = mid, log2
                    else:
                        lo, proof = mid, c2["scope"]
                self.pending.append((self.stack[hi - 1], "red", {"log": logs[hi]}))
                self.pending += [(e, "requeued", {"reason": "stacked on a red ticket"}) for e in self.stack[hi:]]
                self.green = self.stack[:lo]
            if self.tag == "suite" and self.green:
                self.suite7, self.scope = self.green[-1]["head_t"][:7], proof
            if not self.green:
                break
            run("git", "fetch", "origin", cwd=self.git)
            moved = out("git", "rev-parse", "origin/main", cwd=self.git)
            if moved == self.base or tree(self.git, moved) == tree(self.git, self.base):
                break
            top = self.green[-1]
            self.kind, why, self.cc = (
                ("push", "docs only", None) if self.docs else
                decide(top["worktree"], names(self.git, self.base, moved),
                       names(top["worktree"], self.base, top["head_t"])))
            k = self.outside(moved)
            self.land.ledger(f"merge: {labels(self.green)} main moved {k} commits — {self.kind} ({why})",
                             self.green)
            # A rerun verdict past MAX_ROUNDS requeues instead: logged as such, so `rerun` counts real reruns.
            self.land.events.log("main_moved", {
                "pipe": self.pipe, "batch": [label(e) for e in self.green], "phase": "stack", "commits": k,
                "reason": why,
                "decision": "requeue" if self.kind == "rerun" and self.full == MAX_ROUNDS else self.kind})
            if self.kind == "push":
                break
            if self.kind == "rerun" and self.full == MAX_ROUNDS:
                self.land.requeue(self.green, "main keeps moving", self.pipe)
                self.live, self.green = False, []
                break
            self.round(moved)
        for e, result, kw in self.pending:
            self.land.emit(e, result, self.pipe, **kw)
        self.pending = []

    def merge(self):
        """Step 7 over the green tickets, in order."""
        if not self.live or not self.green:
            return
        L, green = self.land, self.green
        top7 = green[-1]["head_t"][:7]
        after_compile = self.tag == "compile"
        then = f", compile green tested @ {top7}" if after_compile else ""
        ran = f"{self.suites} suites" + (f", {self.compiles} compiles" if self.compiles else "")
        if self.docs:
            L.ledger(f"merge: batch {labels(green)} suite skipped (docs only) @ {self.suite7}", green)
        else:
            what = "affected" if self.scope == "affected" else "suite"
            L.ledger(f"merge: batch {labels(green)} {what} green tested @ {self.suite7}{then} ({ran})", green)
        prev_t = self.base
        for i, e in enumerate(green):
            if not self.merge_one(e, green[i:], prev_t, after_compile):
                break
            prev_t = e["head_t"]

    def merge_one(self, e, rest, prev_t, compiled):
        """Steps 7.1-7.6 for `e`, the first of `rest`, whose tested head sits on `prev_t`:
        False when the batch stops here (`e` ended or `rest` was requeued)."""
        L, wt, green = self.land, e["worktree"], self.green
        if not e.get("red_fix") and L.status(wt).returncode == 3:
            L.requeue(rest, "main red", self.pipe)
            return False
        view = run("gh", "pr", "view", e["branch"], "--json", "number,url,state,closedAt,headRefOid",
                   cwd=wt, check=False)
        info = json.loads(view.stdout) if view.returncode == 0 and view.stdout.strip() else {}
        if own_closed_pr(info, e):  # closed by the user: never pushed to or opened again
            L.emit(e, "closed", self.pipe, pr=int(info["number"]), url=info["url"])
            L.requeue(rest[1:], "stacked on a closed ticket", self.pipe)
            return False
        on, pr, claimed = prev_t, None, False  # `on`: the commit e's own commits sit on
        for _ in range(MERGE_RETRIES + 1):  # again only when main moved under the merge
            run("git", "fetch", "origin", cwd=wt)
            main = out("git", "rev-parse", "origin/main", cwd=wt)
            if main != on:
                if run("git", "rebase", "--onto", "origin/main", on, cwd=wt, check=False).returncode:
                    run("git", "rebase", "--abort", cwd=wt, check=False)
                    L.requeue(rest, "main moved: rebase conflict", self.pipe)
                    return False
            if tree(wt, "HEAD") != e["tree"]:
                files = names(wt, prev_t, "origin/main")
                kind, why, cc = (("push", "docs only", None) if self.docs else
                                 decide(wt, files, names(wt, prev_t, green[-1]["head_t"]))
                                 if files else ("rerun", "tree differs", None))
                k = self.outside(main)
                L.ledger(f"merge: {labels(rest)} main moved {k} commits — {kind} ({why})", rest)
                L.events.log("main_moved", {
                    "pipe": self.pipe, "batch": [label(x) for x in rest], "phase": "merge", "commits": k,
                    "decision": "requeue" if kind == "rerun" else kind, "reason": why})
                if kind == "rerun":
                    L.requeue(rest, "main moved: related", self.pipe)
                    return False
                if kind == "compile":
                    rc, log = self.finish(self.start([dict(e, head_t=out("git", "rev-parse", "HEAD", cwd=wt))],
                                                     cc, "compile", main, "merge"))
                    if rc:
                        self.red = True
                        L.emit(e, "red", self.pipe, log=log)
                        L.requeue(rest[1:], "stacked on a red ticket", self.pipe)
                        return False
                    compiled = True
            head = out("git", "rev-parse", "HEAD", cwd=wt)
            run("git", "push", "-u", "--force-with-lease", "origin", "HEAD", cwd=wt)
            body = Path(e["body_file"]).read_text()
            note = ", then compile green after main moved" if compiled else ""
            what = ("suite skipped (docs only)" if self.docs else
                    "affected check green" if self.scope == "affected" else "suite green")
            check = (f"**check:** local {what} on batch top {self.suite7} (tickets {labels(green)}){note}; "
                     "no PR CI by design")
            if re.search(r"^\*\*check:\*\*.*$", body, re.M):
                body = re.sub(r"^\*\*check:\*\*.*$", lambda _: check, body, flags=re.M)
            else:
                body = body.rstrip("\n") + "\n" + check + "\n"
            bf = L.lane / f"body-{safe(e['who'])}-{e['nn']}.md"
            bf.write_text(body)
            if pr is None and info.get("state") == "OPEN":
                pr, url = str(info["number"]), info["url"]
            elif pr is None:
                c = run("gh", "pr", "create", "--base", "main", "--title", e["title"],
                        "--body-file", str(bf), cwd=wt, check=False)
                m = re.search(r"/pull/(\d+)", c.stdout)
                if c.returncode or not m:
                    L.emit(e, "refused", self.pipe, reason=f"gh pr create failed: {(c.stderr or c.stdout).strip()}")
                    L.requeue(rest[1:], "stacked on a refused ticket", self.pipe)
                    return False
                url, pr = c.stdout.strip().splitlines()[-1], m.group(1)
            if e.get("no_merge"):
                L.emit(e, "waiting_user", self.pipe, pr=int(pr), url=url)
                return True
            if e.get("red_fix") and not claimed and L.status(wt).returncode == 3:
                claim = subprocess.run(L.mh + ["claim", "--who", e["who"], "--culprit", e["red_fix"],
                                               "--fix-pr", pr], cwd=wt, capture_output=True, text=True)
                if claim.returncode:
                    L.emit(e, "claim_refused", self.pipe, pr=int(pr),
                           reason=(claim.stderr or claim.stdout).strip())
                    return False
                L.ledger(claim.stdout.strip(), [e])
                claimed = True
            err, moved = gh_merge(wt, pr, head, main)
            if not moved:
                break
            on = main
        if err is not None:
            if SHA_MOVED.search(err):  # a moved head, or a base race gh_merge gave up on: try again next run
                L.requeue(rest, f"merge refused for PR #{pr}: {err}", self.pipe)
            else:
                L.emit(e, "refused", self.pipe, pr=int(pr), reason=err)
                L.requeue(rest[1:], "stacked on a refused ticket", self.pipe)
            return False
        squash = merge_commit(wt, pr)  # gh runs in wt: resolve before the worktree goes
        run("git", "push", "origin", "--delete", e["branch"], cwd=wt, check=False)
        run("git", "worktree", "remove", wt, cwd=L.repo, check=False)
        run("git", "branch", "-D", e["branch"], cwd=L.repo, check=False)
        self.merged += 1
        sha = squash and squash[:7]
        where = f"@ {sha}" if sha else f"(main sha unresolved; tested @ {head[:7]})"
        # The slice line before the result: a `wait` stops reading at the last result.
        L.ledger(f"slice: {e['nn']} PR #{pr} merged {where}", [e])
        L.emit(e, "merged", self.pipe, pr=int(pr), sha=sha, tested=head[:7])
        return True


def land(a):
    lane = lane_dir(os.getcwd())
    with LaneLock(lane):
        kill_orphans(lane)
        L = Land(a.who, lane, a.max)
        old = signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))  # unwinds into the finally
        try:
            return L.run()
        finally:
            if "merged" in L.results.values():
                L.watch()  # the first watch may have ended before the later merges' runs started
            L.stop()
            signal.signal(signal.SIGTERM, old)


def cmd_wait(a):
    """Follow the lane events for <who>'s tickets, starting `land` whenever the lane is idle."""
    cwd = os.getcwd()
    lane = lane_dir(cwd)
    path, q, lock = lane.parent / EVENTS, Queue(lane / "queue.jsonl"), LaneLock(lane)
    evs, off = read_events(path, 0)
    ids = {ev["nn"]: ev["id"] for ev in evs
           if ev.get("event") == "enqueue" and ev.get("who") == a.who and ev.get("nn") in a.nn}
    for nn in a.nn:
        if nn not in ids:
            fail(f"no enqueue of {a.who}/{nn} in {path}")
    mine = {i: nn for nn, i in ids.items()}
    pending, merged, seen = set(mine), set(), {"ticket": False}

    def show(batch):
        for ev in batch:
            if ev.get("event") == "ticket":
                seen["ticket"] = True
                if ev.get("id") in mine:
                    print(json.dumps(ev["line"]), flush=True)
                    if ev["result"] != "requeued":
                        pending.discard(ev["id"])
                        if ev["result"] == "merged":
                            merged.add(ev["id"])
            elif ev.get("event") == "ledger" and set(ev.get("ids") or ()) & mine.keys():
                print(ev["line"], flush=True)

    show(evs)
    child = None
    while pending:
        if child is None and not lock.holder():
            # Queue first: a land logs a ticket's result before it drops the entry, so the drain below
            # holds the result of every entry missing from this snapshot.
            queued = {r.get("id") for r in q.read()}
            evs, off = read_events(path, off)
            show(evs)
            if not pending:
                break
            gone = pending - queued
            if gone:
                fail(f"{','.join(f'{a.who}/{mine[i]}' for i in sorted(gone))} left the queue without a result "
                     f"in {path}")
            with (lane / "land.log").open("a") as f:
                child = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "land", "--who", a.who,
                                          "--max", str(a.max)], cwd=cwd, stdin=subprocess.DEVNULL, stdout=f,
                                         stderr=subprocess.STDOUT, start_new_session=True)
            seen["ticket"] = False
            continue
        time.sleep(WAIT_POLL_S)
        evs, off = read_events(path, off)
        show(evs)
        if child is not None and child.poll() is not None:
            evs, off = read_events(path, off)
            show(evs)
            rc, child = child.returncode, None
            if rc == 3:
                print("main red; lane paused")
                print(subprocess.run([sys.executable, str(HERE / "main_health.py"), "status"], cwd=cwd,
                                     capture_output=True, text=True).stdout.strip())
                return 3
            if rc != 4 and not seen["ticket"] and pending & {r.get("id") for r in q.read()}:
                fail(f"land exited {rc} without a ticket result; see {lane / 'land.log'}")
    return 0 if merged == set(mine) else 1


def main():
    if any(x == "--queue" or x.startswith("--queue=") for x in sys.argv[1:]):
        fail(MOVED, 2)
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("enqueue", help="append a ready ticket (replaces the same who and nn)")
    n.add_argument("--who", required=True, help="run slug of the session that owns the ticket")
    n.add_argument("--nn", required=True)
    n.add_argument("--worktree", required=True)
    n.add_argument("--title", required=True)
    n.add_argument("--body-file", required=True)
    n.add_argument("--no-merge", action="store_true", help="only the user may merge this PR")
    n.add_argument("--red-fix", metavar="CULPRIT", help="this PR fixes red main (sha|#PR)")
    n.add_argument("--full", action="store_true",
                   help="its batch runs the full suite, not the affected check (release PR, unexpected red main)")
    w = sub.add_parser("wait", help="land until these tickets have a final result; print their lines")
    w.add_argument("--who", required=True, help="run slug the tickets were enqueued with")
    w.add_argument("--nn", required=True, nargs="+")
    w.add_argument("--max", type=int, default=MAX_BATCH, help=f"tickets per batch (default {MAX_BATCH})")
    l = sub.add_parser("land", help="land the next two batches once (`wait` starts it)")
    l.add_argument("--who", required=True, help="run slug (event owner)")
    l.add_argument("--max", type=int, default=MAX_BATCH, help=f"tickets per batch (default {MAX_BATCH})")
    a = p.parse_args()
    return {"enqueue": cmd_enqueue, "wait": cmd_wait, "land": land}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
