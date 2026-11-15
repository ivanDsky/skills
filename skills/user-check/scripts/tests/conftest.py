"""Shared fixtures: real PuzzleBox goldens (read-only copies) and a CLI runner."""
import shutil
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import visual_gate  # noqa: E402

FIXTURES = HERE / "fixtures"


@pytest.fixture
def goldens(tmp_path):
    """Copy of the fixtures: `queens-ui/` has no duplicates, `queens-ui-dup/` has one real identical pair."""
    dst = tmp_path / "goldens"
    shutil.copytree(FIXTURES, dst)
    return dst


@pytest.fixture
def gate(capsys):
    """gate(*argv) -> (exit code, stdout)."""
    def run(*argv):
        code = visual_gate.main([str(a) for a in argv])
        return code, capsys.readouterr().out
    return run
