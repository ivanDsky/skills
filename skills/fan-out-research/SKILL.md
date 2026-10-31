---
name: fan-out-research
description: >-
  Spawns one research subagent per declared unknown and clears the ticket
  blocker only when the findings file exists on disk with citations. Use when
  a ticket carries an Unknowns: block.
interaction: afk
requires: []
---

> **TL;DR** Spawns one research subagent per declared unknown until cited findings exist on disk; fires when a ticket carries an Unknowns block.
> **Related**: skill://write-tickets (declares Unknowns), skill://implement (fans research)

# Fan out research

Resolve declared Unknowns with parallel fresh-context subagents. One file per
unknown; findings live on disk — chat replies are status, never findings.

## 1. Collect and triage

1. Gather every `Unknowns:` line across the frontier tickets and the spec.
   One line = one question = one subagent.
2. Ticket contract: an unknown must be answerable from code, docs, or primary
   sources. Answerable only by user preference → that is an intake question,
   not an unknown: hand it to `run-intake` and leave it out of the fan-out.
3. Cap the fan-out by effort level: fast → none (research only when a ticket
   is actually blocked); standard → 1 per unknown, at most 3 in flight;
   thorough → full parallel. Over the cap → unknowns blocking the frontier go
   first, the rest queue; ledger a `Ruling:` line naming the queue.

## 2. Dispatch

1. One subagent per unknown, all dispatched at once, no shared state — a
   failed unknown costs one file, not the batch. Subagent thinking follows
   the effort level (low / medium / high for fast / standard / thorough).
2. The brief is minimal — follow the template in
   [finding-format.md](references/finding-format.md): the question verbatim
   with its ticket backlink, the ABSOLUTE findings path
   `.scratch/<slug>/research/<NN>-<topic>.md`, the citation rule (primary
   sources; every claim traces to its owner), and the reply contract
   (≤5 lines, status only). Never paste session history.

## 3. Verify on disk

1. A finding counts only when its file exists at the absolute path AND every
   citation in it resolves to a real file or URL. No file → the unknown is
   still open. Never accept a chat reply as a finding.
2. Missing file or dead citations → one re-dispatch; still nothing → the
   unknown stays open and the ledger carries the `Ruling:`.

## 4. Feed back

1. Answer resolves the unknown → edit the ticket: a resolution line under the
   unknown plus a link to the findings file. That clears the blocker. Every
   findings file is linked into its ticket before coding starts.
2. Answer forks the design → escalate to `run-intake` as a question; never
   silently edit the ticket toward a new design.
3. Answer kills the ticket → close it, with the reason and the findings link
   under `## Resolution`.

## 5. Close out

1. Do not poll: hand back to `implement` and re-check blockers at each
   frontier scan.
2. Report one line per unknown — resolved / open / forked / killed + file
   path.
3. Debug on (PROFILE.md) → append the ≤4-line `.scratch/run-log.md` entry;
   `depth: not ok` when the fan-out topped the effort cap — always with the
   cause.

Adapted from mattpocock/skills (`research`), MIT.
