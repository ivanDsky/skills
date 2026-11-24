#!/usr/bin/env python3
"""Main health for trunk runs with `pr-check: none`: one shared ledger per clone.

The ledger lives in the git common dir (shared by every worktree, never
committed): <git-common-dir>/agent-builds/main-health.jsonl, append-only.

  watch   background job (pidfile agent-builds/main-health-watch.pid while
          it runs; the lane starts it after a merge): waits for main's CI (newest queued/running run of
          the main workflow) until nothing is pending, records each run
          attempt that ended success or failure (cancelled runs are skipped;
          a `gh run rerun` is a newer attempt of the same run), prints one
          line per state change. Exit 0 green or unknown, 3 red.
  status  records finished runs newer than the ledger, then reads it:
          green|red|unknown before `gh pr merge`; red adds sha, range, cause,
          first failing tests, claim and held PRs. Exit 0 green or unknown,
          3 red (hold the PR).
  claim   who fixes red main (--culprit sha|PR, --fix-pr N). Refused while
          another owner's claim is younger than 30 min; --takeover after.
  hold    record a PR held back while main is red.
  held    held PRs still open: merge them once main is green.

A red run's ledger record carries `failed_tests` (`Class.method` from
`gh run view <id> --log-failed`, else the failed Gradle task paths; at most
50) and `cause_hint`: infra (no job started, runner lost), download
(Robolectric android-all or Gradle artifact fetch), compile, test or unknown.

`status` and `watch` also print `quarantine expired: <Class> #<N> since
<date>` for each `@Ignore("quarantine #<N> until <YYYY-MM-DD>")` in src/test
or src/androidTest Kotlin sources (resources excluded) whose date is past; exit codes ignore it.

Workflow: --workflow, else PROFILE `- main-check:`, else the basename of
PROFILE `- release:`.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

LOCK_WAIT_S = 30
LOCK_STALE_S = 120
CLAIM_TTL_S = 30 * 60
WATCH_INTERVAL_S = 30
RUN_FIELDS = "databaseId,attempt,headSha,status,conclusion,createdAt"
GREEN, RED = "success", "failure"
FAILED_CAP = 50
SHOWN_TESTS = 3
# `gh run view --log-failed` prefixes each line with "<job>\t<step>\t<timestamp> ".
LOG_PREFIX = re.compile(r"^(?:[^\t]*\t[^\t]*\t)?\ufeff?(?:\d{4}-\d\d-\d\dT[\d:.]+Z ?)?")
TEST_FAILED = re.compile(r"^([\w.$]+) > (.+) FAILED$")
TASK_FAILED = re.compile(r"^> Task (:\S+) FAILED$")
COMPILE_TASK = re.compile(r":(?:compile\w*(?:Kotlin|Java\w*)|ksp\w*Kotlin|kapt\w*Kotlin)$")
DOWNLOAD = re.compile(r"MavenArtifactFetcher|org/robolectric/android-all|Could not GET 'http|Could not download ")
RUNNER_LOST = re.compile(r"runner has received a shutdown signal|lost communication with the server", re.I)
QUARANTINE = re.compile(r'@Ignore\(\s*"quarantine #(\d+) until (\d{4}-\d\d-\d\d)"\s*\)')
CLASS_DECL = re.compile(r"\b(?:class|object)\s+(\w+)")
NEXT_DECL = re.compile(r"\b(?:class|object)\s+(\w+)|\bfun\s+(`[^`]+`|\w+)")


def sh(*cmd, cwd=None, check=True):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=check).stdout.strip()


def gh_json(*args, root):
    try:
        return json.loads(sh("gh", *args, cwd=root) or "null")
    except subprocess.CalledProcessError as e:
        sys.exit(f"main_health: gh {' '.join(args)} failed: {e.stderr.strip()}")


def now():
    return datetime.now(timezone.utc)


def stamp():
    return now().strftime("%Y-%m-%dT%H:%M:%SZ")


def age_s(ts):
    return (now() - datetime.fromisoformat(ts.replace("Z", "+00:00"))).total_seconds()


def profile_value(root, key):
    """`- <key>: <value>` from PROFILE.md (trailing `# comment` stripped)."""
    profile = Path(root) / "PROFILE.md"
    if profile.exists():
        m = re.search(rf"^-\s*{re.escape(key)}:\s*([^\s#]+)", profile.read_text(), re.M)
        if m and not m.group(1).startswith("<"):
            return m.group(1)
    return None


def workflow(root, explicit):
    for v in (explicit, profile_value(root, "main-check"), profile_value(root, "release")):
        if v:
            return Path(v).name
    sys.exit("main_health: no workflow: pass --workflow or set PROFILE `- main-check:` / `- release:`")


class Ledger:
    def __init__(self, root):
        common = Path(sh("git", "rev-parse", "--path-format=absolute", "--git-common-dir", cwd=root))
        d = common / "agent-builds"
        d.mkdir(exist_ok=True)
        self.path = d / "main-health.jsonl"
        self.lock = d / "main-health.lock"
        self.pid = d / "main-health-watch.pid"  # the live `watch`, for the lane's alive check

    def read(self):
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text().splitlines() if line.strip()]

    def append(self, rec, unique_run=False):
        """Append under a mkdir lock; unique_run skips a run attempt that is
        not newer than the newest one recorded (several watchers may see the
        same run, and a bootstrap may race a watcher)."""
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
                    sys.exit(f"main_health: ledger locked > {LOCK_WAIT_S}s: {self.lock}")
                time.sleep(0.1)
        try:
            keys = [run_key(r) for r in self.read() if r.get("type") == "run"] if unique_run else []
            if keys and run_key(rec) <= max(keys):
                return False
            with self.path.open("a") as f:
                f.write(json.dumps(rec) + "\n")
            return True
        finally:
            self.lock.rmdir()


class State:
    """Derived from the ledger: latest run verdict and the open incident
    (everything after the last green run)."""

    def __init__(self, records):
        runs = [r for r in records if r.get("type") == "run"]
        self.last = runs[-1] if runs else None
        greens = [i for i, r in enumerate(records) if r.get("type") == "run" and r["conclusion"] == GREEN]
        self.green = records[greens[-1]] if greens else None
        start = greens[-1] + 1 if greens else 0
        incident = records[start:]
        self.reds = [r for r in incident if r.get("type") == "run" and r["conclusion"] == RED]
        self.claim = None
        for r in incident:
            if r.get("type") != "claim":
                continue
            if self.claim and r["who"] == self.claim["who"]:
                self.claim = {**self.claim, **{k: v for k, v in r.items() if v is not None}}
            else:
                self.claim = dict(r)
        self.holds = [r for r in records if r.get("type") == "hold"]
        self.incident_holds = [r for r in incident if r.get("type") == "hold"]

    @property
    def verdict(self):
        if not self.last:
            return "unknown"
        return "green" if self.last["conclusion"] == GREEN else "red"


def parse_failure(log, jobs=None):
    """`failed_tests` and `cause_hint` from `gh run view --log-failed` text.
    jobs (`gh run view --json jobs`, fetched only for an empty log) tells a
    run whose jobs never started from a log that is merely missing."""
    tests, tasks = {}, {}
    download = runner_lost = False
    for raw in log.splitlines():
        line = LOG_PREFIX.sub("", raw, count=1).rstrip()
        m = TEST_FAILED.match(line)
        if m:
            tests[f"{m[1]}.{m[2]}"] = None
        m = TASK_FAILED.match(line)
        if m:
            tasks[m[1]] = None
        download = download or bool(DOWNLOAD.search(line))
        runner_lost = runner_lost or bool(RUNNER_LOST.search(line))
    never_started = not log.strip() and bool(jobs) and not any(j.get("steps") for j in jobs)
    if runner_lost or never_started:
        hint = "infra"
    elif download:
        hint = "download"
    elif any(COMPILE_TASK.search(t) for t in tasks):
        hint = "compile"
    elif tests:
        hint = "test"
    else:
        hint = "unknown"
    if hint == "compile":
        names = [t for t in tasks if COMPILE_TASK.search(t)] + list(tests)
    else:
        names = list(tests or tasks)
    return {"failed_tests": names[:FAILED_CAP], "cause_hint": hint}


def red_details(root, run_id, attempt):
    """Failure fields for a red run attempt. gh errors (log expired, offline)
    leave the log empty: no names, hint from the jobs when they load, else unknown."""
    view = ["gh", "run", "view", str(run_id), "--attempt", str(attempt)]
    r = subprocess.run([*view, "--log-failed"], cwd=root, capture_output=True, text=True)
    log = r.stdout if r.returncode == 0 else ""
    jobs = None
    if not log.strip():
        r = subprocess.run([*view, "--json", "jobs"], cwd=root, capture_output=True, text=True)
        try:
            jobs = json.loads(r.stdout)["jobs"] if r.returncode == 0 else None
        except (ValueError, KeyError, TypeError):
            jobs = None
    return parse_failure(log, jobs)


def run_key(rec):
    """(run id, attempt): `gh run rerun` keeps the id and bumps the attempt.
    Ledger lines from before attempts were recorded count as attempt 1."""
    return rec["run"], rec.get("attempt") or 1


def run_record(run, who, root):
    rec = {"type": "run", "run": run["databaseId"], "attempt": run.get("attempt") or 1, "sha": run["headSha"],
           "conclusion": run["conclusion"], "created": run["createdAt"], "who": who, "at": stamp()}
    if run["conclusion"] == RED:
        rec.update(red_details(root, rec["run"], rec["attempt"]))
    return rec


def quarantine_target(text, end, path):
    """The annotated class, `Class.method` for an annotated test, else the file."""
    decl = NEXT_DECL.search(text, end)
    if decl and decl[1]:
        return decl[1]
    owners = CLASS_DECL.findall(text, 0, end)
    owner = owners[-1] if owners else path
    return f"{owner}.{decl[2].strip('`')}" if decl else owner


def expired_quarantines(root):
    """`quarantine expired: …` lines for quarantines whose date is before today."""
    listed = sh("git", "ls-files", "-z", "-co", "--exclude-standard", "--",
                ":(glob)**/src/test/**/*.kt", ":(glob)**/src/androidTest/**/*.kt",
                ":(exclude,glob)**/src/*/resources/**", cwd=root, check=False)
    today = datetime.now().date().isoformat()  # local date: the day the quarantine's author meant
    lines = []
    for rel in filter(None, listed.split("\0")):
        f = Path(root) / rel
        if not f.is_file():
            continue
        text = f.read_text(errors="replace")
        for m in QUARANTINE.finditer(text):
            if m[2] < today:
                lines.append(f"quarantine expired: {quarantine_target(text, m.end(), rel)} #{m[1]} since {m[2]}")
    return lines


def print_expired_quarantines(root):
    for line in expired_quarantines(root):
        print(line, flush=True)


def failure_summary(red):
    """`<cause>: <first tests>, +N more`; ledger lines from before the fields read unknown."""
    names = red.get("failed_tests") or []
    hint = red.get("cause_hint", "unknown")
    if not names:
        return hint
    more = len(names) - SHOWN_TESTS
    tail = f", +{more}{'+' if len(names) >= FAILED_CAP else ''} more" if more > 0 else ""
    return f"{hint}: {', '.join(names[:SHOWN_TESTS])}{tail}"


def list_runs(root, wf, limit=30, status=None):
    args = ["run", "list", "--workflow", wf, "--branch", "main", "-L", str(limit), "--json", RUN_FIELDS]
    if status:
        args += ["--status", status]
    return gh_json(*args, root=root) or []


def last_green_sha(root, wf, state):
    if state.green:
        return state.green["sha"]
    runs = list_runs(root, wf, limit=1, status=GREEN)
    return runs[0]["headSha"] if runs else None


def red_line(root, wf, state):
    red = state.reds[-1] if state.reds else state.last
    base = last_green_sha(root, wf, state)
    rng = f"{base[:9]}..{red['sha'][:9]}" if base else f"..{red['sha'][:9]} (no green run found)"
    return f"main red at {red['sha'][:9]} (run {red['run']}), range {rng}; cause {failure_summary(red)}"


def claim_line(state):
    c = state.claim
    if not c:
        return "claim: none (the orchestrator whose merge is the culprit claims)"
    fix = f", fix PR #{c['fix_pr']}" if c.get("fix_pr") else ""
    return f"claim: {c['who']} culprit {c['culprit']}{fix}, {int(age_s(c['at']) // 60)} min ago"


def record_new_runs(root, wf, led, who):
    """Record finished success/failure run attempts newer than the last
    recorded one (a rerun of the same id counts as newer), oldest first; an
    empty ledger takes only the newest. Queried by conclusion: superseded
    pushes cancel most runs, so an unfiltered list can hold no finished run
    at all. Returns them."""
    state = State(led.read())
    floor = run_key(state.last) if state.last else None
    finished = list_runs(root, wf, limit=10, status=GREEN) + list_runs(root, wf, limit=10, status=RED)
    key = lambda r: (r["databaseId"], r.get("attempt") or 1)
    done = sorted((r for r in finished if floor is None or key(r) > floor), key=key)
    if floor is None:
        done = done[-1:]
    return [r for r in done if led.append(run_record(r, who, root), unique_run=True)]


def cmd_watch(a, root, wf, led):
    led.pid.write_text(str(os.getpid()))
    try:
        return watch_loop(a, root, wf, led)
    finally:
        led.pid.unlink(missing_ok=True)


def watch_loop(a, root, wf, led):
    prev = State(led.read()).verdict
    changed = False
    while True:
        runs = list_runs(root, wf)
        for _ in record_new_runs(root, wf, led, a.who):
            state = State(led.read())
            if state.verdict != prev:
                print(red_line(root, wf, state) if state.verdict == "red"
                      else f"main green at {state.last['sha'][:9]} (run {state.last['run']})", flush=True)
                prev, changed = state.verdict, True
        pending = [r for r in runs if r["status"] != "completed"]
        if not pending:
            break
        newest = max(pending, key=lambda r: r["databaseId"])
        # Exit code ignored: success, failure and cancel are all read back from the run list.
        subprocess.run(["gh", "run", "watch", str(newest["databaseId"]), "--exit-status",
                        "-i", str(WATCH_INTERVAL_S)], cwd=root, capture_output=True, text=True)
    state = State(led.read())
    if state.verdict == "red" and not changed:
        print(red_line(root, wf, state), flush=True)
    print_expired_quarantines(root)
    print(f"main {state.verdict}; nothing pending", flush=True)
    return 3 if state.verdict == "red" else 0


def cmd_status(a, root, wf, led):
    try:
        record_new_runs(root, wf, led, "status")
    except SystemExit as e:  # gh_json exits on a gh error: keep the ledger verdict
        print(f"main_health: ledger refresh failed: {str(e.code).removeprefix('main_health: ')}", file=sys.stderr)
    state = State(led.read())
    if state.verdict != "red":
        line = state.verdict if not state.last else f"green at {state.last['sha'][:9]} (run {state.last['run']})"
        print(line)
        print_expired_quarantines(root)
        return 0
    print("red")
    print(red_line(root, wf, state))
    print(claim_line(state))
    held = sorted({h["pr"] for h in state.incident_holds})
    print("held: " + (" ".join(f"#{p}" for p in held) if held else "none"))
    print("hold your PR (`hold --pr N`) unless it is the claimed fix PR")
    print_expired_quarantines(root)
    return 3


def cmd_claim(a, root, wf, led):
    state = State(led.read())
    if state.verdict != "red":
        sys.exit(f"main_health: main is {state.verdict}; nothing to claim")
    c = state.claim
    takeover = False
    if c and c["who"] != a.who:
        age = age_s(c["at"])
        if age < CLAIM_TTL_S:
            sys.exit(f"main_health: claimed — {claim_line(state)}; takeover after {CLAIM_TTL_S // 60} min")
        if not a.takeover:
            sys.exit(f"main_health: stale — {claim_line(state)}; rerun with --takeover to take it")
        if c.get("fix_pr"):
            pr = gh_json("pr", "view", str(c["fix_pr"]), "--json", "state,mergedAt", root=root)
            if pr["state"] == "MERGED" and not any(r["created"] > pr["mergedAt"] for r in state.reds):
                sys.exit(f"main_health: fix PR #{c['fix_pr']} merged and no red run since; wait for the watcher")
        takeover = True
    led.append({"type": "claim", "who": a.who, "culprit": a.culprit, "fix_pr": a.fix_pr,
                "takeover": takeover or None, "at": stamp()})
    print(claim_line(State(led.read())) + (" (takeover)" if takeover else ""))
    return 0


def cmd_hold(a, root, wf, led):
    led.append({"type": "hold", "pr": a.pr, "who": a.who, "at": stamp()})
    print(f"held #{a.pr}; merge it once `status` is green (rerun rule applies)")
    return 0


def cmd_held(a, root, wf, led):
    state = State(led.read())
    seen = {}
    for h in state.holds:
        seen.setdefault(h["pr"], h)
    open_prs = [h for p, h in seen.items()
                if gh_json("pr", "view", str(p), "--json", "state", root=root)["state"] == "OPEN"]
    print(f"main {state.verdict}")
    for h in open_prs:
        print(f"#{h['pr']} held by {h['who']} at {h['at']}")
    if not open_prs:
        print("held: none")
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--workflow", help="workflow file or name; default from PROFILE")
    sub = p.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("watch")
    w.add_argument("--who", default="watcher")
    sub.add_parser("status")
    c = sub.add_parser("claim")
    c.add_argument("--who", required=True)
    c.add_argument("--culprit", required=True)
    c.add_argument("--fix-pr", type=int)
    c.add_argument("--takeover", action="store_true")
    h = sub.add_parser("hold")
    h.add_argument("--pr", type=int, required=True)
    h.add_argument("--who", required=True)
    sub.add_parser("held")
    a = p.parse_args()
    root = sh("git", "rev-parse", "--show-toplevel")
    wf = workflow(root, a.workflow)
    led = Ledger(root)
    return {"watch": cmd_watch, "status": cmd_status, "claim": cmd_claim,
            "hold": cmd_hold, "held": cmd_held}[a.cmd](a, root, wf, led)


if __name__ == "__main__":
    sys.exit(main())
