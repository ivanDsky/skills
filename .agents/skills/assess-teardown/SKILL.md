---
name: assess-teardown
description: >-
  Decides fix-forward vs clean redesign for a twice-failed module using an
  independent fresh-context architect, then extracts findings before any
  rebuild. Use when a module fails its second fix round, when a reviewer fires
  the teardown gate with a logged reason, or when the user says a module is
  stuck.
interaction: afk
requires: []
---

# Assess teardown

The teardown gate decides one thing: is this module still fixable, or does the
next attempt start from a clean redesign? The architect is a stranger — fresh
context, high effort, no transcript — so the verdict grades the module, not
the process that broke it.

## 1. Trigger contract

1. The gate fires when the ledger shows 2 failed fix rounds on the same
   module (before round 3), or once at reviewer discretion with the reason
   logged. Review-change counts the rounds; this skill never re-runs fixes
   to find out.
2. User invocation ("this module is stuck") → read the ledger and
   `.scratch/<slug>/review.md` first: a history of failed attempts must
   exist. One failed round or dislike of the code is not a teardown — that
   is the fix loop (`review-change`) or an audit (`ponytail-audit`); say so
   and stop.
3. Ledger the trigger before dispatching:
   `Ruling: teardown gate fired for <module> — <2 failed fix rounds |
   reviewer discretion: <reason>> — cost if wrong: <cost>`.

## 2. Dispatch the architect

1. One architect subagent: fresh context, effort forced high — the PROFILE.md
   effort level does not inherit. The architect decides; it never implements.
2. The brief is a FILE, absolute paths: module path (plus its section of
   `docs/agents/project-map.md` when a map exists), spec excerpt, fix-round
   history summary from the ledger, open review findings. Never the session
   transcript, never the full fix diffs.
3. Report contract: the architect writes the verdict file at the absolute
   path given in the brief. A chat reply without the file is not a verdict.
4. The architect may read the module, its tests, and the neighboring
   interfaces, and may run the test suite. It consults no one.

## 3. Binary verdict, then what

1. The verdict is exactly one of:
   - `fix-forward` — bounded plan: what changes, how verified. The plan
     re-enters the fix loop (`review-change`) as the next round's brief.
   - `clean-redesign` — rationale grounded in evidence: quoted findings,
     test output, ledger lines. Taste or difficulty alone never carries it.
2. Ledger the verdict:
   `Ruling: <verdict> for <module> — <why> — cost if wrong: <cost>`.
   Report verdict + evidence to the user; they may veto once — a veto
   inverts the ruling, halts any rebuild, and is its own ledger line. No
   second veto.

## 4. On redesign — extract, archive, rebuild

1. Extract the findings memo to `.scratch/<slug>/teardown/<module>.md` with
   exactly three sections: **Root cause** (why the attempts failed),
   **Interface contracts** (Consumes/Produces signatures worth keeping),
   **Surviving tests** (passing tests that encode required behavior).
   Nothing else crosses the gate.
2. Verify-on-disk: the memo must exist at that path before anything
   rebuilds. Record the memo path in the ledger.
3. Archive the old branch: rename it with an `archive/` prefix and record
   the sha in the ledger. It is kept for reference and never merged; its fix
   diffs are not reused.
4. Rebuild: open a fresh ticket (docs/agents/issue-tracker.md format)
   referencing the memo path, then dispatch a fresh-context implementer
   whose brief is only the memo + spec excerpt. New work starts from the
   base branch and re-enters the normal gates — implement, then
   review-change. The rebuild implementer spawns no reviewers.

## 5. Close

Report to the user: the verdict, its evidence, and — on redesign — the memo
path and the archived branch name. Ledger lines land as written above.
Debug on → append the ≤4-line `.scratch/run-log.md` entry; a teardown always
logs `depth: not ok` with the cause (`2 failed fix rounds on <module>` or
`reviewer discretion`).

Read [references/architect-brief.md](references/architect-brief.md) before
dispatching the architect — brief, verdict, and memo templates live there.

Adapted from obra/superpowers (`subagent-driven-development` — fix-loop round
cap, fresh implementers), MIT.
