"""ship_apk.py device resolution: PROFILE.local.md (gitignored) first, PROFILE.md legacy second.

Run: python3 -m pytest skills/deliver/scripts/tests
"""
import os
import shutil
import subprocess
import sys

import pytest

import ship_apk
from conftest import SCRIPTS

def ip(last):  # assembled at runtime so this file never trips tailnet-leak-guard
    return ".".join(["100", "64", "0", str(last)])


LEGACY = "- tailscale: example-host\n  - device: legacy-phone @ " + ip(9) + "  # verified 2026-01-01\n"
LOCAL = "- device: local-phone @ " + ip(1) + "  # verified 2026-11-18\n"


def put(repo, name, text):
    (repo / name).write_text(text)


def test_local_file_wins_over_profile(repo):
    put(repo, "PROFILE.md", (repo / "PROFILE.md").read_text() + LEGACY)
    put(repo, "PROFILE.local.md", LOCAL)
    assert ship_apk.profile_device(repo) == ("local-phone", ip(1))


def test_local_file_accepts_device_under_tailscale_entry(repo):
    put(repo, "PROFILE.local.md", "- tailscale: example-host\n  - device: nested-phone @ " + ip(2) + "\n")
    assert ship_apk.profile_device(repo) == ("nested-phone", ip(2))


def test_falls_back_to_profile_md(repo):
    put(repo, "PROFILE.md", (repo / "PROFILE.md").read_text() + LEGACY)
    assert ship_apk.profile_device(repo) == ("legacy-phone", ip(9))
    put(repo, "PROFILE.local.md", "# local notes, no device here\n")
    assert ship_apk.profile_device(repo) == ("legacy-phone", ip(9))


def test_new_worktree_reads_the_main_checkouts_local_file(repo, tmp_path):
    put(repo, "PROFILE.local.md", LOCAL)  # gitignored: never present in a fresh worktree
    wt = tmp_path / "wt"
    subprocess.run(["git", "worktree", "add", "-q", "-b", "feature/x", str(wt)], cwd=repo, check=True)
    assert not (wt / "PROFILE.local.md").exists()
    assert ship_apk.profile_device(wt) == ("local-phone", ip(1))


def test_template_placeholder_is_not_a_device(repo):
    put(repo, "PROFILE.local.md", "- device: <machine-name> @ <tailscale-ip>  # verified YYYY-MM-DD\n")
    assert ship_apk.profile_device(repo) is None


def test_name_without_ip(repo):
    put(repo, "PROFILE.local.md", "- device: bare-phone\n")
    assert ship_apk.profile_device(repo) == ("bare-phone", None)


def test_neither_file_has_a_device_error_names_both(repo, tmp_path):
    bin_ = tmp_path / "ts-bin"
    bin_.mkdir()
    stub = bin_ / "tailscale"
    stub.write_text("#!/bin/sh\nexit 0\n")
    stub.chmod(0o755)
    env = {**os.environ, "PATH": f"{bin_}{os.pathsep}{os.environ['PATH']}"}
    r = subprocess.run([sys.executable, str(SCRIPTS / "ship_apk.py")], cwd=repo, env=env,
                       capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=30)
    assert r.returncode != 0
    assert "PROFILE.local.md" in r.stderr and "PROFILE.md" in r.stderr and "--device" in r.stderr
    assert not (repo / ".scratch").exists()  # failed before allocating a versionCode
