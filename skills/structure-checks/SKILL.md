---
name: structure-checks
description: >-
  Turn the architecture and readability rules into failing checks on Kotlin or
  Android projects (Konsist tests plus detekt) and on web SvelteKit or
  TypeScript projects (ESLint plus dependency-cruiser) — one class per file,
  hard file-size and complexity caps, layer dependencies, no agent-written
  comments, no mocking APIs, Compose and Svelte component rules — with a
  shrink-only ratchet for existing violators, so workers fix by splitting
  instead of arguing with prose. Use when setting up structure checks, when a
  ticket adds or moves Kotlin or web files and needs its structure evidence,
  when files keep growing or holding many classes, when agents leave comments
  or reach for mocks, or when the user says konsist, detekt, eslint,
  dependency-cruiser, structure test, one class per file, file size cap, or
  enforce the architecture rules mechanically.
interaction: mixed
requires: [Gradle build for the Kotlin engine, Node project with ESLint for the web engine]
---

> **TL;DR** Prose rules about structure, comments and mocks get ignored; a failing lint does not. This skill installs the checks on either engine, owns the ratchet, and defines the worker contract: fix by splitting, never edit rules or suppress.
> **Related**: skill://design-architecture (rule text: rules-architecture 17, 19–21 and rules-code-style Comments; this skill enforces, never redefines), skill://micro-architecture (file maps, auto-discovery, one-file-per-variant; its ui-components payload is enforced in part), skill://tdd (testing-rules fakes over mocks, enforced as S8), skill://write-tickets (file map + Evidence), skill://implement (`structure:` before DONE), skill://review-change (runs it in the fast tier), skill://init-profile (opt-in, `structure:` command)

# Structure checks

A rule the worker can skip is advice. This skill makes the structure rules
fail a build. Which engine depends on the project:

| Project | Engine | Carries |
|---|---|---|
| Kotlin / Android | Konsist tests (files, layers, Compose) plus detekt (functions, comments, imports) | S0–S8 |
| Web: SvelteKit, Svelte 5, TypeScript | ESLint (files, functions, comments, mocks) plus dependency-cruiser (layers) | S0–S3, S6 (in part), S7, S8 |

The value here is the rule set, the ratchet, and who may touch what. Rule
text, thresholds and fixes are in
[references/rules-structure.md](references/rules-structure.md) (the only place
the caps are written); the web configs, verified rules and probes are in
[references/web-engine.md](references/web-engine.md).

Provenance, Kotlin: Konsist docs checked 2026-11-04 on docs.konsist.lemonappdev.com;
Gradle `testImplementation("com.lemonappdev:konsist:<version>")` (0.15.1 in
the README at that date — pin whatever the project resolves). Three
constraints from those docs shape the design:

- **No baseline file** ("will be added in the future"). Retrofitting is
  granular scopes or `@Suppress` — so the allowlist below is ours, in the test.
- **`@Suppress("konsist.<test name>")` silences a declaration test**; it is
  the cheapest way for a worker to make a check green. Architecture
  assertions ignore it (remove files from scope instead). Rule S0 bans it.
- **An empty scope passes.** A misspelled module name verifies nothing; the
  `strict` assertion parameter fails on an empty declaration list. Use it.

Provenance, web: every tool in web-engine.md was installed and run in a
scratch lab on 2026-11-23; untested parts are marked `[unverified]` there.

## 1. Setup (HITL — the first time only)

1. `structure:` not yet in PROFILE.md → propose setup (it adds dev
   dependencies and config). Opt-in, one question; declined → record
   `structure: none` in PROFILE.md and stop.
2. Pick the engine from the build files: Gradle with Kotlin sources → Kotlin;
   `package.json` with SvelteKit or TypeScript → web; both → set up each.
   Web: pin TypeScript as web-engine.md says before anything else, since an
   unsupported TypeScript makes dependency-cruiser pass silently.
3. Generate the checks from
   [references/rules-structure.md](references/rules-structure.md) (Kotlin) or
   [references/web-engine.md](references/web-engine.md) (web). S0–S3, S7 and
   S8 are on by default; S4–S6 (Compose UI) are asked, and S6 also asks for
   the route-name suffixes. The caps in S2 may be lowered per project, never
   raised without a dated user ruling.
