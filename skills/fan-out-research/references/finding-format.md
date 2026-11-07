# Finding format

Templates for `fan-out-research`: the dispatch brief and the findings file.
Subagents run fresh and may sit in a different cwd, so briefs carry absolute
paths only and stay self-contained — paste the finding template into the
brief; the child cannot read this file.

## Dispatch brief (one per unknown)

```markdown
Research brief — <NN> of <ticket id>
Question (verbatim): "<unknown line>"
Constraints: answer from code, docs, or primary sources only; follow every
claim to the source that owns it. If the answer is user preference, reply
BLOCKED — a preference has no primary source.
Write findings to: <abs>/.scratch/<slug>/research/<NN>-<topic>.md
Use the finding template below exactly, in caveman voice: fragments fine,
every not/never/only, path, number and quote verbatim. Cite only sources you actually
opened — an absolute file path with line refs, or a URL. A claim without a
citation does not belong in the file.
Reply ≤5 lines, status only: DONE + the findings path, or BLOCKED + reason.
Your reply is never read as a finding; the file is the deliverable.
Do not edit any file except your findings file.
<finding template>
```

## Finding file template

```markdown
# <NN> — <topic> (ticket <id>)

## Answer
<the resolution in a few sentences, or "not answerable from available
sources" + what was tried>

## Evidence
| Claim | Source |
|---|---|
| <claim> | `<abs/path>:L12-L40` or <url> |

## Fork
<no | yes — what this answer changes in the design>
```

## Citation rules

- Primary sources only: source code, official docs, specs, first-party APIs —
  not a write-up of them.
- Every claim traces to its owner: absolute file path with line refs or a
  URL.
- Verify on disk: a finding counts only when the file exists at its absolute
  path and every citation resolves. Dead citations void the finding — the
  unknown stays open.
- One file per unknown, never a shared mega-report: a failed unknown costs
  one file, not the batch.
