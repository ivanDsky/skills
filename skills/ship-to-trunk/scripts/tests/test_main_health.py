"""main_health.py against the real PuzzleBox PROFILE wording and real `gh` JSON.

Regression: #26 — `unknown` reported because most recent runs were cancelled.
Run: python3 -m pytest skills/ship-to-trunk/scripts/tests
"""
import argparse
import json
import os
import subprocess
import sys

import pytest

import main_health
from conftest import FIXTURES, SCRIPTS, init_repo

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


# Red-run failure details. Fixtures are trimmed real `gh run view --log-failed`
# output of PuzzleBox `Main` reds: a flaky test (run 43636165873), a Robolectric
# android-all download (run 44212142333), and a run whose job never started
# (run 43098688199, its real `--json jobs`).
RED_RUN = "43636165873"  # the real failure in real_runs[4:]
FLAKY = "HintSearchTest.invalidate after compute finished but before deliver ran delivers nothing"


def fixture_text(name):
    return (FIXTURES / name).read_text()


def red_records(repo):
    path = repo / ".git" / "agent-builds" / "main-health.jsonl"
    return [r for r in map(json.loads, path.read_text().splitlines()) if r.get("conclusion") == "failure"]


def test_flaky_test_red_records_the_test_and_names_it(repo, gh, real_runs):
    gh.set(runs=real_runs[4:], logs={RED_RUN: fixture_text("gh_run_log_failed_flaky_test.txt")})
    rc, out, _ = mh(repo, "status")
    assert rc == 3
    [rec] = red_records(repo)
    assert (rec["failed_tests"], rec["cause_hint"]) == ([FLAKY], "test")
    assert out.splitlines()[1].endswith(f"; cause test: {FLAKY}")


def test_robolectric_download_red_caps_names_at_50(repo, gh, real_runs):
    gh.set(runs=real_runs[4:], logs={RED_RUN: fixture_text("gh_run_log_failed_robolectric_download.txt")})
    rc, out, _ = mh(repo, "status")
    assert rc == 3
    [rec] = red_records(repo)
    assert rec["cause_hint"] == "download"
    assert len(rec["failed_tests"]) == 50 and len(set(rec["failed_tests"])) == 50  # 148 distinct in the log
    assert rec["failed_tests"][:3] == ["FlatPressTintTest.classMethod", "HomeDoorsTest.classMethod",
                                       "HomeRecentEmptyTabletTest.classMethod"]
    assert out.splitlines()[1].endswith(
        "; cause download: FlatPressTintTest.classMethod, HomeDoorsTest.classMethod, "
        "HomeRecentEmptyTabletTest.classMethod, +47+ more")


def test_job_that_never_started_is_infra(repo, gh, real_runs):
    jobs = json.loads(fixture_text("gh_run_view_jobs_never_started.json"))["jobs"]
    gh.set(runs=real_runs[4:], logs={RED_RUN: ""}, jobs={RED_RUN: jobs})
    rc, out, _ = mh(repo, "status")
    [rec] = red_records(repo)
    assert (rc, rec["failed_tests"], rec["cause_hint"]) == (3, [], "infra")
    assert out.splitlines()[1].endswith("; cause infra")


def test_absent_log_records_no_names_and_unknown(repo, gh, real_runs):
    gh.set(runs=real_runs[4:])  # the fake fails both `run view` calls, like an expired log
    rc, out, _ = mh(repo, "status")
    [rec] = red_records(repo)
    assert (rc, rec["failed_tests"], rec["cause_hint"]) == (3, [], "unknown")
    assert out.splitlines()[1].endswith("; cause unknown")


def test_green_runs_fetch_no_logs(repo, gh, real_runs):
    gh.set(runs=real_runs)
    mh(repo, "status")
    assert not [c for c in gh.calls() if c[:2] == ["run", "view"]]


