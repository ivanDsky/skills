# Check batch

One build, one message, every ticket waiting on the user's eyes.

## Build

1. `python3 $B list --state needs-check --json`. Nothing waiting → say so.
2. Each ticket's last `needs-check` comment names its PR, its merge sha and
   its release flag (`flag: <Key> | none`). Every listed sha must be on
   `origin/main`. A missing one stays out of this batch, and the reply says
   which one and why.
3. Build from a fresh worktree of `origin/main`, never the session's
   checkout: `git worktree add --detach ../check-<date> origin/main`, debug
   variant, every listed flag forced on through its debug override
   (`wire-dev-settings` owns the flag code; `ship-to-trunk` § Feature
   lifecycle). Android: `deliver`'s `ship_apk.py`, exactly
   as `user-check` § 2 runs it. Web: the LAN URL. No runtime: a demo command
   per ticket.
4. Remove the worktree once the build is in the user's hands.

## Message

```
Build <versionName> (main @ <sha>) is on your device. Flags forced on: <keys>.

#12 Score resets after rotation — rotate mid-game; the score stays.
#15 Leaderboard header overlaps on tablets — open the leaderboard on the tablet.
…
Reply per id: ok, or what is wrong.
```

The verify line comes from the ticket's `## Acceptance`, hands-on line first.

## Replies

| Reply for a ticket | Action |
|---|---|
| ok | `set ID --state done --note "user OK on <versionName>"` |
| what it does is wrong | `set ID --state ready-for-agent --note "<user's words>"`. The next worker fixes on top of what merged. Never revert unless the user asks. |
| a different problem seen while checking | a new ticket via § 2 of the skill; the checked ticket follows its own reply |
| no answer for that id | leave it in `needs-check`; the next batch lists it again |

A ticket that bounces back twice is a design problem: its next `set` also
moves it to `ready-for-human` with "two failed checks; needs a decision".
