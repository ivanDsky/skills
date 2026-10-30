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

## firebase

- Requires the firebase CLI. Missing → stop and hand the user the pointer:
  `npm install -g firebase-tools`, then `firebase login`.
- From PROFILE.md `firebase:` entry: the project id.
- Select it (`firebase use <project-id>`), then deploy what the project
  uses — hosting always; functions, rules, or firestore only when the
  project configures them.
- Evidence: the Hosting URL from the deploy output.
- Note the hosting rules in the summary: public or authenticated.

## tailscale

- Requires the tailscale CLI, installed and logged in (`tailscale status`
  answers). Missing → stop with the pointer: https://tailscale.com/download.
- From PROFILE.md `tailscale:` entry: the host, plus the app's local port.
- Tailnet-only by default: `tailscale serve <port>`. Public internet only
  when the ask says so: `tailscale funnel <port>`.
- Evidence: the serve or funnel URL from the CLI output.
- Funnel is a one-way door (public exposure) — default to serve.
