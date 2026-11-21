"""claude_install.py against a throwaway HOME, with the real claude/bots.json.

Run: python3 -m pytest scripts/tests/test_claude_install.py
(or `uv run --with pytest python -m pytest scripts/tests/test_claude_install.py`).
"""
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import claude_install  # noqa: E402

ORCA_GROUP = {"matcher": "*", "hooks": [{"type": "command", "command": "/orca/agent-hooks/claude-hook.sh"}]}
SUPERSET_GROUP = {"hooks": [{"type": "command", "command": "$SUPERSET_HOME_DIR/hooks/notify.sh"}]}
MANIFEST = claude_install.load_manifest()


def snapshot_links(skills):
    return {p.name: os.readlink(p) for p in skills.iterdir() if p.is_symlink()}


def dir_names(path):
    return sorted(p.name for p in path.iterdir())


@pytest.fixture
def home(tmp_path, monkeypatch):
    """A HOME with omp's ~/.agents/skills (third-party skills the manifest names), every bot
    but tester, and a ~/.claude like the one before the bots work."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(claude_install, "find_bun", lambda: "/opt/bun")
    repo_skills = {p.name for p in (claude_install.REPO / "skills").iterdir()}
    for name in sorted(claude_install.manifest_skill_names(MANIFEST) - repo_skills) + ["mole"]:
        (tmp_path / ".agents" / "skills" / name).mkdir(parents=True)
        (tmp_path / ".agents" / "skills" / name / "SKILL.md").write_text("---\nname: %s\n---\n" % name)
    for bot, spec in MANIFEST["bots"].items():
        if bot == "tester":
            continue
        folder = tmp_path / ".orca" / "bots" / bot
        (folder / ".claude").mkdir(parents=True)
        (folder / ".claude" / "settings.json").write_text(json.dumps(spec["settings"], indent=2) + "\n")
        (folder / "SOUL.md").write_text((claude_install.REPO / "claude" / "bots" / bot / "SOUL.md").read_text())
        (folder / "AGENTS.md").write_text("orca-owned\n")
    claude = tmp_path / ".claude"
    skills = claude / "skills"
    skills.mkdir(parents=True)
    (claude / "settings.json").write_text(json.dumps({
        "model": "opus",
        "skillOverrides": {"deploy": "name-only"},
        "hooks": {"PreToolUse": [ORCA_GROUP], "UserPromptSubmit": [SUPERSET_GROUP]},
    }, indent=2))
    (skills / "implement").symlink_to("../../.agents/skills/implement")
    (skills / "mole").symlink_to("../../.agents/skills/mole")
    (skills / "work-tickets").symlink_to("/old/checkout/skills/work-tickets")
    (skills / "wrangler").mkdir()
    (skills / "wrangler" / "SKILL.md").write_text("unmanaged\n")
    (skills / "synced").mkdir()
    (claude / "CLAUDE.md").write_text("# Mine\n\nKeep this.\n")
    return tmp_path


def test_install_scopes_skills_then_uninstall_restores_the_original_home(home, capsys):
    claude = home / ".claude"
    skills = claude / "skills"
    store = home / ".local" / "share" / "ivandsky-skills"
    settings_before = json.loads((claude / "settings.json").read_text())
    links_before = snapshot_links(skills)

    claude_install.main(["install"])
    claude_install.main(["install"])
    out = capsys.readouterr().out

    installed = json.loads((claude / "settings.json").read_text())
    groups = installed["hooks"]["PreToolUse"]
    assert groups[0] == ORCA_GROUP and installed["hooks"]["UserPromptSubmit"] == [SUPERSET_GROUP]
    assert [h["command"] for h in groups[1]["hooks"]] == [
        "/opt/bun %s/hooks/claude/%s.ts" % (store, name) for name in claude_install.HOOKS
    ]
    assert installed["syncClaudeAiSkills"] is False and installed["disableBundledSkills"] is True
    assert installed["skillOverrides"] == {"deploy": "name-only", "plugin-authoring": "off"}
    assert (store / "hooks" / "pre" / "worker-guard.ts").is_file(), "the hook adapter imports ../pre"

    # ~/.claude/skills: the shared set only, into the store; real dirs survive.
    assert sorted(snapshot_links(skills)) == sorted(MANIFEST["shared"])
    assert os.readlink(skills / "caveman") == str(store / "skills" / "caveman")
    assert (store / "skills" / "caveman" / "SKILL.md").is_file(), "omp-only skills resolve through the store"
    assert (store / "skills" / "goldfish-review" / "SKILL.md").is_file(), "skill:// works for uninstalled skills"
    assert (skills / "wrangler" / "SKILL.md").read_text() == "unmanaged\n"
    assert "wrangler is not a symlink" in out

    for bot, spec in MANIFEST["bots"].items():
        if bot == "tester":
            continue
        folder = home / ".orca" / "bots" / bot
        role = [s for s in spec["skills"] if s not in MANIFEST["shared"]]
        assert dir_names(folder / ".claude" / "skills") == sorted(role), bot
        assert json.loads((folder / ".claude" / "settings.json").read_text()) == spec["settings"]
    assert "tester: %s missing" % (home / ".orca" / "bots" / "tester") in out
    assert not (home / ".orca" / "bots" / "tester").exists()
    assert not list((home / ".orca" / "bots" / "lander").glob("**/*.pre-bots-*")), "unchanged files are not rewritten"

    assert sorted(p.name for p in (claude / "agents").iterdir()) == [
        "goldfish.md", "reviewer.md", "scout.md", "security-reviewer.md", "sonic.md",
    ]
    note = (claude / "CLAUDE.md").read_text()
    assert note.startswith("# Mine\n\nKeep this.\n") and note.count(claude_install.BLOCK_BEGIN) == 1

    claude_install.main(["uninstall"])

    assert json.loads((claude / "settings.json").read_text()) == settings_before
    assert snapshot_links(skills) == links_before
    assert (claude / "CLAUDE.md").read_text() == "# Mine\n\nKeep this.\n"
    assert not (claude / "agents").exists()
    assert not claude_install.state_path().exists()
    assert not store.exists()
    builder = home / ".orca" / "bots" / "builder"
    assert not (builder / ".claude" / "skills").exists()
    assert (builder / ".claude" / "settings.json").exists() and (builder / "SOUL.md").exists()


def test_bot_files_edited_by_hand_need_force_and_foreign_entries_stay(home, capsys):
    builder = home / ".orca" / "bots" / "builder"
    claude_install.main(["install"])
    settings = builder / ".claude" / "settings.json"
    edited = dict(MANIFEST["bots"]["builder"]["settings"], effortLevel="low")
    settings.write_text(json.dumps(edited, indent=2) + "\n")
    (builder / ".claude" / "skills" / "my-own").mkdir()
    stale = builder / ".claude" / "skills" / "deliver"
    stale.symlink_to(claude_install.store_link("deliver"))
    capsys.readouterr()

    claude_install.main(["status"])
    status = capsys.readouterr().out
    assert "bot builder: extra skills deliver, my-own; settings.json differs from the manifest" in status

    claude_install.main(["install"])
    out = capsys.readouterr().out
    assert json.loads(settings.read_text())["effortLevel"] == "low"
    assert "settings.json edited by hand; left alone" in out and '-  "effortLevel": "low"' in out
    assert not stale.is_symlink(), "our stale role link is removed"
    assert (builder / ".claude" / "skills" / "my-own").is_dir() and "extra, kept: my-own" in out

    claude_install.main(["install", "--force"])
    assert json.loads(settings.read_text()) == MANIFEST["bots"]["builder"]["settings"]
    assert list((builder / ".claude").glob("settings.json.pre-bots-*")), "--force backs the edit up first"


def test_manifest_change_rewrites_an_untouched_bot_file(home, monkeypatch):
    claude_install.main(["install"])
    changed = json.loads(json.dumps(MANIFEST))
    changed["bots"]["fixer"]["settings"]["effortLevel"] = "medium"
    monkeypatch.setattr(claude_install, "load_manifest", lambda root=None: changed)

    claude_install.main(["install"])

    settings = home / ".orca" / "bots" / "fixer" / ".claude" / "settings.json"
    assert json.loads(settings.read_text())["effortLevel"] == "medium"
