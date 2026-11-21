#!/usr/bin/env python3
"""Install this checkout's skills, guard hooks, subagents and CLAUDE.md note into ~/.claude.

Usage:
    python3 scripts/claude_install.py install     # idempotent; re-run after moving the checkout
    python3 scripts/claude_install.py uninstall   # restores everything install changed
    python3 scripts/claude_install.py status

Claude Code only. omp never reads ~/.claude (skills.enableClaudeUser is off and no
provider is enabled), and nothing here touches ~/.agents/skills or ~/.omp.

What install changes, and what uninstall reverts:
- ~/.claude/settings.json: one PreToolUse group (matcher Bash) running the four
  hooks/claude/*.ts entries with bun. Our entries are recognised by their
  /hooks/claude/<hook>.ts command, so the other groups (Orca, Superset) are never
  touched. Each write first copies the file to settings.json.pre-bots-<timestamp>.
- ~/.claude/agents/<name>.md: symlinks into claude/agents/. An existing file that is
  not our symlink is left alone and reported.
- ~/.claude/skills/<name>: every symlink whose name is a skill in this repo is
  repointed at skills/<name>; missing ones are created. Real directories are left
  alone. The original targets go to ~/.claude/.skills-bots-install.json so
  uninstall restores them exactly.
- ~/.claude/CLAUDE.md: a marked block holding claude/CLAUDE.md. Uninstall removes
  the block, and the file when nothing else is left in it.
"""
import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HOOKS = ("build-queue", "worker-guard", "apk-ship-guard", "tailnet-leak-guard")
HOOK_MARK = "/hooks/claude/"
HOOK_TIMEOUT_S = 30
BLOCK_BEGIN = "<!-- skills-bots:begin -->"
BLOCK_END = "<!-- skills-bots:end -->"


def claude_dir():
    return Path(os.path.expanduser("~")) / ".claude"


def state_path():
    return claude_dir() / ".skills-bots-install.json"


def find_bun():
    found = shutil.which("bun")
    if found:
        return str(Path(found).resolve())
    fallback = Path(os.path.expanduser("~")) / ".bun" / "bin" / "bun"
    if fallback.is_file():
        return str(fallback)
    sys.exit("bun not found on PATH or at ~/.bun/bin/bun; the hooks need it")


def is_our_hook(entry):
    command = entry.get("command", "") if isinstance(entry, dict) else ""
    return HOOK_MARK in command and any(command.endswith("/%s.ts" % h) for h in HOOKS)


def strip_our_hooks(settings):
    """Drop our hook entries (and groups they leave empty); report whether any were found."""
    hooks = settings.get("hooks", {})
    groups = hooks.get("PreToolUse", [])
    kept, found = [], False
    for group in groups:
        entries = group.get("hooks", [])
        rest = [e for e in entries if not is_our_hook(e)]
        if len(rest) != len(entries):
            found = True
            if not rest:
                continue
            group = dict(group, hooks=rest)
        kept.append(group)
    if not found:
        return False
    if kept:
        hooks["PreToolUse"] = kept
    else:
        hooks.pop("PreToolUse", None)
    if not hooks:
        settings.pop("hooks", None)
    return True


def write_settings(path, settings):
    if path.exists():
        backup = path.with_name("%s.pre-bots-%s" % (path.name, time.strftime("%Y%m%d-%H%M%S")))
        shutil.copy2(path, backup)
    path.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n")


def load_settings(path):
    return json.loads(path.read_text()) if path.exists() else {}


def install_hooks(bun):
    path = claude_dir() / "settings.json"
    settings = load_settings(path)
    before = json.dumps(settings, sort_keys=True)
    strip_our_hooks(settings)
    group = {
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": "%s %s" % (bun, REPO / "hooks" / "claude" / ("%s.ts" % h)),
                "timeout": HOOK_TIMEOUT_S,
            }
            for h in HOOKS
        ],
    }
    settings.setdefault("hooks", {}).setdefault("PreToolUse", []).append(group)
    if json.dumps(settings, sort_keys=True) != before:
        write_settings(path, settings)
    print("hooks: %d PreToolUse Bash hooks -> %s" % (len(HOOKS), path))


def uninstall_hooks():
    path = claude_dir() / "settings.json"
    settings = load_settings(path)
    if strip_our_hooks(settings):
        write_settings(path, settings)
        print("hooks: removed from %s" % path)


def points_into(link, root):
    """True for a symlink whose final target lies inside root (Path.is_relative_to: Python 3.9+)."""
    return link.is_symlink() and Path(os.path.realpath(link)).is_relative_to(root.resolve())


