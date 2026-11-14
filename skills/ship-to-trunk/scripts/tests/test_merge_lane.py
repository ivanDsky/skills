"""merge_lane.py: PROFILE parsing on the real PuzzleBox wording, and the lane
end to end against real git repos (bare origin, worktrees) with a stub `gh`.

Regressions: #31 (suite_command took the first backticked text of the
`pr-check: none` comment), no local `main` checkout needed, true PR state after
gh's "'main' is already checked out" error, one lane per queue.
Run: python3 -m pytest skills/ship-to-trunk/scripts/tests
"""
import json
import os
import re
import subprocess
import sys
import time

import pytest

import merge_lane as ml
from conftest import SCRIPTS, git, init_repo

SCRIPT = SCRIPTS / "merge_lane.py"
PR_URL = "https://github.com/example/PuzzleBox/pull/42"


def write_profile(wt, comment_line):
    (wt / "PROFILE.md").write_text(f"## Delivery\n- pr-check: none   # {comment_line}\n"
                                   "- runner: ./gradlew :app:testDebugUnitTest\n"
                                   "- structure: ./gradlew :konsist:test\n")


# ---------------------------------------------------------------- suite_command

def test_suite_command_real_profile_uses_the_gate_command(tmp_path, profile_text):
    (tmp_path / "PROFILE.md").write_text(profile_text)
    (tmp_path / "gradlew").write_text("#!/bin/sh\n")
    assert ml.suite_command(tmp_path) == "./gradlew assembleDebug test"


def test_suite_command_real_profile_without_script_assembles_from_keys(tmp_path, profile_text):
    """Gate script absent -> debug + `runner:` + `structure:` from the real keys."""
    (tmp_path / "PROFILE.md").write_text(profile_text)
    cmd = ml.suite_command(tmp_path)
    assert cmd == "./gradlew assembleDebug && ./gradlew :app:testDebugUnitTest && ./gradlew :konsist:test"
    assert "gh pr checks" not in cmd


@pytest.mark.parametrize("comment", [
    # #31: the first backticked text names the key itself, not a command.
    "`pr-check: none` — no PR CI; gate is `./gradlew assembleDebug test` on the rebased branch",
    "`pr-check` stays none; skip `gh pr checks` waits; local gate `./gradlew assembleDebug test`",
])
def test_suite_command_skips_backticked_prose_31(tmp_path, comment):
    write_profile(tmp_path, comment)
    (tmp_path / "gradlew").write_text("#!/bin/sh\n")
    assert ml.suite_command(tmp_path) == "./gradlew assembleDebug test"


def test_suite_command_never_returns_prose_31(tmp_path):
    write_profile(tmp_path, "`pr-check: none` and `gh pr checks` are not commands")
    cmd = ml.suite_command(tmp_path)
    assert "pr-check" not in cmd and "gh pr" not in cmd
    assert cmd.startswith("./gradlew assembleDebug")


def test_profile_line_splits_value_and_comment(tmp_path, profile_text):
    (tmp_path / "PROFILE.md").write_text(profile_text)
    value, comment = ml.profile_line(tmp_path, "pr-check")
    assert value == "none" and comment.startswith("merge gate: `./gradlew assembleDebug test`")
    assert ml.profile_line(tmp_path, "structure")[0] == "./gradlew :konsist:test"
    assert ml.profile_line(tmp_path, "nope") == (None, None)


# ----------------------------------------------------------------- rerun rule

def gradle_project(root, edges):
    """edges {module: [deps]} -> settings + per-module build files."""
    (root / "settings.gradle.kts").write_text("".join(f'include(":{m}")\n' for m in edges))
    for m, deps in edges.items():
        (root / m).mkdir(exist_ok=True)
        (root / m / "build.gradle.kts").write_text(
            "dependencies {\n" + "".join(f'    implementation(project(":{d}"))\n' for d in deps) + "}\n")


def test_rerun_rule(tmp_path):
    gradle_project(tmp_path, {"app": ["core"], "core": [], "feature": ["core"], "docs": []})
    (tmp_path / "PROFILE.md").write_text("- structure: ./gradlew :konsist:test\n")
    assert ml.rerun_needed(tmp_path, ["docs/a.md"], ["app/A.kt"])[0] is False
    assert ml.rerun_needed(tmp_path, ["core/C.kt"], ["app/A.kt"])[0] is True       # dependency
    assert ml.rerun_needed(tmp_path, ["feature/F.kt"], ["app/A.kt"])[0] is False   # siblings
    again, label = ml.rerun_needed(tmp_path, ["gradle/libs.versions.toml"], ["app/A.kt"])
    assert again and "shared build setup" in label
    assert ml.rerun_needed(tmp_path / "missing", ["x"], ["y"]) == (True, "no module graph")


