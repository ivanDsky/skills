---
name: adopt-tool
description: >-
  Adoption protocol when a new tool, CLI, or capability lands (new command,
  new skill, new environment fact): wire it everywhere it belongs in one
  pass — routing skill entry, workflow-skill references, reviewer mandates,
  TL;DR/Related navigation, evals, README — instead of requesting wiring per
  item. Use when adopting any new capability into the skills repo or when
  the user asks to "wire it into the skills" / "make it mandatory".
interaction: afk
---

> **TL;DR** Adopting a capability is one pass through a fixed checklist — verify → route → wire → mandate → navigate → eval → demo → ship from repo — never a per-item conversation.
> **Related**: skill://android-cli (a completed adoption, use as the reference example), skill://android-env (environment capabilities), skill://review-change (where reviewer mandates live)

# Adopt a capability in one pass

Every new capability historically triggered a follow-up round of "wire it
into other skills / make it mandatory for the reviewer / emphasize it" —
five times in one audited session. This checklist replaces that loop. The
`android-cli` adoption is the worked example.

## Checklist (each step or an explicit skip)

1. **Verify the claim before documenting.** Check `--help`, run the command,
   read the actual output. Assumptions about what a tool can do get
   corrected to what's real (documented corrections beat documented
   fiction). Note the provenance ("checked against X, version Y") in the
   skill.
2. **Route.** Entry in the owning skill's command/capability table: need →
   command → workflow skill that owns it. If no routing skill exists, create
   a small one (command map + placement rules), don't scatter references.
3. **Wire into workflows.** Every workflow skill whose phase the capability
   improves gets one concrete reference (which command, which phase, what it
   replaces). Keep it surgical — one to three lines per skill.
4. **Reviewer mandate.** If the capability produces review evidence, it goes
   into the reviewer brief (`review-change`) as mandatory — reviewer runs it
   itself, not delegated; skipping grades findings `cannot-verify`. State
   ordering if one check must come first.
5. **Navigate.** TL;DR + Related blocks (both directions) on every touched
   skill; README index; `start` direct-paths line.
6. **Eval.** Routing evals: positive triggers fire this skill, negative
   prompts stay with their existing owners.
7. **Demo on real artifacts.** Smoke the capability end-to-end on real or
   synthetic project output before calling it adopted; report the observable
   result (URL, image, command output).
8. **Ship from repo, never local.** Edit the repo → commit → push →
   `npx skills add ivanDsky/skills -g -y -a '*'` (**`add`, not `update`** —
   `update` only refreshes already-installed skills and silently skips new
   ones; `add` is idempotent for existing ones). Installed copies under
   `~/.agents/skills` are
   build outputs; never edit them (audited cost of ignoring this: a full
   redo plus a 445-file accidental commit). Keep `.gitignore` covering
   install artifacts.
9. **Record environment facts once.** Anything the capability needs from the
   machine (paths, trust flags, LAN exposure) goes into the project's
   PROFILE.md `## Environment facts` or the relevant env skill — not into
   conversation memory.

## Anti-patterns

- Documenting a capability that was never run ("verify all suggestions"
  turned out to be only version lookup).
- Wiring into one skill and leaving the reviewer gate, nav, and evals
  behind — that's what generates the follow-up requests.
- Local edits to installed skills that the next `skills update` overwrites.
