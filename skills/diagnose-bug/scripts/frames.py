#!/usr/bin/env python3
"""frames.py — turn a screen recording into timestamped frames and one labelled contact sheet.

Usage:
  frames.py VIDEO [--from S] [--to S] [--fps N] [--max N] [--width PX] [--cols N] [--out DIR]

Writes DIR/f_0001.png … (one per sampled moment) and DIR/sheet.png (a grid, each cell labelled
with its time in seconds), then prints one `<seconds>\t<path>` line per frame and the sheet path.
Look at the sheet first; open single frames only around the moment that matters.

ffmpeg does the decoding with only the `fps` and `scale` filters, which every build has (Homebrew
ffmpeg ships without `drawtext`, the filter hand-written contact sheets kept failing on). Labels
and the grid are drawn with Pillow. --fps is lowered so at most --max frames come out.
Exit codes: 0 done, 1 bad input or a failed tool, 2 a missing dependency (ffmpeg, ffprobe, Pillow).
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def die(msg, code=1):
    print(f"frames.py: {msg}", file=sys.stderr)
    sys.exit(code)


def duration(video):
    p = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(video)],
        capture_output=True, text=True,
    )
    if p.returncode != 0:
        die(f"ffprobe could not read {video}: {p.stderr.strip()}")
    try:
        return float(json.loads(p.stdout)["format"]["duration"])
    except (KeyError, ValueError):
        die(f"ffprobe reported no duration for {video}")


def extract(video, out, start, end, fps, width):
    for old in out.glob("f_*.png"):
        old.unlink()
    p = subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.3f}", "-to", f"{end:.3f}", "-i", str(video),
         "-vf", f"fps={fps:.6f},scale={width}:-2", str(out / "f_%04d.png")],
        capture_output=True, text=True,
    )
    if p.returncode != 0:
        die(f"ffmpeg failed: {p.stderr.strip()}")
    return sorted(out.glob("f_*.png"))


def contact_sheet(frames, times, cols, dest):
    from PIL import Image, ImageDraw, ImageFont

    first = Image.open(frames[0])
    w, h = first.size
    label_h = max(18, w // 14)
    rows = -(-len(frames) // cols)
    sheet = Image.new("RGB", (cols * w, rows * (h + label_h)), "white")
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.load_default(size=label_h - 4)
    except TypeError:  # Pillow < 10.1 has no sized default font
        font = ImageFont.load_default()
    for i, (frame, t) in enumerate(zip(frames, times)):
        x, y = (i % cols) * w, (i // cols) * (h + label_h)
        draw.text((x + 4, y + 2), f"{t:.2f}s  #{i + 1}", fill="black", font=font)
        sheet.paste(Image.open(frame).convert("RGB"), (x, y + label_h))
    sheet.save(dest)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("video", type=Path)
    ap.add_argument("--from", dest="start", type=float, default=0.0, help="start second (default 0)")
    ap.add_argument("--to", dest="end", type=float, help="end second (default: end of video)")
    ap.add_argument("--fps", type=float, default=4.0, help="frames per second to sample (default 4)")
    ap.add_argument("--max", type=int, default=48, help="frame cap; --fps is lowered to fit (default 48)")
    ap.add_argument("--width", type=int, default=360, help="frame width in px (default 360)")
    ap.add_argument("--cols", type=int, default=6, help="contact sheet columns (default 6)")
    ap.add_argument("--out", type=Path, help="output dir (default: /tmp/frames-<video stem>)")
    a = ap.parse_args(argv)

    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            die(f"{tool} not found on PATH (brew install ffmpeg)", 2)
    try:
        import PIL  # noqa: F401
    except ImportError:
        die("Pillow not importable (python3 -m pip install pillow)", 2)
    if not a.video.is_file():
        die(f"no such file: {a.video}")

    total = duration(a.video)
    end = min(a.end if a.end is not None else total, total)
    if not 0 <= a.start < end:
        die(f"empty window --from {a.start} --to {end:.2f} (video is {total:.2f}s)")
    fps = min(a.fps, a.max / (end - a.start))
    out = a.out or Path("/tmp") / f"frames-{a.video.stem.replace(' ', '_')}"
    out.mkdir(parents=True, exist_ok=True)

    frames = extract(a.video, out, a.start, end, fps, a.width)[: a.max]
    if not frames:
        die("ffmpeg produced no frames for that window")
    times = [a.start + i / fps for i in range(len(frames))]
    sheet = out / "sheet.png"
    contact_sheet(frames, times, max(1, min(a.cols, len(frames))), sheet)

    for t, f in zip(times, frames):
        print(f"{t:.2f}\t{f}")
    print(f"sheet\t{sheet}")


if __name__ == "__main__":
    main()
