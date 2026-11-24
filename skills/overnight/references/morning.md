# Morning check

Read when building the morning check (`overnight` § 3). It is
`user-check`'s check doc (`user-check`/references/check-doc.md) with the
night sections added. The user reads it in under five minutes and answers
every item by id in one reply.

```markdown
# Morning: <slug> — <one line: what the night produced>

Build: <versionName | URL | demo command>     Open: <how>
Night: <go time> → <stop time>; <n> merged, <n> parked, <n> Q defaults.

## Scorecard
T1 met | partial (<what is missing>) | not met (<why>)
T2 ...

## Try these
T1 <entry point> → <action> → expect <result>   (from the brief)

## Screens / Motion / Architecture
(as in the check doc; only what changed)

## Defaults I took (reply "Qn no" to undo)
Q1 <question> → took <default>; "no" reverts <commit/ticket>, then <what changes>
Q2 ...

## Needs your yes (parked)
P1 <what> — why it parked — what happens on yes

## Landed
<one line per epic/area: PRs or commits, links>

## Parked or unfinished
<lane> — where it stopped — next step

## Next night
<first step from resume.md> | none

## Reply
`ok`, or by id: "T2: … · Q1 no · P1 yes".
```

Rules:
- Every Q entry in `questions.md` appears; a Q the user answered during the
  night shows the answer and the rework done.
- The scorecard is honest: a criterion not exercised is "not met", never
  "met (untested)".
- Visuals follow the check doc's sourcing rules; no fake recordings.
- The doc is regenerated per feedback round by `user-check`, keeping ids.
