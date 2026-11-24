# Wrangler, D1, Rate Limiting, Turnstile (SvelteKit on one Worker)

Sources (checked 2026-11-23): developers.cloudflare.com/workers/wrangler/configuration, /d1/wrangler-commands, /d1/best-practices/local-development, /d1/platform/pricing, /workers/runtime-apis/bindings/rate-limit, /turnstile/get-started/server-side-validation, /turnstile/troubleshooting/testing, /workers/configuration/secrets, https://svelte.dev/docs/kit/adapter-cloudflare, and the `@sveltejs/adapter-cloudflare` 9.0.0 package source. Names below (`DB`, `RL_BEACON`, `RL_FORM`, `my-app`) and the limits are placeholders; keep what the code already uses and take the numbers from the project's spec.

## wrangler.jsonc

```jsonc
{
  "name": "my-app",
  "compatibility_date": "2026-11-23",
  "observability": { "enabled": true },
  "assets": { "binding": "ASSETS", "directory": "./public" },
  "vars": { "KILL": "0" },
  "d1_databases": [
    { "binding": "DB", "database_name": "my-app", "migrations_dir": "migrations" }
  ],
  "ratelimits": [
    { "name": "RL_BEACON", "namespace_id": "1001", "simple": { "limit": 30, "period": 60 } },
    { "name": "RL_FORM", "namespace_id": "1002", "simple": { "limit": 3, "period": 60 } }
  ]
}
```

- No `main`: adapter-cloudflare 9.0.0 builds with the Cloudflare Vite plugin, writes the deploy config to `.svelte-kit/cloudflare/worker/wrangler.json` and points `.wrangler/deploy/config.json` at it. `wrangler deploy` and `wrangler dev` follow that redirect, so build first. `assets.directory` is overwritten by the adapter; `assets.binding` defaults to `ASSETS`.
- `compatibility_date` from 2026-08-04 on includes `node:async_hooks`; an older date or missing flag makes the adapter add `nodejs_als` itself.
- No `pages_build_output_dir`, no adapter `routes` option, no `_routes.json`.
- `run_worker_first` defaults to false: a file in `static/` beats a route of the same path. `html_handling` defaults to `auto-trailing-slash`, so `/x.html` returns 307 to `/x`. `.assetsignore` uses `.gitignore` syntax; the adapter appends to it.
- Types: `npx wrangler types` writes `worker-configuration.d.ts` (commit it). `vars` get literal types (`KILL: "0"`), so `env.KILL === '1'` fails to type-check; run `wrangler types --strict-vars=false` or compare as `string`. Rerun after every config change; `wrangler types --check` fails stale types in CI.
- Reading env in Kit: secrets and vars through `$app/env/private` (declare them in `src/env.ts`); bindings (`DB`, `RL_*`) through `import { env } from 'cloudflare:workers'`.
- Do not omit `database_id` before a deploy. With no ID, Wrangler's automatic provisioning creates the database at `wrangler deploy` without a jurisdiction, and the jurisdiction cannot be changed later. Create it yourself (below). Before that, a `d1_databases` entry with no `database_id` is fine for local-only work (`d1 migrations apply <DB> --local` was run against wrangler 4.167.0 and works).

## D1

```bash
npx wrangler d1 create my-app --jurisdiction=eu     # once, after the go; the jurisdiction value comes from the project's decision; --update-config writes the id into the config
npx wrangler d1 migrations create my-app <message>   # next numbered SQL file in migrations/
npx wrangler d1 migrations list  my-app --local
npx wrangler d1 migrations apply my-app --local      # also in CI and tests
npx wrangler d1 migrations apply my-app --remote     # after the go
npx wrangler d1 execute my-app --remote --command "SELECT COUNT(*) FROM <table>"
```

