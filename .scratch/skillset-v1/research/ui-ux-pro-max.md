# ui-ux-pro-max — adoption research (T022)

Checked 2026-10-29 on user request (not in the original 12 sources).

## What it is

An AI skill providing design intelligence "across multiple platforms and frameworks": a Python CLI (`search.py`) querying curated CSV datasets — 192 industry reasoning rules, 79 searchable UI styles, 119 UX guidelines, 105 curated icon rows, Google Fonts data — plus design-system generation (master + per-page overrides) and stack-specific guidelines for **22 stacks**. Verified: 142,568 stars, MIT, created 2025-11-30, pushed 2026-10-26 (GitHub API).

## Mobile? YES

Dedicated stack rows for **Android / Jetpack Compose**, iOS / SwiftUI, React Native, Flutter, plus desktop (JavaFX, WPF, WinUI 3, Avalonia, Uno, UWP) and the web ecosystem (React/Next/shadcn, Vue/Nuxt, Angular, Laravel, Svelte/Astro/Three.js, HTML+Tailwind default). Honest caveat: the style taxonomy is web-leaning (43 general visual families vs **2 mobile-specific styles**); mobile value is concentrated in the stack guidelines + UX rules, not style families.

## Why popular / how organized

Sells "professional UI without generic AI slop" for any stack, installable everywhere (Claude marketplace, npm `ui-ux-pro-max-cli`, global install). Repo mirrors one data tree into `.claude/skills/`, `cli/assets/`, `src/` (698 files, 21 MB total — three copies + screenshots; the installable skill is one dir). Search-based design = data on disk queried on demand: low always-on token cost, good progressive-disclosure citizen. Freemium: this repo is the MIT Basic version; a paid Premium exists.

## Adoption verdict

**install-as-is** (their CLI or `npx skills`). Fills the platform-specific UX gap — the mobile source our review-ux axis lacked; complements taste-skill/impeccable (web-only) instead of duplicating. Wiring: `review-change`'s `review-ux.md` axis loads uupm stack guidelines (Compose for us); `references/rules-ui-<platform>.md` payloads can be seeded from its design-system generation. Integration must add trigger cases (auto-activate description unverified) and watch for premium upsell text.

## Sources

- README: https://raw.githubusercontent.com/nextlevelbuilder/ui-ux-pro-max-skill/main/README.md
- Repo API: https://api.github.com/repos/nextlevelbuilder/ui-ux-pro-max-skill ; tree: /git/trees/main?recursive=1
