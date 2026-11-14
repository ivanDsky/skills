# Assumptions and the scope matrix

Read this while writing the spec's Assumptions and Scope matrix sections, and
again for the checkpoint's pre-post diff (SKILL.md § 3 step 0).

## Shown vs assumed

One test per assumption: would the user see it on a screen, meet it in the
flow, or have to decide it? That covers what appears and where, who sees
what, order and copy, defaults the user meets, what visibly happens to their
data, and what it costs them in time or money.

- **Yes → A-item** (A1, A2, ...), shown in full at the checkpoint.
  "A3: friends mode filters the leaderboard; the places tab stays global."
  "A5: an unfinished board autosaves as a draft."
- **No → `assumed: <decision> — <why>`**, the agent's call, listed under
  Assumptions → Assumed in `spec.md`, never in the digest.
  "assumed: one table per board, cascade delete — matches puzzle storage."
  "assumed: sync runs as a periodic background job — existing jobs do."

Rules:

- Unsure → shown. A visible assumption filed as internal is the expensive
  mistake: in the audited sync spec, about 20 of 45 assumptions were internal
  and rubber-stamped, while the UX-visible ones were corrected only after
  the build.
- A mechanism with a visible effect splits in two: the effect is an A-item,
  the mechanism an `assumed:` line ("A7: offline edits appear on the other
  device within a minute of reconnecting" / "assumed: last write wins per
  field").
- An irreversible fork (production deploy, data migration, money, deletion)
  is never an `assumed:` line; it goes to `grilling`.
- Both lists are decisions: tickets reference them and reviewers grade the
  build against them. A user correction to either edits the line in place.
- More than about 12 A-items → run the test again on each; long shown lists
  get rubber-stamped too.

## Scope matrix

Required when the feature adds or changes a setting, mode, filter, role or
scope (friends mode, offline mode, a per-game toggle, a region). One audited
spec said "places stay global" in passing, and the user had to restate the
friends rule three times.

1. List the surfaces from the repo, not from memory: every screen or
   destination in the navigation graph, plus outputs without a screen —
   notifications, widgets, share cards, exports and sync, stats and history,
   search, deep links, background jobs.
2. Table: one row per surface, one column per setting or mode. Each cell
   says how the surface changes ("ranks friends only") or
   `unaffected — <why>`. No empty cells, no "TBD".
3. Every `unaffected` cell on a surface the user can see is also an A-item
   ("A9: the places tab stays global in friends mode"). That is the line
   the user is most likely to correct, so it must be in the digest.
4. Filled before the checkpoint is posted; the pre-post diff fails on an
   empty cell or a visible `unaffected` cell with no A-item. Every affected
   cell must end up in some ticket's DoD.

```
| Surface        | Friends mode                      |
|----------------|-----------------------------------|
| Leaderboard    | ranks friends only                |
| Places tab     | unaffected — global ranking (A9)  |
| Duel invites   | friends listed first              |
| Notifications  | friend results only               |
| Share card     | unaffected — own score only (A10) |
```
