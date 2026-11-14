# Domain and prior-art step

Runs before the intake batch is built, so its findings decide which
questions are still worth asking. Fires when the ask has any of:

- a **creation or authoring flow**: the user makes a thing (a board, a level,
  a template, a post, a rule set);
- an **external integration**: a third-party API or account, a data import
  or export, another app or tool the user already runs;
- a **rule catalog**: game rules, hint deductions, validation rules,
  scoring, permissions.

None applies → skip it and write `prior-art: n/a` in `intake.md`.

## Output

`.scratch/<slug>/prior-art.md`, one section per check below, every finding
with its evidence: a path, a URL, or the search that was run. A check that
found nothing still lists where it looked. Effort: fast → inline lookups
only; standard and thorough → one `scout` per check that needs a search,
all dispatched at once, findings written to the file (same on-disk rule as
`fan-out-research`).

## Checks

1. **The user's own prior work.** Search the user's other local projects (the
   folder that holds this repo, and any project PROFILE.md names) by feature
   keywords, service names, and data files (`*.db`, schema files, API
   clients, exports). Also search this repo's tracker and `.scratch/`
   history. A hit names the repo and path and what it already covers: a
   working importer, a schema, collected data. A load-bearing hit becomes a
   batch question (reuse it or start fresh, recommended: reuse); a minor one
   becomes a hard constraint or an assumption. Never copy credentials or
   tokens; note only that they exist. Audited miss: research for an
   integration ignored the user's existing repo that already held a local
   database for the same service.
2. **This app's conventions.** Find the closest existing flow in this app
   that does the same kind of thing (another editor, another import, another
   rule engine) and note its entry point, screens, persistence, naming and
   test style. The new feature follows it; a deliberate deviation is a batch
   question, never a silent choice.
3. **The complete catalog.** Enumerate a rule catalog in full from its
   primary source (the rulebook, official docs, the API reference, the
   existing engine's code): every rule, case or endpoint with its source,
   then mark each in or out of scope. "The common ones" is not a catalog.
   State how completeness was checked, for example a count against the
   source's index. Audited miss: a hints engine shipped with an incomplete
   deduction catalog.
4. **"How does a user create one" walkthrough** (authoring flows only),
   before any screen design: the numbered steps a first-time user takes from
   the entry point to a saved result, including starting from empty, fixing
   a mistake, validating, and finding the result later. Each step names what
   the user sees and decides. Audited miss: an editor was built paint-first
   and re-sliced after the user said they had no idea how to create a board.

## How the findings feed the run

- A question the findings answer is dropped from the batch; a gap they
  expose becomes a question.
- The walkthrough goes in the message before the ask call, and one batch
  question confirms or corrects it (`run-intake` step 3, authoring rule).
  The confirmed walkthrough opens the spec's Solution.
- Catalog lines land in the spec's Solution or Out of scope, never as a
  sample.
- Prior-work and convention findings become hard constraints or assumptions
  in `intake.md`, each with its evidence path.
