"""visual_gate.py against real PuzzleBox goldens (copied read-only into fixtures)."""
import struct
import zlib
from pathlib import Path

import pytest

import visual_gate as vg

SUMMARY = "visual-gate: "


def summary(out):
    return next(line for line in out.splitlines() if line.startswith(SUMMARY))


def test_clean_set_exits_0_and_prints_summary(goldens, gate, tmp_path):
    code, out = gate("--out", tmp_path / "g", *sorted((goldens / "queens-ui").glob("*.png")))
    assert code == 0
    assert summary(out) == "visual-gate: 5 goldens, 0 duplicates, 5 missing reference, 0 pairs"
    assert (tmp_path / "g" / "index.html").is_file()


def test_real_identical_pair_is_blocking(goldens, gate, tmp_path):
    code, out = gate("--out", tmp_path / "g", goldens / "queens-ui-dup" / "violation-compact-light.png",
                     goldens / "queens-ui-dup" / "hint-compact-light.png")
    assert code == 1
    assert "DUPLICATE" in out and "violation-caption-compact-light.png" in out  # found via sibling check
    assert summary(out).startswith("visual-gate: 2 goldens, 1 duplicates")
    assert "BLOCKING" in (tmp_path / "g" / "index.html").read_text()


def test_duplicates_among_changed_goldens(goldens, gate, tmp_path):
    code, out = gate("--out", tmp_path / "g", *sorted((goldens / "queens-ui-dup").glob("*.png")))
    assert code == 1 and "1 duplicates" in summary(out)


def test_unchanged_duplicate_siblings_do_not_block(goldens, gate, tmp_path):
    """The identical pair exists on disk but neither file changed: not this change's problem."""
    code, out = gate("--out", tmp_path / "g", goldens / "queens-ui-dup" / "hint-compact-light.png")
    assert code == 0 and "0 duplicates" in summary(out)


def test_existing_dir_is_checked(goldens, gate, tmp_path):
    new = tmp_path / "new" / "x.png"
    new.parent.mkdir()
    new.write_bytes((goldens / "queens-ui-dup" / "violation-compact-light.png").read_bytes())
    code, out = gate("--out", tmp_path / "g", "--existing", goldens / "queens-ui-dup", new)
    assert code == 1 and "1 duplicates" in summary(out)


def test_pairs_side_by_side_and_diff(goldens, gate, tmp_path):
    q = goldens / "queens-ui"
    tsv = tmp_path / "pairs.tsv"
    tsv.write_text(f"golden_png\treference_png\n{q/'empty-compact-light.png'}\t{q/'empty-compact-dark.png'}\n"
                   f"{q/'hint-compact-dark.png'}\t\n")
    code, out = gate("--out", tmp_path / "g", "--pairs", tsv, q / "empty-compact-light.png",
                     q / "hint-compact-dark.png")
    assert code == 0
    assert summary(out) == "visual-gate: 2 goldens, 0 duplicates, 1 missing reference, 1 pairs"
    page = (tmp_path / "g" / "index.html").read_text()
    assert "reference empty-compact-dark.png" in page and "pixels differ" in page and "no reference" in page
    assert len(list((tmp_path / "g" / "diff").glob("*.png"))) == 1


def test_size_mismatch_has_no_diff(goldens, gate, tmp_path):
    q = goldens / "queens-ui"
    tsv = tmp_path / "pairs.tsv"
    tsv.write_text(f"{q/'empty-compact-dark.png'}\t{q/'empty-expanded-dark.png'}\n")
    code, _ = gate("--out", tmp_path / "g", "--pairs", tsv)
    page = (tmp_path / "g" / "index.html").read_text()
    assert code == 0 and "size mismatch" in page and not (tmp_path / "g" / "diff").exists()


def test_missing_golden_for_declared_pair_blocks(goldens, gate, tmp_path):
    q = goldens / "queens-ui"
    tsv = tmp_path / "pairs.tsv"
    tsv.write_text(f"{q/'gone.png'}\t{q/'empty-compact-dark.png'}\n")
    code, out = gate("--out", tmp_path / "g", "--pairs", tsv, q / "hint-compact-dark.png")
    assert code == 1 and "MISSING GOLDEN" in out and "1 goldens" in summary(out)


