---
name: web-env
description: >-
  Web/Node environment bootstrap — one pass at session start: runtime and
  package-manager resolution (node, pnpm/npm/bun), env files, port
  conflicts, lockfile discipline, worktree-aware git, dev-server vs build
  triage (stale cache → clean), browser/devtools evidence tools. Use when
  a web command fails with "command not found" or version mismatch, a
  dev server won't start or serves stale content, installs behave oddly,
  or git misbehaves inside a worktree. The web twin of android-env.
interaction: afk
---

> **TL;DR** Run the environment checklist before the first web command of any session — runtime, package manager, env files, ports — and never re-derive fixes mid-session; a dev-server failure that survives a clean reinstall is real, everything else is stale state.
> **Related**: skill://android-env (the Android twin — same triage philosophy), skill://tdd (`references/web-testing.md` — the evidence ladder), skill://deliver (deploy targets), skill://android-cli (the Android routing analog)

# Web environment — derive once per session, not once per command

Project-specific outcomes go in PROFILE.md `## Environment facts`; record
them instead of rediscovering.

## 1. Runtime and package manager

- Resolve versions from the repo first: `package.json` `engines`,
  `".nvmrc"`/`.node-version`, `packageManager` field, lockfile identity
  (`pnpm-lock.yaml` / `package-lock.json` / `bun.lockb` — the lockfile
  names the package manager; never run a different one against a foreign
  lockfile).
- Version mismatch → use the repo's pinned manager (`corepack`/
  `nvm use`), never "upgrade" the repo's tooling to make a command pass.

## 2. Env files

- `.env` / `.env.local` missing → copy `.env.example` and ask for secrets;
  never invent values for API keys, and never commit env files.
- Browser code only sees variables prefixed per framework convention
  (`VITE_`, `NEXT_PUBLIC_`) — a "missing env var" in the browser with a
  present server-side value is almost always a prefix problem.

## 3. Ports and dev servers

- Dev server "address in use" → find the holder (`lsof -i :<port>`), kill
  only processes you started; prefer the project's configured port from
  its config over forcing flags.
- Multiple worktrees = port collisions by design — offset per worktree or
  note the mapping in PROFILE facts.

## 4. Lockfile discipline

- One dependency change = one lockfile diff, reviewed like code. Never
  hand-edit a lockfile; regenerate via the package manager's install after
  editing `package.json`. Big unexpected lockfile churn in a diff is a
  finding, not noise.

## 5. Worktree git (same trap as Android)

In a worktree `.git` is a **file**. Tools assuming a directory (some
`gh` operations, hooks, naive path joins) fail confusingly. Check
`cat .git` first; run the command from the main checkout if the tool can't
handle worktrees; never "fix" by deleting `.git`.

## 6. Dev-server triage — before believing any red

Order, cheapest first:

1. **Stale state** — stale HMR, cached chunks, phantom module errors,
   "file not found" for files that exist: restart the dev server with a
   clean cache (`vite --force`, delete `node_modules/.vite`,
   `.next/cache`, etc.) **before** reading the error as a code problem.
2. **Dependency weirdness** — "works on my machine" symptoms:
   clean reinstall (`rm -rf node_modules && <manager> install`) once;
   if it recurs, it's real — diagnose.
3. **Then** it's a real failure — read the actual error (browser console +
   server terminal, both), diagnose normally.

Build churn discipline: typecheck-only loops (`tsc --noEmit`) between
edits are cheap; full production builds are not — batch changes first.
For UI verification between builds use the ladder
(`tdd/references/web-testing.md`): component tests and rendered captures,
not manual browser clicking.

## 7. Browser evidence tools

- Programmatic capture over manual clicking: Playwright (`page.screenshot`,
  trace viewer) gives reproducible evidence files that feed `review-site`.
- The browser console and network tab are evidence — ask the user for a
  console error text or HAR export rather than guessing; `diagnose-bug`'s
  user-time-last ladder applies on web too.
