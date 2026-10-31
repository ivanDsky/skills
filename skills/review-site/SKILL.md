---
name: review-site
description: >-
  Publishes a run's review artifacts as a small self-contained static site on
  localhost — important changes, screenshots, UI captures, diagrams, and test
  report in one scrollable HTML page. Use when the user says publish the
  review, review dashboard, show me the report on localhost, review site, or
  wants screenshots/diagrams/test evidence browsable in a browser instead of
  reading files.
interaction: afk
requires: []
---

> **TL;DR** Builds a one-file static review site (changes, screenshots, diagrams, test logs) from `.scratch/<slug>/` and serves it on localhost; fires on "publish the review" / "review site".
> **Related**: skill://deliver (REPORT.md source), skill://review-change (REVIEW.md source), skill://archify (diagram artifacts), skill://preview-compose (screenshot captures)

# Review site

Assemble the run's evidence into one small page the user can skim in a
browser. Nothing new is produced here — the site only packages artifacts
that `review-change` and `deliver` already wrote. Missing inputs are listed,
never faked.

## 1. Collect

Inputs live under `.scratch/<slug>/`:

| Section | Source | Written by |
|---|---|---|
| Changes | `REPORT.md` | `deliver` |
| Visual review | `REVIEW.md` | `review-change` |
| Screenshots | `*.png/gif/jpg/webp` (JVM captures, review doc assets) | `preview-compose` suites, review gate |
| Diagrams | `*.html` archify artifacts | `archify` |
| Test report | `build.log`, `*test*.log` | `deliver`, test runner |

No REPORT.md yet → run `deliver`'s report step first; an empty Changes
section makes the page pointless.

## 2. Build

```bash
python3 skills/review-site/scripts/build_site.py .scratch/<slug>
```

(one repo-local path; when installed globally use the skill's installed
script path). Output: `.scratch/<slug>/site/index.html` — self-contained
(images inlined, ≤4MB each, 24 newest), no network, no build tooling. Re-run
anytime; it overwrites in place.

## 3. Serve

```bash
python3 -m http.server 8765 --directory .scratch/<slug>/site
```

Localhost only, by design. Reply with the URL
(`http://localhost:8765`) and one line per section saying what's on the
page. `--out <dir>` relocates the site (e.g. a shared folder); the user
asking for anything beyond localhost — a public URL, a tunnel — is a
one-way door: confirm before exposing, same rule as `deploy-tailscale`
funnel.

## 4. Keep it small

The page must stay skimmable: if it exceeds ~2 minutes to scroll, trim
first — drop superseded screenshots (keep the final state per surface),
tail logs to the last failure + summary, link diagrams instead of nesting
them. The site is a review surface, not an archive; the ledger and
`.scratch/` remain the archive.

No diagram yet but the change was structural → read `skill://archify`, build
the diagram first, then re-run this skill.
