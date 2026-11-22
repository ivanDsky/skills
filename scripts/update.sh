#!/bin/sh
# Update every installed skill in one go; idempotent. Run it after `git pull` in this checkout.
#   1. omp: `npx skills update -g` refreshes ~/.agents/skills from each skill's source
#      (this repo's skills come from GitHub main there, the rest from their own repos).
#   2. Claude Code and the Orca bots: claude_install.py install re-copies this checkout into
#      ~/.local/share/ivandsky-skills and re-applies claude/bots.json to ~/.claude and
#      ~/.orca/bots/<bot>/. Extra arguments go to it (e.g. --force).
# SKIP_OMP=1 skips step 1.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
if [ "${SKIP_OMP:-0}" != 1 ]; then
  npx -y skills update -g -y
fi
python3 "$here/claude_install.py" install "$@"
python3 "$here/claude_install.py" status
