---
name: work-tickets
description: >-
  Worker session for the shared backlog: atomically claim a pack of up to 5
  ready tickets matching a filter (area, type, epic, ids or words), implement
  each as its own small PR merged dark via implement and ship-to-trunk, move
  each to done or needs-check, then claim the next pack until nothing matches.
  Never asks the user; questions go back to the backlog. Use when the user says
  "pick up tickets", "work the leaderboard bugs", "take #42", "grab what's
  ready in sync", or starts a worktree to drain backlog tickets.
interaction: afk
requires: []
---

> **TL;DR** Claims packs of up to 5 matching ready tickets atomically, lands each as its own dark PR through implement and ship-to-trunk, and never leaves a ticket claimed or asks the user.
> **Related**: skill://file-tickets (upstream: files the tickets, runs the check batch), skill://implement (the engine: workers, briefs, merge lane), skill://ship-to-trunk (one PR per ticket, merged dark), skill://diagnose-bug (evidence ladder for bug tickets), skill://review-change (fast tier per ticket)

# Work tickets

You drain the shared backlog in this worktree. Other sessions do the same in
theirs, so every ticket you touch goes through the claim script. Tickets land
one at a time: the release cut never waits for you.

```
B=~/.agents/skills/work-tickets/scripts/backlog.py   # in this repo: skills/work-tickets/scripts/
ME=wt-$(basename "$(git rev-parse --show-toplevel)")
```

The backlog contract (backends, fields, states, commands):
[backlog.md](references/backlog.md).

## 1. Resolve the filter

The ask names an area, a type, an epic, ids, or plain words.
- Area, type, epic, ids → pass them to `claim` as `--area`, `--type`,
  `--epic`, `--ids`.
- Words ("the rotation bug") → `python3 $B list --frontier --search "…"`,
  then claim the matching ids. No match → `list --all --search` and report
  what state the ticket is in, for example `needs-info`, or claimed by
  another session.
- Nothing named → the whole frontier, highest priority first.

Before claiming anything, run `python3 $B list --state claimed`. Tickets still
claimed as `$ME` are from an interrupted run: resume them first (the ledger
and `git log` show how far each got).

## 2. Claim a pack

`python3 $B claim --as $ME --max 5 <filter>`. Exit 3 means nothing is left:
go to § 5. The claim is atomic between sessions on this machine. Never edit a
ticket's state by hand to claim it.

## 3. Land each ticket

Run `implement` on the pack with ledger `.scratch/backlog-$ME/ledger.md`.
Delivery is always one ticket = one PR off fresh `origin/main`, whatever the
run default: merged dark behind its flag, or live when it is a pure bug fix.
Who merges is `ship-to-trunk` § Merge authority, never a rule of this skill:
with the consent line, the agent merges on a green gate plus a clean fast
review. The gate is the required PR check, or under `pr-check: none` the
local suite on the branch rebased onto fresh `origin/main`. Only a missing
consent line, a live change (invariant 7) or a flip PR waits for the user.

Per ticket, before dispatch, write the brief from the ticket
([pack-loop.md](references/pack-loop.md) § Brief):
- the DoD and its evidence command;
- the file scope;
- the tier and effort;
- the flag: a user-visible change ships behind a release flag, off in
  release.

A `bug` ticket starts with `diagnose-bug`'s evidence ladder in the worker,
minus its question batch: the brief's repro steps stand in for the answers.

Tickets in one pack run in parallel when their file scopes are disjoint
(`implement` § 2).

## 4. Close every claim

No ticket stays `claimed` once its outcome is known.

| Outcome | Command |
|---|---|
| merged, logic proven by evidence | `set ID --state done --note "PR #N merged @ <sha>; <evidence>"` |
| merged, `hands-on` | `set ID --state needs-check --note "PR #N merged @ <sha>; flag: <Key\|none>; verify: <one line>"` |
| PR waits for the user (no consent line, or a live change) | `set ID --state needs-check --note "PR #N awaits your merge: <why>"` |
| worker NEEDS_CONTEXT that only the user can answer | `set ID --state needs-info --note "<the question, with a recommended answer>"` |
| needs credentials, a device or a product decision | `set ID --state ready-for-human --note "<what and why>"` |
| BLOCKED, failed twice, or out of time | `unclaim ID --note "<what was tried, where it stopped>"` |

GitHub backend: the PR body carries `Refs #N`. The ticket closes through
`set`, never through the PR keyword, because a hands-on ticket stays open in
`needs-check`.

## 5. Next pack, then stop

When every ticket of the pack has an outcome, claim again with the same
filter (§ 2). Exit 3 → stop and post one digest: per ticket its id, title,
outcome, PR, plus the `needs-check` count, so the user knows a check batch
is waiting in the feedback session (`file-tickets` § 3).

## Rules

- Never call the ask tool. Questions become `needs-info` notes on the ticket;
  the feedback session asks them. Stop the run only for an irreversible or
  destructive operation (`implement` § 4).
- Never claim beyond the filter, never steal another session's claim, and
  never work a ticket you did not claim.
- A ticket that turns out to be feature-sized (needs a spec): `set
  ready-for-human` with "feature: needs the /start chain", then move on.
- New problems found while working become tickets (`new`, filed the
  `file-tickets` way), never scope creep in the current PR.

Fresh skill for this repo's shared backlog; the pick-up loop follows
mattpocock's AFK agent loop (`ready-for-agent` lane), no text adapted.
