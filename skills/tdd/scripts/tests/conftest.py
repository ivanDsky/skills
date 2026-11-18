"""Shared fixtures: a repo root with a fake `./gradlew`, a build-slot stub, JUnit XML fixtures.

fixtures/TEST-pass.xml is a real Gradle JUnit result (a PuzzleBox e2e test, package and
hostname scrubbed); TEST-fail.xml is the same file with the `<failure>` element Gradle writes.
"""
import os
import shutil
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent
FIXTURES = HERE / "fixtures"
sys.path.insert(0, str(SCRIPTS))

TASK = "testDebugUnitTest"
TEST = "com.ivandsky.example.app.e2e.ResumeSolveE2ETest.SC6 a game resumed after a kill records its play time and submits once"


class Repo:
    def __init__(self, root, fake):
        self.root, self.fake = root, fake

    def plan(self, n, xml=None, rc=0, log=""):
        """Script gradle invocation n: result fixture (TEST-pass.xml / TEST-fail.xml / None), exit code, console output."""
        d = self.fake / "plan" / str(n)
        d.mkdir(parents=True)
        if xml:
            shutil.copy(FIXTURES / xml, d / "TEST-com.ivandsky.example.app.e2e.ResumeSolveE2ETest.xml")
        (d / "rc").write_text(str(rc))
        (d / "log").write_text(log)

    def gradle_args(self):
        p = self.fake / "args.log"
        return p.read_text().splitlines() if p.exists() else []

    def slot_calls(self):
        p = self.fake / "slot.log"
        return p.read_text().splitlines() if p.exists() else []


@pytest.fixture
def repo(tmp_path, monkeypatch):
    root, fake = tmp_path / "repo", tmp_path / "fake"
    root.mkdir()
    fake.mkdir()
    shutil.copy(HERE / "fakes" / "gradlew", root / "gradlew")
    (root / "gradlew").chmod(0o755)
    monkeypatch.setenv("FLAKE_FAKE_DIR", str(fake))
    monkeypatch.setenv("FLAKE_FAKE_MODULE_DIR", str(root / "app"))
    monkeypatch.setenv("FLAKE_FAKE_TASK", TASK)
    # Hide any real build-slot; tests that want one install the stub with `with_build_slot`.
    monkeypatch.setenv("PATH", os.pathsep.join(p for p in os.environ["PATH"].split(os.pathsep)
                                               if not (Path(p) / "build-slot").exists()))
    return Repo(root, fake)


@pytest.fixture
def with_build_slot(tmp_path, monkeypatch):
    bin_ = tmp_path / "bin"
    bin_.mkdir()
    shutil.copy(HERE / "fakes" / "build-slot", bin_ / "build-slot")
    monkeypatch.setenv("PATH", f"{bin_}{os.pathsep}{os.environ['PATH']}")
