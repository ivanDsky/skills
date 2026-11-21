"""frames.py end to end on a generated clip.

Contract under test: frames sampled inside the --from/--to window with times printed per frame;
the frame cap lowers the rate instead of truncating the window; the sheet is a labelled grid;
bad windows exit 1 with one line. Needs ffmpeg/ffprobe (with lavfi) and Pillow.
Run: python3 -m pytest skills/diagnose-bug/scripts/tests
"""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "frames.py"

if not (shutil.which("ffmpeg") and shutil.which("ffprobe")):
    pytest.fail("ffmpeg and ffprobe are required for these tests", pytrace=False)


@pytest.fixture(scope="module")
def clip(tmp_path_factory):
    """A 6 s, 10 fps, 320x240 test pattern."""
    path = tmp_path_factory.mktemp("clip") / "Screen Recording.mp4"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=duration=6:size=320x240:rate=10",
         "-pix_fmt", "yuv420p", str(path)],
        check=True,
    )
    return path


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True)


def parse(stdout):
    rows = [line.split("\t") for line in stdout.strip().splitlines()]
    assert rows[-1][0] == "sheet"
    return [float(t) for t, _ in rows[:-1]], [Path(p) for _, p in rows[:-1]], Path(rows[-1][1])


def test_window_and_times(clip, tmp_path):
    p = run(clip, "--from", 2, "--to", 4, "--fps", 2, "--out", tmp_path)
    assert p.returncode == 0, p.stderr
    times, frames, sheet = parse(p.stdout)
    assert times == [2.0, 2.5, 3.0, 3.5]
    assert all(f.is_file() for f in frames)
    assert sheet.is_file()


def test_cap_lowers_rate_and_keeps_whole_window(clip, tmp_path):
    p = run(clip, "--fps", 10, "--max", 6, "--out", tmp_path)
    assert p.returncode == 0, p.stderr
    times, frames, _ = parse(p.stdout)
    assert len(frames) == 6
    assert times[-1] == pytest.approx(5.0)


def test_sheet_is_a_labelled_grid(clip, tmp_path):
    from PIL import Image

    p = run(clip, "--to", 3, "--fps", 2, "--width", 160, "--cols", 3, "--out", tmp_path)
    assert p.returncode == 0, p.stderr
    _, frames, sheet = parse(p.stdout)
    w, h = Image.open(frames[0]).size
    sw, sh = Image.open(sheet).size
    assert len(frames) == 6
    assert sw == 3 * w
    assert sh > 2 * h  # two rows plus a label strip on each


def test_rerun_replaces_old_frames(clip, tmp_path):
    assert run(clip, "--fps", 4, "--out", tmp_path).returncode == 0
    p = run(clip, "--to", 1, "--fps", 2, "--out", tmp_path)
    _, frames, _ = parse(p.stdout)
    assert sorted(tmp_path.glob("f_*.png")) == frames


@pytest.mark.parametrize("args", [("--from", 5, "--to", 2), ("--from", 9)])
def test_empty_window_fails_with_one_line(clip, tmp_path, args):
    p = run(clip, *args, "--out", tmp_path)
    assert p.returncode == 1
    assert p.stderr.startswith("frames.py: empty window")


def test_missing_file(tmp_path):
    p = run(tmp_path / "nope.mp4")
    assert p.returncode == 1
    assert "no such file" in p.stderr
