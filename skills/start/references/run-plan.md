# Run plan decisions

Read when the run plan carries a review-site, delivery or UI-tier decision,
and when `debug` is on. Each decision bundles into the plan, never a separate
round trip; SKILL.md § Run plan, then fire holds the summary.

## Review-site publish

PROFILE.md `Review site publish:` decides — `always` → the plan lists
`review-site` firing after deliver; `off` → skip silently; `ask` (the
default) → one yes/no ("publish the review dashboard when this run ships?")
that routes deliver's report step for this run only. Run effort `thorough`
defaults to yes (effort-mapping.md § Rules).

## Delivery

PROFILE.md `## Delivery` `changes:` decides:

- `pr` → the plan lists `open-pr` after deliver and the run branch is cut
  before the first commit (several tickets or > ~20 files → a `gh stack`,
  one layer per ticket).
- `trunk` → the plan lists `ship-to-trunk`: no run branch, one worktree +
  slice PR per ticket off fresh `origin/main`, ticket 01 adds the release
  flag, the flip PR is the release (stacks only by its exception).
- `main` → commits land on the default branch.
- `ask` (typed by the user at setup, or an old PROFILE without the answer)
  → one question ("trunk (small PRs into main), one PR, or straight to
  main?") answered for this run only.

The style is the user's per-project decision from `init-profile` question 9;
start never switches it on its own. Asked before `implement` starts, because
the branch must exist before the first commit.

Trunk needs a required PR check (a workflow on `pull_request` that main's
protection requires): missing → the plan's first ticket is the check setup
and slices wait for it plus the user's branch protection (`ship-to-trunk`);
local gates substitute only when PROFILE says `pr-check: none` (CI on main
only; merge gate = local suite on the rebased branch). No `merge dark slices
on green` consent line → say once that every PR waits for the user.

## UI tier

The ask builds or changes a reusable composable → infer the tier per module
(`micro-architecture`/references/ui-components.md, "Tier first"):
design-system, shared or published module → `library`; feature-local →
`app`. Record it as a ledger line `Ruling: ui-tier <module> = library|app —
<why>`. When it is ambiguous (single module, shared `ui/components`
package), ask one question ("library rules (MUST) or app rules (SHOULD) for
<module>?").

## Debug run log

PROFILE.md `debug: on`, or "debug on" said this session → create
`.scratch/run-log.md`; every chain skill appends one bounded entry (≤4 lines):

`<skill> | fired by <trigger> | contributed: <what changed> | depth: ok | skipped: <none | what + why>`

`depth != ok` when a size estimate is exceeded, >2 fix rounds run, research
fan-out tops 3 subagents, or a gate re-ran — always with the cause. Off = no
log. The per-run ledger (`.scratch/<slug>/ledger.md`) is a different file.
