# Architect brief, verdict, and memo templates

Read before dispatching the architect (step 2 of assess-teardown). The brief
is a file; the dispatch prompt carries only the brief path, one line of
context, and the report contract — never session history.

## Architect brief (file template)

```markdown
# Teardown assessment: <module path>

You are an independent architect. Grade this module as a stranger would: the
attempts below were made by someone else, and you owe them neither loyalty
nor blame. Decide whether the module is still fixable or must be redesigned
from scratch.

## Module
<path, one-line purpose, the project-map section covering it>

## Spec excerpt
<verbatim excerpt covering this module's requirements>

## Fix-round history (from the ledger)
<per round: findings, what was changed, why the round failed>

## Open findings
<current Critical/Important findings, verbatim>

## Task
Read the module and its tests; run the test suite. Write your verdict to
<absolute verdict path> in the format below. Back every claim with evidence —
quoted findings, test output, ledger lines. Do not implement anything and do
not consult the implementer or reviewer.
```

Never paste the transcript or the full fix diffs into a brief — summarize
instead. The architect's fresh context is the point.

## Verdict format

The verdict file holds exactly one of:

    VERDICT: fix-forward
    EVIDENCE:
    - <quoted finding / test output / ledger line>
    PLAN (bounded):
    - what changes: <concrete, file-scoped>
    - how verified: <command + expected output>

    VERDICT: clean-redesign
    EVIDENCE:
    - <quoted finding / test output / ledger line>
    RATIONALE:
    - <why the attempts failed structurally, not locally>

No third verdict. A `fix-forward` plan that would rewrite most of the module
is a redesign — say so instead of filing it as a fix.

## Findings memo (redesign only)

`.scratch/<slug>/teardown/<module>.md`, exactly three sections:

```markdown
# Teardown memo: <module>

## Root cause
<why the fix attempts failed — the structural reason>

## Interface contracts
Consumes: <signatures this module needs from neighbors>
Produces: <signatures neighbors need from this module>
<only contracts worth keeping; a contract the redesign should break goes
under Root cause instead>

## Surviving tests
<passing tests that encode required behavior: path + what each pins down>
```

The rebuild implementer's brief is this memo + the spec excerpt — nothing
else from the old attempt crosses over.
