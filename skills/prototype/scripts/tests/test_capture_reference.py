"""capture_reference.py with a stub browser that writes a PNG header at the requested size.

Contract under test: one PNG per frame x viewport x theme, named
<screen>__<state>__<phone|tablet>__<light|dark>.png; theme and frame=1 added to
each URL; exit 1 on a missing or wrong-size PNG, 2 on a bad frames file.
Run: python3 -m pytest skills/prototype/scripts/tests
"""
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import capture_reference as cr  # noqa: E402

SCRIPT = SCRIPTS / "capture_reference.py"

FRAMES = """\
# studio contract, frozen with the user
screen\tstate\tpage\tthemes
studio-board\tdefault\t01-studio.html?s=default\tlight,dark
studio-board\tlongest\t01-studio.html?s=longest&v=b
unique-toast\tshown\t02-toast.html\tdark
"""

STUB = r'''#!/usr/bin/env python3
import struct, sys, zlib
args = dict(a[2:].split("=", 1) for a in sys.argv[1:-1] if "=" in a)
w, h = (int(x) for x in args["window-size"].split(","))
s = float(args["force-device-scale-factor"])
mode = "%s"
if mode == "none":
    sys.exit(0)
if mode == "small":
    w -= 1
ihdr = struct.pack(">IIBBBBB", round(w * s), round(h * s), 8, 2, 0, 0, 0)
chunk = struct.pack(">I", 13) + b"IHDR" + ihdr + struct.pack(">I", zlib.crc32(b"IHDR" + ihdr))
with open(args["screenshot"], "wb") as fh:
    fh.write(b"\x89PNG\r\n\x1a\n" + chunk)
with open(args["screenshot"] + ".url", "w") as fh:
    fh.write(sys.argv[-1])
'''


def stub(tmp_path, mode="ok"):
    path = tmp_path / ("browser-" + mode)
    path.write_text("#!%s\n" % sys.executable + STUB.split("\n", 1)[1] % mode)
    path.chmod(0o755)
    return path


def run(tmp_path, *extra, mode="ok"):
    frames = tmp_path / "frames.tsv"
    frames.write_text(FRAMES)
    out = tmp_path / "reference"
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--base-url", "http://192.0.2.10:8766", "--frames", str(frames),
         "--out", str(out), "--browser", str(stub(tmp_path, mode)), *extra],
        capture_output=True, text=True, timeout=60)
    return proc, out


def test_names_every_frame_viewport_theme(tmp_path):
    proc, out = run(tmp_path)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert sorted(p.name for p in out.glob("*.png")) == [
        "studio-board__default__phone__dark.png",
        "studio-board__default__phone__light.png",
        "studio-board__default__tablet__dark.png",
        "studio-board__default__tablet__light.png",
        "studio-board__longest__phone__light.png",
        "studio-board__longest__tablet__light.png",
        "unique-toast__shown__phone__dark.png",
        "unique-toast__shown__tablet__dark.png",
    ]
    assert cr.png_size(out / "studio-board__default__tablet__dark.png") == (1280, 800)
    assert cr.png_size(out / "unique-toast__shown__phone__dark.png") == (412, 915)
    assert "8 of 8 captured" in proc.stdout


def test_url_keeps_page_query_and_adds_theme_and_frame(tmp_path):
    proc, out = run(tmp_path)
    url = (out / "studio-board__longest__phone__light.png.url").read_text()
    assert url == "http://192.0.2.10:8766/01-studio.html?s=longest&v=b&theme=light&frame=1"


def test_scale_and_viewport_override(tmp_path):
    proc, out = run(tmp_path, "--scale", "2", "--viewport", "phone=360x800", "--only", "unique-toast")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert sorted(p.name for p in out.glob("*.png")) == [
        "unique-toast__shown__phone__dark.png", "unique-toast__shown__tablet__dark.png"]
    assert cr.png_size(out / "unique-toast__shown__phone__dark.png") == (720, 1600)


@pytest.mark.parametrize("mode", ["none", "small"])
def test_missing_or_wrong_size_png_fails(tmp_path, mode):
    proc, _ = run(tmp_path, "--only", "unique-toast__shown", mode=mode)
    assert proc.returncode == 1
    assert "FAIL unique-toast__shown__phone__dark.png" in proc.stdout


def test_dry_run_captures_nothing(tmp_path):
    proc, out = run(tmp_path, "--dry-run")
    assert proc.returncode == 0
    assert len(proc.stdout.splitlines()) == 8
    assert not out.exists()


@pytest.mark.parametrize("text, message", [
    ("Studio\tdefault\t01.html\n", "kebab-case"),
    ("board\tdefault\t01.html\tsepia\n", "not light or dark"),
    ("board\tdefault\n", "need screen"),
    ("board\tdefault\t01.html\nboard\tdefault\t02.html\n", "listed twice"),
    ("# nothing\n", "no frames"),
])
def test_bad_frames_rejected(text, message):
    with pytest.raises(cr.UsageError, match=message):
        cr.parse_frames(text)


def test_bad_frames_file_exits_2(tmp_path):
    frames = tmp_path / "frames.tsv"
    frames.write_text("board\tdefault__x\t01.html\n")
    proc = subprocess.run([sys.executable, str(SCRIPT), "--base-url", "http://h/", "--frames", str(frames),
                           "--out", str(tmp_path / "o")], capture_output=True, text=True)
    assert proc.returncode == 2
    assert "kebab-case" in proc.stderr


def test_find_browser_order():
    none = lambda name: None  # noqa: E731
    assert cr.find_browser("/x/chrome", env={"PROTOTYPE_BROWSER": "/y"}) == "/x/chrome"
    assert cr.find_browser(env={"PROTOTYPE_BROWSER": "/y"}) == "/y"
    assert cr.find_browser(env={}, which=lambda n: "/usr/bin/chromium" if n == "chromium" else None) == "/usr/bin/chromium"
    mac = cr.MAC_APPS[3]
    assert cr.find_browser(env={}, which=none, exists=lambda p: p == mac) == mac
