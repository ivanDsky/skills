"""main_health.py against the real PuzzleBox PROFILE wording and real `gh` JSON.

Regression: #26 — `unknown` reported because most recent runs were cancelled.
Run: python3 -m pytest skills/ship-to-trunk/scripts/tests
"""
import subprocess
import sys

import pytest

from conftest import SCRIPTS, init_repo

SCRIPT = SCRIPTS / "main_health.py"
SUPERSEDED = "cancelled"


@pytest.fixture
def repo(tmp_path, profile_text):
    return init_repo(tmp_path / "repo", {"PROFILE.md": profile_text})


def mh(repo, *args):
    r = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=repo, capture_output=True, text=True, timeout=30)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def test_workflow_comes_from_release_basename_of_real_profile(repo, gh, real_runs):
    gh.set(runs=real_runs)
    assert mh(repo, "status")[0] == 0
    run_list = [c for c in gh.calls() if c[:2] == ["run", "list"]]
    assert run_list and all(c[c.index("--workflow") + 1] == "release.yml" for c in run_list)
    assert all(c[c.index("--branch") + 1] == "main" for c in run_list)


def test_real_runs_green_at_newest_success(repo, gh, real_runs):
    gh.set(runs=real_runs)
    rc, out, _ = mh(repo, "status")
    assert (rc, out) == (0, "green at 889eafb35 (run 43640083876)")


def test_most_recent_runs_cancelled_is_not_unknown(repo, gh, real_runs):
    """#26: 28 of 30 runs cancelled (newest 28 here, re-labelled from real rows)."""
    runs = [dict(r, conclusion=SUPERSEDED) for r in real_runs[:28]] + real_runs[28:]
    assert [r["conclusion"] for r in runs].count(SUPERSEDED) >= 28
    gh.set(runs=runs)
    rc, out, _ = mh(repo, "status")
    assert rc == 0
    assert out.startswith("green at ") and out != "unknown"
    assert out == "green at " + runs[28]["headSha"][:9] + " (run 43619431758)"  # newest real success below the cancelled block


def test_cancelled_runs_do_not_hide_a_real_failure(repo, gh, real_runs):
    """Real window: three cancelled runs newer than the one real failure."""
    window = real_runs[4:]  # cancelled x3, failure, then successes
    assert [r["conclusion"] for r in window[:4]] == ["cancelled"] * 3 + ["failure"]
    gh.set(runs=window)
    rc, out, _ = mh(repo, "status")
    lines = out.splitlines()
    assert rc == 3 and lines[0] == "red"
    assert "run 43636165873" in lines[1]
    assert lines[2].startswith("claim: none")
    assert lines[3] == "held: none"


def test_only_cancelled_runs_is_unknown_not_red(repo, gh, real_runs):
    gh.set(runs=[dict(r, conclusion=SUPERSEDED) for r in real_runs[:7]])
    rc, out, _ = mh(repo, "status")
    assert (rc, out) == (0, "unknown")


def test_ledger_lives_in_git_common_dir_not_the_tree(repo, gh, real_runs):
    gh.set(runs=real_runs)
    mh(repo, "status")
    assert (repo / ".git" / "agent-builds" / "main-health.jsonl").is_file()
    assert not (repo / "agent-builds").exists()


def test_claim_hold_and_takeover_rules(repo, gh, real_runs, real_prs):
    gh.set(runs=real_runs[4:], prs=real_prs)
    assert mh(repo, "status")[0] == 3
    rc, out, _ = mh(repo, "claim", "--who", "orch-a", "--culprit", "43636165873", "--fix-pr", "971")
    assert rc == 0 and "orch-a culprit 43636165873, fix PR #971" in out
    rc, _, err = mh(repo, "claim", "--who", "orch-b", "--culprit", "x")
    assert rc == 1 and "claimed" in err
    assert mh(repo, "hold", "--pr", "970", "--who", "orch-b")[0] == 0
    assert mh(repo, "hold", "--pr", "971", "--who", "orch-b")[0] == 0
    # `held` lists only PRs still open: 970 is the real merged PR, 971 the real open one.
    rc, out, _ = mh(repo, "held")
    assert rc == 0 and "#971 held by orch-b" in out and "#970" not in out


def test_claim_refused_when_main_not_red(repo, gh, real_runs):
    gh.set(runs=real_runs)
    rc, _, err = mh(repo, "claim", "--who", "a", "--culprit", "x")
    assert rc == 1 and "nothing to claim" in err


def test_no_workflow_configured_is_a_usage_error(tmp_path, gh):
    repo = init_repo(tmp_path / "bare", {"README.md": "x"})
    rc, _, err = mh(repo, "status")
    assert rc != 0 and "no workflow" in err
