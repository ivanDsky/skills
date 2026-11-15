# Page rules

Read before building or briefing a page (SKILL.md § 2). The page brief's
checklist is the short form of these rules.

## Every page

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

## Design question (what should it look like / feel like)

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

## Logic question (does this state model / flow feel right)

1. Buttons for every event, free-play plus 1-3 guided scenarios for the
   cases that are hard on paper.
2. After every action, render the full state (and the transition taken)
   on the page.

## Anti-patterns

- Variants that differ only in colour or spacing.
- A page that needs `npm install`, a server-side build, or network.
- Judging on the laptop browser when the target is the phone.
- Polishing the losing variants, or writing tests for the page.
- Browser runs or screenshots before the user sees it — they cost time and
  the user's own look replaces them. Screenshots exist only at the contract
  freeze, captured from approved pages.
- Porting by translating the HTML line by line instead of from the handoff.
- An ask that describes visual options without a served, checked URL.
- A local file path or "will send next" in place of a link.
