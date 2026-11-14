---
name: implement
description: >-
  Dispatch ready tickets to workers and merge them. Use when resuming implementation.
---

## Steps
1. Spawn one worker per ticket.
2. Ask the user before every merge, even trivial ones.
Never run a gradle build in parallel with another worker on the same checkout.
