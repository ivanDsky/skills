#!/usr/bin/env python3
"""Run every skills/*/scripts/tests suite with pytest.

Usage:
    python3 scripts/test_skills.py [skill-dir ...]    # default: every skills/*

lint_skills.py calls run_script_tests() so a failing script test fails lint.
One pytest process per tests directory (their conftest.py / fixtures never mix).
Runner: `python -m pytest` when pytest is importable, else
`uv run --with pytest python -m pytest` when uv is on PATH, else a failure
(never a skip). A tests directory with a requirements.txt (third-party imports
of the script under test) runs under `uv run --with-requirements` when uv is on
PATH. Exit codes: 0 all pass, 1 failure or no pytest runner.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"

# Vendored upstream tests that locate the upstream repo layout and cannot be
# collected here. Path relative to the tests directory -> why.
UPSTREAM_ONLY = {
    "ui-ux-pro-max": {
        "test_catalog_refresh.py": "needs the upstream repo root",
        "test_catalog_summary_line_endings.py": "needs the upstream repo root",
        "test_relevance_evaluator.py": "needs the upstream repo root",
        "test_skill_script_paths.py": "needs the upstream .claude/skills + cli/assets trees",
    },
}


def tests_dir(skill_dir):
    d = Path(skill_dir) / "scripts" / "tests"
    return d if d.is_dir() else None


def pytest_command():
    """argv prefix that runs pytest, or None."""
    if subprocess.run([sys.executable, "-c", "import pytest"], capture_output=True).returncode == 0:
        return [sys.executable, "-m", "pytest"]
    if shutil.which("uv"):
        return ["uv", "run", "--quiet", "--with", "pytest", "python", "-m", "pytest"]
    return None


def run_script_tests(skill_dirs=None):
    """[(skill name, ok, output)] — one entry per skill that has scripts/tests."""
    if skill_dirs is None:
        skill_dirs = sorted(p for p in SKILLS.iterdir() if p.is_dir())
    pytest = pytest_command()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    results = []
    for skill in skill_dirs:
        d = tests_dir(skill)
        if not d:
            continue
        name = Path(skill).resolve().name
        if not pytest:
            results.append((name, False, "no pytest runner: `python3 -m pip install pytest` or install uv"))
            continue
        ignores = [f"--ignore={d / f}" for f in UPSTREAM_ONLY.get(name, {})]
        runner = pytest
        if (d / "requirements.txt").is_file() and shutil.which("uv"):
            runner = ["uv", "run", "--quiet", "--with", "pytest", "--with-requirements",
                      str(d / "requirements.txt"), "python", "-m", "pytest"]
        p = subprocess.run([*runner, "-q", "-p", "no:cacheprovider", *ignores, str(d)],
                           capture_output=True, text=True, env=env, cwd=str(REPO))
        results.append((name, p.returncode == 0, (p.stdout + p.stderr).strip()))
    return results


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    results = run_script_tests([Path(a) for a in argv] or None)
    for name, ok, output in results:
        print(f"{name}: {'PASS' if ok else 'FAIL'} — {output.splitlines()[-1] if output else 'no output'}")
        if not ok:
            print(output)
    return 0 if all(ok for _, ok, _ in results) else 1


if __name__ == "__main__":
    sys.exit(main())
