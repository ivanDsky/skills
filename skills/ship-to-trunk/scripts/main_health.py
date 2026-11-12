#!/usr/bin/env python3
"""Main health for trunk runs with `pr-check: none`: one shared ledger per clone.

The ledger lives in the git common dir (shared by every worktree, never
committed): <git-common-dir>/agent-builds/main-health.jsonl, append-only.

  watch   background job: waits for main's CI (newest queued/running run of
          the main workflow) until nothing is pending, records each run that
          ended success or failure (cancelled runs are skipped), prints one
          line per state change. Exit 0 green or unknown, 3 red.
  status  green|red|unknown before `gh pr merge`; red adds sha, range, claim
          and held PRs. Exit 0 green or unknown, 3 red (hold the PR).
  claim   who fixes red main (--culprit sha|PR, --fix-pr N). Refused while
          another owner's claim is younger than 30 min; --takeover after.
  hold    record a PR held back while main is red.
  held    held PRs still open: merge them once main is green.

Workflow: --workflow, else PROFILE `- main-check:`, else the basename of
PROFILE `- release:`.
"""
import argparse
import json
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
RUN_FIELDS = "databaseId,headSha,status,conclusion,createdAt"
GREEN, RED = "success", "failure"


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

    def read(self):
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text().splitlines() if line.strip()]

    def append(self, rec, unique_run=False):
        """Append under a mkdir lock; unique_run skips a run already recorded
        (several watchers may see the same run)."""
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
            if unique_run and any(r.get("type") == "run" and r["run"] == rec["run"] for r in self.read()):
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


def run_record(run, who):
    return {"type": "run", "run": run["databaseId"], "sha": run["headSha"],
            "conclusion": run["conclusion"], "created": run["createdAt"], "who": who, "at": stamp()}


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
    return f"main red at {red['sha'][:9]} (run {red['run']}), range {rng}"


def claim_line(state):
    c = state.claim
    if not c:
        return "claim: none (the orchestrator whose merge is the culprit claims)"
    fix = f", fix PR #{c['fix_pr']}" if c.get("fix_pr") else ""
    return f"claim: {c['who']} culprit {c['culprit']}{fix}, {int(age_s(c['at']) // 60)} min ago"


def record_new_runs(root, wf, led, who, runs):
    """Record finished success/failure runs newer than the last recorded one,
    oldest first; an empty ledger takes only the newest. Returns them."""
    state = State(led.read())
    floor = state.last["run"] if state.last else None
    done = sorted((r for r in runs if r["status"] == "completed" and r["conclusion"] in (GREEN, RED)
                   and (floor is None or r["databaseId"] > floor)), key=lambda r: r["databaseId"])
    if floor is None:
        done = done[-1:]
    return [r for r in done if led.append(run_record(r, who), unique_run=True)]


def cmd_watch(a, root, wf, led):
    prev = State(led.read()).verdict
    changed = False
    while True:
        runs = list_runs(root, wf)
        for _ in record_new_runs(root, wf, led, a.who, runs):
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
    print(f"main {state.verdict}; nothing pending", flush=True)
    return 3 if state.verdict == "red" else 0


def cmd_status(a, root, wf, led):
    state = State(led.read())
    if not state.last:
        record_new_runs(root, wf, led, "status", list_runs(root, wf))
        state = State(led.read())
    if state.verdict != "red":
        line = state.verdict if not state.last else f"green at {state.last['sha'][:9]} (run {state.last['run']})"
        print(line)
        return 0
    print("red")
    print(red_line(root, wf, state))
    print(claim_line(state))
    held = sorted({h["pr"] for h in state.incident_holds})
    print("held: " + (" ".join(f"#{p}" for p in held) if held else "none"))
    print("hold your PR (`hold --pr N`) unless it is the claimed fix PR")
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
