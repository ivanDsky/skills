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
> **Related**: skill://deliver (REPORT.md source), skill://user-check (REVIEW.md check-doc source), skill://archify (diagram artifacts), skill://preview-compose (screenshot captures)

# Review site

Assemble the run's evidence into one small page the user can skim in a
browser. Nothing new is produced here — the site only packages artifacts
that `user-check`, `review-change` and `deliver` already wrote. Missing
inputs are listed, never faked.

## 1. Collect

Inputs live under `.scratch/<slug>/`:

| Section | Source | Written by |
|---|---|---|
| Changes | `REPORT.md` | `deliver` |
| Visual review | `REVIEW.md` (check doc) | `user-check` |
| Screenshots | `*.png/gif/jpg/webp` (JVM captures, check doc assets) | `preview-compose` suites, `user-check` |
| Diagrams | `*.html` archify artifacts | `archify` |
| Test report | `build.log`, `suite.log`, `*test*.log` | `user-check`/`deliver` builds, `review-change` suite run |

No REPORT.md yet and the run is at `user-check` → publish with the check doc
alone (Changes lists as missing). Otherwise run `deliver`'s report step
first; an empty Changes section makes a delivery page pointless.

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
python3 -m http.server 8765 --bind 0.0.0.0 --directory .scratch/<slug>/site
```

Bound to all interfaces so the page opens from any device on the LAN/tailnet.
Hand it out under `prototype` § 3 Serve: a long-lived server (never one that
dies with the turn), the tailnet URL first and the LAN URL second
(`http://<ip>:8765`, never localhost or a file path; the generator prints the
serve command), and its curl check (with retries) right before the
link goes out. Reachable only inside the local network — anything beyond
(public URL, tunnel) is a one-way door: confirm before exposing, same rule
as `deploy-tailscale` funnel.

## 4. Keep it small

The page must stay skimmable: if it exceeds ~2 minutes to scroll, trim
first — drop superseded screenshots (keep the final state per surface),
tail logs to the last failure + summary, link diagrams instead of nesting
them. The site is a review surface, not an archive; the ledger and
`.scratch/` remain the archive.

No diagram yet but the change was structural → read `skill://archify`, build
the diagram first, then re-run this skill.
