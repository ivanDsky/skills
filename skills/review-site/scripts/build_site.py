#!/usr/bin/env python3
"""Build a self-contained review site from a run's .scratch/<slug>/ directory.

Usage: python3 build_site.py <scratch-slug-dir> [--out <dir>]
Output: <out>/index.html (default: <scratch-slug-dir>/site/index.html), fully
self-contained (images inlined as base64) — one file, zero dependencies,
served by any static file server.

Collected, in section order:
  1. Changes        — REPORT.md (deliver's user-facing report), if present
  2. Visual review  — REVIEW.md (review-change's doc), if present
  3. Screenshots    — *.png/*.gif/*.jpg/*.webp under the slug dir (cap 24,
                      newest first), inlined
  4. Diagrams       — *.html diagram/explainer artifacts (linked, not inlined)
  5. Test report    — build.log tail + any *test*.log/*.txt tails
Everything else is ignored — the site stays small and review-focused.
"""
import argparse
import base64
import html
import re
import shutil
import sys
from pathlib import Path

IMG_EXTS = {".png", ".gif", ".jpg", ".jpeg", ".webp"}
MAX_IMG_BYTES = 4 * 1024 * 1024
MAX_IMAGES = 24
LOG_TAIL_LINES = 120


def md_to_html(text: str) -> str:
    try:
        import markdown  # type: ignore
        return markdown.markdown(text, extensions=["tables", "fenced_code"])
    except ImportError:
        pass
    out, in_code = [], False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            out.append("<pre>" if not in_code else "</pre>")
            in_code = not in_code
            continue
        if in_code:
            out.append(html.escape(line))
            continue
        s = html.escape(line)
        s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r'<img alt="\1" src="\2">', s)
        s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
        s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
        if re.match(r"^#{1,4} ", s):
            level = len(s) - len(s.lstrip("#"))
            s = f"<h{level}>{s.lstrip('# ').strip()}</h{level}>"
        elif re.match(r"^\s*[-*] ", s):
            s = f"<li>{s.strip()[2:]}</li>"
        out.append(f"<p>{s}</p>" if s.strip() and not s.startswith(("<h", "<li", "<p")) else s)
    return "\n".join(out)


def inline_image(path: Path) -> str:
    data = base64.b64encode(path.read_bytes()).decode()
    return f"data:image/{path.suffix.lstrip('.').replace('jpg', 'jpeg')};base64,{data}"


def log_tail(path: Path) -> str:
    lines = path.read_text(errors="replace").splitlines()
    return "\n".join(lines[-LOG_TAIL_LINES:])


def section(title: str, body: str) -> str:
    return f"<section><h2>{html.escape(title)}</h2>{body}</section>"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug_dir", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    slug = args.slug_dir.resolve()
    if not slug.is_dir():
        sys.exit(f"not a directory: {slug}")
    out = (args.out or slug / "site").resolve()
    out.mkdir(parents=True, exist_ok=True)

    sections = []
    candidates = {
        "Changes": [slug / "REPORT.md"],
        "Visual review": [slug / "REVIEW.md", slug / "review" / "REVIEW.md"],
    }
    for name, paths in candidates.items():
        for f in paths:
            if f.is_file():
                sections.append(section(name, md_to_html(f.read_text())))
                break

    shots = sorted(
        (p for p in slug.rglob("*") if p.suffix.lower() in IMG_EXTS
         and p.stat().st_size <= MAX_IMG_BYTES and "site" not in p.relative_to(slug).parts),
        key=lambda p: p.stat().st_mtime, reverse=True)[:MAX_IMAGES]
    if shots:
        cards = "".join(
            f'<figure><figcaption>{html.escape(str(p.relative_to(slug)))}</figcaption>'
            f'<img loading="lazy" src="{inline_image(p)}"></figure>'
            for p in shots)
        sections.append(section(f"Screenshots ({len(shots)})", f'<div class="grid">{cards}</div>'))

    diagrams = [p for p in slug.rglob("*.html") if p.name != "index.html"
                and "site" not in p.relative_to(slug).parts]
    if diagrams:
        items = "".join(
            f'<li><a href="../{html.escape(str(p.relative_to(slug)))}">{html.escape(p.stem)}</a></li>'
            for p in diagrams)
        # copy diagrams next to index so relative assets resolve
        for p in diagrams:
            dst = out / p.relative_to(slug)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dst)
        sections.append(section("Diagrams", f"<ul>{items}</ul>"))

    logs = [slug / "build.log"] + sorted(slug.rglob("*test*.log")) + sorted(slug.glob("*test*.txt"))
    log_html = "".join(
        f"<h3>{html.escape(p.name)}</h3><pre>{html.escape(log_tail(p))}</pre>"
        for p in dict.fromkeys(logs) if p.is_file())
    if log_html:
        sections.append(section("Test report", log_html))

    title = slug.name
    body = "\n".join(sections) or "<p>No report artifacts found.</p>"
    (out / "index.html").write_text(
        f"""<!doctype html><meta charset="utf-8">
<title>Review — {html.escape(title)}</title>
<style>
:root {{ color-scheme: light dark; }}
body {{ font: 15px/1.6 system-ui, sans-serif; max-width: 60rem; margin: 2rem auto; padding: 0 1rem; }}
h1, h2 {{ border-bottom: 1px solid #8884; padding-bottom: .2rem; }}
pre {{ background: #8881; padding: .8rem; overflow-x: auto; border-radius: 6px; font-size: 13px; }}
img {{ max-width: 100%; border: 1px solid #8884; border-radius: 6px; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem; }}
figure {{ margin: 0; }} figcaption {{ font-size: 12px; opacity: .7; word-break: break-all; }}
</style>
<h1>Review — {html.escape(title)}</h1>
{body}""")
    print(f"site ready: {out / 'index.html'}")
    print(f"serve: python3 -m http.server 8765 --bind 0.0.0.0 --directory {out}")
    return 0


if __name__ == "__main__":
    main()
