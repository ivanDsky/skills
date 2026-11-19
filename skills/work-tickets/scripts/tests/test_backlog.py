import json
import os
import subprocess
import time
from pathlib import Path

import pytest

import backlog
from conftest import HERE, Backlog, make_repo


def claim_ids(b, *args):
    p = b.run("claim", "--as", "w", *args, check=False)
    return [l.split("\t")[0] for l in p.stdout.splitlines()], p.returncode


# ---------------------------------------------------------------- local backend

def test_local_backlog_is_shared_by_every_worktree(local, repo, tmp_path):
    tid = local.new("Score resets after rotation")
    wt = tmp_path / "wt"
    subprocess.run(["git", "worktree", "add", "-q", str(wt)], cwd=repo, check=True)
    other = Backlog(wt, {"BACKLOG_BACKEND": "local"})
    assert other.json("show", tid)["title"] == "Score resets after rotation"
    assert list((repo / ".git" / "backlog" / "tickets").glob(f"{tid}-*.md"))


def test_frontier_skips_blocked_and_orders_by_priority(local):
    a = local.new("Parent")
    b = local.new("Child", "leaderboard", "bug", "--blocked-by", a)
    c = local.new("Urgent", "leaderboard", "bug", "--priority", "p1")
    d = local.new("Other area", "sync")
    ids = [t["id"] for t in local.json("list", "--frontier", "--area", "leaderboard")]
    assert ids == [c, a]
    local.run("set", a, "--state", "done", "--note", "PR #1 merged")
    ids = [t["id"] for t in local.json("list", "--frontier")]
    assert ids == [c, b, d]


def test_claim_takes_a_capped_pack_and_never_the_same_ticket_twice(local):
    made = [local.new(f"Bug {i}") for i in range(7)]
    first, rc1 = claim_ids(local, "--area", "leaderboard", "--max", "5")
    second, rc2 = claim_ids(local, "--area", "leaderboard", "--max", "5")
    third, rc3 = claim_ids(local, "--area", "leaderboard")
    assert (len(first), len(second), third) == (5, 2, [])
    assert sorted(first + second) == sorted(made)
    assert (rc1, rc2, rc3) == (0, 0, 3)
    t = local.json("show", first[0])
    assert (t["state"], t["claimed_by"]) == ("claimed", "w")


def test_parallel_claims_partition_the_frontier(local):
    made = {local.new(f"Bug {i}") for i in range(12)}
    procs = [local.popen("claim", "--as", f"w{i}", "--max", "5") for i in range(4)]
    got = []
    for p in procs:
        out, err = p.communicate(timeout=60)
        assert p.returncode in (0, 3), err
        got += [l.split("\t")[0] for l in out.splitlines()]
    assert len(got) == len(set(got)) == 12
    assert set(got) == made


def test_claim_by_ids_only_takes_ready_ones(local):
    a, b = local.new("A"), local.new("B", "leaderboard", "bug", "--state", "needs-info")
    got, _ = claim_ids(local, "--ids", f"{a},{b}")
    assert got == [a]


def test_unclaim_returns_ticket_to_the_pool(local):
    a = local.new("A")
    claim_ids(local)
    local.run("unclaim", a, "--note", "needs a device I lack")
    t = local.json("show", a)
    assert (t["state"], t["claimed_by"]) == ("ready-for-agent", "")
    assert "needs a device I lack" in t["body"]
    assert local.run("unclaim", a, "--note", "x", check=False).returncode == 1


def test_done_ticket_shows_in_release_notes_query(local):
    a, b = local.new("Shipped"), local.new("Not yet")
    claim_ids(local)
    local.run("set", a, "--state", "needs-check", "--note", "PR #4 merged")
    assert local.json("show", a)["claimed_by"] == "w"
    local.run("set", a, "--state", "done", "--note", "user OK on build 412")
    today = time.strftime("%Y-%m-%d", time.gmtime())
    assert [t["id"] for t in local.json("list", "--state", "done", "--closed-since", today)] == [a]
    assert [t["id"] for t in local.json("list")] == [b]


def test_search_finds_duplicates_across_closed(local):
    a = local.new("Leaderboard score resets after rotation")
    local.run("set", a, "--state", "wontfix", "--note", "dup")
    assert local.json("list", "--search", "rotation score") == []
    assert [t["id"] for t in local.json("list", "--all", "--search", "rotation score")] == [a]


