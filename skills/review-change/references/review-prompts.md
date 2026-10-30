# Reviewer prompts and verdict templates

Read this before dispatching the standard reviewer or the thorough
dual-verdict subagent.

## Shared brief shape (minimal, never session history)

- Diff command + commit list (`git diff <base>...HEAD`,
  `git log <base>..HEAD --oneline`).
- Spec excerpt with its numbered assumptions.
- Care-axes (ranked) + the `references/rules-*.md` payloads they select.
- Relevant ledger lines.

## Standard reviewer — one report, under 400 words

Ask for, in care-axes order:

- (a) spec breaches — quote the spec line each finding violates;
- (b) quality findings against the rules payloads and care-axes;
- (c) scope creep — behavior in the diff nobody asked for.

Findings graded Critical / Important / Minor, each citing the owning hunk.

## Dual-verdict subagent (thorough) — fresh context, most capable model

Same brief. Two separate verdicts in one report:

```
## Spec compliance
Verdict: ✅ | ❌ | ⚠️ cannot-verify
Per numbered spec decision (assumptions included): met / partial / missing /
not asked for — each with the proving diff hunk or screenshot path.

## Quality
Verdict: Approved | Needs-fixes
Findings by grade (Critical / Important / Minor), each with the owning
diff hunk and the care-axis it threatens.
```

Rules: the axes are never merged or reranked — a change can pass one and fail
the other. A verdict without quoted evidence is cannot-verify, not ✅. No spec
→ skip that axis and say so. Findings land in `.scratch/<slug>/review.md`.
