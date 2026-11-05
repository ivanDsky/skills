# Page brief (one subagent per task)

The parent fills the brackets and sends this as the whole dispatch prompt.
No session history; the subagent reads only what is listed.

```markdown
You are building ONE throwaway prototype page. Speed matters more than code quality.

Task: <the task verbatim, one question>
Kind: design | logic
Output: <ABSOLUTE path>/.scratch/<slug>/prototype/<NN>-<task>.html   (write only this file)
Theme source: <paths to Color.kt / Theme.kt / Type.kt or web theme | "none — use Material 3 baseline">
Models for fake data: <paths | "none">
Target surface: phone (~412 px frame) | tablet | desktop

Read first: the `prototype` skill (sections 2-3), and for design: `senior-ux`,
then `emil-design-eng`, `apple-design`, `animation-vocabulary`.

Checklist (all required):
- [ ] One file; inline CSS/JS; no build, CDN, or network.
- [ ] Header strip: the question, the failing user need (design), "PROTOTYPE — throwaway".
- [ ] Theme values as CSS custom properties named after the app's tokens.
- [ ] Fake data inline, shaped like the models, incl. longest label and empty list.
- [ ] Design: 2-3 structurally different variants; bottom switcher; `?v=a|b|c`; keys 1-3;
      state row (`?s=`): default / empty / loading / error / longest / dark.
      Switcher ≤ ~2 rows, short labels, collapsible — the screen being judged stays visible.
- [ ] Design: contrast ≥ 4.5:1, 48 px targets, reduced-motion respected.
- [ ] Logic: a button per event, 1-3 guided scenarios, full state rendered after every action.
- [ ] Inline script parses: `node --check -` on it exits 0. No browser run, no screenshots.

Reply (≤5 lines): status DONE | BLOCKED, the file path, one line per variant
(what is structurally different), and "script-checked: yes | no".
```
