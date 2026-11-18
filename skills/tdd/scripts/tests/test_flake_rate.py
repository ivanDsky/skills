"""flake_rate.py end to end against a fake `./gradlew` replaying canned JUnit XML and exit codes.

Contract under test: N runs, none stops the loop; per-test pass/fail/abort counts; verdict
stable / flaky / broken; logs and XML kept per run; build-slot used when on PATH; stale XML
never leaks into the next run; exit 0 on completed runs.
Run: python3 -m pytest skills/tdd/scripts/tests
"""
import subprocess
import sys

import pytest

from conftest import SCRIPTS, TEST

SCRIPT = SCRIPTS / "flake_rate.py"
CRASH_LOG = ("> Task :app:testDebugUnitTest FAILED\n"
             "Process 'Gradle Test Executor 3' finished with non-zero exit value 134\n")


def flake(repo, n, *extra):
    return subprocess.run([sys.executable, str(SCRIPT), "--root", str(repo.root), "--tests", "*ResumeSolveE2ETest",
                           "--runs", str(n), "--out", str(repo.root / "out"), *extra],
                          capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=60)


def lines(r):
    return r.stdout.splitlines()


def test_all_pass_is_stable(repo):
    for i in range(1, 4):
        repo.plan(i, "TEST-pass.xml")
    r = flake(repo, 3)
    assert r.returncode == 0, r.stderr
    assert lines(r)[:2] == [f"{TEST} pass 3/3 fail 0 abort 0", "verdict: stable"]


def test_mixed_is_flaky_and_exit_stays_zero(repo):
    for i, x in enumerate(["TEST-pass.xml", "TEST-fail.xml", "TEST-pass.xml", "TEST-pass.xml"], 1):
        repo.plan(i, x, rc=0 if x == "TEST-pass.xml" else 1, log="There were failing tests\n" if i == 2 else "")
    r = flake(repo, 4)
    assert r.returncode == 0
    assert lines(r)[:2] == [f"{TEST} pass 3/4 fail 1 abort 0", "verdict: flaky"]


def test_all_fail_is_broken(repo):
    for i in (1, 2):
        repo.plan(i, "TEST-fail.xml", rc=1)
    r = flake(repo, 2)
    assert lines(r)[:2] == [f"{TEST} pass 0/2 fail 2 abort 0", "verdict: broken"]


def test_failing_run_does_not_stop_the_loop(repo):
    repo.plan(1, "TEST-fail.xml", rc=1)
    repo.plan(2, "TEST-pass.xml")
    repo.plan(3, "TEST-pass.xml")
    flake(repo, 3)
    assert len(repo.gradle_args()) == 3


def test_jvm_crash_without_xml_is_abort_not_fail(repo):
    """Robolectric worker killed under load: 'exit value 134', no XML -> abort."""
    repo.plan(1, "TEST-pass.xml")
    repo.plan(2, None, rc=1, log=CRASH_LOG)
    repo.plan(3, "TEST-pass.xml")
    r = flake(repo, 3)
    assert lines(r)[:2] == [f"{TEST} pass 2/3 fail 0 abort 1", "verdict: flaky"]
    assert "run 2/3: 0 tests recorded, JVM crash" in r.stderr


def test_stale_xml_of_the_previous_run_is_not_read(repo):
    """Run 2 produces nothing: it must not inherit run 1's pass."""
    repo.plan(1, "TEST-pass.xml")
    repo.plan(2, None, rc=1, log="FAILURE: Build failed with an exception (compile error)\n")
    r = flake(repo, 2)
    assert lines(r)[:1] == [f"{TEST} pass 1/2 fail 0 abort 1"]
    assert not list((repo.root / "out" / "run2").glob("*.xml"))


def test_every_run_aborting_reports_the_filter_as_broken(repo):
    repo.plan(1, None, rc=1, log=CRASH_LOG)
    repo.plan(2, None, rc=1, log=CRASH_LOG)
    r = flake(repo, 2)
    assert lines(r)[:2] == ["*ResumeSolveE2ETest pass 0/2 fail 0 abort 2", "verdict: broken"]
    assert r.returncode == 0


def test_logs_and_xml_kept_per_run(repo):
    repo.plan(1, "TEST-pass.xml", log="BUILD SUCCESSFUL\n")
    repo.plan(2, "TEST-fail.xml", rc=1, log="There were failing tests\n")
    flake(repo, 2)
    out = repo.root / "out"
    assert "BUILD SUCCESSFUL" in (out / "run1" / "gradle.log").read_text()
    assert "There were failing tests" in (out / "run2" / "gradle.log").read_text()
    assert "<failure" not in next((out / "run1").glob("*.xml")).read_text()
    assert "<failure" in next((out / "run2").glob("*.xml")).read_text()


def test_gradle_command_line(repo):
    repo.plan(1, "TEST-pass.xml")
    flake(repo, 1, "--module", ":feature:ui", "--task", "testReleaseUnitTest")
    assert repo.gradle_args() == [":feature:ui:testReleaseUnitTest --tests *ResumeSolveE2ETest --rerun"]


def test_default_module_and_task(repo):
    repo.plan(1, "TEST-pass.xml")
    flake(repo, 1)
    assert repo.gradle_args() == [":app:testDebugUnitTest --tests *ResumeSolveE2ETest --rerun"]


def test_build_slot_wraps_every_run_when_on_path(repo, with_build_slot):
    for i in (1, 2):
        repo.plan(i, "TEST-pass.xml")
    flake(repo, 2)
    assert repo.slot_calls() == ["./gradlew :app:testDebugUnitTest --tests *ResumeSolveE2ETest --rerun"] * 2


def test_no_build_slot_runs_gradle_directly(repo):
    repo.plan(1, "TEST-pass.xml")
    r = flake(repo, 1)
    assert r.returncode == 0 and repo.slot_calls() == []


def test_missing_gradlew_is_a_usage_error(repo):
    (repo.root / "gradlew").unlink()
    r = flake(repo, 1)
    assert r.returncode == 2 and "no gradlew" in r.stderr


def test_missing_tests_filter_is_a_usage_error(repo):
    r = subprocess.run([sys.executable, str(SCRIPT), "--root", str(repo.root)], capture_output=True, text=True)
    assert r.returncode == 2
