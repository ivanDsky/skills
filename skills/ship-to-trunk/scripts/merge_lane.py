#!/usr/bin/env python3
"""Merge lane for trunk runs with `pr-check: none`: land one ready ticket.

Run by the orchestrator, one ticket at a time, as one background bash job.
Workers never run it: they push the branch and report ready.

  merge_lane.py land --worktree <path> --title "<conventional title>"
                     --body-file <f> --who <run slug> [--no-merge]
                     [--red-fix <sha|#PR>]

Sequence (merge-loop.md, `pr-check: none`): fetch + rebase onto origin/main,
suite (PROFILE `pr-check: none` comment command, else assemble debug + unit
`runner:` + `structure:`; through `build-slot` when it is on PATH), fetch
again and apply the rerun rule, push with lease, `gh pr create` (an open PR
for the branch is reused: re-landing a held, approved or refused PR is
safe),
`main_health.py status`, `gh pr merge <n> --squash --delete-branch
--match-head-commit <sha>`, remove the worktree.

Rerun rule (mechanical): main moved while the suite ran -> rerun (back to
the rebase, at most 3 rounds) when a module main changed and a module the
ticket changed are the same or depend on each other transitively (modules
from `include(...)` in settings.gradle.kts, dependencies from `project(":x")`
and `projects.x` in the build files), when main touched `build-logic/`,
`gradle/`, root build/settings/properties files or the `structure:` rules
module, or when no module graph is readable. Otherwise push the green head.

Exit codes:
  0  merged: prints `slice: <NN> PR #<n> merged @ <sha7>` (+ the
     `merge: ... rerun|push` ledger line when main moved)
  3  main is red: PR created and held (`main_health.py hold`), worktree kept
  4  rebase conflict: rebase aborted, conflicting files printed
  5  suite red (log path printed), or main kept moving for 3 rounds
  6  --no-merge: suite green, PR open, URL printed (live change, flip PR)
  1  anything else (gh/git failure, merge refused, --red-fix claim
     refused): message on stderr, worktree kept

--red-fix <sha|#PR>: this PR is the fix of red main (culprit given). While
main is red the lane records `main_health.py claim --who <who> --culprit
<x> --fix-pr <n>` (refused claim -> exit 1, nothing merged) and merges
despite the red status; local suite included. Without it a red main holds.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
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


def land(a):
    wt = str(Path(a.worktree).resolve())
    if not Path(wt).is_dir():
        fail(f"no worktree at {wt}")
    branch = out("git", "rev-parse", "--abbrev-ref", "HEAD", cwd=wt)
    common = Path(out("git", "rev-parse", "--path-format=absolute", "--git-common-dir", cwd=wt))
    root = str(common.parent)
    slug, _, tail = branch.rpartition("/")
    slug = slug or a.who
    nn = re.match(r"(\d+)", tail)
    nn = nn.group(1) if nn else tail
    mh = [sys.executable, str(HERE / "main_health.py")]
    ledger = []
    cmd = suite_command(wt)
    if shutil.which("build-slot"):
        cmd_run = ["build-slot", "bash", "-c", cmd]
    else:
        cmd_run = ["bash", "-c", cmd]

    for rnd in range(1, MAX_ROUNDS + 1):
        run("git", "fetch", "origin", cwd=wt)
        if run("git", "rebase", "origin/main", cwd=wt, check=False).returncode:
            files = out("git", "diff", "--name-only", "--diff-filter=U", cwd=wt)
            run("git", "rebase", "--abort", cwd=wt, check=False)
            print("rebase conflict; rebase aborted. Conflicting files:")
            print(files)
            return 4
        base = out("git", "rev-parse", "origin/main", cwd=wt)
        log = Path(root) / ".scratch" / slug / "logs" / f"lane-{nn}-{sha7(wt)}.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("w") as f:
            rc = subprocess.run(cmd_run, cwd=wt, stdout=f, stderr=subprocess.STDOUT).returncode
        if rc:
            print(f"suite red (exit {rc}); log: {log}")
            return 5
        run("git", "fetch", "origin", cwd=wt)
        moved = out("git", "rev-parse", "origin/main", cwd=wt)
        if moved == base:
            break
        k = out("git", "rev-list", "--count", f"{base}..{moved}", cwd=wt)
        again, label = rerun_needed(wt, names(wt, f"{base}..{moved}"), names(wt, base, "HEAD"))
        ledger.append(f"merge: {nn} main moved {k} commits — {'rerun' if again else 'push'} ({label})")
        if not again:
            break
        if rnd == MAX_ROUNDS:
            print("main keeps moving; " + ledger[-1])
            print(f"last suite log: {log}")
            return 5

    head = out("git", "rev-parse", "HEAD", cwd=wt)
    run("git", "push", "-u", "--force-with-lease", "origin", "HEAD", cwd=wt)
    existing = run("gh", "pr", "view", branch, "--json", "number,url,state", cwd=wt, check=False)
    info = json.loads(existing.stdout) if existing.returncode == 0 and existing.stdout.strip() else {}
    if info.get("state") == "OPEN":
        pr, url = str(info["number"]), info["url"]
    else:
        created = run("gh", "pr", "create", "--base", "main", "--title", a.title,
                      "--body-file", a.body_file, cwd=wt, check=False)
        m = re.search(r"/pull/(\d+)", created.stdout)
        if created.returncode or not m:
            fail(f"gh pr create failed: {created.stderr.strip() or created.stdout.strip()}")
        url, pr = created.stdout.strip().splitlines()[-1], m.group(1)

    status = subprocess.run(mh + ["status"], cwd=wt, capture_output=True, text=True)
    if status.returncode == 3 and a.red_fix:
        claim = subprocess.run(mh + ["claim", "--who", a.who, "--culprit", a.red_fix, "--fix-pr", pr],
                               cwd=wt, capture_output=True, text=True)
        if claim.returncode:
            fail(f"claim refused for fix PR #{pr}: {(claim.stderr or claim.stdout).strip()}; "
                 f"PR open, worktree kept at {wt}")
        print(claim.stdout.strip())
    elif status.returncode == 3:
        print(status.stdout.strip())
        print(run(*mh, "hold", "--pr", pr, "--who", a.who, cwd=wt).stdout.strip())
        print(f"main red: PR #{pr} held, worktree kept at {wt}\n{url}")
        return 3
    elif status.returncode:
        fail(f"main_health status failed: {status.stderr.strip()}")
    if a.no_merge:
        print(f"suite green on {head[:7]}; PR #{pr} open, not merged (--no-merge): {url}")
        return 6

    merged = run("gh", "pr", "merge", pr, "--squash", "--delete-branch",
                 "--match-head-commit", head, cwd=wt, check=False)
    if merged.returncode:
        fail(f"gh pr merge #{pr} refused: {merged.stderr.strip()}; PR open, worktree kept at {wt}")
    run("git", "worktree", "remove", wt, cwd=root, check=False)
    print(f"slice: {nn} PR #{pr} merged @ {head[:7]}")
    for line in ledger:
        print(line)
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    l = sub.add_parser("land", help="land one ready ticket")
    l.add_argument("--worktree", required=True)
    l.add_argument("--title", required=True)
    l.add_argument("--body-file", required=True)
    l.add_argument("--who", required=True, help="run slug (ledger owner, log dir fallback)")
    l.add_argument("--no-merge", action="store_true", help="stop after the PR opens (exit 6)")
    l.add_argument("--red-fix", metavar="CULPRIT", help="this PR fixes red main (sha|#PR): claim and merge despite red")
    a = p.parse_args()
    a.body_file = str(Path(a.body_file).resolve())
    return land(a)


if __name__ == "__main__":
    sys.exit(main())
