"""Shared fixtures: hermetic git, a backlog CLI runner, a `gh` stub on PATH."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parent / "backlog.py"
sys.path.insert(0, str(HERE.parent))


@pytest.fixture(autouse=True)
def hermetic(monkeypatch, tmp_path):
    for k, v in {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull,
                 "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
                 "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com",
                 "GIT_TERMINAL_PROMPT": "0"}.items():
        monkeypatch.setenv(k, v)
    for k in ("BACKLOG_BACKEND", "BACKLOG_REPO", "BACKLOG_DIR", "BACKLOG_WHO"):
        monkeypatch.delenv(k, raising=False)


class Backlog:
    def __init__(self, cwd, env):
        self.cwd, self.env = cwd, env

    def run(self, *args, input=None, check=True):
        p = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=self.cwd, input=input,
                           capture_output=True, text=True, env={**os.environ, **self.env})
        if check and p.returncode:
            raise AssertionError(f"backlog {args} -> {p.returncode}\n{p.stdout}\n{p.stderr}")
        return p

    def out(self, *args, **kw):
        return self.run(*args, **kw).stdout.strip()

    def new(self, title, area="leaderboard", type_="bug", *extra):
        return self.out("new", "--title", title, "--type", type_, "--area", area,
                        "--body-file", "-", *extra, input=f"Brief for {title}.\n")

    def json(self, *args):
        return json.loads(self.out(*args, "--json"))

    def popen(self, *args):
        return subprocess.Popen([sys.executable, str(SCRIPT), *args], cwd=self.cwd, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                env={**os.environ, **self.env})


def make_repo(path, files=None):
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=path, check=True)
    for name, text in (files or {}).items():
        (path / name).write_text(text)
    subprocess.run(["git", "commit", "-q", "--allow-empty", "-m", "init"], cwd=path, check=True)
    return path


@pytest.fixture
def repo(tmp_path):
    return make_repo(tmp_path / "repo")


@pytest.fixture
def local(repo):
    b = Backlog(repo, {"BACKLOG_BACKEND": "local"})
    b.run("init")
    return b


class Gh:
    def __init__(self, d):
        self.dir = d
        (d / "state.json").write_text(json.dumps({"issues": {}, "labels": [], "next": 1}))

    def state(self):
        return json.loads((self.dir / "state.json").read_text())

    def issue(self, n):
        return self.state()["issues"][str(n)]

    def labels(self, n):
        return sorted(l["name"] for l in self.issue(n)["labels"])


@pytest.fixture
def gh(tmp_path, monkeypatch):
    d = tmp_path / "gh-fake"
    (d / "bin").mkdir(parents=True)
    shutil.copy(HERE / "fakes" / "gh", d / "bin" / "gh")
    monkeypatch.setenv("PATH", f"{d / 'bin'}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("GH_FAKE_DIR", str(d))
    return Gh(d)


@pytest.fixture
def github(repo, gh):
    b = Backlog(repo, {"BACKLOG_BACKEND": "github", "BACKLOG_REPO": "o/r"})
    b.run("init")
    return b
