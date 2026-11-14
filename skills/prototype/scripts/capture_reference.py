#!/usr/bin/env python3
"""Capture a UI contract's reference screenshots from the approved prototype pages.

Usage:
    capture_reference.py --base-url URL --frames FRAMES.tsv --out DIR
        [--viewport phone=412x915] [--viewport tablet=1280x800] [--scale 1]
        [--only SCREEN[__STATE]] [--browser PATH] [--wait-ms 1500] [--dry-run]

FRAMES.tsv is tab-separated; blank lines, `#` comments and a header row whose
first cell is `screen` are skipped:

    screen     state     page                          themes
    results    default   01-results.html?s=default     light,dark
    results    empty     01-results.html?s=empty       light

Every frame is captured at every viewport (phone and tablet) and every listed
theme (empty column = light) into DIR/<screen>__<state>__<viewport>__<theme>.png,
the file names the contract's `Reference:` lines and the visual gate's pairs
file use. Each URL gets `theme=<theme>&frame=1` added: the contract page renders
that theme with its switcher and header strip hidden.

Browser: --browser, else $PROTOTYPE_BROWSER, else the first Chromium-family
binary found on PATH, in /Applications, or in the Playwright cache.

Exit codes: 0 every PNG written at the expected size, 1 a capture failed or a
PNG has the wrong size, 2 usage error (bad frames file, no browser).
"""
import argparse
import glob
import os
import re
import shutil
import struct
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

TOKEN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
THEMES = ("light", "dark")
VIEWPORTS = {"phone": (412, 915), "tablet": (1280, 800)}
PATH_NAMES = (
    "chromium", "chromium-browser", "google-chrome", "google-chrome-stable",
    "chrome", "chrome-headless-shell", "microsoft-edge", "brave-browser",
)
MAC_APPS = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
)
PLAYWRIGHT_GLOBS = (
    "~/Library/Caches/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-*/chrome-headless-shell",
    "~/.cache/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-*/chrome-headless-shell",
)


class UsageError(Exception):
    pass


@dataclass(frozen=True)
class Frame:
    screen: str
    state: str
    page: str
    themes: tuple


@dataclass(frozen=True)
class Capture:
    name: str
    url: str
    width: int
    height: int


def parse_frames(text):
    frames, seen = [], set()
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        cells = [c.strip() for c in line.split("\t")]
        if cells[0] == "screen":
            continue
        if len(cells) < 3 or not cells[2]:
            raise UsageError("line %d: need screen<TAB>state<TAB>page[<TAB>themes]" % n)
        screen, state, page = cells[0], cells[1], cells[2]
        for label, value in (("screen", screen), ("state", state)):
            if not TOKEN.match(value):
                raise UsageError("line %d: %s %r must be kebab-case [a-z0-9-]" % (n, label, value))
        themes = tuple(t.strip() for t in (cells[3] if len(cells) > 3 else "").split(",") if t.strip()) or ("light",)
        bad = [t for t in themes if t not in THEMES]
        if bad:
            raise UsageError("line %d: theme %r is not light or dark" % (n, bad[0]))
        if (screen, state) in seen:
            raise UsageError("line %d: %s__%s listed twice" % (n, screen, state))
        seen.add((screen, state))
        frames.append(Frame(screen, state, page, themes))
    if not frames:
        raise UsageError("frames file lists no frames")
    return frames


def parse_viewport(spec):
    m = re.match(r"^(phone|tablet)=(\d+)x(\d+)$", spec)
    if not m:
        raise UsageError("viewport %r must be phone=WxH or tablet=WxH" % spec)
    return m.group(1), (int(m.group(2)), int(m.group(3)))


def frame_url(base_url, page, theme):
    parts = urlsplit(urljoin(base_url if base_url.endswith("/") else base_url + "/", page))
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k not in ("theme", "frame")]
    query += [("theme", theme), ("frame", "1")]
    return urlunsplit(parts._replace(query=urlencode(query)))


