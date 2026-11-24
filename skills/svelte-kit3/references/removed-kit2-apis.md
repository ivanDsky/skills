# Kit 2 habits that break in SvelteKit 3

Source: https://svelte.dev/docs/kit/llms.txt § Migrating to SvelteKit v3 (checked 2026-11-23). Auto-migrate an old project with `npx sv migrate sveltekit-3`.

Minimums: Node 22.17, TypeScript 6, Svelte 5.57.1, Vite 8.0.12, `@sveltejs/vite-plugin-svelte` 7. With `adapter-cloudflare`: wrangler `^4.67.0`.

## Catch them in a diff

```bash
rg -n '\$app/stores|\$app/environment|\$service-worker|\$lib|platform\.(env|ctx|cf|caches)|svelte\.config|\b(pushState|replaceState|invalidateAll|handleValidationError|checkOrigin|resolveRoute)\b|import \{[^}]*\b(json|text)\b[^}]*\} from .@sveltejs/kit.' src vite.config.ts package.json
```

## Config and aliases

| Kit 2 habit | Kit 3 |
|---|---|
| `svelte.config.js` with `kit: {...}` | `sveltekit({ adapter, compilerOptions, ... })` in `vite.config.ts`; options are top-level |
| `$lib/foo` | `#lib/foo.ts` (explicit extension), from `"imports": { "#lib": "./src/lib/index.js", "#lib/*": "./src/lib/*" }` in `package.json`; `files.lib` is gone |
| tsconfig extends `./.svelte-kit/tsconfig.json` | extends `$app/tsconfig` and sets its own `include`/`exclude` |
| `csrf.checkOrigin: false` | removed; CSRF is always on; allow hosts with `csrf.trustedOrigins`; cross-origin mutating requests need a `Content-Type` |
| `prerender.origin` | `paths.origin` |
| `vitePlugin`, `preloadStrategy`, `experimental.handleRenderingErrors`, `experimental.instrumentation` | removed; pass vite-plugin-svelte options to `sveltekit()` directly; instrumentation is automatic when `src/instrumentation.server.js` exists; `experimental.tracing` is now top-level `tracing` |
| `src/params/*.js` matcher files | one `src/params.ts` using `defineParams` from `@sveltejs/kit/params` |

## Modules

| Kit 2 habit | Kit 3 |
|---|---|
| `import { page } from '$app/stores'` and `$page` | `import { page, navigating, updated } from '$app/state'`; read `page.url`, no `$` prefix; `page.url` is readonly |
| `$app/environment` | `$app/env` (`browser`, `building`, `dev`, `version`) |
| `$service-worker` | `version` from `$app/env`; `assets`, `immutable`, `prerendered` from `$app/manifest`; `resolved` from `$app/paths`; typed worker context in `$app/service-worker` |
| `base`, `assets`, `resolveRoute` from `$app/paths` | `resolve('blog/hello')` and `asset('foo.png')`; no leading `/` on paths; only route ids such as `'/blog/[slug]'` start with `/` |
| `pushState` / `replaceState` | `goto(url, { shallow: true, state, replace })` |
| `invalidateAll()` | `refreshAll()` (keeps `page.state`) |
| `goto` `keepFocus` + `noScroll`, `replaceState` | `reset: false`, `replace` |
| `$env/static/*`, `$env/dynamic/*` (deprecated, removed in Kit 4) | `src/env.ts` with `defineEnvVars` from `@sveltejs/kit/env`, read via `$app/env/private` and `$app/env/public` |
| `json(data)`, `text(s)` helpers | `Response.json(data)`, `new Response(s)` |
| `error(404, { message, code })` | `error(404, 'message', { code })`: second argument is always a string |
| `handleValidationError` | removed; `handleError` gets `kind: 'validation'` |
| `Handle` and other hook types from `@sveltejs/kit` | `@sveltejs/kit/hooks` |
| `redirect(307, 'https://other.site')` | needs `{ external: true }` (or an origin array) |
| `data-sveltekit-preload-data="off"` | `="false"` |

## Behaviour changes

- `handleError` now receives every error, including expected `error()` ones.
- A `204` from a `+server` handler has no body; do not parse it.
- `goto()` rejects for URLs that match no route; external URLs use `window.location.href`.
- `use:enhance` form actions use the status passed to `fail()`.
- A link to the current page triggers `refreshAll()`.
- `version.pollInterval` defaults to one hour, so `updated.current` flips on its own.

## Server-only and env

- A module is server-only when a filename segment is `server` (`stuff.server.ts`, `server.ts`) or it sits in any `server` directory except under `src/routes` and `static`. Importing it from browser code fails the build.
- `$app/env/private` cannot be imported by browser code; mark browser-safe variables `public: true` in `src/env.ts`.
- Remote functions are experimental: they need `experimental.remoteFunctions` plus `compilerOptions.experimental.async`, and a `remote` filename segment. Do not use them unless the ADRs say so.

## adapter-cloudflare

- `platform.env` and `platform.ctx` are gone: `import { env, waitUntil } from 'cloudflare:workers'`. `cf` is `request.cf`; `caches` is a global.
- Run `wrangler types` to type bindings. `fs` does not exist in a Worker: use `read` from `$app/server` or prerender.
- `adapter-cloudflare-workers` (Workers Sites) is deprecated. Deploy details: skill://deploy-cloudflare.