def install_agents():
    src_dir = REPO / "claude" / "agents"
    dest_dir = claude_dir() / "agents"
    dest_dir.mkdir(parents=True, exist_ok=True)
    for src in sorted(src_dir.glob("*.md")):
        dest = dest_dir / src.name
        if dest.is_symlink() and points_into(dest, src_dir):
            dest.unlink()
        elif dest.exists() or dest.is_symlink():
            print("agents: %s exists and is not ours; left alone" % dest)
            continue
        dest.symlink_to(src)
        print("agents: %s -> %s" % (dest, src))


def uninstall_agents():
    dest_dir = claude_dir() / "agents"
    if not dest_dir.is_dir():
        return
    for dest in sorted(dest_dir.iterdir()):
        if points_into(dest, REPO / "claude" / "agents"):
            dest.unlink()
            print("agents: removed %s" % dest)
    if not any(dest_dir.iterdir()):
        dest_dir.rmdir()


def load_state():
    path = state_path()
    return json.loads(path.read_text()) if path.exists() else {"skills": {}}


def repo_skills():
    return sorted(p.name for p in (REPO / "skills").iterdir() if (p / "SKILL.md").is_file())


def install_skills():
    state = load_state()
    originals = state["skills"]
    dest_dir = claude_dir() / "skills"
    dest_dir.mkdir(parents=True, exist_ok=True)
    changed = 0
    for name in repo_skills():
        dest = dest_dir / name
        target = REPO / "skills" / name
        if dest.exists() and not dest.is_symlink():
            print("skills: %s is a real directory; left alone" % dest)
            continue
        if name not in originals:
            originals[name] = os.readlink(dest) if dest.is_symlink() else None
        if dest.is_symlink():
            if os.readlink(dest) == str(target):
                continue
            dest.unlink()
        dest.symlink_to(target)
        changed += 1
    state_path().write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
    print("skills: %d linked to %s (%d changed)" % (len(originals), REPO / "skills", changed))


def uninstall_skills():
    path = state_path()
    if not path.exists():
        return
    dest_dir = claude_dir() / "skills"
    for name, original in sorted(load_state()["skills"].items()):
        dest = dest_dir / name
        if dest.exists() and not dest.is_symlink():
            print("skills: %s became a real directory; left alone" % dest)
            continue
        if dest.is_symlink():
            dest.unlink()
        if original is not None:
            dest.symlink_to(original)
    path.unlink()
    print("skills: original links restored")


def without_block(text):
    start = text.find(BLOCK_BEGIN)
    end = text.find(BLOCK_END)
    if start < 0 or end < start:
        return text
    return (text[:start].rstrip("\n") + "\n\n" + text[end + len(BLOCK_END):].lstrip("\n")).strip("\n")


def install_note():
    path = claude_dir() / "CLAUDE.md"
    rest = without_block(path.read_text()) if path.exists() else ""
    note = (REPO / "claude" / "CLAUDE.md").read_text().strip("\n")
    block = "%s\n%s\n%s" % (BLOCK_BEGIN, note, BLOCK_END)
    path.write_text((rest + "\n\n" if rest.strip() else "") + block + "\n")
    print("note: block written to %s" % path)


def uninstall_note():
    path = claude_dir() / "CLAUDE.md"
    if not path.exists() or BLOCK_BEGIN not in path.read_text():
        return
    rest = without_block(path.read_text())
    if rest.strip():
        path.write_text(rest + "\n")
    else:
        path.unlink()
    print("note: block removed from %s" % path)


def status():
    settings = load_settings(claude_dir() / "settings.json")
    hooks = [e["command"] for g in settings.get("hooks", {}).get("PreToolUse", [])
             for e in g.get("hooks", []) if is_our_hook(e)]
    print("hooks: %d installed" % len(hooks))
    for command in hooks:
        print("  " + command)
    agents_dir = claude_dir() / "agents"
    agents = [p.name for p in sorted(agents_dir.iterdir())
              if points_into(p, REPO / "claude" / "agents")] if agents_dir.is_dir() else []
    print("agents: %s" % (", ".join(agents) or "none"))
    skills_dir = claude_dir() / "skills"
    ours = [n for n in repo_skills() if points_into(skills_dir / n, REPO / "skills")]
    print("skills: %d of %d linked to this checkout" % (len(ours), len(repo_skills())))
    note = claude_dir() / "CLAUDE.md"
    print("note: %s" % ("installed" if note.exists() and BLOCK_BEGIN in note.read_text() else "absent"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("command", choices=("install", "uninstall", "status"))
    args = parser.parse_args(argv)
    if args.command == "install":
        install_hooks(find_bun())
        install_agents()
        install_skills()
        install_note()
    elif args.command == "uninstall":
        uninstall_hooks()
        uninstall_agents()
        uninstall_skills()
        uninstall_note()
    else:
        status()
    return 0


if __name__ == "__main__":
    sys.exit(main())
