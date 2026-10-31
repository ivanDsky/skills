---
name: deploy-tailscale
description: >-
  Ship the built APK to the user's registered tailnet test device — resolve the
  device once, persist the name and IP mapping in PROFILE.md — over Taildrop
  (`tailscale file cp`) or a tailnet-only `tailscale serve` link, verified by
  size and checksum evidence; `funnel` only on explicit ask. Use when deliver
  dispatches on the PROFILE.md tailscale target, or the user asks to send or
  share an APK or build to their device over Tailscale.
interaction: afk
requires: [tailscale]
---

> **TL;DR** Ships the built APK to the registered tailnet device via Taildrop or serve, checksum-verified; fires on the PROFILE.md tailscale target.
> **Related**: skill://deliver (dispatches targets), skill://deploy-firebase (sibling target)

# Deploy Tailscale

Deliver built first — never rebuild here; the APK path comes from the build
step and carries the canonical name
`<app_name>-<sem_ver>-<debug|release>.apk` (deliver renames it; Gradle's
`app-<variant>.apk` never reaches this skill). The name is what the device's
Downloads list shows — no version ambiguity between installs.
Tailnet-only by default: this skill never exposes anything to the public
internet unless the user explicitly asks for funnel.

## 1. Preconditions

1. `tailscale status` answers → installed and logged in. Command missing or
   errors → stop and hand the pointer: https://tailscale.com/download. Never
   improvise another transfer path or swap in another target.
2. The artifact exists and is fresh from the green build. Missing → stop and
   return to deliver; do not rebuild.

## 2. Resolve the device (persist once)

1. PROFILE.md `tailscale:` entry already has a `device:` line → trust it and
   skip discovery, but verify it still answers: `tailscale status | grep
   <name>`. Gone or renamed → rediscover and rewrite the line.
2. No `device:` line → run `tailscale status`. Columns: Tailscale IP, machine
   name, owner, OS, connection state. Pick the user's test device: Android OS,
   owner is this tailnet user. Exactly one candidate → take it. Two or more →
   one question to the user, then stop asking.
3. Persist immediately after first discovery, under the `tailscale:` line:

   ```markdown
   - tailscale: <host>
     - device: <machine-name> @ <tailscale-ip>  # verified YYYY-MM-DD
   ```

   Future runs skip discovery and only grep. Address forms: machine name
   (MagicDNS) or `100.x.y.z` IP; `tailscale file cp --targets` lists valid
   copy targets when in doubt.

## 3. Share the APK — pick one channel

1. **Taildrop push — the default.** `tailscale file cp <apk> <device>:`. Best
   for one device, one artifact, fire-and-forget. On Android the file arrives
   as a notification in Downloads — the phone runs no CLI, so `tailscale file
   get` never applies to it; `file get` is for CLI receivers (desktop,
   server). Taildrop limits: own personal devices only, tagged nodes cannot
   receive, both ends need Tailscale running. The long form `tailscale file
   copy` is not in the docs — use `cp`, and `tailscale file --help` at first
   run if a variant is wanted.
2. **Serve pull — the alternative.** `tailscale serve
   <absolute-path-to-builds-dir>` renders a directory listing over HTTPS on
   the tailnet (`--https` is the default listener); send the
   `https://<device>.<tailnet>.ts.net` URL. Best for several variants to pick
   from, Taildrop unavailable, or the device pulls later. Foreground serving
   ends on Ctrl+C; `--bg` keeps it up; `tailscale serve status` inspects,
   `tailscale serve reset` clears. macOS App Store/Standalone clients cannot
   serve files or directories (sandbox) — only ports; fall back to Taildrop.
3. **Funnel — one-way door.** `tailscale funnel` exposes the URL to the whole
   internet (allowed ports: 443, 8443, 10000). Only on an explicit user ask,
   and name the exposure in the delivery summary. Never self-initiate.
4. Conflict rule: one named device → Taildrop; anything the user will fetch
   or that has multiple files → serve.

## 4. Evidence — deployed means verified

1. Taildrop: cp's confirmation output plus local `shasum -a 256 <apk>`; on
   the device, size from `adb shell stat` when adb is connected, otherwise
   the user's confirmation from Downloads. Record both sizes at minimum.
2. Serve: `curl -fsSI <url>` must return 200 with a Content-Length matching
   the local file, or download and compare `shasum -a 256` hashes.
3. Append the evidence to `.scratch/<slug>/ledger.md` so deliver can close
   the ticket with it. No evidence → not deployed; say so in the summary and
   leave the ticket open.

Read [references/channel-and-verify.md](references/channel-and-verify.md)
when choosing between channels on an edge case, when a `file cp` target fails
to resolve, or when building the verify command for an odd device. Official
doc URLs live in [references/sources.md](references/sources.md) — check there
before inventing any flag.

Grounded in official Tailscale documentation and CLI reference; see
[references/sources.md](references/sources.md) for every cited URL.
