# Night brief

Read when writing `.scratch/<slug>/overnight/brief.md` (`overnight` § 1
step 6). The brief is the only thing the night knows about the user. Every
worker brief and every captain brief carries its path, plus the `Decision:`
lines its work touches, verbatim. Plain prose; facts and rules, no
rationale beyond one clause. ≤ ~120 lines; overflow goes to linked files.

```markdown
# Night brief: <slug>

Go: <date time>, by the user's explicit yes. Morning check: <date time>.
Executor: this session (captains) | bot team <name>, lead <bot>.

## Outcome
<one sentence: what the user holds in the morning>

## Scope
In: <items, ticket ids>
Out: <named neighbours>
Stretch (in order): <items> | none

## Acceptance
T1 <entry point> → <action> → <expected>
T2 ...

## Decisions
D1 <decision> (mirrored as ledger `Decision: overnight <slug> — …`)
D2 ...

## Contingencies
C1 if <event> → <action>
C2 ...

## Envelope
May decide: <list>
Pre-approved tonight: <gate> — <limit>   (one line each)
Never tonight: release, flag flip, production deploy, anything public,
data deletion, force-push to main, money<, project additions>
Night questions: none sent; Q and P entries wait for the morning check.

## Environment
Preflight <time>: <item> ok, <item> ok, ...
Morning delivery: <build → device | served URL>, dry run ok at <time>

## Budget
Agents ≤ <n>; spend cap <value | none>; stop dispatching at <morning − 1h>.

## Assumed (user waved off)
assumed: <decision> — <default>

## Amendments
(appended only; each line dated and mirrored as a `Decision:` line)
```

Rules:
- A decision appears once, as D-n; tickets and specs point to it.
- `Pre-approved tonight` lists only what the user said yes to in the
  grill. A gate not listed keeps its daytime rule, which at night means
  park.
- The brief is never edited in place after go; changes go to
  `## Amendments`.
