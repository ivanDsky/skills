# Code style rules — user payload

The user's swappable style payload (sibling of `rules-architecture.md`):
replace per user or project; the procedures stay generic. Five-part template
from ciembor/agent-rules-books (MIT). Governs comments, naming, and the
AI-slop patterns reviewers flag.

## Comments — user bar (2026-10-29, tightened 2026-11-23), MUST NOT

The code itself is the documentation: names, types, and structure carry the
explanation. Never write a comment. The only comments that may exist are
these, and `structure-checks` S7 fails the build on any other:

1. One line `WHY: <reason>` — a constraint, invariant, or workaround the code
   cannot show ("WHY: single-threaded by contract, tracker claims must not
   race"). Include the reason, never only the what.
2. `@ts-expect-error <reason>`, and a lint-disable directive with
   `-- <reason>`. A directive for a structure rule is never allowed (S0).
3. A legal header: `SPDX-License-Identifier:` or `@license`.
4. A tool pragma the runner reads: `@vitest-environment`, `#region`.
5. A doc comment (TSDoc/KDoc) on a port or contract interface that other
   code implements, stating contract and error modes, and nowhere else.

MUST NOT: narrate the code ("increment the counter"), echo a signature,
duplicate the spec, mention the task, PR or caller, leave a banner or
section divider, leave commented-out code (deleted is deleted — git
remembers), log a decision in a comment (decisions live in the ledger/ADR),
or leave a TODO or FIXME (the tracker holds them; a note nobody tracks is
not done thinking). Never use a comment in place of code: an elided body
marked "add logic here" is a failure
([Aider, lazy comments](https://aider.chat/docs/unified-diffs)). Rename,
extract or add a type instead. (Clean Code ch. 4; user bar)

Why: wrong documentation greatly hinders model understanding of code
([Macke and Doyle](https://arxiv.org/abs/2404.03114)); about one in five
comments from the best model tested was inaccurate
([Kang et al.](https://arxiv.org/abs/2406.14836)); across 88 models comment
volume did not predict pass rate, and a wrong-topic comment cost 20.8%
([Pan et al.](https://aclanthology.org/2026.findings-emnlp.916.pdf)); and in
an agent-rule study every rule that helped was a negative constraint
([Zhang et al.](https://arxiv.org/abs/2604.11088)), so this is written as a
prohibition and enforced by lint. The human evidence is mixed
([Chin and Holmes](https://www.cs.ubc.ca/~rtholmes/papers/icpc_2026_chin.pdf)),
so the case rests on staleness cost and agent behaviour. Vendor agent
prompts converge on default-off, WHY-only (third-party captures, not
vendor publications):
[Claude Code](https://github.com/Piebald-AI/claude-code-system-prompts/blob/main/system-prompts/system-prompt-comment-why-only-guidance.md),
[Gemini CLI](https://raw.githubusercontent.com/google-gemini/gemini-cli/main/GEMINI.md),
[Codex](https://github.com/openai/codex/blob/main/codex-rs/core/gpt-5.2-codex_prompt.md).

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
- A file reads at a glance and a function fits one screen: the caps in
  `structure-checks` S2 are enforced limits, and the fix is to split by
  responsibility (rules-architecture rule 17), never to compress or trim.
- Early returns; no nested ternaries.
- Idiomatic Kotlin: expression bodies where they read, `data` types over
  ceremony, stdlib before hand-rolled helpers.
- Format is scripted (lint/format on save); style debates are config
  changes, not review findings.

## Review use

`review-change` grades style findings against this file: a comment-slop or
AI-slop finding is Important by default (Critical when it hides a real bug,
like a swallowing catch). A comment outside the allowlist is Important even
when S7 is not configured. `implement` applies it while writing, not after.
