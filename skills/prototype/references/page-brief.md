# Page brief (one subagent per task)

The parent fills the brackets and sends this as the whole dispatch prompt.
No session history; the subagent reads only what is listed.

```markdown
You are building ONE throwaway prototype page. Speed matters more than code quality.

Task: <the task verbatim, one question>
Kind: design | logic | contract (screen: <name>; states: <list>; themes: light | light,dark)
Output: <ABSOLUTE path>/.scratch/<slug>/prototype/<NN>-<task>.html   (write only this file)
Theme source: <paths to Color.kt / Theme.kt / Type.kt or web theme | "none — use Material 3 baseline">
Models for fake data: <paths | "none">
Target surface: phone (~412 px frame) | tablet | desktop | contract: phone + tablet, no frame
Taste rules and decisions: <PROFILE `## Taste rules` + in-scope `Decision:` lines, pasted | "none">

Read first: `prototype`/references/page-rules.md, then for design: `senior-ux`,
then `emil-design-eng`, `apple-design`, `animation-vocabulary`; for contract also
`prototype`/references/contract.md § Contract pages.

Checklist (all required):
- [ ] One file; inline CSS/JS; no build, CDN, or network.
- [ ] Header strip: the question, the failing user need (design), "PROTOTYPE — throwaway".
- [ ] Theme values as CSS custom properties named after the app's tokens.
- [ ] Fake data inline, shaped like the models, incl. longest label and empty list.
- [ ] Design: 2-3 structurally different variants; bottom switcher; `?v=a|b|c`; keys 1-3;
      state row (`?s=`): default / empty / loading / error / longest / dark.
      Switcher ≤ ~2 rows, short labels, collapsible — the screen being judged stays visible.
- [ ] Design and contract: contrast ≥ 4.5:1, 48 px targets, reduced-motion respected.
- [ ] Logic: a button per event, 1-3 guided scenarios, full state rendered after every action.
- [ ] Contract: the chosen direction only, no variants; layout at the app's breakpoints (tablet
      designed, not stretched); `?s=<state>`, `?theme=light|dark`, `?frame=1` hides strip and
      switcher; every listed state renders; every taste rule above holds.
- [ ] Inline script parses: `node --check -` on it exits 0. No browser run, no screenshots
      (contract frames are captured by the parent at freeze).

Reply (≤5 lines): status DONE | BLOCKED, the file path, one line per variant
(what is structurally different), and "script-checked: yes | no".

Hard rules (a guard hook blocks the bash ones):
- Never pkill, killall, or `gradlew --stop`; other lanes' builds share the machine.
- Never pipe `yes` into a command (`yes | cmd`); use its non-interactive flag (`--yes`, `-y`), and stop only processes you started, by pid.
- A hook runs `gradlew` and `ship_apk.py` behind `build-slot`; that prefix is expected: never cancel, kill or script around it.
- Write only inside your worktree, plus the report/findings path your brief names.
- Stage explicit paths; never `git add -A`, `git add .` or `--all`.
- Never delete caches (~/.gradle, ~/Library, ~/.android); disk full means BLOCKED.
- Run `df -h ~` before a build; under 15 GB free, report BLOCKED.
- Never merge or enable auto-merge; report ready.
- Never call the ask tool (`AskUserQuestion`); questions go in the report as NEEDS_CONTEXT.
```