def test_title_with_colon_and_quotes_round_trips(local):
    a = local.new('Crash: "Strands" editor on save')
    assert local.json("show", a)["title"] == 'Crash: "Strands" editor on save'


def test_attach_copies_screenshot_next_to_backlog(local, tmp_path):
    shot = tmp_path / "shot.png"
    shot.write_bytes(b"\x89PNG")
    a = local.out("new", "--title", "Glitch", "--type", "bug", "--area", "ui", "--body-file", "-",
                  "--attach", str(shot), input="brief")
    t = local.json("show", a)
    kept = [w for w in t["body"].split() if w.endswith("shot.png")]
    assert kept and Path(kept[0].rstrip(",")).read_bytes() == b"\x89PNG"


def test_lock_held_by_dead_pid_is_broken(local, repo):
    lock = repo / ".git" / "backlog" / ".lock"
    lock.mkdir()
    (lock / "pid").write_text("999999")
    local.new("A")
    assert not lock.exists()


def test_lock_held_by_live_owner_is_respected(local, repo, monkeypatch):
    lock = repo / ".git" / "backlog" / ".lock"
    lock.mkdir()
    (lock / "pid").write_text(str(os.getpid()))
    monkeypatch.setattr(backlog, "LOCK_WAIT_S", 0.3)
    with pytest.raises(backlog.Fail, match="locked"):
        with backlog.Lock(lock):
            pass
    assert lock.exists()


def test_profile_tracker_section_selects_backend(tmp_path, gh):
    r = make_repo(tmp_path / "p", {"PROFILE.md": "# P\n\n## Tracker            # shared backlog\n"
                                                 "- backend: github   # github | local\n- repo: o/r\n\n"
                                                 "## Delivery\n- backend: local\n"})
    b = Backlog(r, {})
    b.run("init")
    assert "state:ready-for-agent" in gh.state()["labels"]


def test_missing_profile_defaults_to_local(repo):
    b = Backlog(repo, {})
    assert "local backlog" in b.out("init")


# ---------------------------------------------------------------- github backend

def test_github_new_encodes_fields_as_labels(github, gh):
    a = github.new("Parent")
    b = github.new("Child", "sync", "enhancement", "--blocked-by", a, "--hands-on", "--epic", "streaks")
    assert (a, b) == ("#1", "#2")
    assert gh.labels(2) == ["area:sync", "epic:streaks", "hands-on", "p2",
                            "state:ready-for-agent", "type:enhancement"]
    t = github.json("show", "2")
    assert (t["blocked_by"], t["area"], t["hands_on"]) == (["#1"], "sync", True)
    assert "Blocked by: #1" in gh.issue(2)["body"]


def test_github_claim_flips_state_label_and_records_claimer(github, gh):
    a = github.new("A")
    got, _ = claim_ids(github)
    assert got == [a]
    assert "state:claimed" in gh.labels(1) and "state:ready-for-agent" not in gh.labels(1)
    assert github.json("show", a)["claimed_by"] == "w"
    assert any("claimed by w" in c for c in gh.issue(1)["comments"])


def test_github_parallel_claims_partition_the_frontier(github):
    made = {github.new(f"Bug {i}") for i in range(8)}
    procs = [github.popen("claim", "--as", f"w{i}", "--max", "3") for i in range(4)]
    got = []
    for p in procs:
        out, err = p.communicate(timeout=120)
        assert p.returncode in (0, 3), err
        got += [l.split("\t")[0] for l in out.splitlines()]
    assert len(got) == len(set(got)) == 8 and set(got) == made


def test_github_done_closes_and_wontfix_closes_not_planned(github, gh):
    a, b = github.new("A"), github.new("B")
    github.run("set", a, "--state", "done", "--note", "PR #9 merged")
    github.run("set", b, "--state", "wontfix", "--note", "duplicate of #1")
    assert (gh.issue(1)["state"], gh.issue(1)["reason"]) == ("CLOSED", "completed")
    assert (gh.issue(2)["state"], gh.issue(2)["reason"]) == ("CLOSED", "not planned")
    github.run("set", a, "--state", "ready-for-agent", "--note", "regressed")
    assert gh.issue(1)["state"] == "OPEN"


def test_real_gh_issue_json_parses():
    rows = json.loads((HERE / "fixtures" / "gh_issue_list.json").read_text())
    ts = [backlog.GitHub("cli/cli").from_issue(r) for r in rows]
    assert ts[0]["id"] == "#15066" and ts[0]["state"] == "ready-for-agent"
    closed = [t for t in ts if t["closed_at"]]
    assert closed and all(t["state"] == "done" for t in closed)


