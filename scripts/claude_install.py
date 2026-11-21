#!/usr/bin/env python3
"""Install the skills, guard hooks, subagents, CLAUDE.md note and Orca bot setup into Claude Code.

Usage:
    python3 scripts/claude_install.py install [--force]   # idempotent; re-run after every git pull
    python3 scripts/claude_install.py status               # drift report, changes nothing
    python3 scripts/claude_install.py uninstall            # reverts what install changed

scripts/update.sh runs `npx skills update` (omp) and then this install.

Claude Code only. omp never reads ~/.claude, and nothing here writes ~/.agents/skills or ~/.omp.

Store. install copies this checkout's skills/, hooks/ and claude/ into
~/.local/share/ivandsky-skills (replacing the previous copy), and adds to store/skills a
symlink for every skill in ~/.agents/skills that this repo doesn't ship. store/skills is
then the full canonical skills dir: every link and hook below points into the store, so
removing or moving the checkout breaks nothing, and skill://<name> resolves there.

What install changes, and what uninstall reverts:
- ~/.claude/settings.json: one PreToolUse group (matcher Bash) running the four
  hooks/claude/*.ts entries with bun, recognised by their /hooks/claude/<hook>.ts command
  so other groups (Orca, Superset) are never touched; plus the manifest's user_settings
  keys (synced claude.ai skills, bundled skills and the built-in plugin-authoring skill off;
  object values are merged into the existing object). Each write first copies the file to
  settings.json.pre-bots-<timestamp>. Original key values are kept for uninstall.
- ~/.claude/agents/<name>.md: symlinks into store/claude/agents. A file that is not our
  symlink is left alone and reported.
- ~/.claude/skills: only the manifest's shared set, as symlinks into store/skills. Every
  other symlink is removed; real directories are left alone and reported. Original link
  targets go to ~/.claude/.skills-bots-install.json so uninstall restores them exactly.
- ~/.claude/CLAUDE.md: a marked block holding claude/CLAUDE.md.
- ~/.orca/bots/<bot>/ for each bot in claude/bots.json whose folder exists (a missing
  folder is reported, never created: bots are created in Orca):
  - .claude/skills/<skill>: symlinks into store/skills for the bot's role set. Our stale
    links are removed; anything else in that dir is kept and reported as extra.
  - .claude/settings.json from the manifest, and SOUL.md from claude/bots/<bot>/SOUL.md.
    A file that differs from the manifest and from what install last wrote was edited by
    hand: install prints the diff and overwrites it only with --force (after a backup).
    Uninstall leaves both files in place.
"""
import argparse
import difflib
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
STORE_PARTS = ("skills", "hooks", "claude")
COPY_IGNORE = shutil.ignore_patterns("__pycache__", ".DS_Store", "node_modules", ".pytest_cache")
HOOKS = ("build-queue", "worker-guard", "apk-ship-guard", "tailnet-leak-guard")
HOOK_MARK = "/hooks/claude/"
HOOK_TIMEOUT_S = 30
BLOCK_BEGIN = "<!-- skills-bots:begin -->"
BLOCK_END = "<!-- skills-bots:end -->"
SETTINGS_FILE = "settings.json"
SOUL_FILE = "SOUL.md"


def home():
    return Path(os.path.expanduser("~"))


def claude_dir():
    return home() / ".claude"


def store():
    return home() / ".local" / "share" / "ivandsky-skills"


def agents_skills():
    return home() / ".agents" / "skills"


def bots_dir():
    return home() / ".orca" / "bots"


def state_path():
    return claude_dir() / ".skills-bots-install.json"


def load_manifest(root=REPO):
    return json.loads((root / "claude" / "bots.json").read_text())


def find_bun():
    found = shutil.which("bun")
    if found:
        return str(Path(found).resolve())
    fallback = home() / ".bun" / "bin" / "bun"
    if fallback.is_file():
        return str(fallback)
    sys.exit("bun not found on PATH or at ~/.bun/bin/bun; the hooks need it")