def test_missing_reference_file_counts_but_does_not_block(goldens, gate, tmp_path):
    q = goldens / "queens-ui"
    tsv = tmp_path / "pairs.tsv"
    tsv.write_text(f"{q/'hint-compact-dark.png'}\t{q/'nope.png'}\n")
    code, out = gate("--out", tmp_path / "g", "--pairs", tsv)
    assert code == 0 and "1 missing reference, 0 pairs" in summary(out)


def test_phone_tablet_light_dark_grouped_per_screen(goldens, gate, tmp_path):
    q = goldens / "queens-ui"
    gate("--out", tmp_path / "g", q / "empty-compact-dark.png", q / "empty-compact-light.png",
         q / "empty-expanded-dark.png")
    page = (tmp_path / "g" / "index.html").read_text()
    assert page.count("<h3>") == 1 and "queens-ui/empty" in page
    assert "phone · dark" in page and "phone · light" in page and "tablet · dark" in page
    assert "only" not in page.split("<h3>")[1].split("</h3>")[0]


def test_single_form_coverage_is_flagged(goldens, gate, tmp_path):
    gate("--out", tmp_path / "g", goldens / "queens-ui" / "hint-compact-dark.png")
    assert "only phone captured" in (tmp_path / "g" / "index.html").read_text()


def test_frames_render_as_ordered_strip(goldens, gate, tmp_path):
    q = goldens / "queens-ui"
    anim = tmp_path / "anim"
    anim.mkdir()
    for name, src in [("reveal-frame10-compact-light.png", "empty-compact-light.png"),
                      ("reveal-frame2-compact-light.png", "empty-compact-dark.png"),
                      ("reveal-t300ms-compact-light.png", "hint-compact-dark.png")]:
        (anim / name).write_bytes((q / src).read_bytes())
    code, out = gate("--out", tmp_path / "g", *sorted(anim.glob("*.png")))
    page = (tmp_path / "g" / "index.html").read_text()
    assert code == 0 and "class='strip'" in page and page.count("<h3>") == 1
    assert page.index("frame 2<") < page.index("frame 10<") and page.index("frame 10<") < page.index("frame 300<")


def test_compose_check_is_listed_never_pixel_guessed(goldens, gate, tmp_path):
    _, out = gate("--out", tmp_path / "g", goldens / "queens-ui" / "hint-compact-dark.png")
    page = (tmp_path / "g" / "index.html").read_text()
    assert "48dp" in page and "android-testing.md" in page and "48dp" in out


def test_usage_errors(gate, tmp_path):
    assert gate("--out", tmp_path / "g")[0] == 2
    assert gate("--out", tmp_path / "g", tmp_path / "missing.png")[0] == 2


def _chunk(kind, body):
    return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))


def _png(w, h, pixels, filters):
    """Independent encoder: RGBA rows, per-row filter type from `filters`."""
    bpp, stride, raw, prev = 4, w * 4, b"", bytes(w * 4)
    for y in range(h):
        row = pixels[y * stride:(y + 1) * stride]
        ft = filters[y % len(filters)]
        out = bytearray()
        for i in range(stride):
            a = row[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            if ft == 0:
                pred = 0
            elif ft == 1:
                pred = a
            elif ft == 2:
                pred = b
            elif ft == 3:
                pred = (a + b) // 2
            else:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
            out.append((row[i] - pred) & 255)
        raw += bytes([ft]) + bytes(out)
        prev = row
    return (vg.PNG_SIG + _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + _chunk(b"IDAT", zlib.compress(raw)) + _chunk(b"IEND", b""))


def test_decoder_handles_every_png_filter():
    w, h = 7, 10
    pixels = bytes((x * 37 + y * 11 + i * 53) % 251 for y in range(h) for x in range(w) for i in range(4))
    got = vg.decode_png(_png(w, h, pixels, [0, 1, 2, 3, 4]))
    assert got[:2] == (w, h) and b"".join(got[2]) == pixels


def test_pixel_diff_identical_and_changed():
    w, h = 6, 6
    base = bytes(range(w * h * 4))
    same = vg.pixel_diff(_png(w, h, base, [0]), _png(w, h, base, [4]))
    assert same[0] == 0.0
    changed = bytearray(base)
    changed[0] ^= 0xFF
    pct, thumb = vg.pixel_diff(_png(w, h, base, [0]), _png(w, h, bytes(changed), [0]))
    assert pct == pytest.approx(100 / 36) and thumb.startswith(vg.PNG_SIG)
    assert vg.pixel_diff(_png(w, h, base, [0]), _png(w, h + 1, base + bytes(w * 4), [0])) is None
