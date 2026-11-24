# Night grill tree

Read when running `overnight` § 1 step 3. Each branch lists what must be
settled before go and the default to recommend. A branch the repo, PROFILE
or the ledger already answers is skipped, never re-asked. Branches are in
prerequisite order: a later branch joins a round only once the earlier ones
it depends on are settled.

## 1. Outcome

- What the user holds in the morning: a build on the device, a served URL,
  a merged epic, a spec plus tickets, research findings. One sentence.
- Default: the build or URL of the whole chunk, ready for one check.

## 2. Scope and stop line

- In: features, screens, tickets by id. Out: named neighbours that look
  in scope and are not.
- Stretch list, ordered: what to do if the DoD is met early.
- Default: no stretch; spare time hardens what landed.

## 3. Acceptance

- Each criterion checkable in the morning ("T1: tap X → Y shows").
  These become the morning scorecard and every ticket's DoD.
- Default: review clean + build green + happy path demos.

## 4. Product and taste

- Every user-visible choice the chunk contains: flows, empty and error
  states, copy tone, layout direction, motion feel words resolved per
  `animation-vocabulary`. PROFILE `## Taste rules` pasted, not re-asked.
- Choices the user will not settle now → design options built side by
  side (`prototype` variants) and picked in the morning; never one guess.

## 5. Architecture and seams

- New modules, ports, data shapes, persisted formats, extension points
  (`micro-architecture` table). Persisted formats and migrations are
  decided now or the lane parks; they are never night defaults.
- Default: follow existing ADRs and patterns; no new seam without a named
  second variant.

## 6. Forks and contingencies

- Every known "either A or B" in the chunk gets an answer or a rule ("try
  A; if it costs more than one fix round, B").
- External risks: an API or library that may not work, a quota, a flaky
  suite. Each gets "if it fails, do X".

## 7. Autonomy envelope

- May decide alone: naming, internal structure, test shape, ordering,
  anything reversible inside scope.
- Pre-approved tonight (the user's explicit yes, listed): spec freeze,
  ticket set, implement, dark merges, a dependency bump, a dev-server
  deploy. Each line names its limit.
- Never at night, not delegable: release, flag flip, production deploy,
  anything public, data deletion, force-push to main, money.
- Questions at night: none reach the user; every Q and P entry waits for
  the morning check. Not a grill question.

## 8. Environment at night

- Devices awake and reachable? Servers, tokens, rate limits, CI minutes,
  disk. Machines that sleep, VPNs that drop.
- Who runs it: this session or the bot team, and which models
  (`start`/references/effort-mapping.md).
- Default: this session with captains; preflight proves every item.

## 9. Budget and morning time

- Wall-clock end (the morning time), max parallel agents, spend cap if
  the user has one.
- Default: morning time 08:00 local, agents per PROFILE, no extra cap.

## 10. Pre-mortem

Always the last round: the 3-5 likeliest ways the night is wasted, each
with a contingency answer. Typical: preflight-passing environment that
dies at 2 a.m.; an open design fork found mid-run; a flaky suite blocking
merges; a worker widening scope; the morning build path broken.