def test_green_rerun_of_the_red_run_turns_main_green(repo, gh, real_runs):
    """`gh run rerun <id> --failed` keeps the databaseId and bumps the attempt."""
    gh.set(runs=real_runs[4:], logs={RED_RUN: fixture_text("gh_run_log_failed_flaky_test.txt")})
    assert mh(repo, "status")[0] == 3
    rerun = [dict(r, conclusion="success", attempt=2) if str(r["databaseId"]) == RED_RUN else r
             for r in real_runs[4:]]
    gh.set(runs=rerun)
    rc, out, _ = mh(repo, "watch", "--who", "t")
    sha = next(r["headSha"] for r in rerun if str(r["databaseId"]) == RED_RUN)
    assert rc == 0 and out.splitlines() == [f"main green at {sha[:9]} (run {RED_RUN})", "main green; nothing pending"]
    assert mh(repo, "status")[:2] == (0, f"green at {sha[:9]} (run {RED_RUN})")


def test_ledger_skips_a_run_attempt_older_than_the_newest_recorded(repo):
    """Closes the bootstrap race: a `status` on an empty ledger and a watcher
    may each append; only strictly newer (run, attempt) keys land."""
    led = main_health.Ledger(str(repo))
    rec = lambda run, attempt: {"type": "run", "run": run, "attempt": attempt, "conclusion": "failure"}
    assert led.append(rec(10, 1), unique_run=True)
    assert not led.append(rec(9, 1), unique_run=True)
    assert not led.append(rec(10, 1), unique_run=True)
    assert led.append(rec(10, 2), unique_run=True)
    assert [main_health.run_key(r) for r in led.read()] == [(10, 1), (10, 2)]


@pytest.mark.parametrize("log, want", [
    # Real line from run 44212142333: the fetch error itself names android-all.
    ("test (ui)\tUNKNOWN STEP\t2026-11-18T00:59:35.6617086Z java.io.IOException: Server returned HTTP "
     "response code: 429 for URL: https://gcp.mirrors.maven.org/maven2/org/robolectric/android-all-instrumented/"
     "14-robolectric-10818077-i7/android-all-instrumented-14-robolectric-10818077-i7.jar",
     ([], "download")),
    ("> Task :feature:play:impl:compileDebugKotlin FAILED\nFooTest > bar FAILED\nBUILD FAILED in 1m",
     ([":feature:play:impl:compileDebugKotlin", "FooTest.bar"], "compile")),
    # A real test failure next to a download error: the download wins.
    ("FooTest > bar FAILED\n    java.lang.AssertionError at MavenArtifactFetcher.java:130",
     (["FooTest.bar"], "download")),
    ("##[error]The runner has received a shutdown signal.", ([], "infra")),
    ("> Task :konsist:test FAILED\n", ([":konsist:test"], "unknown")),
    ("", ([], "unknown")),
])
def test_parse_failure_hints(log, want):
    got = main_health.parse_failure(log)
    assert (got["failed_tests"], got["cause_hint"]) == want


def test_a_run_with_no_jobs_is_unknown_not_infra():
    """A broken workflow file yields zero jobs: a defect with a culprit, not a rerun."""
    assert main_health.parse_failure("", [])["cause_hint"] == "unknown"
    jobs = json.loads(fixture_text("gh_run_view_jobs_never_started.json"))["jobs"]
    assert main_health.parse_failure("", jobs)["cause_hint"] == "infra"


# Quarantine expiry: the fixture tree has one expired quarantine (a method in
# androidTest), one live one (a class in test) and a past date in main sources.
@pytest.fixture
def qrepo(tmp_path, profile_text):
    tree = FIXTURES / "quarantine_tree"
    files = {str(p.relative_to(tree)): p.read_text() for p in tree.rglob("*.kt")}
    return init_repo(tmp_path / "qrepo", {"PROFILE.md": profile_text, **files})


EXPIRED = "quarantine expired: FullReplayE2ETest.aStoredReplayThatTheResultOpensHasNamedControls #812 since 2026-11-10"


def test_status_reports_only_the_expired_quarantine(qrepo, gh, real_runs):
    gh.set(runs=real_runs)
    rc, out, _ = mh(qrepo, "status")
    assert (rc, out.splitlines()) == (0, ["green at 889eafb35 (run 43640083876)", EXPIRED])


