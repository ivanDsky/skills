# Code style rules — user payload

The user's swappable style payload (sibling of `rules-architecture.md`):
replace per user or project; the procedures stay generic. Five-part template
from ciembor/agent-rules-books (MIT). Governs comments, naming, and the
AI-slop patterns reviewers flag.

## Comments — user bar (2026-10-29), MUST

The code itself is the documentation: names, types, and structure carry the
explanation. A comment is justified ONLY when it says what the code cannot:

1. WHY: the invariant, the decision, the reason a constraint exists
   ("single-threaded by contract: tracker claims must not race"). MUST.
2. A non-obvious gotcha the language cannot express (workaround + ticket link).
   MUST include the why, not just the what.
3. Public-API doc lines on interfaces others build against (KDoc on a
   repository interface: contract, error modes). SHOULD be one line.

MUST NOT: narrate the code ("increment the counter"), echo signatures,
duplicate the spec, leave commented-out code (deleted is deleted — git
remembers), or log decisions in comments (decisions live in the ledger/ADR).
A TODO without a ticket reference is not done thinking. (Clean Code ch. 4;
user bar)

## AI-slop patterns — reviewers flag on sight, MUST fix

The tells that code was generated, not thought:

- Comment echoes code; comment narrates the next five lines.
- Defensive checks for states that cannot occur (`if (list != null)` after a
  non-null guarantee) — the caller's contract is the check.
- Copy-pasted near-duplicates instead of one parameterized implementation.
- Deep nesting where a guard clause / early return reads flat.
- Names that job-title instead of say meaning: `Manager`, `Helper`, `Util`,
  `Processor`, `ServiceImpl`, `Data2`.
- Dead code, unused parameters, speculative options nobody calls.
- try/catch that swallows, or log-and-rethrow stacked three layers deep.
- A mapping/DTO layer that transforms a type into an identical type.
- Abstraction with exactly one implementation and no test fake (speculative
  seam — see rules-architecture bias list).
- Clever one-liners a reader must decode; a flat five-liner wins.

## Readability rules — SHOULD

- Names come from the project glossary and the domain; a name is a contract,
  not a label.
- One abstraction per file, short files (see rules-architecture rule 17).
- Small functions that fit one screen; early returns; no nested ternaries.
- Idiomatic Kotlin: expression bodies where they read, `data` types over
  ceremony, stdlib before hand-rolled helpers.
- Format is scripted (lint/format on save); style debates are config
  changes, not review findings.

## Review use

`review-change` grades style findings against this file: a comment-slop or
AI-slop finding is Important by default (Critical when it hides a real bug,
like a swallowing catch). `implement` applies it while writing, not after.