# ---------------------------------------------------------------- series hold

def test_series_claim_holds_same_area_feature_tickets(local):
    s1 = local.new("Move packages 1", "core", "task", "--series", "move-core")
    feat = local.new("Feature in core", "core", "enhancement")
    other = local.new("Feature elsewhere", "sync", "enhancement")
    got, _ = claim_ids(local, "--ids", s1)
    assert got == [s1]
    p = local.run("claim", "--as", "w", check=False)
    assert [l.split("\t")[0] for l in p.stdout.splitlines()] == [other]
    assert f"skipped {feat}: area core held by series move-core ({s1})" in p.stderr
    p = local.run("list", "--frontier", "--json")
    assert [t["id"] for t in json.loads(p.stdout)] == []
    assert f"skipped {feat}: area core held by series move-core ({s1})" in p.stderr


def test_series_done_releases_the_hold(local):
    s1 = local.new("Move packages 1", "core", "task", "--series", "move-core")
    feat = local.new("Feature in core", "core", "enhancement")
    claim_ids(local, "--ids", s1)
    local.run("set", s1, "--state", "done", "--note", "merged")
    got, rc = claim_ids(local)
    assert (got, rc) == ([feat], 0)


def test_same_series_ticket_is_not_held(local):
    s1 = local.new("Move 1", "core", "task", "--series", "move-core")
    s2 = local.new("Move 2", "core", "task", "--series", "move-core")
    claim_ids(local, "--ids", s1)
    got, rc = claim_ids(local)
    assert (got, rc) == ([s2], 0)


def test_ids_on_held_ticket_exits_3_with_skip_line(local):
    s1 = local.new("Move 1", "core", "task", "--series", "move-core")
    feat = local.new("Feature in core", "core", "enhancement")
    claim_ids(local, "--ids", s1)
    p = local.run("claim", "--as", "w", "--ids", feat, check=False)
    assert p.returncode == 3 and p.stdout == ""
    assert f"skipped {feat}: area core held by series move-core ({s1})" in p.stderr


def test_set_series_changes_and_clears_it(local):
    a = local.new("A", "core")
    local.run("set", a, "--series", "move-core")
    t = local.json("show", a)
    assert (t["series"], t["state"]) == ("move-core", "ready-for-agent")
    assert "series move-core" in local.out("show", a)
    local.run("set", a, "--series", "")
    assert local.json("show", a)["series"] == ""
    assert local.run("set", a, "--series", "Bad Name", check=False).returncode == 1


def test_github_series_label_round_trip(github, gh):
    a = github.new("Move 1", "core", "task", "--series", "move-core")
    assert "series:move-core" in gh.labels(1)
    assert github.json("show", a)["series"] == "move-core"
    github.run("set", a, "--series", "move-pkgs")
    assert "series:move-pkgs" in gh.labels(1) and "series:move-core" not in gh.labels(1)
    github.run("set", a, "--series", "")
    assert not [l for l in gh.labels(1) if l.startswith("series:")]
    b = github.new("Move 2", "core", "task", "--series", "move-core")
    feat = github.new("Feature", "core", "enhancement")
    claim_ids(github, "--ids", b)
    p = github.run("claim", "--as", "w", check=False)
    assert p.returncode == 3
    assert f"skipped {feat}: area core held by series move-core ({b})" in p.stderr


def test_series_claimed_first_holds_later_feature_in_same_call(local):
    s1 = local.new("Move 1", "core", "task", "--series", "move-core", "--priority", "p1")
    feat = local.new("Feature", "core", "enhancement")
    p = local.run("claim", "--as", "w")
    assert [l.split("\t")[0] for l in p.stdout.splitlines()] == [s1]
    assert f"skipped {feat}: area core held by series move-core ({s1})" in p.stderr


def test_feature_claimed_first_holds_later_series_in_same_call(local):
    feat = local.new("Feature", "core", "enhancement", "--priority", "p1")
    s1 = local.new("Move 1", "core", "task", "--series", "move-core")
    p = local.run("claim", "--as", "w")
    assert [l.split("\t")[0] for l in p.stdout.splitlines()] == [feat]
    assert f"skipped {s1}: series move-core waits for area core work ({feat})" in p.stderr
