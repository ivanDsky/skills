"""build_identity.py against the real PuzzleBox PROFILE wording, a real git repo and a stub `adb`.

Contract under test: versionCode = max(device, ledger, committed) + 1, allocated
under a lock, never prompting.
Run: python3 -m pytest skills/deliver/scripts/tests
"""
import json
import subprocess
import sys

import pytest

import build_identity as bi
from conftest import SCRIPTS

SCRIPT = SCRIPTS / "build_identity.py"
APP_ID = "com.example.puzzlebox"


def run(repo, *args, timeout=30):
    # stdin closed: any prompt would hit EOF and fail the test instead of hanging it.
    return subprocess.run([sys.executable, str(SCRIPT), "--root", str(repo), *args], capture_output=True,
                          text=True, stdin=subprocess.DEVNULL, timeout=timeout)


def allocate(repo, *extra, variant="debug"):
    r = run(repo, "allocate", "--variant", variant, *extra)
    assert r.returncode == 0, r.stderr
    return dict(line.split("=", 1) for line in r.stdout.splitlines() if "=" in line)


def ledger(repo):
    p = repo / ".git" / "agent-builds" / "versions.jsonl"
    return [json.loads(l) for l in p.read_text().splitlines()] if p.exists() else []


def seed_ledger(repo, *codes):
    d = repo / ".git" / "agent-builds"
    d.mkdir(exist_ok=True)
    (d / "versions.jsonl").write_text("".join(
        json.dumps({"code": c, "semver": "0.32.0", "n": 1, "release": False, "version_name": f"0.32.0-seed.{c}",
                    "apk": f"PuzzleBox-0.32.0-seed.{c}-{c}-debug.apk", "slug": "seed", "branch": "seed",
                    "sha": "abc1234", "time": "2026-11-14T00:00:00+00:00"}) + "\n" for c in codes))


def test_profile_values_from_real_wording(repo):
    assert bi.profile_value(repo, "app-id") == APP_ID
    assert bi.profile_value(repo, "app-name") == "PuzzleBox"
    assert bi.profile_value(repo, "version") == "0.32.0"   # trailing long `# comment` stripped
    assert bi.committed_code(repo) == 100                   # last integer of the real versionCode line


@pytest.mark.parametrize("device,ledger_codes,expected", [
    ((260,), (250, 255), 261),     # device highest
    ((260,), (250, 300), 301),     # ledger highest
    ((120,), (), 121),             # device above committed 100, empty ledger
    ((), (), 101),                 # nothing but committed
    ((0,), (), 101),               # app not installed on the device
    ((90, 140), (130,), 141),      # several devices: highest one counts
])
def test_code_is_max_of_device_ledger_committed_plus_one(repo, adb, device, ledger_codes, expected):
    adb(*device)
    seed_ledger(repo, *ledger_codes)
    got = allocate(repo)
    assert int(got["VERSION_CODE"]) == expected


def test_committed_value_wins_when_it_is_the_highest(repo, adb):
    adb(10)
    seed_ledger(repo, 20)
    assert int(allocate(repo, "--base-code", "500")["VERSION_CODE"]) == 501


def test_outputs_and_ledger_record(repo, adb):
    adb(210)
    got = allocate(repo)
    assert got["VERSION_CODE"] == "211"
    assert got["VERSION_NAME"] == "0.32.0-sync-engine.1"
    assert got["APK_NAME"] == "PuzzleBox-0.32.0-sync-engine.1-211-debug.apk"
    assert got["SLUG"] == "sync-engine"
    assert got["GRADLE_ARGS"] == "'-PagentVersionCode=211 -PagentVersionName=0.32.0-sync-engine.1'"
    rec, = ledger(repo)
    assert rec["code"] == 211 and rec["branch"] == "feature/sync-engine" and rec["device_codes"] == {"emulator-5554": 210}


def test_second_allocate_moves_past_the_ledger_even_if_device_lags(repo, adb):
    adb(210)
    first = allocate(repo)
    second = allocate(repo)  # device still reports 210; the ledger knows 211
    assert (int(first["VERSION_CODE"]), int(second["VERSION_CODE"])) == (211, 212)
    assert second["VERSION_NAME"] == "0.32.0-sync-engine.2"


def test_unreachable_device_falls_back_without_prompting(repo, adb):
    seed_ledger(repo, 150)
    r = run(repo, "allocate", "--variant", "debug")
    assert r.returncode == 0
    assert "device not reachable" in r.stderr
    assert "VERSION_CODE=151" in r.stdout


def test_never_prompts_on_missing_input(repo):
    """Missing app-id/version -> exit with a message naming the flag, no input()."""
    (repo / "PROFILE.md").write_text("## Version\n- app-name: PuzzleBox\n")
    r = run(repo, "allocate", "--variant", "debug")
    assert r.returncode != 0 and "missing app-id" in r.stderr
    r = run(repo, "allocate", "--variant", "debug", "--app-id", APP_ID)
    assert r.returncode != 0 and "missing version" in r.stderr
    assert "input(" not in SCRIPT.read_text()


def test_parallel_allocations_get_unique_codes(repo, adb):
    adb(210)
    procs = [subprocess.Popen([sys.executable, str(SCRIPT), "--root", str(repo), "allocate", "--variant", "debug",
                               "--slug", f"w{i}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              stdin=subprocess.DEVNULL, text=True) for i in range(4)]
    for p in procs:
        out, err = p.communicate(timeout=60)
        assert p.returncode == 0, err
    codes = sorted(r["code"] for r in ledger(repo))
    assert codes == [211, 212, 213, 214]


def test_release_only_from_main_and_once_per_semver(repo, adb):
    adb(210)
    r = run(repo, "allocate", "--variant", "release", "--release")
    assert r.returncode != 0 and "only from main" in r.stderr
    subprocess.run(["git", "checkout", "-q", "-b", "main"], cwd=repo, check=True)
    got = allocate(repo, "--release", variant="release")
    assert got["VERSION_NAME"] == "0.32.0" and got["VERSION_CODE"] == "211"
    r = run(repo, "allocate", "--variant", "release", "--release")
    assert r.returncode != 0 and "already released" in r.stderr


def test_which_maps_installed_code_to_ledger_record(repo, adb):
    adb(210)
    allocate(repo)
    adb(211)
    r = run(repo, "which")
    assert r.returncode == 0 and "versionCode 211" in r.stdout and "feature/sync-engine" in r.stdout
    adb(999)
    assert "not in ledger" in run(repo, "which").stdout


def test_slug_rules():
    assert bi.slug_for("feature/Sync Engine!", "abc1234") == "sync-engine"
    assert bi.slug_for("HEAD", "abc1234") == "sha-abc1234"
    assert len(bi.slug_for("x" * 40, "abc")) <= 24
