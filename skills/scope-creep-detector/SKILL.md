---
name: scope-creep-detector
description: >-
  Compares a git diff (working tree, staged, branch, or saved) against a one-line intent and
  flags scope creep: unrelated files, new dependencies, public API renames, config/CI edits,
  oversized hunks, formatting-only noise, and subsystem spread, then assigns keep, split, or
  justify verdicts. Use when checking whether a change or PR grew beyond its fix, whether
  staged changes are too broad, what unrelated files got touched, or during implement/review
  to catch drift before it reaches a reviewer. Local, offline, read-only.
interaction: afk
requires: [python3, git]
---

A one-line fix should not force a reviewer through fourteen files in three subsystems. This
skill diffs the change against its stated intent, surfaces scope signals, and turns them into
keep, split, or justify decisions. It is the tracer-bullet scope guard for the implement and
review steps: run it the moment a fix starts touching files it should not, and again before
opening a PR. The script is stdlib-only, makes no network calls, and changes nothing.

## 1. Establish the intent

Use the user's one-line intent (`fix null deref in parser`, `add retry limit to webhook
delivery`). If none was given, the script falls back to the branch name; when that is generic
or detached from the work, ask for one line of intent before trusting the relatedness score.

## 2. Run the classifier

Run from this skill directory:

```bash
python3 scripts/scope_creep.py --repo /path/to/repo --intent "fix null deref in parser" --json
```

`--staged` for the index, `--base main` for a branch diff, `--diff -` for a unified diff on
stdin. Leave `--hunk-threshold` alone unless the repo documents a reason to change it.

## 3. Read the signals

Read [references/scope-signals.md](references/scope-signals.md) before recommending anything.
JSON keys: `in_scope` (intent/path keyword overlap), `likely_creep` (no overlap, with reasons
and signals), `new_deps`, `api_renames`, `config_edits`, `stats` (subsystem counts, oversized
hunks, formatting-only files). Empty arrays are evidence too: say "no signal detected", never
"guaranteed in scope". The classifier is triage evidence, not proof of authorial intent.

## 4. Give every `likely_creep` item a verdict

1. **Keep** — necessary for the intent, connection is direct. State the connection in one
   sentence.
2. **Split** — can land independently, belongs to another subsystem, or adds a dependency, API
   rename, config edit, or oversized hunk the intent does not need. Name the files or hunks for
   the follow-up change.
3. **Justify** — a cross-cutting edit that cannot be separated safely. State the invariant or
   build constraint that requires it and the reviewer risk.

Prefer split when evidence is ambiguous. A zero relatedness score means "verify the
connection", not "unrelated": path matching is a cheap proxy, not proof.

## 5. Report

Compact structure: intent and diff source; files and subsystems touched with additions and
deletions; in-scope changes; likely creep with signal evidence; keep/split/justify table;
proposed follow-up grouping. Name file paths and hunk headers. For an oversized mixed hunk,
describe the smallest coherent edit — the script cannot split hunks itself.

## Boundaries

Read-only and offline; never stage, revert, or commit without asking. Not for correctness or
security review inside an agreed scope, formatting, commit messages, or repo-wide growth
history.

---

Adapted from [Shubhamsaboo/awesome-llm-apps](https://github.com/Shubhamsaboo/awesome-llm-apps)
`agent_skills/scope-creep-detector` (Apache-2.0).
