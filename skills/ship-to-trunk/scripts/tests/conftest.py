"""Shared fixtures: hermetic git, a `gh` stub on PATH, real captured gh JSON."""
import json
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
def hermetic_git(monkeypatch, tmp_path):
    for k, v in {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull,
                 "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
                 "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com",
                 "GIT_TERMINAL_PROMPT": "0"}.items():
        monkeypatch.setenv(k, v)


def load(name):
    return json.loads((FIXTURES / name).read_text())


@pytest.fixture
def real_runs():
    """30 real `gh run list --json databaseId,headSha,status,conclusion,createdAt`
    rows of the PuzzleBox `Main` workflow, newest first: 22 success, 7 cancelled, 1 failure."""
    return load("gh_run_list_main.json")


@pytest.fixture
def real_prs():
    return {"970": load("gh_pr_view_merged.json"), "971": load("gh_pr_view_open.json")}


class Gh:
    def __init__(self, d):
        self.dir = d
        self.state = {"runs": [], "prs": {}, "merge": "ok"}
        self.save()

    def save(self):
        (self.dir / "state.json").write_text(json.dumps(self.state))

    def reload(self):
        self.state = json.loads((self.dir / "state.json").read_text())

    def set(self, **kw):
        self.state.update(kw)
        self.save()

    def calls(self):
        p = self.dir / "calls.log"
        return [json.loads(l) for l in p.read_text().splitlines()] if p.exists() else []


@pytest.fixture
def gh(tmp_path, monkeypatch):
    d = tmp_path / "gh-fake"
    d.mkdir()
    bin_ = d / "bin"
    bin_.mkdir()
    for tool in ("gh", "build-slot"):
        shutil.copy(HERE / "fakes" / tool, bin_ / tool)
    monkeypatch.setenv("PATH", f"{bin_}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("GH_FAKE_DIR", str(d))
    return Gh(d)


@pytest.fixture
def profile_text():
    return (FIXTURES / "PROFILE.puzzlebox.md").read_text()


def init_repo(path, files, executable=()):
    path.mkdir(parents=True, exist_ok=True)
    git("init", "-q", "-b", "main", cwd=path)
    for name, text in files.items():
        f = path / name
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text)
        if name in executable:
            f.chmod(0o755)
    git("add", "-A", cwd=path)
    git("commit", "-q", "-m", "init", cwd=path)
    return path
