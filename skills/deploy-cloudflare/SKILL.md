---
name: deploy-cloudflare
description: Builds, tests locally and deploys a SvelteKit app as one Cloudflare Worker with static assets, D1, a Rate Limiting binding and Turnstile, using Wrangler, and never goes public without an explicit go. Use when touching wrangler.jsonc, D1 migrations, rate limits, Turnstile, Worker secrets or `wrangler` commands, or when asked to deploy or go public on Cloudflare.
interaction: hitl
requires: [wrangler]
---

> **TL;DR** Local first, then a tailnet-only preview, then ask. No Cloudflare resource is created, changed, read or deployed without the owner's explicit go in this same session.
> **Related**: skill://wrangler, skill://workers-best-practices, skill://frameworks-on-cloudflare (generic Cloudflare detail; do not duplicate), skill://deliver (`web-preview`), skill://deploy-tailscale, skill://svelte-kit3

# Deploy a SvelteKit app to Cloudflare

<critical>
HARD RULE. A public deploy needs the owner's explicit go, given in this session. An older go, a PROFILE line or a ticket does not count. Until then the app is served on the tailnet only (`skill://deliver` kind `web-preview`). Use Wrangler and `wrangler.jsonc` (what adapter-cloudflare reads), not the new `cf` CLI.
</critical>

Project specifics (Worker and database names, D1 jurisdiction, limits and budgets, what the owner approved) come from `PROFILE.md` and the project's ADRs, never from this skill.

Commands that need the go: every `wrangler` command without `--local` or `--dry-run` that touches the account (`deploy`, `preview`, `versions upload|deploy`, `secret put|delete`, `rollback`, `delete`, `triggers deploy`, `d1 create`, `d1 execute|migrations apply|export --remote`, `tail`, `login`). `tail` and remote D1 reads touch user data, so they need it too. Local runs and `--dry-run` do not.

## 1. Read the contract

1. Read `PROFILE.md` (Consent ledger, Deploy targets), the ADRs and spec sections on hosting and abuse limits, and `package.json`. Done when: you know the Worker name, the D1 name and jurisdiction, and the numbers (rate limits, any write breaker or kill switch).
2. Read the installed `@sveltejs/adapter-cloudflare` `peerDependencies.wrangler` and install a wrangler that satisfies it. The Kit docs state `^4.67.0`; adapter 9.0.0 itself asks for `^4.162.0`, and the package is the source of truth.

## 2. Configure

3. Read `references/wrangler-d1-ratelimit-turnstile.md`, then write `wrangler.jsonc`: `name`, `compatibility_date` (the day you create it), `assets` and the bindings. Done when: `main` is absent (adapter 9.0.0 sets the Worker entry itself and errors if `main` points at `.svelte-kit/cloudflare`) and `pages_build_output_dir` is absent.
4. Secrets only in `.dev.vars` (gitignored) locally and `wrangler secret put` in production. Never in `wrangler.jsonc`, never in a commit.
5. Static assets answer before the Worker (`run_worker_first` defaults to false), so a static file shadows a route of the same path, and `/x.html` redirects to `/x` with a 307. `_headers` and `_redirects` affect static responses only.

## 3. Local first

6. Build, run `wrangler d1 migrations apply <DB> --local`, then `wrangler dev` and exercise each endpoint with curl: normal, oversize, malformed, over the rate limit, and any kill switch or breaker the spec defines (it must return its documented response and write nothing). Use Turnstile's dummy keys, never the real secret (see the reference). Done when: every case behaves as the spec says against the local D1.
7. Always pass `--local` or `--remote` to `d1` commands; without `--local` they hit the remote database.
8. Run `wrangler deploy --dry-run` to confirm the bundle and bindings. It uploads nothing.

## 4. Tailnet-only preview

9. Serve the build as `skill://deliver` kind `web-preview` and send the tailnet URL. Done when: the URL answered `curl -fsS` with retries from the tailnet address.

## 5. The go gate

10. Ask the owner for the go and show: the Worker name, the `*.workers.dev` URL it will have, the `d1 create ... --jurisdiction=<value from the project's decision>` command, which commands touch the account, and any open rate-limit decision (reference § Rate limit period). Done when: the owner's explicit go is in this session. No go means stop and say so.

## 6. Deploy (only after the go)

11. Owner runs `wrangler login` (browser). Then once: `npx wrangler d1 create <DB> --jurisdiction=<value>` (the jurisdiction cannot change later); write the returned `database_id` into `wrangler.jsonc`. Never let `wrangler deploy` auto-provision the database: with no `database_id` it creates one with no jurisdiction.
12. `npx wrangler d1 migrations apply <DB> --remote`, `npx wrangler secret put TURNSTILE_SECRET`, build, `npx wrangler deploy`. A first-deploy `Types file not found at worker-configuration.d.ts` means run `npx wrangler types` once and redeploy.
13. Smoke-test the deployed URL (a page, a valid and an invalid write request) and check the D1 row count with `d1 execute --remote`. Done when: the pages load, a valid request stores one row, and an invalid one is rejected. Then update the `PROFILE.md` deploy target note, and report the URL and the version id.
14. Rollback: `npx wrangler rollback`. A kill-switch var in `vars` stops writes without touching pages: change it, then deploy.

## Hold the line

- D1 free plan, per account: 5M rows read and 100k rows written per day (reset 00:00 UTC); each index adds one written row per insert. Hitting it fails queries for every database on the account, so any write breaker must trip well below it.
- Durable Objects and Workflows do not work with adapter-cloudflare.
- Do not add a public read endpoint to look at data; read it with `wrangler d1 execute --remote` after the go.
- This skill covers adapter-cloudflare on Workers static assets; `adapter-cloudflare-workers` and Pages are different setups. Funnel, a custom domain or a `wrangler preview` branch also need the go.

Verified against developers.cloudflare.com (Workers static assets, D1, Rate Limiting, Turnstile, Wrangler) and https://svelte.dev/docs/kit/adapter-cloudflare, plus the adapter-cloudflare 9.0.0 package source. Fresh skill; builds on `skill://wrangler` from cloudflare/skills.