def plan(frames, base_url, viewports, only=None):
    captures = []
    for f in frames:
        key = "%s__%s" % (f.screen, f.state)
        if only and only not in (f.screen, key):
            continue
        for vp, (w, h) in viewports.items():
            for theme in f.themes:
                captures.append(Capture("%s__%s__%s.png" % (key, vp, theme), frame_url(base_url, f.page, theme), w, h))
    if not captures:
        raise UsageError("--only %r matches no frame" % only)
    return captures


def find_browser(explicit=None, env=os.environ, which=shutil.which, exists=os.path.isfile):
    if explicit:
        return explicit
    if env.get("PROTOTYPE_BROWSER"):
        return env["PROTOTYPE_BROWSER"]
    for name in PATH_NAMES:
        hit = which(name)
        if hit:
            return hit
    for path in MAC_APPS:
        if exists(path):
            return path
    for pattern in PLAYWRIGHT_GLOBS:
        hits = sorted(glob.glob(os.path.expanduser(pattern)))
        if hits:
            return hits[-1]
    return None


def browser_argv(browser, capture, out_path, scale, wait_ms):
    return [
        browser, "--headless=new", "--disable-gpu", "--hide-scrollbars",
        "--no-first-run", "--no-default-browser-check",
        "--window-size=%d,%d" % (capture.width, capture.height),
        "--force-device-scale-factor=%s" % scale,
        "--virtual-time-budget=%d" % wait_ms,
        "--screenshot=%s" % out_path, capture.url,
    ]


def png_size(path):
    with open(path, "rb") as fh:
        head = fh.read(24)
    if len(head) < 24 or head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


def capture_all(captures, out_dir, browser, scale, wait_ms, run=subprocess.run):
    out_dir.mkdir(parents=True, exist_ok=True)
    failures = 0
    for c in captures:
        out = out_dir / c.name
        if out.exists():
            out.unlink()
        try:
            run(browser_argv(browser, c, out, scale, wait_ms), stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, timeout=60, check=False)
        except subprocess.TimeoutExpired:
            pass
        want = (round(c.width * float(scale)), round(c.height * float(scale)))
        got = png_size(out) if out.exists() else None
        if got == want:
            print("wrote %s %dx%d" % (out, got[0], got[1]))
        else:
            failures += 1
            print("FAIL %s: %s (want %dx%d) from %s" % (
                c.name, "no PNG" if got is None else "%dx%d" % got, want[0], want[1], c.url))
    return failures


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--base-url", required=True, help="served prototype directory URL")
    ap.add_argument("--frames", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path, help="the contract's reference/ directory")
    ap.add_argument("--viewport", action="append", default=[], help="phone=WxH or tablet=WxH override")
    ap.add_argument("--scale", default="1", help="device scale factor")
    ap.add_argument("--only", help="re-capture one screen or screen__state")
    ap.add_argument("--browser")
    ap.add_argument("--wait-ms", type=int, default=1500, help="virtual time for the page to settle")
    ap.add_argument("--dry-run", action="store_true", help="print the plan, capture nothing")
    args = ap.parse_args(argv)
    try:
        viewports = dict(VIEWPORTS)
        viewports.update(parse_viewport(v) for v in args.viewport)
        float(args.scale)
        frames = parse_frames(args.frames.read_text(encoding="utf-8"))
        captures = plan(frames, args.base_url, viewports, args.only)
        if args.dry_run:
            for c in captures:
                print("%s\t%dx%d\t%s" % (c.name, c.width, c.height, c.url))
            return 0
        browser = find_browser(args.browser)
        if not browser:
            raise UsageError("no Chromium-family browser found: pass --browser or set PROTOTYPE_BROWSER "
                             "(npx playwright install chromium-headless-shell installs one)")
    except (UsageError, OSError, ValueError) as exc:
        print("capture_reference: %s" % exc, file=sys.stderr)
        return 2
    failures = capture_all(captures, args.out, browser, args.scale, args.wait_ms)
    print("%d of %d captured" % (len(captures) - failures, len(captures)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
