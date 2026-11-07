# Stacked PRs (`gh stack`)

> `trunk` runs: stacks are the exception (see `ship-to-trunk`) — only while a parent PR waits on the user; each layer merges as soon as it is green, never atomically.

Read when a `pr` run spans more than ~20 changed files or several tickets,
when a fix must land in a lower layer, or when the user asks for stacked PRs.
A stack is a linear chain of branches, one PR per layer, each PR based on the
one below. The reader reviews one small layer at a time, and GitHub merges
the chain atomically.

Tool: the `gh stack` extension (GitHub-native stacks, GA 2026-10-06).
Verified against `gh stack version 0.3.0` `--help`; reference:
https://docs.github.com/en/pull-requests/reference/stacked-prs-cli-commands.
Missing → `gh extension install github/gh-stack`.

## When

| Run shape | Branching |
|---|---|
| ≤ ~20 files, one concern | one branch `<slug>`, one PR |
| > ~20 files or several tickets | stack: one layer per ticket, tracer bullet at the bottom |
| parallel-safe tickets running concurrently | they share one layer — a stack is linear |

## Create (implement, before the first commit)

```bash
gh stack init <slug>/01-<ticket>        # creates (or adopts) the bottom branch; enables rerere
# ... commit ticket 01 ...
gh stack add <slug>/02-<ticket>         # run from the top branch; -Am "msg" commits first
```

The build-identity slug becomes the last branch segment (`01-<ticket>`), so
each layer's installs get their own name.

A run that already landed on one branch: cut a branch at each ticket's last
commit (`git branch <slug>/0N-<ticket> <sha>`), then `gh stack init
<slug>/01-… <slug>/02-… …` adopts them in order.

## Fix a lower layer

A fix goes into the layer that owns the code — never a new layer or PR:

```bash
gh stack checkout <slug>/01-<ticket>    # or a PR number
# ... commit the fix ...
gh stack rebase --upstack               # replays every layer above
gh stack push                           # --force-with-lease for all layers
```

Conflict → resolve, `gh stack rebase --continue` (or `--abort`). `user-check`
fast fixes follow the same rule: each commits into the owning layer.
Restructuring (reorder, merge or drop layers) asks the user first:
`gh stack modify` is an interactive TUI only. The scripted alternative is
`gh stack unstack`, then `gh stack init` with the new branch order.

## Submit (open-pr §4)

```bash
gh stack submit --auto                  # push all layers, one draft PR each, auto titles
gh pr edit <N> --title "<t>" --body-file .scratch/<slug>/pr-<NN>.md   # per layer
gh stack view --short                   # confirm order and PR numbers
```

`--auto` creates **drafts**. Bodies are written once, after `user-check`
OK and a green `review-change`, per layer:

- **Bottom PR**: the run's Summary, Before/after and Diagram, plus a
  "Stack" line listing every layer PR in order.
- **Every layer**: one line on what this layer does, ≤3 Changes, ≤3 Check
  these (links into *this* PR's diff), Not verified. ≤ ~150 words.

## Merge (open-pr §5)

`gh stack merge` refuses drafts. Same consent rules as a single PR, then:

```bash
gh stack submit --open                  # mark every layer ready (or gh pr ready <N>)
gh stack merge --yes --merge            # atomic: all layers or none; or --squash | --rebase
gh stack sync --prune                   # fetch, fast-forward trunk, delete merged branches
```

`gh stack sync` aborts on a diverged branch in a non-interactive terminal:
rebase that layer by hand (`gh stack rebase`), then re-run it.
