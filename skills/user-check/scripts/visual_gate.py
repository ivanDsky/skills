#!/usr/bin/env python3
"""Visual gate: inspect changed golden PNGs before any APK leaves.

Usage:
    visual_gate.py --out <dir> [--pairs <tsv>] [--existing <dir> ...] <golden.png> ...

Inputs
    golden.png    changed golden screenshots (e.g. `git diff --name-only
                  --diff-filter=AM -- '*.png'`).
    --pairs TSV   columns golden_png<TAB>reference_png; the reference may be
                  empty; an optional header row (`golden_png`) is skipped.
                  Paths resolve against the cwd, then the TSV's directory.
                  Pair goldens join the golden set.
    --existing D  extra directory of existing goldens to check duplicates
                  against; each changed golden's own directory (the same
                  test's other goldens, non-recursive) is always included.

Checks
    duplicates    byte-identical (md5) PNGs among the changed goldens and
                  against existing goldens of the same test. Blocking.
    pairs         golden vs reference side by side, plus a pixel-diff image
                  when the sizes match. A pair whose golden file is missing
                  is blocking; a missing or empty reference only counts.
    grouping      goldens grouped per screen/state, phone and tablet, light
                  and dark. Names: `<screen>__<state>__<phone|tablet>__<light|dark>`
                  or tokens anywhere in the stem (compact|phone|pixel and
                  expanded|medium|tablet; light|dark).
    frames        stems with `frame<N>`, `frame-<N>` or `t<N>ms` are
                  mid-animation frames; they render as a strip ordered by N.
    not checkable touch targets and text overflow cannot be read from PNGs;
                  the gallery lists them as a required Compose semantics
                  check instead of guessing from pixels.

Output: <out>/index.html plus images, static and self-contained, served with
review-site's serve command. Last stdout lines:
    visual-gate: N goldens, D duplicates, M missing reference, P pairs
Exit: 0 clean, 1 blocking (duplicates, or a declared pair's golden missing),
2 usage error. Python 3 stdlib only.
"""
import argparse
import hashlib
import html
import itertools
import re
import shutil
import struct
import sys
import zlib
from pathlib import Path

PNG_SIG = b"\x89PNG\r\n\x1a\n"
PHONE = {"compact", "phone", "pixel"}
TABLET = {"expanded", "medium", "tablet"}
THEMES = {"light", "dark"}
FRAME_RE = re.compile(r"(?:^|[-_])(?:frame[-_]?(\d+)|t(\d+)ms)(?=[-_]|$)")
MAX_DIFF_PIXELS = 3_000_000
THUMB_WIDTH = 480
COMPOSE_CHECK = (
    "Touch targets and text overflow are not readable from PNGs. Required "
    "before the APK: a semantics-based Compose test in the module tests "
    "asserting every clickable node's touch bounds are at least 48dp on both "
    "axes and that no text overflows at the screens' widest font scale "
    "(canonical place: tdd references/android-testing.md, rung 2 semantic JVM "
    "tests; component previews: preview-compose). Missing or red means no APK."
)


# ---------------------------------------------------------------- PNG codec