4. Ratchet, so the first run is not red and never gets worse:
   - A greenfield project starts with zero suppressions and no allowlist.
   - Kotlin, existing project: every current Konsist violator lands in
     `structure/allowlist.txt` — one project-relative path per line, comment
     with the rule id. The tests exclude allowlisted paths from their
     violations **and fail on any allowlist entry that no longer violates**.
     detekt adopts with `./gradlew detektBaseline`; the baseline only shrinks.
   - Web, existing project: `eslint --fix --suppress-all` once for each newly
     adopted rule writes `eslint-suppressions.json`. CI fails when it gains
     entries against `main` (growth check in web-engine.md).
   - The ratchet is for old code only; it never excuses new code.
5. Prove the checks can fail on every engine in use, then delete the probes.
   Kotlin: a two-type file, a narrating comment, a mockk import and an
   over-long function, each red with the file named. Web: the probe list in
   web-engine.md, then confirm no `missing-tsc-transpiler` in the output. A
   structure suite that was never seen red is not evidence.
6. Write the PROFILE.md `Testing style` line `structure: <exact command>` and
   confirm it runs at least one check:
   - Kotlin: the project's unit-test task filtered to the structure package,
     plus `detekt`.
   - Web: the project's lint script, e.g. `pnpm lint` (ESLint plus
     dependency-cruiser in one command).

## 2. Worker contract (implement briefs carry this as a Standards line)

- Run the `structure:` command before DONE; report `structure: <result>`.
- Red → **fix by splitting or moving code**, or by deleting the comment or
  the mock. Never suppress a structure rule, never extend a baseline or
  allowlist, never edit the protected files:
  - Kotlin: `structure/**`, `structure/allowlist.txt`, `detekt.yml`, the
    detekt baseline.
  - Web: `eslint.config.*`, `tools/eslint/**`, `.dependency-cruiser.*`,
    `eslint-suppressions.json`, the CI growth check.

  Needing a change is NEEDS_CONTEXT or a `Ruling:` the controller or user
  signs.
- A new file lands with its responsibility in the ticket's file map. The
  split is by responsibility, not by line count — a file shredded into
  fragments to dodge a cap (`utils2`, `part2`) is a worse failure than the one
  it hides (Goodhart): reviewers read the file map against the real files.
- Trimming comments never fixes size: comments are already banned (S7) and
  the count excludes them.

## 3. Review contract

`review-change` runs the `structure:` command itself in the fast tier. Red is
❌; not configured on a Kotlin or web diff is `cannot-verify`. A diff that
touches the protected files without a ledgered `Ruling:` is an Important
finding. Coverage row: `structure: <n> new/moved files, command exit <code>,
protected files untouched: yes/no`.

## 4. Limits

- Counts and shapes, cannot judge cohesion — the file map plus review do
  that. The Svelte component rules beyond S1, S2 block caps and `ui-leaf`
  are review work.
- Web engine pins: dependency-cruiser 18.9 and typescript-eslint 8.74 do not
  support TypeScript 7.0, so pin TypeScript 6 or the first supported 7.x;
  dependency-cruiser on an unsupported version skips every TS source and
  still exits green.
- A glob-based plugin registry (micro-architecture auto-discovery) has no
  edge for dependency-cruiser to see, and template nesting in `.svelte`
  markup is not measured.
- `eslint-plugin-boundaries` is optional editor feedback, never a second
  gate: two copies of one layer policy drift apart.
- Rules are the user's bar: raising or relaxing one needs a dated user ruling
  in `rules-structure.md`, never a per-ticket edit.

Konsist: github.com/LemonAppDev/konsist (Apache-2.0 — dependency, no code
vendored). Also detekt (Apache-2.0), ESLint (MIT), dependency-cruiser (MIT):
dependencies, no code vendored. Rule text sources: `design-architecture`
rules 17 and 19–21 and its Comments section; `tdd` testing-rules.
