---
name: example-skill
description: Walkthrough example showing this repo's skill layout — SKILL.md plus a references/ file with progressive disclosure. Use to see the format before writing your own skill; safe to delete.
---

# Example Skill

This skill exists to demonstrate the layout used in this repo. Delete it
once your real skills are in place.

## What the layout demonstrates

- `SKILL.md` stays short: routing happens off the `description`, and the
  body holds only what every run needs.
- `references/format-notes.md` holds the longer material, reached only
  when the pointer below fires.

## Steps

1. Read `references/format-notes.md`. Done when: you can state what the
   description field must contain for reliable routing.
2. Copy `_template/` to `skills/<new-name>/` and start a real skill.
   Done when: `python3 install.py --check` passes with the new skill.
3. Remove this skill with `git rm -r skills/example-skill`. Done when:
   `python3 install.py --list` no longer shows it.

A `scripts/` directory works the same way as `references/`: helper
scripts the instructions call by relative path.
