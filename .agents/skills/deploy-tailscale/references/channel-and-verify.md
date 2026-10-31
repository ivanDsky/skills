# Channel and verify details

Read this when: the channel choice is not obvious, a `file cp` target fails
to resolve, or the device is unusual (tagged node, desktop receiver, no adb).
Everything below is grounded in the official docs listed in
[sources.md](sources.md).

## Taildrop (`tailscale file cp`)

- Usage: `tailscale file cp <files...> <target>:` — the trailing colon marks
  the target host. Flags: `--targets` (list valid targets), `--name=<name>`
  (rename on arrival; use for stdin), `--verbose`, `--update-interval=<time>`
  (progress-line repaint, default 250ms).
- Target resolution: machine name (MagicDNS) or Tailscale IP. If a name fails,
  run `tailscale file cp --targets` and copy the exact spelling from the list.
- Receiver behavior: on Android/iOS/desktop apps the file lands in the app's
  received-files area (Android: notification, then Downloads in the Files
  app). `tailscale file get <target-directory>` only runs where the CLI runs
  (desktop, server); flags: `--conflict=(skip|overwrite|rename)` (default
  skip), `--wait` (block until a file arrives), `--loop`.
- Limits: transfer only between your own personal devices; nodes you have
  tagged cannot send or receive Taildrop; both ends must run Tailscale. An
  interrupted transfer can usually resume for up to an hour — except when the
  receiver is macOS or iOS.
- Evidence recipe (Android test device, adb connected):
  1. `shasum -a 256 app/build/outputs/apk/debug/app-debug.apk`
  2. `tailscale file cp <apk> <device>: --verbose`
  3. `adb shell stat -c '%s' /sdcard/Download/app-debug.apk` — compare bytes
     with the local size; hash on-device with `adb shell sha256sum <path>`
     when the device image provides it. No adb → user confirms the size in
     Downloads; record both sizes in the ledger.

## Serve (`tailscale serve`)

- Directory mode: `tailscale serve <absolute-path-to-builds-dir>` — relative
  paths are not accepted for file/directory targets; the listing shows the
  APKs with the tailnet URL `https://<device>.<tailnet>.ts.net`.
- Useful flags: `--https=<port>` (default), `--http=<port>`, `--bg`
  (survive the terminal), `--set-path=<path>` (mount under a subpath),
  `--yes` (skip prompts). Subcommands: `tailscale serve status`,
  `tailscale serve reset`.
- The listener is tailnet-only. macOS App Store and Standalone variants
  cannot serve files or directories (app sandbox) — only reverse-proxy to
  local ports. On such hosts, serve a small local port or use Taildrop.
- Stop serving when done: Ctrl+C (foreground) or `tailscale serve reset`
  (after `--bg`). A forgotten serve keeps the build directory reachable by
  every tailnet device.
- Evidence recipe: `curl -fsSI <url>/<apk>.apk` → HTTP 200 and
  Content-Length equal to the local byte count; strongest form downloads and
  compares `shasum -a 256` output.

## Funnel (one-way door)

- `tailscale funnel` shares the same target types as serve but on the public
  internet; HTTPS is forced and only ports 443, 8443, 10000 are allowed.
- Requires funnel enabled in the tailnet policy; treat every funnel command
  as an exposure event: ask only when the user explicitly said funnel, and
  record the public URL and take-down plan (`funnel reset` / Ctrl+C) in the
  delivery summary.

## Choosing in one line

One device, one file, now → Taildrop. Many files, many variants, or the user
pulls later → serve. Public internet → funnel, explicit ask only.
