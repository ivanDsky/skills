# Worker hard rules

The one canonical block. Every worker spawn carries it verbatim; every other
dispatch template points here. Agents broke these in prose more than once, so
the bash-detectable ones (kill, `gradlew --stop`, blind `git add`, deleting
caches) are also refused by the `hooks/pre/worker-guard.ts` guard hook
(install: README § Hooks). The rest are on the worker. `hooks/pre/build-queue.ts`
rewrites a worker's `gradlew` and `ship_apk.py` calls to run behind `build-slot`;
workers who took that prefix for their own slip cancelled, killed or scripted
around 200 queued builds (audit 2026-11-21), hence the second line.

```
Hard rules (a guard hook blocks the bash ones):
- Never pkill, killall, or `gradlew --stop`; other lanes' builds share the machine.
- A hook runs `gradlew` and `ship_apk.py` behind `build-slot`; that prefix is expected: never cancel, kill or script around it.
- Write only inside your worktree, plus the report/findings path your brief names.
- Stage explicit paths; never `git add -A`, `git add .` or `--all`.
- Never delete caches (~/.gradle, ~/Library, ~/.android); disk full means BLOCKED.
- Run `df -h ~` before a build; under 15 GB free, report BLOCKED.
- Never merge or enable auto-merge; report ready.
- Never call the ask tool; questions go in the report as NEEDS_CONTEXT.
```

## Maintaining it

- Change the block here first, then paste the same text into each template
  that is sent as a spawn prompt: `dispatch.md` (implementation workers),
  `prototype`/references/page-brief.md, `fan-out-research`/references/finding-format.md.
  `bun test hooks/` fails when a copy drifts.
- Templates that are only files or catalog pages (architect brief, goldfish
  lenses, merge-loop fix workers) carry the one-line pointer
  `Hard rules: skill://implement/references/hard-rules.md` instead.
- The captain (`start`/references/lifecycle.md § Captain brief) carries the block with only the merge line swapped for its merge_lane.py line.
- The disk floor is 15 GB free unless `PROFILE.md` names another; the worker
  states the number it saw in its BLOCKED report.
- A rule an agent breaks twice and a hook can detect becomes a guard case in
  `hooks/pre/worker-guard.ts` with allowed and blocked tests.
