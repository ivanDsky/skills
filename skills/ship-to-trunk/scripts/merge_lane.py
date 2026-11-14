#!/usr/bin/env python3
"""Merge lane for trunk runs with `pr-check: none`: land ready tickets in batches.

Run by the orchestrator as one background bash job whenever the queue is
non-empty and no lane job runs. Workers never run it: they push the branch
and report ready; the orchestrator enqueues the ticket.

  merge_lane.py enqueue --queue <file> --nn <NN> --worktree <path>
                        --title "<conventional title>" --body-file <f>
                        [--no-merge] [--red-fix <sha|#PR>]
  merge_lane.py land    --queue <file> --who <run slug> [--max 4]

Queue: `.scratch/<slug>/lane/queue.jsonl`, one JSON object per ready ticket,
edited only under a mkdir lock (`<queue>.lock`). `enqueue` fills the rest
from the worktree and replaces an entry with the same nn (a ticket that
re-enters after a fix):
  {"nn","worktree","branch","head","base","title","body_file",
   "no_merge":false,"red_fix":null}
`base` is the ticket's merge-base with origin/main; `base..head` is its own
commits, restacked from scratch on every lane run. `no_merge: true` marks a
PR only the user may merge (unflaggable live change, flip PR). `red_fix`
(culprit sha|#PR) marks the fix PR of a red main.

`land` output: one JSON line per ticket touched, {"nn","result",...}, plus
plain ledger lines (`merge: ...`, `slice: ...`; lines not starting with `{`).
result is one of
  merged        (+ pr, sha)
  conflict      (+ files): rebase conflict, rebase aborted
  red           (+ log): the ticket turned the suite red
  waiting_user  (+ url): `no_merge` ticket, PR open, suite green
  claim_refused (+ reason): `red_fix` claim refused, nothing merged
  invalid       (+ reason): worktree missing
  requeued      (+ reason): stays at the head of the queue, in order
Finished tickets (everything but requeued) leave the queue.
Exit 0 when every ticket of the batch merged, 1 otherwise, 3 when main was
red at the start and the queue holds no `red_fix` ticket (nothing touched).

Sequence:
 1. `main_health.py status`. Red -> `main red; lane paused`, exit 3: the
    queue is the hold, no PR is opened. Red with a `red_fix` ticket queued
    -> that ticket lands alone (steps 3-7; 7.1 skipped; after its PR exists
    `main_health.py claim --who <who> --culprit <x> --fix-pr <n>`, refused ->
    claim_refused; then it merges despite red).
 2. Batch: the queue head, up to --max (default 4), stopping before the first
    `no_merge` or `red_fix` ticket; such a ticket at the head lands alone
    (a `no_merge` one ends with its PR open: waiting_user, no merge).
 3. Stack: `git fetch origin`; ticket 1 is rebased onto origin/main, ticket k
    onto the rebased head of k-1. Conflict at k: abort, result conflict,
    the next ticket stacks on k-1.
 4. One suite on the top worktree: the command in PROFILE's `pr-check: none`
    comment, else assemble debug + unit `runner:` + `structure:`; through
    `build-slot` when on PATH; log `.scratch/<slug>/logs/lane-<NN-NN>-<sha7>.log`.
 5. Red batch: binary search over prefix length (one suite per step on that
    prefix's top head, no extra rebases). The first ticket that turns the
    prefix red gets `red`; the green prefix proceeds; tickets after it are
    requeued ("stacked on a red ticket"). About 1 + log2(batch) suites.
 6. Rerun rule before merging (below). Related -> back to 3 on the new
    origin/main, at most 3 rounds, then the batch is requeued ("main keeps
    moving").
 7. Merge in order, k = 1..n: 7.1 `main_health.py status`, red -> the rest
    requeued ("main red"). 7.2 `git fetch origin`,
    `git rebase --onto origin/main <tested head of k-1>`; the new head's tree
    must equal k's tested tree (the squash of k-1 left main at k-1's tested
    tree). 7.3 Tree differs -> main moved under the batch: rerun rule over
    the outside commits against tickets k..n; related -> k..n requeued
    ("main moved: related"). 7.4 push `--force-with-lease`; reuse the OPEN PR
    of the branch (`gh pr view`), else `gh pr create` (body check line:
    `local suite green on batch top <sha7> (tickets <NN,NN>); no PR CI by
    design`). 7.5 `gh pr merge <n> --squash --delete-branch
    --match-head-commit <sha>` (always with the PR number; refused ->
    requeued). 7.6 `git worktree remove`.
 8. Ledger lines: `merge: batch <NN,NN> suite green @ <sha7> (<s> suites)`,
    each rerun decision `merge: <NN..> main moved <k> commits - rerun|push
    (<modules>)`, one `slice: <NN> PR #<n> merged @ <sha7>` per merge.

Rerun rule (mechanical): main moved -> rerun when a module main changed and a
module the batch changed are the same or depend on each other transitively
(modules from `include(...)` in settings.gradle.kts, dependencies from
`project(":x")` and `projects.x` in the build files), when main touched
`build-logic/`, `gradle/`, root build/settings/properties files or the
`structure:` rules module (any `:a:b` prefix of a `structure:` path that is a
module), or when no module graph is readable. Otherwise carry on.

The suite tests only the batch top. The intermediate main states (after the
1st, 2nd, ... merge of a batch) are not tested on their own.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

MAX_ROUNDS = 3
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


def suite_command(wt):
    _, comment = profile_line(wt, "pr-check")
    if comment:
        ticks = re.findall(r"`([^`]+)`", comment)
        cmd = next((t for t in ticks if not t.startswith("<")), None)
        if cmd:
            return cmd
    parts = ["./gradlew assembleDebug"]
    for key in ("runner", "structure"):
        v, _ = profile_line(wt, key)
        if v:
            parts.append(v)
    return " && ".join(parts)


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


def rerun_needed(wt, main_files, ticket_files):
    """(rerun?, modules label) per the rerun rule."""
    graph = module_graph(wt)
    if not graph:
        return True, "no module graph"
    mods, deps = graph
    theirs, shared = to_modules(mods, main_files)
    mine, _ = to_modules(mods, ticket_files)
    label = ",".join(sorted(theirs | mine)) or "-"
    if shared:
        return True, label + " +shared build setup"
    structure, _ = profile_line(wt, "structure")
    for m in re.findall(r":([A-Za-z0-9_.:-]+)", structure or ""):
        parts = m.split(":")
        if any(":".join(parts[:i]) in mods and ":".join(parts[:i]) in theirs
               for i in range(1, len(parts) + 1)):
            return True, label + " +structure rules"
    for t in mine:
        for m in theirs:
            if t == m or m in closure(deps, t) or t in closure(deps, m):
                return True, label
    return False, label


def sha7(wt):
    return out("git", "rev-parse", "--short=7", "HEAD", cwd=wt)


def names(wt, *rng):
    return [l for l in out("git", "diff", "--name-only", *rng, cwd=wt).splitlines() if l]


LOCK_WAIT_S = 30
LOCK_STALE_S = 120


class Queue:
    """JSONL queue, edited only under a mkdir lock (main_health ledger style)."""

    def __init__(self, path):
        self.path = Path(path)
        self.lock = Path(str(path) + ".lock")

    def read(self):
        if not self.path.exists():
            return []
        return [json.loads(l) for l in self.path.read_text().splitlines() if l.strip()]

    def update(self, fn):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.time() + LOCK_WAIT_S
        while True:
            try:
                self.lock.mkdir()
                break
            except FileExistsError:
                try:
                    if time.time() - self.lock.stat().st_mtime > LOCK_STALE_S:
                        self.lock.rmdir()
                        continue
                except FileNotFoundError:
                    continue
                if time.time() > deadline:
                    fail(f"queue locked > {LOCK_WAIT_S}s: {self.lock}")
                time.sleep(0.1)
        try:
            recs = fn(self.read())
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text("".join(json.dumps(r) + "\n" for r in recs))
            tmp.replace(self.path)
        finally:
            self.lock.rmdir()


def cmd_enqueue(a):
    wt = str(Path(a.worktree).resolve())
    if not Path(wt).is_dir():
        fail(f"no worktree at {wt}")
    e = {"nn": a.nn, "worktree": wt,
         "branch": out("git", "rev-parse", "--abbrev-ref", "HEAD", cwd=wt),
         "head": out("git", "rev-parse", "HEAD", cwd=wt),
         "base": out("git", "merge-base", "HEAD", "origin/main", cwd=wt),
         "title": a.title, "body_file": str(Path(a.body_file).resolve()),
         "no_merge": a.no_merge, "red_fix": a.red_fix}
    Queue(a.queue).update(lambda recs: [r for r in recs if r["nn"] != a.nn] + [e])
    print(f"queued {a.nn} @ {e['head'][:7]} ({e['branch']})")
    return 0


def land(a):
    q = Queue(a.queue)
    out_ = {"results": {}, "slices": []}

    def emit(nn, result, **kw):
        print(json.dumps({"nn": nn, "result": result, **kw}), flush=True)
        out_["results"][nn] = result
        if result != "requeued":
            q.update(lambda recs: [r for r in recs if r["nn"] != nn])

    def requeue(entries, reason):
        for e in entries:
            emit(e["nn"], "requeued", reason=reason)

    recs = []
    for r in q.read():
        if Path(r["worktree"]).is_dir():
            recs.append(r)
        else:
            emit(r["nn"], "invalid", reason=f"no worktree at {r['worktree']}")
    if not recs:
        return 0 if not out_["results"] else 1

    mh = [sys.executable, str(HERE / "main_health.py")]

    def status(wt):
        s = subprocess.run(mh + ["status"], cwd=wt, capture_output=True, text=True)
        if s.returncode not in (0, 3):
            fail(f"main_health status failed: {s.stderr.strip()}")
        return s

    st = status(recs[0]["worktree"])
    red_start = st.returncode == 3
    if red_start:
        fx = next((r for r in recs if r.get("red_fix")), None)
        if not fx:
            print("main red; lane paused")
            print(st.stdout.strip())
            return 3
        cands = [fx]
    elif recs[0].get("no_merge") or recs[0].get("red_fix"):
        cands = [recs[0]]
    else:
        cands = []
        for r in recs:
            if len(cands) >= a.max or r.get("no_merge") or r.get("red_fix"):
                break
            cands.append(r)

    wt0 = cands[0]["worktree"]
    common = Path(out("git", "rev-parse", "--path-format=absolute", "--git-common-dir", cwd=wt0))
    logdir = q.path.resolve().parent.parent / "logs"
    suites = [0]
    cmd = suite_command(wt0)
    cmd_run = (["build-slot"] if shutil.which("build-slot") else []) + ["bash", "-c", cmd]

    def suite(prefix):
        top = prefix[-1]
        suites[0] += 1
        logdir.mkdir(parents=True, exist_ok=True)
        log = logdir / f"lane-{'-'.join(e['nn'] for e in prefix)}-{top['head_t'][:7]}.log"
        with log.open("w") as f:
            rc = subprocess.run(cmd_run, cwd=top["worktree"], stdout=f, stderr=subprocess.STDOUT).returncode
        return rc, str(log)

    green, base, pending = [], None, []
    for rnd in range(1, MAX_ROUNDS + 1):
        run("git", "fetch", "origin", cwd=wt0)
        base = out("git", "rev-parse", "origin/main", cwd=wt0)
        stack, pending, prev = [], [], base
        for e in cands:
            wt = e["worktree"]
            run("git", "checkout", "-q", "-B", e["branch"], e["head"], cwd=wt)
            if run("git", "rebase", "--onto", prev, e["base"], cwd=wt, check=False).returncode:
                files = out("git", "diff", "--name-only", "--diff-filter=U", cwd=wt).splitlines()
                run("git", "rebase", "--abort", cwd=wt, check=False)
                pending.append((e["nn"], "conflict", {"files": files}))
                continue
            e = dict(e, head_t=out("git", "rev-parse", "HEAD", cwd=wt),
                     tree=out("git", "rev-parse", "HEAD^{tree}", cwd=wt))
            stack.append(e)
            prev = e["head_t"]
        green = stack
        if stack:
            rc, log = suite(stack)
            if rc:
                logs, lo, hi = {len(stack): log}, 0, len(stack)
                while hi - lo > 1:
                    mid = (lo + hi) // 2
                    rc2, log2 = suite(stack[:mid])
                    if rc2:
                        hi, logs[mid] = mid, log2
                    else:
                        lo = mid
                pending.append((stack[hi - 1]["nn"], "red", {"log": logs[hi]}))
                pending += [(e["nn"], "requeued", {"reason": "stacked on a red ticket"}) for e in stack[hi:]]
                green = stack[:lo]
        if not green:
            break
        run("git", "fetch", "origin", cwd=wt0)
        moved = out("git", "rev-parse", "origin/main", cwd=wt0)
        if moved == base:
            break
        top = green[-1]
        again, label = rerun_needed(top["worktree"], names(wt0, f"{base}..{moved}"),
                                    names(top["worktree"], base, top["head_t"]))
        k = out("git", "rev-list", "--count", f"{base}..{moved}", cwd=wt0)
        print(f"merge: {','.join(e['nn'] for e in green)} main moved {k} commits — "
              f"{'rerun' if again else 'push'} ({label})")
        if not again:
            break
        if rnd == MAX_ROUNDS:
            requeue(cands, "main keeps moving")
            return 1
    for nn, result, kw in pending:
        emit(nn, result, **kw)
    if not green:
        return 1

    nns = ",".join(e["nn"] for e in green)
    top7 = green[-1]["head_t"][:7]
    print(f"merge: batch {nns} suite green @ {top7} ({suites[0]} suites)")
    prev_t, merged = base, 0
    for i, e in enumerate(green):
        rest = green[i:]
        wt = e["worktree"]
        if not e.get("red_fix") and status(wt).returncode == 3:
            requeue(rest, "main red")
            break
        run("git", "fetch", "origin", cwd=wt)
        main = out("git", "rev-parse", "origin/main", cwd=wt)
        if i > 0 or main != base:
            if run("git", "rebase", "--onto", "origin/main", prev_t, cwd=wt, check=False).returncode:
                run("git", "rebase", "--abort", cwd=wt, check=False)
                requeue(rest, "main moved: rebase conflict")
                break
        if out("git", "rev-parse", "HEAD^{tree}", cwd=wt) != e["tree"]:
            files = names(wt, prev_t, "origin/main")
            again, label = (rerun_needed(wt, files, names(wt, prev_t, green[-1]["head_t"]))
                            if files else (True, "tree differs"))
            k = int(out("git", "rev-list", "--count", f"{base}..origin/main", cwd=wt)) - merged
            print(f"merge: {','.join(x['nn'] for x in rest)} main moved {k} commits — "
                  f"{'rerun' if again else 'push'} ({label})")
            if again:
                requeue(rest, "main moved: related")
                break
        head = out("git", "rev-parse", "HEAD", cwd=wt)
        run("git", "push", "-u", "--force-with-lease", "origin", "HEAD", cwd=wt)
        body = Path(e["body_file"]).read_text()
        check = f"**check:** local suite green on batch top {top7} (tickets {nns}); no PR CI by design"
        if re.search(r"^\*\*check:\*\*.*$", body, re.M):
            body = re.sub(r"^\*\*check:\*\*.*$", lambda _: check, body, flags=re.M)
        else:
            body = body.rstrip("\n") + "\n" + check + "\n"
        bf = q.path.resolve().parent / f"body-{e['nn']}.md"
        bf.write_text(body)
        view = run("gh", "pr", "view", e["branch"], "--json", "number,url,state", cwd=wt, check=False)
        info = json.loads(view.stdout) if view.returncode == 0 and view.stdout.strip() else {}
        if info.get("state") == "OPEN":
            pr, url = str(info["number"]), info["url"]
        else:
            c = run("gh", "pr", "create", "--base", "main", "--title", e["title"],
                    "--body-file", str(bf), cwd=wt, check=False)
            m = re.search(r"/pull/(\d+)", c.stdout)
            if c.returncode or not m:
                requeue(rest, f"gh pr create failed: {(c.stderr or c.stdout).strip()}")
                break
            url, pr = c.stdout.strip().splitlines()[-1], m.group(1)
        if e.get("no_merge"):
            emit(e["nn"], "waiting_user", pr=int(pr), url=url)
            continue
        if e.get("red_fix") and status(wt).returncode == 3:
            claim = subprocess.run(mh + ["claim", "--who", a.who, "--culprit", e["red_fix"], "--fix-pr", pr],
                                   cwd=wt, capture_output=True, text=True)
            if claim.returncode:
                emit(e["nn"], "claim_refused", pr=int(pr), reason=(claim.stderr or claim.stdout).strip())
                break
            print(claim.stdout.strip())
        m = run("gh", "pr", "merge", pr, "--squash", "--delete-branch", "--match-head-commit", head,
                cwd=wt, check=False)
        if m.returncode:
            requeue(rest, f"merge refused for PR #{pr}: {m.stderr.strip()}")
            break
        run("git", "worktree", "remove", wt, cwd=str(common.parent), check=False)
        emit(e["nn"], "merged", pr=int(pr), sha=head[:7])
        out_["slices"].append(f"slice: {e['nn']} PR #{pr} merged @ {head[:7]}")
        prev_t, merged = e["head_t"], merged + 1
    for line in out_["slices"]:
        print(line)
    return 0 if all(out_["results"].get(e["nn"]) == "merged" for e in cands) else 1


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("enqueue", help="append a ready ticket (replaces the same nn)")
    n.add_argument("--queue", required=True)
    n.add_argument("--nn", required=True)
    n.add_argument("--worktree", required=True)
    n.add_argument("--title", required=True)
    n.add_argument("--body-file", required=True)
    n.add_argument("--no-merge", action="store_true", help="only the user may merge this PR")
    n.add_argument("--red-fix", metavar="CULPRIT", help="this PR fixes red main (sha|#PR)")
    l = sub.add_parser("land", help="land the queue head as one batch")
    l.add_argument("--queue", required=True)
    l.add_argument("--who", required=True, help="run slug (claim owner)")
    l.add_argument("--max", type=int, default=4, help="tickets per batch (default 4)")
    a = p.parse_args()
    return {"enqueue": cmd_enqueue, "land": land}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
