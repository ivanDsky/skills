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

## Teardown gate

Fire `assess-teardown` when a module hits 2 failed fix rounds (before round 3),
or once at reviewer discretion with a logged reason. The brief carries only:
module path, spec excerpt, fix-round history from the ledger, open findings —
never the transcript, never the full fix diffs.

On `fix-forward`, the bounded plan re-enters the fix loop. On `clean redesign`,
the rebuild inherits only root cause, interface contracts, and surviving tests;
old fix diffs are not reused. Either way the verdict is reported to the user.