# ----------------------------------------------------------- lane end to end

class Lane:
    """origin (bare) <- main checkout `co` <- ticket worktree `wt` on branch ticket/1."""

    def __init__(self, tmp_path, profile_text):
        self.root = tmp_path / "lane"
        self.origin = self.root / "origin.git"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(self.origin)], check=True)
        self.co = init_repo(self.root / "co", {
            "PROFILE.md": profile_text.replace("./gradlew assembleDebug test", "./suite.sh"),
            "suite.sh": "#!/bin/sh\nexit 0\n",
        }, executable=("suite.sh",))
        git("remote", "add", "origin", str(self.origin), cwd=self.co)
        git("push", "-q", "-u", "origin", "main", cwd=self.co)
        self.wt = self.root / "wt1"
        git("worktree", "add", "-q", "-b", "ticket/1", str(self.wt), "origin/main", cwd=self.co)
        (self.wt / "feature.txt").write_text("hello\n")
        git("add", "feature.txt", cwd=self.wt)
        git("commit", "-q", "-m", "feat: one", cwd=self.wt)
        self.queue = self.root / ".scratch" / "run" / "lane" / "queue.jsonl"
        self.body = self.root / "body.md"
        self.body.write_text("## Summary\nthing\n")

    def lane(self, *args, **kw):
        return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, timeout=60, **kw)

    def enqueue(self, nn="01", *extra):
        r = self.lane("enqueue", "--queue", str(self.queue), "--nn", nn, "--worktree", str(self.wt),
                      "--title", "feat: one", "--body-file", str(self.body), *extra)
        assert r.returncode == 0, r.stderr
        return r

    def land(self):
        return self.lane("land", "--queue", str(self.queue), "--who", "test-run")

    def queue_nns(self):
        return [json.loads(l)["nn"] for l in self.queue.read_text().splitlines() if l.strip()]

    @staticmethod
    def results(r):
        return [json.loads(l) for l in r.stdout.splitlines() if l.startswith("{")]


@pytest.fixture
def lane(tmp_path, gh, profile_text, real_runs):
    gh.set(runs=real_runs, create_url=PR_URL, create_branch="ticket/1")
    return Lane(tmp_path, profile_text)


def test_land_merges_without_main_checked_out_locally(lane, gh):
    # No local main anywhere: the checkout is detached and the branch is gone.
    git("checkout", "-q", "--detach", cwd=lane.co)
    git("branch", "-q", "-D", "main", cwd=lane.co)
    lane.enqueue()
    r = lane.land()
    assert r.returncode == 0, r.stdout + r.stderr
    assert lane.results(r) == [{"nn": "01", "result": "merged", "pr": 42, "sha": lane.results(r)[0]["sha"]}]
    assert re.search(r"^merge: batch 01 suite green @ \w{7} \(1 suites\)$", r.stdout, re.M)
    assert re.search(r"^slice: 01 PR #42 merged @ \w{7}$", r.stdout, re.M)
    merge = [c for c in gh.calls() if c[:2] == ["pr", "merge"]]
    assert merge and "--delete-branch" not in merge[0] and merge[0][2] == "42"
    assert not lane.wt.exists()
    assert git("branch", "--list", "main", cwd=lane.co) == ""      # lane never recreated it
    assert lane.queue_nns() == []
    assert (gh.dir / "slot.log").read_text().strip() == "bash -c ./suite.sh"  # suite goes through build-slot
    # branch pushed then deleted on origin
    assert git("branch", "--list", "ticket/1", cwd=lane.origin) == ""


def test_already_checked_out_error_but_pr_merged_counts_as_merged(lane, gh):
    gh.set(merge="checkout_error")
    lane.enqueue()
    r = lane.land()
    assert r.returncode == 0, r.stdout + r.stderr
    assert lane.results(r)[0]["result"] == "merged"
    assert lane.queue_nns() == []
    assert any(c[:3] == ["pr", "view", "42"] for c in gh.calls())  # state read back, not assumed


