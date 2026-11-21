"""claude_install.py round trip against a throwaway HOME.

Run: python3 -m pytest scripts/tests/test_claude_install.py
(or `uv run --with pytest python -m pytest scripts/tests/test_claude_install.py`).
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import claude_install  # noqa: E402

ORCA_GROUP = {"matcher": "*", "hooks": [{"type": "command", "command": "/orca/agent-hooks/claude-hook.sh"}]}
SUPERSET_GROUP = {"hooks": [{"type": "command", "command": "$SUPERSET_HOME_DIR/hooks/notify.sh"}]}


def snapshot_links(skills):
    return {p.name: os.readlink(p) for p in skills.iterdir() if p.is_symlink()}


def test_install_twice_then_uninstall_restores_the_original_home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(claude_install, "find_bun", lambda: "/opt/bun")
    claude = tmp_path / ".claude"
    skills = claude / "skills"
    skills.mkdir(parents=True)
    settings = {
        "model": "opus",
        "hooks": {"PreToolUse": [ORCA_GROUP], "UserPromptSubmit": [SUPERSET_GROUP]},
    }
    (claude / "settings.json").write_text(json.dumps(settings, indent=2))
    (skills / "implement").symlink_to("../../.agents/skills/implement")
    (skills / "unrelated").symlink_to("../../.agents/skills/unrelated")
    (skills / "tdd").mkdir()
    (skills / "tdd" / "SKILL.md").write_text("user's own tdd\n")
    (claude / "CLAUDE.md").write_text("# Mine\n\nKeep this.\n")
    links_before = snapshot_links(skills)

    claude_install.main(["install"])
    claude_install.main(["install"])

    installed = json.loads((claude / "settings.json").read_text())
    groups = installed["hooks"]["PreToolUse"]
    assert groups[0] == ORCA_GROUP
    assert installed["hooks"]["UserPromptSubmit"] == [SUPERSET_GROUP]
    assert len(groups) == 2 and groups[1]["matcher"] == "Bash"
    assert [h["command"] for h in groups[1]["hooks"]] == [
        "/opt/bun %s/hooks/claude/%s.ts" % (claude_install.REPO, name) for name in claude_install.HOOKS
    ]
    assert os.readlink(skills / "implement") == str(claude_install.REPO / "skills" / "implement")
    assert os.readlink(skills / "work-tickets") == str(claude_install.REPO / "skills" / "work-tickets")
    assert (skills / "tdd" / "SKILL.md").read_text() == "user's own tdd\n"
    assert os.readlink(skills / "unrelated") == "../../.agents/skills/unrelated"
    assert sorted(p.name for p in (claude / "agents").iterdir()) == [
        "goldfish.md", "reviewer.md", "scout.md", "security-reviewer.md", "sonic.md",
    ]
    note = (claude / "CLAUDE.md").read_text()
    assert note.startswith("# Mine\n\nKeep this.\n")
    assert note.count(claude_install.BLOCK_BEGIN) == 1 and "skill://<name>" in note

    claude_install.main(["uninstall"])

    assert json.loads((claude / "settings.json").read_text()) == settings
    assert snapshot_links(skills) == links_before
    assert (claude / "CLAUDE.md").read_text() == "# Mine\n\nKeep this.\n"
    assert not (claude / "agents").exists()
    assert not claude_install.state_path().exists()
    assert list(claude.glob("settings.json.pre-bots-*")), "every settings write leaves a backup"
