---
name: prototype
description: >-
  Fast throwaway prototype of ONE task as a single self-contained HTML page:
  2-3 switchable design variants judged by senior-ux method, or a clickable
  state/logic demo, opened on the user's own phone over the LAN, then ported
  into the app. Several tasks → one subagent per task, one page each, plus an
  index page. Use when the user says prototype, quick sketch, mock it up,
  "show me options", "would this work?", or wants to see a screen or flow
  before it is built into the app.
interaction: mixed
requires: [python3 (serves the page on the LAN)]
---

> **TL;DR** One task → one throwaway HTML file in `.scratch/`, built in minutes: design questions get 2-3 structurally different variants on a switcher (senior-ux decides the method, the user picks on their phone); logic questions get buttons that drive the state with the state always visible. Small picks are ported straight into the app; big ones go through `graduate-prototype`.
> **Related**: skill://senior-ux (method for every design prototype), skill://emil-design-eng, skill://apple-design, skill://animation-vocabulary (taste and motion names), skill://graduate-prototype (exit for big ports), skill://start (quick vs big triage), skill://preview-compose (the Compose port's previews), skill://web-env (browser smoke check)

# Prototype

The point is speed: a page the user can judge today instead of a feature
built to find out it was wrong. Everything that does not help the user decide
is cut.

## 0. Is this the right path?

This skill is the **quick** prototype: one question, answerable on a page,
nothing real touched. Use the chain + prototype flag in `start` instead when
the prototype needs real app code, real persisted data, several modules, or
is meant to ship. Close call → quick: a page costs minutes, and its answer
tells you whether the big one is worth running.

## 1. One task per page

- One task = one question = one HTML file. Never two questions in a page.
- Several tasks → **one fresh subagent per task**, all dispatched at once,
  each with the brief in [references/page-brief.md](references/page-brief.md)
  and its own absolute output path. The parent writes nothing but the index.
- Output lives in `.scratch/<slug>/prototype/` (gitignored, throwaway by
  construction): `<NN>-<task>.html` per task and `index.html` linking every
  page with its question and status. One task → still write the index (one
  link), so the URL is always the same.

## 2. Build the page

Rules for every page — full checklist in the brief:

- **One self-contained file**: inline CSS and JS, no build, no CDN or network
  (opens offline on the phone). A header strip names the question and says
  `PROTOTYPE — throwaway`.
- **Look like the app**: copy the project's theme values (Compose
  `Color.kt` / `Theme.kt` / `Type.kt`, or the web theme) into CSS custom
  properties named after the app's tokens; none exists → Material 3
  baseline. Phone-width frame (~412 px) for mobile screens.
- **Fake data inline**, shaped like the real models (read them), realistic
  lengths — including the longest label and an empty list.
- **No tests, no error handling, no abstractions**, no persistence beyond
  memory. Speed over code quality; the code is deleted.

**Design question** (what should it look like / feel like):

1. Read `senior-ux` first and follow it; then `emil-design-eng`,
   `apple-design`, `animation-vocabulary` for taste and motion names.
   Start from senior-ux question 1: name the user need that fails today —
   that sentence goes in the header strip.
2. **2-3 variants, structurally different** (layout, hierarchy, primary
   affordance — not colours). Two that look alike → redo one.
3. **Switcher**: fixed bottom bar with variant buttons, `?v=a|b|c` in the
   URL, keys `1`-`3`. A second row toggles states — default, empty,
   loading, error, longest content, dark (`?s=`) — because senior-ux walks
   every state before judging. Keep it compact: at most ~2 rows (short
   labels, horizontal scroll) and collapsible to a single handle, so the
   phone still shows most of the screen being judged.
4. Measure, don't eyeball: contrast ≥ 4.5:1, 48 px targets, sizes at the
   densest state. Motion uses tokenized durations, exit faster than enter,
   and respects `prefers-reduced-motion`.

**Logic question** (does this state model / flow feel right):

1. Buttons for every event, free-play plus 1-3 guided scenarios for the
   cases that are hard on paper.
2. After every action, render the full state (and the transition taken)
   on the page.

## 3. Check, serve, ask

1. Smoke (the parent, after all pages are back): load each page in a
   headless browser (`web-env` Playwright when available), switch every
   variant and state, no console errors or network requests; capture a
   screenshot per variant into `.scratch/<slug>/prototype/shots/` and look
   at them. No browser available → say "not browser-checked" in the reply.
2. Serve: `python3 -m http.server 8766 --bind 0.0.0.0 --directory
   .scratch/<slug>/prototype` and reply with the LAN URL
   `http://<lan-ip>:8766/` (tailnet address from PROFILE `Environment facts`
   when the phone is remote), never localhost.
3. Ask one message per batch: per page, the question, the variants in one
   line each, and "which one, or which parts of each?" The verdict is the
   user's (senior-ux HITL gate); never pick for them.

## 4. After the verdict — port it

Write `.scratch/<slug>/prototype/<NN>-<task>.handoff.md`: the question and
the verdict, the chosen variant (and parts taken from others), tokens used →
app theme tokens (new ones named), every state shown, interactions and motion
(named with `animation-vocabulary` terms), copy strings, and what was faked.
This is the port's spec.

- **Small port → straight into the app**, no spec or tickets: the port passes
  `start`'s quick-task checklist (contained files, no new public interface,
  no persisted data change, no new module). It is real code now: normal
  rules apply — `tdd`, `preview-compose` previews/screenshot tests for every
  state in the handoff, `structure-checks` when configured — and it gets the
  fast-tier `review-change`. The prototype HTML is never copied into the app.
- **Big port → full flow**: hand the handoff files to `graduate-prototype`,
  which turns them into tickets for the standard chain.
- Rejected or discarded → one line in the handoff (what was learned), done.

## Anti-patterns

- Variants that differ only in colour or spacing.
- A page that needs `npm install`, a server-side build, or network.
- Judging on the laptop browser when the target is the phone.
- Polishing the losing variants, or writing tests for the page.
- Porting by translating the HTML line by line instead of from the handoff.

Adapted from mattpocock/skills (`prototype` — throwaway-answers-a-question,
variant switcher, visible state), MIT. Single-file page, senior-ux method,
per-task fan-out, and the port paths are ours.
