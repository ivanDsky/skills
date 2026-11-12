# Fix loop and teardown

Read this when findings go back to the implementer, or when the teardown gate
fires.

## Fix round

1. Resume the same implementer with the findings file path
   (`.scratch/<slug>/review.md`). Critical and Important findings only — Minors
   are never fixed in-round; ledger each as
   `Ruling: minor <what> deferred — <why>`.
2. Re-review only the fix diff (`git diff <pre-fix-sha>...HEAD`): did each
   finding actually close, and did the fix break anything inside the
   already-reviewed surface? Never a full re-review.
3. A round fails when any Critical/Important finding survives or a new one of
   the same grade appears. Count failed rounds per module in the ledger.

## Triage — what the implementer may do with a finding

Each finding gets exactly one response, recorded in the findings file:

- **FIX** — change the code; the default.
- **CONTEST** — only with evidence the reviewer could have read (a spec
  assumption number, a ledger Ruling, a test, a line in the diff). "I wrote
  it that way" is not evidence. A finding that says the work is hard to
  understand is never contestable — fix the unclear part.
- **ESCALATE** — the finding is right but the fix changes a spec decision or
  an interface other tickets rely on: ledger a `Ruling:` and escalate — a
  worker to its orchestrator, the orchestrator to the user through the ask
  tool (`start` § Waiting on the user); do not decide alone.
- **DECLINE** — out of scope for this change; allowed only for a Minor, with
  the ledger line `Ruling: minor <what> deferred — <why>`.

A contest the reviewer cannot refute from the cited evidence closes the
finding; one it can refute makes it a FIX.

## Convergence

- Findings keep stable ids across rounds, so a fix is checked against the
  same id, not a reworded copy.
- Keep a settled list (closed, contested-and-accepted, declined): a re-review
  does not re-raise a settled id without new evidence.
- A reviewer or lens that failed, timed out, or could not be dispatched is
  **not run** — never counted as a clean pass. Report it as not run and name
  the missing coverage.
- Churn: the same location flips between findings across rounds, or fixes
  keep reopening each other → stop looping and feed the teardown gate below.

## Teardown gate

Fire `assess-teardown` when a module hits 2 failed fix rounds (before round 3),
or once at reviewer discretion with a logged reason. The brief carries only:
module path, spec excerpt, fix-round history from the ledger, open findings —
never the transcript, never the full fix diffs.

On `fix-forward`, the bounded plan re-enters the fix loop. On `clean redesign`,
the rebuild inherits only root cause, interface contracts, and surviving tests;
old fix diffs are not reused. Either way the verdict is reported to the user.
