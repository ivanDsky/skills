# Triage cases

Worked examples per branch. Read when the branch call is close; the tree in
SKILL.md stays the contract.

| Ask | Branch | Why |
|---|---|---|
| "/start fix the typo in the settings footer" | Quick task | 1 file, no interface, no irreversible op, no deploy → inline ponytail run, no artifacts. |
| "/start add a settings page with toggles for notifications" | Feature | New public interface (new page + persisted settings) → full chain. |
| "/start could we render the timeline as one big canvas? sketch it" | Prototype | The ask is really a question; a cheap demoable answer beats a spec → chain + prototype flag, fast-tier gates. |
| "/start build the billing export" (first chain-worthy ask in a repo with no orientation map) | Unmapped codebase → re-triage | Run `map-codebase`, fill PROFILE.md care-axes, then classify again — often the map reveals the ask is smaller or bigger than it looked. |
| "/start continue" with frontier tickets open | Resume offer | List in-flight tickets, offer resume (straight to `implement`); classify nothing new. |
| "/start quick patch" that adds a public API endpoint | Feature (override rejected) | The quick-task test is a checklist, not a label; a new public interface fails it regardless of what the ask calls itself. |
| "/start prototype the importer — and we WILL ship it to prod" | Prototype, deploy question | Prototype flag holds, but the intake batch must carry the deploy question (`deploy: main | standalone | none`) so shipping is explicit, not silent. |

Near-miss pattern: a user says "quick" but the checklist says feature — the
checklist wins; say so in one line in the run plan.
