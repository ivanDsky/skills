# The shared backlog

Every ticket lives in one **backlog** per repo, shared by every worktree and
session. A feedback session files tickets, worker sessions claim them, and
the feature chain (`write-tickets` → `implement`) publishes and claims through
the same backlog. Nothing ticket-shaped lives in one worktree's `.scratch/`:
`.scratch/<slug>/` keeps a run's spec, ledger, briefs and reports, not its
tickets.

All reads and writes go through one script, so both backends behave the same:

```
B=~/.agents/skills/work-tickets/scripts/backlog.py
python3 $B -h
```

## Backend (PROFILE.md `## Tracker`)

```
## Tracker
backend: github          # github | local
repo: owner/name         # github only; default: the origin remote
```

`init-profile` asks once. Its default is `github` when `origin` is on GitHub
and `gh auth status` passes, and `local` otherwise. Run
`python3 $B init` once after choosing. It creates the labels on GitHub, or
the backlog directory for the local backend.

| | `github` | `local` |
|---|---|---|
| Ticket | one issue, id `#123` | one file `tickets/T0001-<slug>.md`, id `T0001` |
| Where | GitHub, visible from the web and phone | `<git-common-dir>/backlog/`, visible to every worktree of the clone on this machine, never committed |
| Fields | labels (`state:*`, `type:*`, `area:*`, `epic:*`, `p1`–`p3`, `hands-on`) plus a `Blocked by:` body line | YAML frontmatter |
| Screenshots | copied to `<git-common-dir>/backlog/assets/<id>/` and linked by path (gh cannot upload images) | same directory |
| Claims | a local lock, then the `state:claimed` label and a `claimed-by` comment | a local lock, then the frontmatter |

Claims are atomic between sessions on one machine; that is the supported
setup. Two machines claiming from one GitHub backlog can race.

## Ticket fields

| Field | Values | Set by |
|---|---|---|
| `title` | behaviour-level, domain words | filer |
| `type` | `bug`, `enhancement`, `task` | filer |
| `area` | kebab-case product area (`leaderboard`, `sync`, `strands-editor`) | filer; workers filter on it |
| `epic` | the feature slug when the ticket comes from a spec, else empty | `write-tickets` |
| `priority` | `p1` (broken for users), `p2` (default), `p3` (polish) | filer |
| `state` | see below; exactly one | lifecycle |
| `hands-on` | yes when only the user can judge the result (UI, motion, feel) | filer |
| `blocked-by` | ids that must be `done` first | filer |
| `claimed-by`, `claimed-at` | the session or worker name and time | `claim` |

The body is the **agent brief**. Write it in this order:

1. what is wrong or wanted, in the user's words, quoted;
2. the expected behaviour;
3. acceptance checks (how a worker proves it);
4. out of scope;
5. links to screenshots.

It names behaviour, types and contracts, never file paths or line numbers,
because tickets wait for days while the code moves.

## States

```
needs-info ──answer──> ready-for-agent ──claim──> claimed ──merged──> needs-check ──user OK──> done
     ↑                       │  ↑                    │                    │  (no hands-on: straight to done)
     └────── question ───────┘  └──── unclaim ───────┘                    └──user says no──> ready-for-agent
ready-for-human: judgment, credentials or device access no agent has.   wontfix: closed with the reason.
```

- **Frontier**: `ready-for-agent`, every `blocked-by` id `done`, sorted by
  priority and then age.
- **`needs-check`**: the change is merged (dark or live) and waits for the
  user's hands-on check. The feedback session batches these into one build
  (`file-tickets` § Check batch). Workers never ask the user for a check.
- `done` and `wontfix` close the ticket. Every transition takes a note that
  goes into the ticket's comments.

## Operations

| Need | Command |
|---|---|
| File | `new --title T --type bug --area A [--priority p1] [--hands-on] [--epic S] [--blocked-by ID,ID] [--state needs-info] --body-file F [--attach PNG ...]` → prints the id |
| Look for duplicates before filing | `list --search "words" --all` |
| Read | `show ID` |
| Frontier, filtered | `list --frontier [--area A] [--type T] [--epic S] [--json]` |
| Claim a pack | `claim --as NAME [--area A] [--type T] [--epic S] [--ids ID,ID] [--max 5]` → the claimed ids, possibly none |
| Give one back | `unclaim ID --note "why"` |
| Move state | `set ID --state needs-check --note "PR #N merged @ sha"` (`done`, `wontfix`, `needs-info`, `ready-for-agent`, …) |
| Comment | `comment ID --note "…"` |
| Attach | `attach ID PATH ...` |
| Release notes | `list --state done --closed-since YYYY-MM-DD` |
| Stale claims | `list --state claimed` (shows the age of each claim) |

Reference tickets by id plus title in chat and ledgers, never by bare id.

## Runs from before the backlog

A run that started before this contract keeps its `.scratch/<slug>/tickets/`
files until each ticket closes; finish it the old way. New tickets never go
there, including hardening tickets for such a run: they are published to the
backlog with `--epic <slug>`.
