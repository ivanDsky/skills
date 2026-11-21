---
name: file-tickets
description: >-
  Feedback session for the shared backlog: turn a stream of user feedback,
  bug reports, screenshots and ideas into deduplicated tickets with agent
  briefs (area, type, priority, state) that worker sessions in other worktrees
  pick up; never implements. Also runs the batched hands-on check of merged
  tickets in needs-check. Use when the user wants to dump feedback or bugs
  into the backlog, says "file this", "log these issues", "note it for
  later", or asks for one build to check what landed.
interaction: hitl
requires: []
---

> **TL;DR** Files every point of user feedback as a deduplicated backlog ticket with an agent brief, never implements, and batches hands-on checks of merged tickets into one build.
> **Related**: skill://work-tickets (downstream: workers claim what this files), skill://start (feature-sized asks go through the full chain), skill://diagnose-bug (bug evidence ladder, run by the worker), skill://user-check (how a build reaches the user), skill://deliver (release notes from done tickets)

# File tickets

You are the feedback session. The user talks; you file. Every point becomes a
ticket a worker can pick up days later in another worktree, without this
conversation. You never edit code, open worktrees for changes, or fix
anything "quickly"; even a one-line fix becomes a ticket. Read-only lookups in
the code to phrase a brief well are fine.

All backlog access goes through one script (contract, states and fields:
`work-tickets`/references/backlog.md):

```
B=~/.agents/skills/work-tickets/scripts/backlog.py   # in this repo: skills/work-tickets/scripts/
```

## 1. Read first

1. PROFILE.md `## Tracker`. Missing → ask the `init-profile` tracker question
   once (recommend `github` when `origin` is GitHub and `gh auth status`
   passes, else `local`), write the section back, run `python3 $B init`.
2. `python3 $B list` once per session: the open tickets and the areas in use.
   New tickets reuse those area names.

## 2. Per user message

1. Split the message into points, one observable behaviour each. "The timer
   is wrong and the button is ugly" is two points. Quote the user's words;
   never paraphrase away a detail.
2. Dedupe each point: `python3 $B list --all --search "<2–3 key words>"`, and
   try a synonym when nothing matches. Then:
   - an open duplicate → `comment` with the new words and any screenshot;
   - a `done` match that broke again → new ticket, "regression of <id>" in
     the brief;
   - a `wontfix` match → tell the user and file only if they insist.
3. Size each point:
   - **Ticket-sized**: one behaviour, no open design question → file it.
   - **Feature-sized**: a new screen, several capabilities, or a design the
     user has not settled → one `enhancement` ticket in `ready-for-human`,
     brief "feature: needs the /start chain". A session that runs `/start`
     on it publishes the real slices with `--epic`.
4. File: `python3 $B new --title … --type bug|enhancement|task --area …
   [--priority p1] [--hands-on] [--series …] [--blocked-by …] [--state …]
   --body-file - [--attach <png> …]`. The brief template and the field rules
   are in [filing.md](references/filing.md). Hands-on = only the user can
   judge the result (look, motion, feel, copy). Series = one name for every
   ticket of a move or refactor series in one area; it holds that area's
   other tickets while the series is claimed (`work-tickets` § 2).
5. State: `ready-for-agent` when a worker can act on the brief alone;
   `needs-info` when the expected behaviour is unknown; `ready-for-human`
   when the work needs credentials, a device or a decision only the user
   can make.
6. Reply in one short table (id, title, state, area), plus at most one
   ask-tool call. That call carries every `needs-info` question from this
   message, with the recommended answer first. The answers go into the
   tickets (`comment`, then `set --state ready-for-agent`). Never hold a
   ticket back to wait for an answer.

## 3. Check batch

Workers never ask the user for a check. A merged ticket that needs the
user's eyes waits in `needs-check`. When the user asks to check, or several
tickets are waiting, build once and hand over one message covering all of
them:
`python3 $B list --state needs-check`, build from fresh `origin/main` with
every flag of those tickets forced on (`user-check` § 2), then list the verify
steps per ticket. Replies route per [check-batch.md](references/check-batch.md):
OK → `done`, wrong → back to `ready-for-agent` with the user's words, new
problem → a new ticket.

## 4. Status and releases

- "What's in flight?" → `list --state claimed` (claim ages) and
  `list --frontier`. A claim older than a day with no PR is stale: offer
  `unclaim`, never steal it silently.
- Release notes: `list --state done --closed-since <last release date>`. The
  cut takes `main` as it is. Tickets not done roll to the next release, and
  no session has to finish first (`deliver`).

## Rules

- Never implement. "Just fix it now" → file a `p1` ticket, tell the user a
  worker picks it up (`work-tickets` in a worktree), and name the command.
- Briefs name behaviour and contracts, never file paths or line numbers: the
  code moves before a worker arrives.
- One point, one ticket. Never bundle unrelated points to save tickets.
- Screenshots and recordings always go in with `--attach`. A path in chat dies
  with the session. Read a recording with `diagnose-bug`/scripts/frames.py to
  quote the moment (seconds) in the brief.

Fresh skill for this repo's shared backlog. Its triage states follow
mattpocock/skills (`triage`, MIT); no text adapted.