def load_json(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def load_state():
    state = load_json(state_path(), {})
    state.setdefault("skills", {})
    state.setdefault("user_settings", {})
    state.setdefault("bots", {})
    return state


def save_state(state):
    state_path().parent.mkdir(parents=True, exist_ok=True)
    state_path().write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def backup(path):
    if path.exists():
        shutil.copy2(path, path.with_name("%s.pre-bots-%s" % (path.name, time.strftime("%Y%m%d-%H%M%S"))))


def canonical_skills():
    """Skill name -> source dir: this repo's skills, then the rest of ~/.agents/skills."""
    found = {p.name: p for p in sorted((REPO / "skills").iterdir()) if (p / "SKILL.md").is_file()}
    if agents_skills().is_dir():
        for p in sorted(agents_skills().iterdir()):
            if p.name not in found and (p / "SKILL.md").is_file():
                found[p.name] = p
    return found


def manifest_skill_names(manifest):
    names = set(manifest["shared"])
    for spec in manifest["bots"].values():
        names.update(spec["skills"])
    return names


def check_manifest(manifest, available):
    unknown = sorted(manifest_skill_names(manifest) - set(available))
    if unknown:
        sys.exit("claude/bots.json names skills that exist neither in skills/ nor in %s: %s"
                 % (agents_skills(), ", ".join(unknown)))


# --- store -----------------------------------------------------------------

def git_commit():
    try:
        out = subprocess.run(["git", "-C", str(REPO), "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def sync_store(available):
    root = store()
    root.mkdir(parents=True, exist_ok=True)
    for part in STORE_PARTS:
        fresh = root / (".%s.new" % part)
        stale = root / (".%s.old" % part)
        for leftover in (fresh, stale):
            if leftover.exists():
                shutil.rmtree(leftover)
        shutil.copytree(REPO / part, fresh, symlinks=True, ignore=COPY_IGNORE)
        if part == "skills":
            for name, src in available.items():
                if not (fresh / name).exists():
                    (fresh / name).symlink_to(src)
        current = root / part
        if current.exists():
            current.rename(stale)
        fresh.rename(current)
        if stale.exists():
            shutil.rmtree(stale)
    source = {"repo": str(REPO), "commit": git_commit(), "installed": time.strftime("%Y-%m-%d %H:%M:%S")}
    (root / "source.json").write_text(json.dumps(source, indent=2) + "\n")
    print("store: %s <- %s (%s), %d skills" % (root, REPO, source["commit"], len(available)))


def store_link(name):
    return store() / "skills" / name


def is_store_link(path):
    return path.is_symlink() and os.readlink(path) == str(store_link(path.name))


# --- ~/.claude/settings.json ------------------------------------------------

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
    backup(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n")


def install_settings(bun, manifest, state):
    path = claude_dir() / SETTINGS_FILE
    settings = load_json(path, {})
    before = json.dumps(settings, sort_keys=True)
    strip_our_hooks(settings)
    group = {
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": "%s %s" % (bun, store() / "hooks" / "claude" / ("%s.ts" % h)),
                "timeout": HOOK_TIMEOUT_S,
            }
            for h in HOOKS
        ],
    }
    settings.setdefault("hooks", {}).setdefault("PreToolUse", []).append(group)
    originals = state["user_settings"]
    for key, value in manifest.get("user_settings", {}).items():
        if key not in originals:
            originals[key] = {"present": key in settings, "value": settings.get(key)}
        settings[key] = merged_setting(settings.get(key), value)
    if json.dumps(settings, sort_keys=True) != before:
        write_settings(path, settings)
    print("settings: %d PreToolUse Bash hooks, %s -> %s"
          % (len(HOOKS), ", ".join(sorted(manifest.get("user_settings", {}))), path))


def merged_setting(current, value):
    return dict(current, **value) if isinstance(current, dict) and isinstance(value, dict) else value


def uninstall_settings(state):
    path = claude_dir() / SETTINGS_FILE
    settings = load_json(path, {})
    before = json.dumps(settings, sort_keys=True)
    strip_our_hooks(settings)
    for key, original in state["user_settings"].items():
        if original["present"]:
            settings[key] = original["value"]
        else:
            settings.pop(key, None)
    if json.dumps(settings, sort_keys=True) != before:
        write_settings(path, settings)
        print("settings: hooks and user settings reverted in %s" % path)


# --- ~/.claude/agents --------------------------------------------------------

def is_our_agent(dest):
    return dest.is_symlink() and os.readlink(dest).endswith("/claude/agents/" + dest.name)


def install_agents():
    src_dir = store() / "claude" / "agents"
    dest_dir = claude_dir() / "agents"
    dest_dir.mkdir(parents=True, exist_ok=True)
    for src in sorted(src_dir.glob("*.md")):
        dest = dest_dir / src.name
        if is_our_agent(dest):
            if os.readlink(dest) == str(src):
                continue
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
        if is_our_agent(dest):
            dest.unlink()
            print("agents: removed %s" % dest)
    if not any(dest_dir.iterdir()):
        dest_dir.rmdir()


# --- ~/.claude/skills (shared set) -------------------------------------------

def is_claude_owned(name):
    """Entries Claude Code itself manages in ~/.claude/skills (synced claude.ai skills, trash)."""
    return name.startswith(".") or name.lower() == "synced"


def install_shared(manifest, state):
    originals = state["skills"]
    dest_dir = claude_dir() / "skills"
    dest_dir.mkdir(parents=True, exist_ok=True)
    shared = set(manifest["shared"])
    removed = []
    for dest in sorted(dest_dir.iterdir()):
        if dest.name in shared or is_claude_owned(dest.name):
            continue
        if dest.is_symlink():
            originals.setdefault(dest.name, os.readlink(dest))
            dest.unlink()
            removed.append(dest.name)
        else:
            print("skills: %s is not a symlink; left alone (remove it by hand if it should go)" % dest)
    for name in manifest["shared"]:
        dest = dest_dir / name
        if dest.exists() and not dest.is_symlink():
            print("skills: %s is a real directory; left alone" % dest)
            continue
        originals.setdefault(name, os.readlink(dest) if dest.is_symlink() else None)
        if is_store_link(dest):
            continue
        if dest.is_symlink():
            dest.unlink()
        dest.symlink_to(store_link(name))
    print("skills: %d shared in %s%s" % (len(shared), dest_dir,
                                         "; removed %s" % ", ".join(removed) if removed else ""))


def uninstall_shared(state):
    dest_dir = claude_dir() / "skills"
    for name, original in sorted(state["skills"].items()):
        dest = dest_dir / name
        if dest.exists() and not dest.is_symlink():
            print("skills: %s became a real directory; left alone" % dest)
            continue
        if dest.is_symlink():
            dest.unlink()
        if original is not None:
            dest.symlink_to(original)
    if state["skills"]:
        print("skills: original links restored in %s" % dest_dir)


# --- ~/.claude/CLAUDE.md -----------------------------------------------------

def without_block(text):
    start = text.find(BLOCK_BEGIN)
    end = text.find(BLOCK_END)
    if start < 0 or end < start:
        return text
    return (text[:start].rstrip("\n") + "\n\n" + text[end + len(BLOCK_END):].lstrip("\n")).strip("\n")


def install_note():
    path = claude_dir() / "CLAUDE.md"
    current = path.read_text() if path.exists() else ""
    rest = without_block(current)
    note = (store() / "claude" / "CLAUDE.md").read_text().strip("\n")
    block = "%s\n%s\n%s" % (BLOCK_BEGIN, note, BLOCK_END)
    text = (rest + "\n\n" if rest.strip() else "") + block + "\n"
    if text != current:
        path.write_text(text)
    print("note: block in %s" % path)


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


# --- Orca bots ---------------------------------------------------------------

def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def desired_files(bot, spec, root):
    """File name -> manifest content for one bot."""
    files = {SETTINGS_FILE: json.dumps(spec["settings"], indent=2, ensure_ascii=False) + "\n"}
    soul = root / "claude" / "bots" / bot / SOUL_FILE
    if soul.is_file():
        files[SOUL_FILE] = soul.read_text()
    return files


def bot_file_path(folder, name):
    return folder / ".claude" / name if name == SETTINGS_FILE else folder / name


def same_content(name, current, wanted):
    if name == SETTINGS_FILE:
        try:
            return json.loads(current) == json.loads(wanted)
        except ValueError:
            return False
    return current == wanted


def show_diff(path, current, wanted):
    diff = difflib.unified_diff(current.splitlines(True), wanted.splitlines(True),
                                str(path), "manifest", n=2)
    sys.stdout.writelines("    " + line if line.endswith("\n") else "    " + line + "\n" for line in diff)


def sync_bot_skills(folder, wanted):
    dest_dir = folder / ".claude" / "skills"
    dest_dir.mkdir(parents=True, exist_ok=True)
    extra = []
    for dest in sorted(dest_dir.iterdir()):
        if dest.name in wanted:
            continue
        if is_store_link(dest):
            dest.unlink()
        elif not is_claude_owned(dest.name):
            extra.append(dest.name)
    for name in wanted:
        dest = dest_dir / name
        if is_store_link(dest):
            continue
        if dest.exists() and not dest.is_symlink():
            extra.append(name + " (real dir, not linked)")
            continue
        if dest.is_symlink():
            dest.unlink()
        dest.symlink_to(store_link(name))
    return extra


def install_bots(manifest, state, force):
    for bot, spec in manifest["bots"].items():
        folder = bots_dir() / bot
        if not folder.is_dir():
            print("bot %s: %s missing; create the bot in Orca, then re-run install" % (bot, folder))
            continue
        wanted = list(dict.fromkeys(s for s in spec["skills"] if s not in manifest["shared"]))
        extra = sync_bot_skills(folder, wanted)
        hashes = state["bots"].setdefault(bot, {})
        notes = []
        for name, content in desired_files(bot, spec, store()).items():
            path = bot_file_path(folder, name)
            current = path.read_text() if path.exists() else None
            if current is not None and same_content(name, current, content):
                hashes[name] = sha256(current)
                continue
            if current is not None and hashes.get(name) != sha256(current) and not force:
                notes.append("%s edited by hand; left alone (--force overwrites)" % name)
                show_diff(path, current, content)
                continue
            if current is not None:
                backup(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            hashes[name] = sha256(content)
            notes.append("%s written" % name)
        if extra:
            notes.append("extra, kept: %s" % ", ".join(extra))
        print("bot %s: %d role skills%s" % (bot, len(wanted), "; " + "; ".join(notes) if notes else ""))


def uninstall_bots(manifest, state):
    for bot in sorted(set(manifest["bots"]) | set(state["bots"])):
        dest_dir = bots_dir() / bot / ".claude" / "skills"
        if not dest_dir.is_dir():
            continue
        for dest in sorted(dest_dir.iterdir()):
            if is_store_link(dest):
                dest.unlink()
        if not any(dest_dir.iterdir()):
            dest_dir.rmdir()
        print("bot %s: skill links removed (settings.json and SOUL.md kept)" % bot)


# --- commands ----------------------------------------------------------------

def install(force):
    manifest = load_manifest()
    available = canonical_skills()
    check_manifest(manifest, available)
    bun = find_bun()
    sync_store(available)
    state = load_state()
    install_settings(bun, manifest, state)
    install_agents()
    install_shared(manifest, state)
    install_note()
    install_bots(manifest, state, force)
    save_state(state)


def uninstall():
    state = load_state()
    uninstall_settings(state)
    uninstall_agents()
    uninstall_shared(state)
    uninstall_note()
    uninstall_bots(load_manifest(), state)
    if state_path().exists():
        state_path().unlink()
    if store().exists():
        shutil.rmtree(store())
        print("store: removed %s" % store())


def status():
    manifest = load_manifest()
    available = canonical_skills()
    unknown = sorted(manifest_skill_names(manifest) - set(available))
    if unknown:
        print("manifest: unknown skills %s" % ", ".join(unknown))
    source = load_json(store() / "source.json", None)
    print("store: %s" % ("%s <- %s (%s, %s)" % (store(), source["repo"], source["commit"], source["installed"])
                         if source else "not installed"))
    settings = load_json(claude_dir() / SETTINGS_FILE, {})
    hooks = [e["command"] for g in settings.get("hooks", {}).get("PreToolUse", [])
             for e in g.get("hooks", []) if is_our_hook(e)]
    in_store = sum(str(store()) in c for c in hooks)
    print("hooks: %d installed, %d into the store" % (len(hooks), in_store))
    for key, value in manifest.get("user_settings", {}).items():
        current = settings.get(key)
        print("settings: %s=%s%s" % (key, json.dumps(current), "" if merged_setting(current, value) == current
                                      else " (manifest: %s)" % json.dumps(value)))
    agents_dir = claude_dir() / "agents"
    agents = [p.name for p in sorted(agents_dir.iterdir()) if is_our_agent(p)] if agents_dir.is_dir() else []
    print("agents: %s" % (", ".join(agents) or "none"))
    skills_dir = claude_dir() / "skills"
    entries = sorted(skills_dir.iterdir()) if skills_dir.is_dir() else []
    missing = [n for n in manifest["shared"] if not is_store_link(skills_dir / n)]
    extra = [p.name for p in entries if p.name not in manifest["shared"] and not is_claude_owned(p.name)]
    print("skills: %d of %d shared linked%s%s" % (
        len(manifest["shared"]) - len(missing), len(manifest["shared"]),
        "; missing %s" % ", ".join(missing) if missing else "",
        "; extra %s" % ", ".join(extra) if extra else ""))
    note = claude_dir() / "CLAUDE.md"
    print("note: %s" % ("installed" if note.exists() and BLOCK_BEGIN in note.read_text() else "absent"))
    for bot, spec in manifest["bots"].items():
        folder = bots_dir() / bot
        if not folder.is_dir():
            print("bot %s: folder missing" % bot)
            continue
        wanted = [s for s in spec["skills"] if s not in manifest["shared"]]
        dest_dir = folder / ".claude" / "skills"
        have = sorted(dest_dir.iterdir()) if dest_dir.is_dir() else []
        drift = []
        lacking = [n for n in wanted if not is_store_link(dest_dir / n)]
        surplus = [p.name for p in have if p.name not in wanted and not is_claude_owned(p.name)]
        if lacking:
            drift.append("missing skills %s" % ", ".join(lacking))
        if surplus:
            drift.append("extra skills %s" % ", ".join(surplus))
        for name, content in desired_files(bot, spec, REPO).items():
            path = bot_file_path(folder, name)
            if not path.exists():
                drift.append("%s missing" % name)
            elif not same_content(name, path.read_text(), content):
                drift.append("%s differs from the manifest" % name)
        print("bot %s: %s" % (bot, "; ".join(drift) if drift else "in sync (%d role skills)" % len(wanted)))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("command", choices=("install", "uninstall", "status"))
    parser.add_argument("--force", action="store_true",
                        help="install: overwrite bot settings.json / SOUL.md edited by hand")
    args = parser.parse_args(argv)
    if args.command == "install":
        install(args.force)
    elif args.command == "uninstall":
        uninstall()
    else:
        status()
    return 0


if __name__ == "__main__":
    sys.exit(main())