def png_size(data):
    if data[:8] != PNG_SIG or data[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", data[16:24])


def _chunks(data):
    pos = 8
    while pos + 8 <= len(data):
        n, kind = struct.unpack(">I4s", data[pos:pos + 8])
        yield kind, data[pos + 8:pos + 8 + n]
        pos += 12 + n


def _unfilter(raw, h, stride, bpp):
    rows, prev, pos = [], bytearray(stride), 0
    for _ in range(h):
        ft = raw[pos]
        line = bytearray(raw[pos + 1:pos + 1 + stride])
        pos += 1 + stride
        if ft == 1:
            for c in range(bpp):
                line[c::bpp] = bytes(a & 255 for a in itertools.accumulate(line[c::bpp]))
        elif ft == 2:
            line = bytearray((a + b) & 255 for a, b in zip(line, prev))
        elif ft == 3:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 255
        elif ft == 4:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                b = prev[i]
                c = prev[i - bpp] if i >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                line[i] = (line[i] + pred) & 255
        elif ft != 0:
            raise ValueError("bad PNG filter %d" % ft)
        rows.append(line)
        prev = line
    return rows


def _to_rgba(row, w, channels):
    if channels == 4:
        return bytes(row)
    out = bytearray(w * 4)
    if channels == 3:
        out[0::4], out[1::4], out[2::4], out[3::4] = row[0::3], row[1::3], row[2::3], b"\xff" * w
    elif channels == 1:
        out[0::4] = out[1::4] = out[2::4] = row
        out[3::4] = b"\xff" * w
    else:  # 2: gray + alpha
        out[0::4] = out[1::4] = out[2::4] = row[0::2]
        out[3::4] = row[1::2]
    return bytes(out)


def decode_png(data):
    """(w, h, [RGBA row bytes]) for non-interlaced 8-bit gray/RGB/RGBA PNGs, else None."""
    size = png_size(data)
    if not size:
        return None
    w, h = size
    depth, ctype, _, _, interlace = data[24:29]
    channels = {0: 1, 2: 3, 4: 2, 6: 4}.get(ctype)
    if depth != 8 or interlace or channels is None or w * h > MAX_DIFF_PIXELS:
        return None
    idat = b"".join(body for kind, body in _chunks(data) if kind == b"IDAT")
    rows = _unfilter(zlib.decompress(idat), h, w * channels, channels)
    return w, h, [_to_rgba(r, w, channels) for r in rows]


def encode_rgb_png(w, h, rows):
    raw = b"".join(b"\x00" + bytes(r) for r in rows)

    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))

    return (PNG_SIG + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def pixel_diff(golden_data, ref_data):
    """(diff percent, thumbnail png bytes) or None when undecodable or sizes differ."""
    a, b = decode_png(golden_data), decode_png(ref_data)
    if not a or not b or a[:2] != b[:2]:
        return None
    w, h, ra = a
    rb = b[2]
    k = max(1, -(-w // THUMB_WIDTH))
    tw, th = -(-w // k), -(-h // k)
    cells = [bytearray(tw) for _ in range(th)]
    shade = [bytearray(tw) for _ in range(th)]
    differing = 0
    for y in range(h):
        pa, pb = ra[y], rb[y]
        if pa == pb:
            continue
        cy = y // k
        for x in range(w):
            if pa[x * 4:x * 4 + 4] != pb[x * 4:x * 4 + 4]:
                differing += 1
                cells[cy][x // k] = 1
    for y in range(0, h, k):
        row, srow = ra[y], shade[y // k]
        for x in range(0, w, k):
            r, g, bl = row[x * 4], row[x * 4 + 1], row[x * 4 + 2]
            srow[x // k] = 128 + ((r + g + bl) // 3) // 2  # dimmed luminance
    out = []
    for cy in range(th):
        line = bytearray(tw * 3)
        for cx in range(tw):
            if cells[cy][cx]:
                line[cx * 3:cx * 3 + 3] = b"\xe0\x20\x20"
            else:
                v = shade[cy][cx]
                line[cx * 3:cx * 3 + 3] = bytes((v, v, v))
        out.append(line)
    return 100.0 * differing / (w * h), encode_rgb_png(tw, th, out)


# ----------------------------------------------------------------- analysis

class Entry:
    def __init__(self, path):
        self.path = path
        self.data = path.read_bytes()
        self.md5 = hashlib.md5(self.data).hexdigest()
        self.size = png_size(self.data)
        self.ref = None  # Path or None
        self.ref_declared = False
        stem = path.stem.lower()
        frame = FRAME_RE.search(stem)
        self.frame = None
        if frame:
            self.frame = int(frame.group(1) or frame.group(2))
            stem = stem[:frame.start()] + stem[frame.end():]
        tokens = [t for t in re.split(r"_{1,}|-+", stem) if t]
        self.form = "other"
        self.theme = "any"
        keep = []
        for t in tokens:
            if t in PHONE:
                self.form = "phone"
            elif t in TABLET:
                self.form = "tablet"
            elif t in THEMES:
                self.theme = t
            else:
                keep.append(t)
        self.key = "/".join([path.parent.name] + ["-".join(keep) or path.stem.lower()])


def resolve(p, base):
    path = Path(p)
    if path.is_absolute() or path.exists():
        return path
    return base / path


def read_pairs(tsv):
    pairs = []
    for line in tsv.read_text().splitlines():
        if not line.strip():
            continue
        cols = line.split("\t")
        if cols[0].strip() == "golden_png":
            continue
        pairs.append((cols[0].strip(), cols[1].strip() if len(cols) > 1 else ""))
    return pairs


def analyse(golden_args, pairs_tsv, existing_dirs):
    base = pairs_tsv.parent if pairs_tsv else Path.cwd()
    entries, missing_golden, bad_refs = {}, [], []
    for g in golden_args:
        p = Path(g)
        entries[p.resolve()] = Entry(p)
    declared = {}
    if pairs_tsv:
        for g, r in read_pairs(pairs_tsv):
            gp = resolve(g, base)
            if not gp.is_file():
                missing_golden.append(g)
                continue
            e = entries.setdefault(gp.resolve(), Entry(gp))
            if r:
                rp = resolve(r, base)
                e.ref_declared = True
                if rp.is_file():
                    e.ref = rp
                else:
                    bad_refs.append(r)
    order = sorted(entries.values(), key=lambda e: str(e.path))

    # duplicates: changed goldens vs changed + existing siblings
    pool = {e.path.resolve(): e.md5 for e in order}
    dirs = {e.path.parent.resolve() for e in order} | {Path(d).resolve() for d in existing_dirs}
    for d in sorted(dirs):
        for f in sorted(d.glob("*.png")):
            pool.setdefault(f.resolve(), hashlib.md5(f.read_bytes()).hexdigest())
    by_md5 = {}
    for f, digest in pool.items():
        by_md5.setdefault(digest, []).append(f)
    changed = {e.path.resolve() for e in order}
    duplicates = [sorted(fs) for fs in by_md5.values() if len(fs) > 1 and changed & set(fs)]
    duplicates.sort()
    return order, duplicates, missing_golden, bad_refs


# --------------------------------------------------------------------- html

CSS = """
:root{color-scheme:light dark}
body{font:15px/1.5 system-ui,sans-serif;max-width:90rem;margin:1.5rem auto;padding:0 1rem}
h1,h2{border-bottom:1px solid #8884;padding-bottom:.2rem}
.banner{padding:.6rem 1rem;border-radius:6px;font-weight:600}
.bad{background:#e0202022;border:1px solid #e02020}.ok{background:#20a04022;border:1px solid #20a040}
.note{background:#8881;border:1px solid #8884;border-radius:6px;padding:.6rem 1rem}
.cells{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:1rem;align-items:start}
.cell{border:1px solid #8884;border-radius:6px;padding:.5rem}
.cell.tablet{grid-column:span 2}
.row{display:flex;gap:.5rem;align-items:flex-start;flex-wrap:wrap}
.row figure{margin:0;flex:1 1 30%}
.strip{display:flex;gap:.4rem;overflow-x:auto}.strip figure{margin:0;flex:0 0 auto;max-width:240px}
img{max-width:100%;border:1px solid #8884;border-radius:4px}
figcaption,.meta{font-size:12px;opacity:.75;word-break:break-all}
code{background:#8882;padding:0 .25rem;border-radius:3px}
"""


def fig(src, cap):
    return f'<figure><img loading="lazy" src="{html.escape(src)}"><figcaption>{html.escape(cap)}</figcaption></figure>'


def build_gallery(out, order, duplicates, missing_golden, bad_refs, summary):
    used = set()

    def put(sub, name, data):
        d = out / sub
        d.mkdir(exist_ok=True)
        stem = re.sub(r"[^A-Za-z0-9._-]", "_", name)
        n, cand = 0, stem
        while (sub, cand) in used:
            n += 1
            cand = f"{n}-{stem}"
        used.add((sub, cand))
        (d / cand).write_bytes(data)
        return f"{sub}/{cand}"

    groups = {}
    for e in order:
        groups.setdefault(e.key, []).append(e)

    body = []
    blocking = bool(duplicates or missing_golden)
    body.append(f'<div class="banner {"bad" if blocking else "ok"}">'
                f'{"BLOCKING — no APK until fixed. " if blocking else "No blocking findings. "}'
                f'{html.escape(summary)}</div>')
    if duplicates:
        items = "".join("<li>" + " = ".join(f"<code>{html.escape(str(f))}</code>" for f in grp) + "</li>"
                        for grp in duplicates)
        body.append(f"<h2>Blocking: byte-identical goldens</h2><ul>{items}</ul>"
                    "<p class='meta'>Identical bytes mean one state was recorded twice or a "
                    "variant renders the same; fix the test so each golden shows its own state.</p>")
    if missing_golden:
        items = "".join(f"<li><code>{html.escape(g)}</code></li>" for g in missing_golden)
        body.append(f"<h2>Blocking: declared pair with a missing golden</h2><ul>{items}</ul>")
    if bad_refs:
        items = "".join(f"<li><code>{html.escape(r)}</code></li>" for r in bad_refs)
        body.append(f"<h2>Reference file declared but not found</h2><ul>{items}</ul>")
    body.append(f"<h2>Required Compose check</h2><p class='note'>{html.escape(COMPOSE_CHECK)}</p>")

    body.append("<h2>Screens</h2>")
    for key in sorted(groups):
        es = groups[key]
        forms = {e.form for e in es} - {"other"}
        cov = ""
        if forms and forms != {"phone", "tablet"}:
            cov = f' <span class="meta">only {"/".join(sorted(forms))} captured</span>'
        body.append(f"<h3>{html.escape(key)}{cov}</h3><div class='cells'>")
        cells = {}
        for e in es:
            cells.setdefault((e.form, e.theme), []).append(e)
        for (form, theme), cell in sorted(cells.items()):
            parts = [f"<div class='cell {form}'><div class='meta'>{html.escape(form)} · {html.escape(theme)}</div>"]
            frames = sorted((e for e in cell if e.frame is not None), key=lambda e: e.frame)
            plain = [e for e in cell if e.frame is None]
            if frames:
                parts.append("<div class='strip'>" + "".join(
                    fig(put("img", f"{e.md5[:8]}-{e.path.name}", e.data), f"frame {e.frame}") for e in frames) + "</div>")
            for e in plain:
                row = [fig(put("img", f"{e.md5[:8]}-{e.path.name}", e.data),
                           f"golden {e.path.name} {e.size[0]}x{e.size[1]}" if e.size else f"golden {e.path.name}")]
                if e.ref:
                    rdata = e.ref.read_bytes()
                    rsize = png_size(rdata)
                    row.append(fig(put("ref", f"{e.md5[:8]}-{e.path.name}", rdata),
                                   f"reference {e.ref.name} {rsize[0]}x{rsize[1]}" if rsize else f"reference {e.ref.name}"))
                    if rsize and e.size and rsize == e.size:
                        d = pixel_diff(e.data, rdata)
                        if d:
                            row.append(fig(put("diff", f"{e.md5[:8]}-{e.path.name}", d[1]), f"diff {d[0]:.2f}% pixels differ"))
                    elif rsize and e.size:
                        row.append(f"<p class='meta'>size mismatch: golden {e.size[0]}x{e.size[1]} vs reference "
                                   f"{rsize[0]}x{rsize[1]}; no pixel diff</p>")
                else:
                    row.append("<p class='meta'>no reference</p>")
                parts.append("<div class='row'>" + "".join(row) + "</div>")
            parts.append("</div>")
            body.append("".join(parts))
        body.append("</div>")
    (out / "index.html").write_text(
        "<!doctype html><meta charset='utf-8'><title>Visual gate</title>"
        f"<style>{CSS}</style><h1>Visual gate</h1>" + "\n".join(body))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Visual gate for changed golden PNGs.")
    ap.add_argument("goldens", nargs="*", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--pairs", type=Path)
    ap.add_argument("--existing", type=Path, action="append", default=[])
    args = ap.parse_args(argv)
    missing = [p for p in args.goldens if not p.is_file()]
    if missing:
        print("not a file: " + ", ".join(map(str, missing)), file=sys.stderr)
        return 2
    if args.pairs and not args.pairs.is_file():
        print(f"not a file: {args.pairs}", file=sys.stderr)
        return 2
    if not args.goldens and not args.pairs:
        ap.print_usage(sys.stderr)
        return 2

    order, duplicates, missing_golden, bad_refs = analyse(
        [str(p) for p in args.goldens], args.pairs, args.existing)
    n_pairs = sum(1 for e in order if e.ref)
    n_missing_ref = sum(1 for e in order if not e.ref)
    summary = (f"visual-gate: {len(order)} goldens, {len(duplicates)} duplicates, "
               f"{n_missing_ref} missing reference, {n_pairs} pairs")
    if args.out.exists():
        shutil.rmtree(args.out)
    args.out.mkdir(parents=True)
    build_gallery(args.out, order, duplicates, missing_golden, bad_refs, summary)

    for grp in duplicates:
        print("DUPLICATE: " + " = ".join(map(str, grp)))
    for g in missing_golden:
        print(f"MISSING GOLDEN for declared pair: {g}")
    for r in bad_refs:
        print(f"missing reference file: {r}")
    print("required Compose check (not readable from PNGs): touch targets >= 48dp and text overflow, "
          "semantics test in the module tests; details in the gallery")
    print(summary)
    print(f"gallery: {(args.out / 'index.html').resolve()}")
    print(f"serve: python3 -m http.server 8765 --bind 0.0.0.0 --directory {args.out.resolve()}")
    return 1 if duplicates or missing_golden else 0


if __name__ == "__main__":
    sys.exit(main())
