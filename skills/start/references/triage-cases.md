# Triage cases

Worked examples per branch. Read when the branch call is close; the tree in
SKILL.md stays the contract.

| Ask | Branch | Why |
|---|---|---|
| "/start fix the typo in the settings footer" | Quick task | 1 file, no interface, no irreversible op, no deploy → inline ponytail run, no artifacts. |
| "/start add a settings page with toggles for notifications" | Feature | New public interface (new page + persisted settings) → full chain. |
| "/start could we render the timeline as one big canvas? sketch it" | Prototype (big) | The question is about real rendering performance on real data — a fake page cannot answer it → chain + prototype flag, fast-tier gates. |
| "/start prototype the reminders screen, show me a few options" | Prototype (quick) | A look-and-feel question answerable on a page → `prototype`: 2-3 variants in one HTML file, judged on the phone; no intake/spec/tickets. |
| "/start mock up settings, profile and paywall before we build them" | Prototype (quick, 3 tasks) | Three questions → three subagents, one page each, plus the index page. |
| "/start build the billing export" (first chain-worthy ask in a repo with no orientation map) | Unmapped codebase → re-triage | Run `map-codebase`, fill PROFILE.md care-axes, then classify again — often the map reveals the ask is smaller or bigger than it looked. |
| "/start continue" with frontier tickets open | Resume offer | List in-flight tickets, offer resume (straight to `implement`); classify nothing new. |
| "/start quick patch" that adds a public API endpoint | Feature (override rejected) | The quick-task test is a checklist, not a label; a new public interface fails it regardless of what the ask calls itself. |
| "/start prototype the importer — and we WILL ship it to prod" | Prototype, deploy question | Prototype flag holds, but the intake batch must carry the deploy question (`deploy: main | standalone | none`) so shipping is explicit, not silent. |

Near-miss pattern: a user says "quick" but the checklist says feature — the
checklist wins; say so in one line in the run plan.