- Jurisdictions: `eu`, `fedramp`, `us`. A jurisdiction makes the location hint irrelevant.
- Always pass `--local` or `--remote`. The docs: without `--local` a command runs against the remote database. Local state persists between `wrangler dev` runs in `.wrangler/state` (`--persist-to <dir>` moves it).
- Free plan, per account: 5M rows read/day, 100k rows written/day, reset 00:00 UTC, queries fail once hit. Each index adds one written row per insert, so a write breaker (if the project has one) must trip well below the cap. 500 MB per database, 7-day Time Travel, 50 queries per Worker invocation. Batch writes with `DB.batch([...])`.
- `wrangler d1 export my-app --remote --output backup.sql` before any destructive migration (needs the go).

## Rate Limiting binding

```ts
import { env } from 'cloudflare:workers';
const { success } = await env.RL_BEACON.limit({ key: sid });   // key: any string, e.g. a session id; success false => 429
```

- `period` is 10 or 60 seconds only; `namespace_id` is a string integer, unique per account; Wrangler ≥ 4.36.0.
- Counts are per Cloudflare location and eventually consistent, so a burst can exceed the limit. Cloudflare advises against IP keys (shared NATs) and says strict limits need Durable Objects, which adapter-cloudflare does not support.
- Local `wrangler dev` runs the binding with the same config.

### Rate limit period (a limit longer than 60 s)

The binding's `period` is 10 or 60 seconds, so a spec limit such as "3 per hour per IP" cannot be expressed with it alone. When the project's limit is longer than 60 s, options to put to the owner:
1. A binding burst guard (for example 3 per 60 s) plus a D1-backed hourly cap keyed by a session id. This stores no IP.
2. A D1 hourly counter keyed by a salted IP hash: a limit per IP, but it stores IP-derived data, which conflicts with any "no IP stored" rule in the spec or ADRs.
Do not pick silently. Record the answer in the spec and in the reply to the owner.

## Turnstile

Client: the widget, on the protected form submit only; it posts the token in the form field `cf-turnstile-response`. Server (in the form's endpoint):

```ts
const res = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
  method: 'POST',
  body: new URLSearchParams({ secret: TURNSTILE_SECRET, response: token, idempotency_key: crypto.randomUUID() })
});
const verified = (await res.json<{ success: boolean }>()).success;   // success false: reject
```

- A token is valid 300 s and single-use (`timeout-or-duplicate`). What to do with a missing token (the widget could not load) is a project decision in the spec, for example storing the row flagged unverified; a present but failing token is rejected.
- Dummy keys for local and tests. Sitekeys: `1x00000000000000000000AA` always passes, `2x00000000000000000000AB` always blocks, `3x00000000000000000000FF` forces an interactive challenge. Secrets: `1x0000000000000000000000000000000AA` passes, `2x0000000000000000000000000000000AA` fails, `3x0000000000000000000000000000000AA` reports the token already spent. Dummy token: `XXXX.DUMMY.TOKEN.XXXX`. Test keys reject real tokens and real keys reject the dummy token.
- The real sitekey is public (`public: true` in `src/env.ts`); the real secret is only a Worker secret.

## Secrets and vars

- Local: `.dev.vars` (or `.env`, not both), gitignored. Per environment: `.dev.vars.<env>`.
- Production: `npx wrangler secret put TURNSTILE_SECRET` deploys a new version immediately (after the go); `wrangler versions secret put` is the gradual form. `secrets.required` in the config fails a deploy that lacks one.
- Vars such as `KILL` live in `wrangler.jsonc` and need a deploy to change.

## Other gotchas

- `_headers`/`_redirects` live in the project root (the adapter errors if they sit in `static/`) and affect static responses only; set headers for dynamic responses in `handle` or the endpoint.
- Analytics beacons must be `text/plain`: Kit's CSRF check rejects a form-type POST without an Origin header.
- `fs` is unavailable in the Worker; use `read` from `$app/server` or prerender.
- `wrangler deploy` can fail the first time with `✘ [ERROR] Types file not found at worker-configuration.d.ts.`: run `npx wrangler types`.
