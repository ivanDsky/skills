"""Shared fixtures: hermetic git, an `adb` stub on PATH, the real PuzzleBox PROFILE wording."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent
FIXTURES = HERE / "fixtures"
sys.path.insert(0, str(SCRIPTS))


def git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


@pytest.fixture(autouse=True)
def hermetic_git(monkeypatch):
    for k, v in {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull,
                 "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
                 "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com"}.items():
        monkeypatch.setenv(k, v)


@pytest.fixture
def adb(tmp_path, monkeypatch):
    """Call `adb(codes)` to set the installed versionCodes, one device per entry; none = no device."""
    bin_ = tmp_path / "fake-bin"
    bin_.mkdir()
    shutil.copy(HERE / "fakes" / "adb", bin_ / "adb")
    monkeypatch.setenv("PATH", f"{bin_}{os.pathsep}{os.environ['PATH']}")

    def set_codes(*codes):
        monkeypatch.setenv("ADB_FAKE_CODES", ",".join(str(c) for c in codes))

    set_codes()
    return set_codes


@pytest.fixture
def repo(tmp_path):
    """A clone-like repo on branch feature/sync-engine with the real PuzzleBox PROFILE.md
    and the real versionCode line (fallback 100) of app/build.gradle.kts."""
    r = tmp_path / "repo"
    (r / "app").mkdir(parents=True)
    (r / "PROFILE.md").write_text((FIXTURES / "PROFILE.puzzlebox.md").read_text())
    (r / "app" / "build.gradle.kts").write_text(
        "android {\n" + (FIXTURES / "app.build.gradle.kts.snippet").read_text() + "}\n")
    git("init", "-q", "-b", "feature/sync-engine", cwd=r)
    git("add", "-A", cwd=r)
    git("commit", "-q", "-m", "init", cwd=r)
    return r
