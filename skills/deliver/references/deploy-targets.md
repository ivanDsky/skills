# Deploy targets

One checklist per PROFILE.md deploy target. Read only the section matching
the target being deployed. Rule for all targets: deploy only what the build
produced, and stop rather than invent a missing config value (project id,
host, port) — ask or leave the target undeployed.

## local

- Command comes straight from the PROFILE.md `local:` entry. Run it as
  written; never guess a variant.
- Capture output to `.scratch/<slug>/deploy-local.log`.
- Evidence: the command output plus the URL or port the app serves on.

## firebase (web targets: hosting, functions, rules)

- Android app distribution lives in the dedicated `deploy-firebase` skill
  (test users, tester groups, APK/AAB) — this section is web hosting only.
- Requires the firebase CLI. Missing → stop and hand the user the pointer:
  `npm install -g firebase-tools`, then `firebase login`.
- From PROFILE.md `firebase:` entry: the project id.
- Select it (`firebase use <project-id>`), then deploy what the project
  uses — hosting always; functions, rules, or firestore only when the
  project configures them.
- Evidence: the Hosting URL from the deploy output.
- Note the hosting rules in the summary: public or authenticated.

## tailscale (web serving)

- APK/device sharing lives in the dedicated `deploy-tailscale` skill — this
  section serves a running web app over the tailnet only.
- Requires the tailscale CLI, installed and logged in (`tailscale status`
  answers). Missing → stop with the pointer: https://tailscale.com/download.
- From PROFILE.md `tailscale:` entry: the host, plus the app's local port.
- Tailnet-only by default: `tailscale serve <port>`. Public internet only
  when the ask says so: `tailscale funnel <port>`.
- Evidence: the serve or funnel URL from the CLI output.
- Funnel is a one-way door (public exposure) — default to serve.

## web-preview (tailnet-only build for the user to try)

- For a web app the user will look at on a phone or tablet. It never deploys
  publicly: no Cloudflare, funnel, tunnel, or `wrangler dev --remote|--tunnel`
  here. Going public needs the owner's explicit go (`deploy-cloudflare`).
- Build first with the project's build command (PROFILE.md or `package.json`);
  a failed build stops the target. Serve the build output, not the dev server.
- Serve it as a long-lived service, never a one-shot command that dies with the
  turn: the harness's service tool (omp: bash with `name` + `ready` set to the
  port) or `nohup python3 -m http.server <port> --bind 0.0.0.0 --directory
  <build dir> >/dev/null 2>&1 &` for a static build. An app with server routes
  (a Worker, `/api`) needs its own preview command bound to all interfaces
  (`pnpm preview --host 0.0.0.0 --port <port>`, or `wrangler dev --ip 0.0.0.0
  --port <port>`); use the PROFILE.md entry when it names one. A listener
  already on that port for that directory
  (`lsof -nP -iTCP:<port> -sTCP:LISTEN`) is reused.
- URL: tailnet first (`tailscale ip -4`, or the PROFILE.md address), LAN second
  (`ipconfig getifaddr en0`). Never localhost or a file path.
- Check the tailnet URL before sending it, with retries: `for i in 1 2 3 4 5;
  do curl -fsS -o /dev/null -m 5 <url> && break; sleep 2; done`. A fresh server
  can stall non-loopback connects for a few seconds. Still failing → restart the
  server and check again; an unchecked link is never sent.
- Evidence: the build output, the checked URL and the curl result. Same serve
  rule as `prototype` § 3.
