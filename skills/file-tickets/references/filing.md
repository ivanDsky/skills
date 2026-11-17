# Filing a ticket

## Brief template (the ticket body)

```markdown
## Reported
> <the user's words, verbatim; one quote per message that touched this point>

## Expected
<the behaviour the user wants, one or two sentences, domain words>

## Reproduce            (bugs only)
1. <screen or entry point, by name>
2. <action>
Seen: <what happens>   Build: <versionName or "unknown">

## Acceptance
- <observable check a worker can prove: a test, a preview render, a log line>
- <hands-on tickets: the one thing the user will look at in the check batch>

## Out of scope
- <what this ticket must not touch or change>

## Notes
<optional: suspected cause, related tickets by id + title, "regression of …">
```

Screenshots attached with `--attach` show up as a comment with their stored
paths; do not paste them into the template.

## Field rules

- **Title**: behaviour, not a solution. "Score resets after rotating the
  device", not "Save score in SavedStateHandle".
- **Type**: `bug` = it used to work or obviously should. `enhancement` = new
  or changed behaviour. `task` = no user-visible change (dependency, config,
  docs).
- **Area**: the product surface a worker filters on, kebab-case
  (`leaderboard`, `daily-puzzle`, `settings`). Reuse an area from `list`.
  Create a new one only when nothing fits, and say so in the reply.
- **Priority**: `p1` = broken for users now (crash, data loss, blocked flow).
  `p2` = default. `p3` = polish.
- **Hands-on**: yes when acceptance needs a human judgment (looks right,
  feels right, reads right). A purely logical fix with a test is not
  hands-on.
- **Blocked by**: only real ordering ("the share sheet needs the export
  format first"). Never block on "related".

## What never goes in a brief

- File paths, line numbers, class names that are not public contracts.
- An implementation plan. The worker decides the how; the brief fixes the
  what and the check.
- The conversation. The brief stands alone: a worker without this session
  can act on it.

## needs-info

File the ticket anyway with what is known, `--state needs-info`, and put the
open question at the top of the brief under `## Question`. Ask it in the
message's single ask-tool call. On the answer: `comment` with it, edit
nothing else, then `set --state ready-for-agent --note "answered"`.
