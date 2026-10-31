# Sources

Official Tailscale documentation fetched 2026-10-30 to ground every command
and flag in this skill. The ticket's suggested URLs (kb/1084 "file-share",
kb/1247 "tailscale-serve") redirect elsewhere — kb/1084 is "Share your
machines with other users"; the canonical pages are listed here.

- Tailscale CLI command reference (`file cp/get`, `status` flags and output
  columns): https://tailscale.com/kb/1080/cli
- `tailscale serve` command reference (file/directory mode, `--https`/`--http`,
  `--bg`, `--set-path`, `status`/`reset`, macOS sandbox caveat):
  https://tailscale.com/docs/reference/tailscale-cli/serve
- `tailscale funnel` command reference (public exposure, ports 443/8443/10000):
  https://tailscale.com/docs/reference/tailscale-cli/funnel
- Taildrop feature page (own-devices limit, tagged-node restriction, Android
  receive = notification → Downloads, resume behavior):
  https://tailscale.com/docs/features/taildrop
- Tailscale Funnel feature page (funnel node attribute in the tailnet policy
  file required, MagicDNS + HTTPS enabled, beta, ports 443/8443/10000):
  https://tailscale.com/docs/features/tailscale-funnel
- CLI source confirming `file cp <files...> <target>:` usage and `file get`
  flags (`--wait`, `--loop`, `--conflict`): https://github.com/tailscale/tailscale/blob/main/cmd/tailscale/cli/file.go

Not documented anywhere official: a `tailscale file copy` long form. The
skill uses `cp` and defers variants to `tailscale file --help` at first run.
