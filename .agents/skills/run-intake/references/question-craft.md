# Question craft and the deep sweep

Read this when you picked the deep gear, or when the focused batch is hard to
fill with genuinely load-bearing questions.

## Word the question so "yes" accepts your recommendation

- Put the recommendation in the question itself: "Add OAuth on top of
  email/password?" — not "How should auth work?"
- One decision per question. If "it depends", split the dependency out first.
- Ask about outcomes and constraints ("must it work offline?"), not
  implementations — unless the user named the implementation.

## Rank by blast radius

A question is load-bearing when the wrong guess costs rework or risk: public
interfaces, data shapes, security, money, deletion, deploy targets, anything
hard to reverse. Styling, naming, and internal structure are assumptions, not
questions.

## Deep-gear sweep checklist

Walk every area that applies; skip areas the ask cannot touch. Each becomes
one or two questions with a recommended default.

1. Scope: what is in, what is explicitly out, what is phase 2.
2. Users: who uses it, permissions, multi-tenant?
3. Data: new stores, migrations, retention, PII.
4. Interfaces: API surface, CLI, UI entry points, breaking changes.
5. Integrations: external services, auth, rate limits, failure handling.
6. Deploy: targets, rollback, feature flags, downtime tolerance.
7. Money and volume: costs incurred, expected load, quota.
8. Testing: what must be covered, how the user verifies.
9. Safety: irreversible operations, backups, audit trail.
10. Effort and dates: quality bar, deadline, what gets cut first.