def test_expired_quarantine_keeps_red_exit_code(qrepo, gh, real_runs):
    gh.set(runs=real_runs[4:])
    rc, out, _ = mh(qrepo, "status")
    assert rc == 3 and out.splitlines()[-1] == EXPIRED


def test_watch_reports_expired_quarantine_before_its_verdict(qrepo, gh, real_runs):
    gh.set(runs=real_runs)
    rc, out, _ = mh(qrepo, "watch", "--who", "t")
    assert rc == 0 and out.splitlines()[-2:] == [EXPIRED, "main green; nothing pending"]


@pytest.mark.parametrize("text, want", [
    ('@Ignore("quarantine #7 until 2020-01-01")\nclass FooTest {', "FooTest"),
    ('class FooTest {\n  @Ignore("quarantine #7 until 2020-01-01")\n  @Test fun `a b`() {}', "FooTest.a b"),
    ('@Ignore("quarantine #7 until 2020-01-01")\n', "x/src/test/Foo.kt"),
])
def test_quarantine_target(text, want):
    m = main_health.QUARANTINE.search(text)
    assert main_health.quarantine_target(text, m.end(), "x/src/test/Foo.kt") == want


def test_status_refreshes_stale_ledger(repo, gh, real_runs):
    """A ledger holding green run N must not pass a main whose newer run N+1 failed."""
    gh.set(runs=real_runs)
    assert mh(repo, "status")[0] == 0
    newer = dict(real_runs[0], databaseId=real_runs[0]["databaseId"] + 1, conclusion="failure")
    gh.set(runs=[newer, *real_runs])
    rc, out, _ = mh(repo, "status")
    assert rc == 3 and out.splitlines()[0] == "red"
    assert out.splitlines()[1].startswith(f"main red at {newer['headSha'][:9]} (run {newer['databaseId']})")


def test_status_keeps_ledger_verdict_when_gh_fails(repo, gh, real_runs):
    gh.set(runs=real_runs)
    assert mh(repo, "status")[0] == 0
    gh.set(run_list_error="HTTP 502")
    rc, out, err = mh(repo, "status")
    assert (rc, out) == (0, "green at 889eafb35 (run 43640083876)")
    assert err.startswith("main_health: ledger refresh failed:") and "HTTP 502" in err


def test_watch_writes_and_removes_pidfile(repo, gh, monkeypatch):
    pidfile = repo / ".git" / "agent-builds" / "main-health-watch.pid"
    seen = []

    def list_runs(*a, **kw):
        seen.append(pidfile.read_text() if pidfile.exists() else None)
        return []
    monkeypatch.setattr(main_health, "list_runs", list_runs)
    root = str(repo)
    assert main_health.cmd_watch(argparse.Namespace(who="t"), root, "release.yml", main_health.Ledger(root)) == 0
    assert seen and set(seen) == {str(os.getpid())}
    assert not pidfile.exists()


def test_quarantine_in_resources_ignored(tmp_path, profile_text, gh, real_runs):
    """A Konsist fixture under src/test/resources is test data, not a quarantine of this repo."""
    stale = '@Ignore("quarantine #1 until 2000-01-01")\nclass X {}\n'
    repo = init_repo(tmp_path / "r", {
        "PROFILE.md": profile_text,
        "konsist/src/test/resources/fixtures/S11/sample/src/test/kotlin/X.kt": stale,
        "konsist/src/test/resources/Y.kt": stale,
    })
    gh.set(runs=real_runs)
    assert mh(repo, "status")[:2] == (0, "green at 889eafb35 (run 43640083876)")
    assert main_health.expired_quarantines(str(repo)) == []
    init_repo(tmp_path / "r2", {"PROFILE.md": profile_text, "app/src/test/kotlin/X.kt": stale})
    assert main_health.expired_quarantines(str(tmp_path / "r2")) == ["quarantine expired: X #1 since 2000-01-01"]