def test_already_checked_out_error_but_pr_still_open_is_not_merged(lane, gh):
    gh.set(merge="checkout_error_open")
    lane.enqueue()
    r = lane.land()
    assert r.returncode == 1
    res = lane.results(r)
    assert res[0]["result"] == "requeued" and "merge refused for PR #42" in res[0]["reason"]
    assert lane.wt.exists() and lane.queue_nns() == ["01"]
    assert not any(l.startswith("slice:") for l in r.stdout.splitlines())


def test_refused_merge_requeues(lane, gh):
    gh.set(merge="refused")
    lane.enqueue()
    r = lane.land()
    assert r.returncode == 1 and lane.results(r)[0]["result"] == "requeued"
    assert lane.queue_nns() == ["01"]


def test_no_merge_ticket_waits_for_user_with_pr_open(lane, gh):
    lane.enqueue("01", "--no-merge")
    r = lane.land()
    assert r.returncode == 1
    assert lane.results(r) == [{"nn": "01", "result": "waiting_user", "pr": 42, "url": PR_URL}]
    assert not any(c[:2] == ["pr", "merge"] for c in gh.calls())


def test_red_main_pauses_the_lane_and_touches_nothing(lane, gh, real_runs):
    gh.set(runs=real_runs[4:])  # real window whose newest finished run is the failure
    lane.enqueue()
    r = lane.land()
    assert r.returncode == 3
    assert r.stdout.splitlines()[0] == "main red; lane paused"
    assert lane.queue_nns() == ["01"]
    assert not any(c[:2] in (["pr", "create"], ["pr", "merge"]) for c in gh.calls())


def test_failing_suite_marks_ticket_red_and_merges_nothing(lane, gh):
    (lane.wt / "suite.sh").write_text("#!/bin/sh\necho boom\nexit 1\n")
    git("commit", "-q", "-am", "break suite", cwd=lane.wt)
    lane.enqueue()
    r = lane.land()
    res = lane.results(r)
    assert r.returncode == 1 and res[0]["result"] == "red"
    assert "boom" in open(res[0]["log"]).read()
    assert not any(c[:2] == ["pr", "merge"] for c in gh.calls())


def test_invalid_when_worktree_has_uncommitted_changes(lane):
    lane.enqueue()
    (lane.wt / "feature.txt").write_text("dirty\n")
    r = lane.land()
    assert r.returncode == 1 and lane.results(r)[0]["result"] == "invalid"


def test_enqueue_replaces_same_nn(lane):
    lane.enqueue("01")
    lane.enqueue("01")
    assert lane.queue_nns() == ["01"]


# -------------------------------------------------------------------- lane lock

def test_second_land_exits_4_while_a_lane_is_held(lane, gh):
    lane.enqueue()
    with ml.LaneLock(lane.queue):  # this process is the live owner
        r = lane.land()
        assert r.returncode == 4 and "lane busy" in r.stderr
        assert lane.queue_nns() == ["01"]
        assert not any(c[:2] == ["pr", "create"] for c in gh.calls())
    assert not (lane.queue.parent / "queue.jsonl.lane").exists()  # released on exit


def test_two_concurrent_lands_only_one_runs(lane, gh):
    (lane.wt / "suite.sh").write_text("#!/bin/sh\nsleep 2\nexit 0\n")
    git("commit", "-q", "-am", "slow suite", cwd=lane.wt)
    lane.enqueue()
    first = subprocess.Popen([sys.executable, str(SCRIPT), "land", "--queue", str(lane.queue), "--who", "a"],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    lock = lane.queue.parent / "queue.jsonl.lane"
    deadline = time.time() + 20
    while not lock.exists() and time.time() < deadline:
        time.sleep(0.05)
    assert lock.exists()
    second = lane.lane("land", "--queue", str(lane.queue), "--who", "b")
    out1, err1 = first.communicate(timeout=60)
    assert second.returncode == 4 and "lane busy" in second.stderr
    assert first.returncode == 0, out1 + err1
    assert len([c for c in gh.calls() if c[:2] == ["pr", "merge"]]) == 1


def test_stale_lane_lock_with_dead_owner_is_reclaimed(tmp_path):
    dead = subprocess.Popen([sys.executable, "-c", "pass"])
    dead.wait()
    q = tmp_path / "q" / "queue.jsonl"
    (tmp_path / "q" / "queue.jsonl.lane").mkdir(parents=True)
    (tmp_path / "q" / "queue.jsonl.lane" / "pid").write_text(str(dead.pid))
    with ml.LaneLock(q) as lock:
        assert (lock.path / "pid").read_text() == str(os.getpid())
    assert not lock.path.exists()
