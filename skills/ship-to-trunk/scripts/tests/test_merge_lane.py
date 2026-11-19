"""merge_lane.py: PROFILE parsing on the real PuzzleBox wording, and the lane
end to end against real git repos (bare origin, worktrees) with a stub `gh`.

Regressions: #31 (suite_command took the first backticked text of the
`pr-check: none` comment), no local `main` checkout needed, true PR state after
gh's "'main' is already checked out" error, one lane per repository (sessions
share it through enqueue + wait), batches A and B pipelined on two scratch
worktrees.
Run: python3 -m pytest skills/ship-to-trunk/scripts/tests
"""
import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

import merge_lane as ml
from conftest import FIXTURES, SCRIPTS, git, init_repo

SCRIPT = SCRIPTS / "merge_lane.py"
PR_URL = "https://github.com/example/PuzzleBox/pull/42"
PR7_URL = "https://github.com/example/PuzzleBox/pull/7"
REVIEW_REQUIRED = "GraphQL: At least 1 approving review is required by reviewers with write access. (mergePullRequest)"


def write_profile(wt, comment_line):
    (wt / "PROFILE.md").write_text(f"## Delivery\n- pr-check: none   # {comment_line}\n"
                                   "- runner: ./gradlew :app:testDebugUnitTest\n"
                                   "- structure: ./gradlew :konsist:test\n")


# ---------------------------------------------------------------- suite_command

def test_suite_command_real_profile_uses_the_gate_command(tmp_path, profile_text):
    (tmp_path / "PROFILE.md").write_text(profile_text)
    (tmp_path / "gradlew").write_text("#!/bin/sh\n")
    assert ml.suite_command(tmp_path) == "./gradlew assembleDebug test"


def test_suite_command_real_profile_without_script_assembles_from_keys(tmp_path, profile_text):
    """Gate script absent -> debug + `runner:` + `structure:` from the real keys."""
    (tmp_path / "PROFILE.md").write_text(profile_text)
    cmd = ml.suite_command(tmp_path)
    assert cmd == "./gradlew assembleDebug && ./gradlew :app:testDebugUnitTest && ./gradlew :konsist:test"
    assert "gh pr checks" not in cmd


@pytest.mark.parametrize("comment", [
    # #31: the first backticked text names the key itself, not a command.
    "`pr-check: none` — no PR CI; gate is `./gradlew assembleDebug test` on the rebased branch",
    "`pr-check` stays none; skip `gh pr checks` waits; local gate `./gradlew assembleDebug test`",
])
def test_suite_command_skips_backticked_prose_31(tmp_path, comment):
    write_profile(tmp_path, comment)
    (tmp_path / "gradlew").write_text("#!/bin/sh\n")
    assert ml.suite_command(tmp_path) == "./gradlew assembleDebug test"


def test_suite_command_never_returns_prose_31(tmp_path):
    write_profile(tmp_path, "`pr-check: none` and `gh pr checks` are not commands")
    cmd = ml.suite_command(tmp_path)
    assert "pr-check" not in cmd and "gh pr" not in cmd
    assert cmd.startswith("./gradlew assembleDebug")


def test_profile_line_splits_value_and_comment(tmp_path, profile_text):
    (tmp_path / "PROFILE.md").write_text(profile_text)
    value, comment = ml.profile_line(tmp_path, "pr-check")
    assert value == "none" and comment.startswith("merge gate: `./gradlew assembleDebug test`")
    assert ml.profile_line(tmp_path, "structure")[0] == "./gradlew :konsist:test"
    assert ml.profile_line(tmp_path, "nope") == (None, None)


# ----------------------------------------------------------------- rerun rule

def graph_files(edges):
    """edges {module: [deps]} -> settings + per-module build files as {path: text}."""
    files = {"settings.gradle.kts": "".join(f'include(":{m}")\n' for m in edges)}
    for m, deps in edges.items():
        files[f"{m}/build.gradle.kts"] = (
            "dependencies {\n" + "".join(f'    implementation(project(":{d}"))\n' for d in deps) + "}\n")
    return files


def gradle_project(root, edges):
    for name, text in graph_files(edges).items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(text)


CHAIN = {"app": ["feature"], "feature": ["core"], "core": [], "docs": [], "konsist": []}


@pytest.mark.parametrize("main_files,ticket_files,kind,modules", [
    (["feature/F2.kt"], ["feature/F.kt"], "rerun", []),                # same module
    (["core/C.kt"], ["feature/F.kt"], "compile", ["feature"]),         # main changed a dependency
    (["core/C.kt"], ["app/A.kt"], "compile", ["app"]),                 # ... transitively
    (["app/A.kt"], ["feature/F.kt"], "compile", ["app", "feature"]),   # main changed a dependent
    (["app/A.kt"], ["core/C.kt"], "compile", ["app", "core"]),         # ... transitively
    (["docs/a.md"], ["app/A.kt"], "push", []),                         # unrelated module
    (["README.md"], ["feature/F.kt"], "push", []),                     # outside every module
    (["feature/F.kt"], ["README.md"], "push", []),
])
def test_judge_same_module_reruns_dependency_only_compiles_unrelated_pushes(
        tmp_path, main_files, ticket_files, kind, modules):
    gradle_project(tmp_path, CHAIN)
    got, _, mods = ml.judge(tmp_path, main_files, ticket_files)
    assert (got, mods) == (kind, modules)


def test_judge_siblings_sharing_a_dependency_push(tmp_path):
    gradle_project(tmp_path, {"app": ["core"], "core": [], "feature": ["core"]})
    assert ml.judge(tmp_path, ["feature/F.kt"], ["app/A.kt"])[0] == "push"


@pytest.mark.parametrize("main_files,why", [
    (["gradle/libs.versions.toml"], "shared build setup"),
    (["build-logic/src/Conv.kt"], "shared build setup"),
    (["settings.gradle.kts"], "shared build setup"),
    (["konsist/K.kt"], "structure rules"),
])
def test_judge_shared_setup_and_structure_rules_rerun_even_for_an_unrelated_batch(tmp_path, main_files, why):
    gradle_project(tmp_path, CHAIN)
    (tmp_path / "PROFILE.md").write_text("- structure: ./gradlew :konsist:test\n")
    kind, label, mods = ml.judge(tmp_path, main_files, ["docs/a.md"])
    assert kind == "rerun" and why in label and mods == []


def test_judge_without_a_module_graph_reruns(tmp_path):
    assert ml.judge(tmp_path / "missing", ["x"], ["y"]) == ("rerun", "no module graph", [])


def stub_gradlew(root, body):
    (root / "gradlew").write_text(f"#!/bin/sh\n{body}\n")
    (root / "gradlew").chmod(0o755)


def test_compile_command_derives_the_tasks_from_module_paths(tmp_path):
    stub_gradlew(tmp_path, "exit 0")
    assert ml.compile_command(tmp_path, ["app", "feature:play"]) == (
        "./gradlew :app:compileDebugKotlin :app:compileDebugUnitTestKotlin "
        ":feature:play:compileDebugKotlin :feature:play:compileDebugUnitTestKotlin")


def test_compile_command_is_none_without_a_wrapper_or_when_a_task_does_not_resolve(tmp_path):
    assert ml.compile_command(tmp_path, ["app"]) is None
    stub_gradlew(tmp_path, "echo \"Task 'compileDebugKotlin' not found\" >&2\nexit 1")
    assert ml.compile_command(tmp_path, ["app"]) is None


# ------------------------------------------------------------------ e2e step

NESTED = {"app": ["feature:home:api"], "feature:home:api": [], "feature:home:impl": ["feature:home:api"],
          "docs": []}
E2E_KEY = "- e2e: ./gradlew :app:e2eTest   # "


def nested_repo(root, profile, edges=NESTED):
    """A git repo whose modules may be nested (`feature:home:api` lives in feature/home/api)."""
    files = {"PROFILE.md": profile}
    if edges:
        files["settings.gradle.kts"] = "".join(f'include(":{m}")\n' for m in edges)
        for m, deps in edges.items():
            files[f"{m.replace(':', '/')}/build.gradle.kts"] = "".join(
                f'dependencies {{ implementation(project(":{d}")) }}\n' for d in deps)
    return init_repo(root, files)


def commit_files(repo, *files):
    """(base, head) around one commit adding `files`."""
    base = git("rev-parse", "HEAD", cwd=repo)
    for f in files:
        (repo / f).parent.mkdir(parents=True, exist_ok=True)
        (repo / f).write_text("x\n")
    git("add", "-A", cwd=repo)
    git("commit", "-q", "-m", "change", cwd=repo)
    return base, git("rev-parse", "HEAD", cwd=repo)


@pytest.mark.parametrize("comment,globs", [
    ("when: app, :feature:*:api; main CI runs it on every push", ["app", "feature:*:api"]),
    ("when: app,feature:*:api", ["app", "feature:*:api"]),
    ("when: feature:*:api. User ruling 2026-11-19: the e2e tier boots the app", ["feature:*:api"]),  # prose tail
    ("when: feature:*:api — e2e boots the app", ["feature:*:api"]),  # prose tail, no stop sign
    ("when: `app`, `:core:navigation`", ["app", "core:navigation"]),  # backticks
    ("when: app, core:navigation.", ["app", "core:navigation"]),  # trailing dot
    ("JVM end-to-end tier, no filter", []),
])
def test_e2e_globs_read_only_the_comma_separated_when_list(comment, globs):
    assert ml.e2e_globs(comment) == globs


@pytest.mark.parametrize("comment,files,trigger", [
    ("when: app, :feature:*:api; main CI runs it on every push", ["feature/home/api/A.kt"], ["feature:home:api"]),
    ("when: app,feature:*:api", ["app/A.kt", "docs/a.md"], ["app"]),
    ("when: `feature:*:api`. The e2e tier boots the app", ["feature/home/api/A.kt"], ["feature:home:api"]),
    ("JVM end-to-end tier, no filter", ["docs/a.md"], ["docs"]),
    ("when: app, feature:*:api", ["gradle/libs.versions.toml"], [ml.SHARED_SETUP]),  # shared build setup alone
    ("when: app", ["build-logic/src/C.kt", "docs/a.md"], [ml.SHARED_SETUP]),
    ("when: docs", ["build.gradle.kts", "docs/a.md"], ["docs", ml.SHARED_SETUP]),
])
def test_e2e_plan_is_due_when_the_batch_touches_a_when_module(tmp_path, comment, files, trigger):
    repo = nested_repo(tmp_path / "r", E2E_KEY + comment + "\n")
    assert ml.e2e_plan(repo, *commit_files(repo, *files)) == ("./gradlew :app:e2eTest", trigger)


@pytest.mark.parametrize("comment,files", [
    ("when: app, feature:*:api", ["feature/home/impl/B.kt", "docs/a.md"]),  # no module matches
    ("when: app, feature:*:api", ["README.md"]),                            # outside every module
    ("when: app", ["feature/home/api/A.kt"]),  # a dependency of app: direct touches only, no closure
    ("when: feature:*:api — e2e boots the app", ["app/A.kt"]),  # prose after the list is no glob
])
def test_e2e_plan_is_not_due_when_no_batch_module_matches(tmp_path, comment, files):
    repo = nested_repo(tmp_path / "r", E2E_KEY + comment + "\n")
    assert ml.e2e_plan(repo, *commit_files(repo, *files)) == (None, [])


@pytest.mark.parametrize("profile", [
    "- runner: ./gradlew test\n",
    "- e2e: none   # when: app\n",
    "- e2e: OFF\n",
])
def test_e2e_plan_without_the_key_or_turned_off_is_none(tmp_path, profile):
    repo = nested_repo(tmp_path / "r", profile)
    assert ml.e2e_plan(repo, *commit_files(repo, "app/A.kt")) == (None, None)


def test_e2e_plan_without_a_module_graph_is_due(tmp_path):
    flat = nested_repo(tmp_path / "flat", E2E_KEY + "when: app\n", edges=None)
    assert ml.e2e_plan(flat, *commit_files(flat, "x.kt")) == ("./gradlew :app:e2eTest", [])


# ----------------------------------------------------------- lane end to end

GRAPH = {"app": ["feature"], "feature": ["core"], "core": [], "docs": []}
# A build (the suite, a gradle run) calls the test's on_build script when there is one: main moves under it.
HOOK = '[ -x "$GH_FAKE_DIR/on_build" ] && "$GH_FAKE_DIR/on_build"\n'
SUITE_SH = "#!/bin/sh\n" + HOOK + "exit 0\n"
# Fake wrapper: logs argv; --dry-run resolves unless no_tasks exists; a real run fails when compile_red exists.
GRADLEW = ("#!/bin/sh\n"
           'echo "$*" >> "$GH_FAKE_DIR/gradle.log"\n'
           'case "$*" in *--dry-run*) [ -e "$GH_FAKE_DIR/no_tasks" ] && exit 1; exit 0;; esac\n'
           + HOOK +
           '[ -e "$GH_FAKE_DIR/compile_red" ] && { echo "e: compile error in :feature"; exit 1; }\n'
           "exit 0\n")


class Lane:
    """origin (bare) <- main checkout `co` <- ticket worktree `wt` on branch ticket/1."""

    def __init__(self, tmp_path, profile_text, graph=None, ticket_file="feature.txt"):
        self.root = tmp_path / "lane"
        self.origin = self.root / "origin.git"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(self.origin)], check=True)
        self.co = init_repo(self.root / "co", {
            "PROFILE.md": profile_text.replace("./gradlew assembleDebug test", "./suite.sh"),
            "suite.sh": SUITE_SH,
            "gradlew": GRADLEW,
            ".gitignore": "build/\n",
            **(graph_files(graph) if graph else {}),
        }, executable=("suite.sh", "gradlew"))
        git("remote", "add", "origin", str(self.origin), cwd=self.co)
        git("push", "-q", "-u", "origin", "main", cwd=self.co)
        self.wt = self.add_ticket("1", ticket_file)
        self.dir = Path(git("rev-parse", "--path-format=absolute", "--git-common-dir", cwd=self.co)) / "agent-builds" / "lane"
        self.queue = self.dir / "queue.jsonl"
        self.body = self.root / "body.md"
        self.body.write_text("## Summary\nthing\n")

    def lane(self, *args, **kw):
        kw.setdefault("cwd", self.co)
        return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, timeout=60, **kw)

    def enqueue(self, nn="01", *extra, wt=None, who="test-run"):
        r = self.lane("enqueue", "--who", who, "--nn", nn, "--worktree", str(wt or self.wt),
                      "--title", "feat: one", "--body-file", str(self.body), *extra)
        assert r.returncode == 0, r.stderr
        return r

    def land(self, *extra):
        return self.lane("land", "--who", "test-run", *extra)

    def wait(self, who, *nns):
        """A session's `wait` as a background process (stdout, stderr piped)."""
        return subprocess.Popen([sys.executable, str(SCRIPT), "wait", "--who", who, "--nn", *nns], cwd=self.co,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def idle(self):
        """Until no `land` holds the lane (a `wait` may return while its land still cleans up)."""
        deadline = time.time() + 60
        while ml.LaneLock(self.dir).holder() and time.time() < deadline:
            time.sleep(0.05)
        assert not ml.LaneLock(self.dir).holder()

    def pr_body(self, nn, who="test-run"):
        return self.dir / f"body-{who}-{nn}.md"

    def queue_nns(self):
        return [json.loads(l)["nn"] for l in self.queue.read_text().splitlines() if l.strip()]

    @staticmethod
    def results(r):
        return [json.loads(l) for l in r.stdout.splitlines() if l.startswith("{")]

    def add_ticket(self, nn, rel):
        """Worktree wt<nn> on branch ticket/<nn> off origin/main with one commit adding `rel`."""
        wt = self.root / f"wt{nn}"
        git("worktree", "add", "-q", "-b", f"ticket/{nn}", str(wt), "origin/main", cwd=self.co)
        (wt / rel).parent.mkdir(parents=True, exist_ok=True)
        (wt / rel).write_text(f"hello {nn}\n")
        git("add", rel, cwd=wt)
        git("commit", "-q", "-m", f"feat: ticket {nn}", cwd=wt)
        return wt

    def move_main(self, *files, times=1, hook="on_build", only=None, also=""):
        """Land up to `times` outside commits touching `files` on origin/main, one per call of the
        $GH_FAKE_DIR/<hook> script: `on_build` runs in every suite/gradle run, `after_merge` in every merge.
        `only`: a shell pattern the calling directory must match ("*/wt/0": batch A's checks only).
        `also`: a shell line run in the main checkout before the commit (an edit beyond `files`)."""
        script = Path(os.environ["GH_FAKE_DIR"]) / hook
        quoted = " ".join(f"'{f}'" for f in files)
        guard = f'case "$(pwd)" in {only}) ;; *) exit 0;; esac\n' if only else ""
        script.write_text(f"""#!/bin/sh
{guard}n=$(cat "$0.n" 2>/dev/null || echo 0)
[ "$n" -ge {times} ] && exit 0
echo $((n + 1)) > "$0.n"
cd '{self.co}' && git pull -q --ff-only origin main || exit 1
for f in {quoted}; do mkdir -p "$(dirname "$f")"; echo "$n" > "$f"; done
{also}
git add -A && git commit -q -m "outside $n" && git push -q origin main
""")
        script.chmod(0o755)


@pytest.fixture
def lane(tmp_path, gh, profile_text, real_runs):
    gh.set(runs=real_runs, create_url=PR_URL, create_branch="ticket/1")
    return Lane(tmp_path, profile_text)


@pytest.fixture
def make_lane(tmp_path, gh, profile_text, real_runs):
    """Lane factory over a Gradle-shaped repo (app -> feature -> core, docs); ticket 01 adds `ticket_file`."""
    gh.set(runs=real_runs, create_url=PR_URL, create_branch="ticket/1")
    return lambda **kw: Lane(tmp_path, profile_text, graph=GRAPH, **kw)


@pytest.fixture
def glane(make_lane):
    return make_lane(ticket_file="feature/F.kt")


def merge_lines(r):
    return [l for l in r.stdout.splitlines() if l.startswith("merge:")]


def gradle_log(gh):
    p = gh.dir / "gradle.log"
    return p.read_text().splitlines() if p.exists() else []


def compile_tasks(*modules):
    return " ".join(f":{m}:{t}" for m in modules for t in ml.COMPILE_TASKS)


def test_land_merges_without_main_checked_out_locally(lane, gh):
    # No local main anywhere: the checkout is detached and the branch is gone.
    git("checkout", "-q", "--detach", cwd=lane.co)
    git("branch", "-q", "-D", "main", cwd=lane.co)
    gh.set(land=True)
    lane.enqueue()
    r = lane.land()
    assert r.returncode == 0, r.stdout + r.stderr
    merge = [c for c in gh.calls() if c[:2] == ["pr", "merge"]]
    assert merge and "--delete-branch" not in merge[0] and merge[0][2] == "42"
    tested = merge[0][merge[0].index("--match-head-commit") + 1][:7]
    squash = git("rev-parse", "main", cwd=lane.origin)[:7]  # GitHub's squash on main, not the tested head
    assert squash != tested
    assert lane.results(r) == [{"who": "test-run", "nn": "01", "result": "merged", "pr": 42,
                                "sha": squash, "tested": tested}]
    assert re.search(r"^merge: batch test-run/01 suite green tested @ \w{7} \(1 suites\)$", r.stdout, re.M)
    assert re.search(rf"^slice: 01 PR #42 merged @ {squash}$", r.stdout, re.M)
    assert not lane.wt.exists()
    assert git("branch", "--list", "main", cwd=lane.co) == ""      # lane never recreated it
    assert lane.queue_nns() == []
    assert (gh.dir / "slot.log").read_text().strip() == "bash -c ./suite.sh"  # suite goes through build-slot
    # branch pushed then deleted on origin
    assert git("branch", "--list", "ticket/1", cwd=lane.origin) == ""


def test_merge_without_a_merge_commit_from_gh_says_so_and_names_the_tested_head(lane, gh):
    lane.enqueue()  # no land: gh reports the merged PR's mergeCommit as null
    r = lane.land()
    assert r.returncode == 0, r.stdout + r.stderr
    (merge,) = [c for c in gh.calls() if c[:2] == ["pr", "merge"]]
    tested = merge[merge.index("--match-head-commit") + 1][:7]
    assert lane.results(r) == [{"who": "test-run", "nn": "01", "result": "merged", "pr": 42,
                                "sha": None, "tested": tested}]
    assert f"slice: 01 PR #42 merged (main sha unresolved; tested @ {tested})" in r.stdout.splitlines()
    assert ["pr", "view", "42", "--json", "mergeCommit", "-q", ".mergeCommit.oid"] in gh.calls()


def test_already_checked_out_error_but_pr_merged_counts_as_merged(lane, gh):
    gh.set(merge="checkout_error")
    lane.enqueue()
    r = lane.land()
    assert r.returncode == 0, r.stdout + r.stderr
    assert lane.results(r)[0]["result"] == "merged"
    assert lane.queue_nns() == []
    assert any(c[:3] == ["pr", "view", "42"] for c in gh.calls())  # state read back, not assumed


def test_already_checked_out_error_but_pr_still_open_is_refused(lane, gh):
    gh.set(merge="checkout_error_open")
    lane.enqueue()
    r = lane.land()
    assert r.returncode == 1
    (res,) = lane.results(r)
    assert (res["result"], res["pr"]) == ("refused", 42) and "already checked out" in res["reason"]
    assert lane.wt.exists() and lane.queue_nns() == []
    assert not any(l.startswith("slice:") for l in r.stdout.splitlines())


def test_refused_merge_is_final_and_requeues_the_ticket_stacked_on_it(lane, gh):
    gh.set(merge="refused")
    lane.enqueue("01")
    lane.enqueue("02", wt=lane.add_ticket("2", "two.txt"))
    r = lane.land()
    assert r.returncode == 1
    assert lane.results(r) == [
        {"who": "test-run", "nn": "01", "result": "refused", "pr": 42, "reason": REVIEW_REQUIRED},
        {"who": "test-run", "nn": "02", "result": "requeued", "reason": "stacked on a refused ticket"}]
    assert lane.queue_nns() == ["02"]
    assert len([c for c in gh.calls() if c[:2] == ["pr", "merge"]]) == 1


def test_transient_merge_refusal_is_retried_then_merges(lane, gh):
    gh.set(merge_seq=["not_mergeable"])  # GitHub has not computed mergeability yet
    lane.enqueue()
    r = lane.land()
    assert r.returncode == 0, r.stdout + r.stderr
    assert [(x["result"], x["pr"]) for x in lane.results(r)] == [("merged", 42)]
    assert len([c for c in gh.calls() if c[:2] == ["pr", "merge"]]) == 2


def test_failed_pr_create_is_refused(lane, gh):
    gh.set(create_error="GraphQL: No commits between main and ticket/1 (createPullRequest)")
    lane.enqueue()
    r = lane.land()
    assert r.returncode == 1
    assert lane.results(r) == [{"who": "test-run", "nn": "01", "result": "refused",
                                "reason": "gh pr create failed: GraphQL: No commits between main and ticket/1 "
                                          "(createPullRequest)"}]
    assert lane.queue_nns() == [] and not any(c[:2] == ["pr", "merge"] for c in gh.calls())


@pytest.mark.parametrize("closed_at, on_head", [(None, False), ("2020-01-01T00:00:00Z", True)],
                         ids=["closed-after-enqueue", "older-but-on-its-head"])
def test_own_closed_pr_is_final_and_never_pushed_or_recreated(lane, gh, closed_at, on_head):
    lane.enqueue()
    gh.set(prs={"7": {"number": 7, "url": PR7_URL, "state": "CLOSED", "headRefName": "ticket/1",
                      "closedAt": closed_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                      "headRefOid": git("rev-parse", "HEAD", cwd=lane.wt) if on_head else "0" * 40}})
    r = lane.land()
    assert r.returncode == 1
    assert lane.results(r) == [{"who": "test-run", "nn": "01", "result": "closed", "pr": 7, "url": PR7_URL}]
    assert not any(c[:2] in (["pr", "create"], ["pr", "merge"]) for c in gh.calls())
    assert git("branch", "--list", "ticket/1", cwd=lane.origin) == ""  # never pushed
    assert lane.queue_nns() == []


def test_older_closed_pr_of_a_reused_branch_name_gets_a_new_pr(lane, gh):
    gh.set(prs={"7": {"number": 7, "url": PR7_URL, "state": "CLOSED", "headRefName": "ticket/1",
                      "closedAt": "2020-01-01T00:00:00Z", "headRefOid": "0" * 40}})
    lane.enqueue()
    r = lane.land()
    assert r.returncode == 0, r.stdout + r.stderr
    assert [(x["result"], x["pr"]) for x in lane.results(r)] == [("merged", 42)]
    assert len([c for c in gh.calls() if c[:2] == ["pr", "create"]]) == 1


def test_legacy_entry_without_enqueue_time_owns_any_closed_pr(lane, gh):
    """An entry queued before `enqueued` existed: its branch's CLOSED PR is its own, never a crash."""
    lane.enqueue()
    entry = json.loads(lane.queue.read_text())
    del entry["enqueued"]
    lane.queue.write_text(json.dumps(entry) + "\n")
    gh.set(prs={"7": {"number": 7, "url": PR7_URL, "state": "CLOSED", "headRefName": "ticket/1",
                      "closedAt": "2020-01-01T00:00:00Z", "headRefOid": "0" * 40}})
    r = lane.land()
    assert r.returncode == 1, r.stdout + r.stderr
    assert lane.results(r) == [{"who": "test-run", "nn": "01", "result": "closed", "pr": 7, "url": PR7_URL}]
    assert git("branch", "--list", "ticket/1", cwd=lane.origin) == ""  # never pushed


def test_refused_red_fix_on_red_main_pauses_the_lane(lane, gh, real_runs):
    gh.set(runs=real_runs[4:], merge="refused")  # real window whose newest finished run is the failure
    lane.enqueue("01", "--red-fix", "abc1234")
    r = lane.land()
    assert r.returncode == 3, r.stdout + r.stderr
    assert [x["result"] for x in lane.results(r)] == ["refused"]
    assert "main red; lane paused" in r.stdout.splitlines()


def test_no_merge_ticket_waits_for_user_with_pr_open(lane, gh):
    lane.enqueue("01", "--no-merge")
    r = lane.land()
    assert r.returncode == 1
    assert lane.results(r) == [{"who": "test-run", "nn": "01", "result": "waiting_user", "pr": 42, "url": PR_URL}]
    assert not any(c[:2] == ["pr", "merge"] for c in gh.calls())


def test_red_main_pauses_the_lane_and_touches_nothing(lane, gh, real_runs):
    gh.set(runs=real_runs[4:])  # real window whose newest finished run is the failure
    lane.enqueue()
    r = lane.land()
    assert r.returncode == 3
    assert r.stdout.splitlines()[0] == "main red; lane paused"
    assert lane.queue_nns() == ["01"]
    assert not any(c[:2] in (["pr", "create"], ["pr", "merge"]) for c in gh.calls())


def test_failing_suite_marks_ticket_red_and_merges_nothing(lane, gh):
    (lane.wt / "suite.sh").write_text("#!/bin/sh\necho boom\nexit 1\n")
    git("commit", "-q", "-am", "break suite", cwd=lane.wt)
    lane.enqueue()
    r = lane.land()
    res = lane.results(r)
    assert r.returncode == 1 and res[0]["result"] == "red"
    assert "boom" in open(res[0]["log"]).read()
    assert not any(c[:2] == ["pr", "merge"] for c in gh.calls())


def test_invalid_when_worktree_has_uncommitted_changes(lane):
    lane.enqueue()
    (lane.wt / "feature.txt").write_text("dirty\n")
    r = lane.land()
    assert r.returncode == 1 and lane.results(r)[0]["result"] == "invalid"


def test_enqueue_replaces_same_who_and_nn_but_keeps_another_sessions_nn(lane):
    lane.enqueue("01")
    lane.enqueue("01")
    lane.enqueue("01", who="other-run")
    assert [(json.loads(l)["who"], json.loads(l)["nn"]) for l in lane.queue.read_text().splitlines()] == [
        ("test-run", "01"), ("other-run", "01")]


def test_concurrent_enqueues_all_reach_the_queue_and_the_event_log(lane):
    nns = [f"{n:02}" for n in range(1, 13)]
    procs = [subprocess.Popen([sys.executable, str(SCRIPT), "enqueue", "--who", "test-run", "--nn", nn,
                               "--worktree", str(lane.wt), "--title", "feat: one", "--body-file", str(lane.body)],
                              cwd=lane.co, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for nn in nns]
    outs = [p.communicate(timeout=60) for p in procs]
    assert [p.returncode for p in procs] == [0] * len(nns), outs
    assert sorted(lane.queue_nns()) == nns
    assert sorted(e["nn"] for e in events(lane, "enqueue")) == nns


def test_queue_flag_is_gone_and_says_what_replaced_it(lane):
    for args in (("enqueue", "--queue", "x", "--nn", "01"), ("land", "--queue=x", "--who", "t")):
        r = lane.lane(*args)
        assert r.returncode == 2 and r.stdout == ""
        (line,) = r.stderr.splitlines()
        assert "--queue is gone" in line and "wait --who" in line
        assert line.endswith("re-enqueue anything left in the old .scratch/<slug>/lane/queue.jsonl")


# -------------------------------------------------------------------- lane lock

def test_second_land_exits_4_while_a_lane_is_held(lane, gh):
    lane.enqueue()
    with ml.LaneLock(lane.dir):  # this process is the live owner
        r = lane.land()
        assert r.returncode == 4 and "lane busy" in r.stderr
        assert lane.queue_nns() == ["01"]
        assert not any(c[:2] == ["pr", "create"] for c in gh.calls())
    assert ml.LaneLock(lane.dir).holder() is None  # released on exit


def test_two_concurrent_lands_only_one_runs(lane, gh):
    # The suite holds until the test releases it (bounded at 60 s), so the second land always meets the lock.
    (lane.wt / "suite.sh").write_text('#!/bin/sh\ni=0\nuntil [ -e "$GH_FAKE_DIR/release" ] || [ $i -ge 1200 ]; '
                                      'do sleep 0.05; i=$((i+1)); done\nexit 0\n')
    git("commit", "-q", "-am", "suite waits for release", cwd=lane.wt)
    lane.enqueue()
    first = subprocess.Popen([sys.executable, str(SCRIPT), "land", "--who", "a"], cwd=lane.co,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    deadline = time.time() + 20
    while ml.LaneLock(lane.dir).holder() != first.pid and time.time() < deadline:
        time.sleep(0.05)
    assert ml.LaneLock(lane.dir).holder() == first.pid
    second = lane.land()
    (gh.dir / "release").write_text("")
    out1, err1 = first.communicate(timeout=60)
    assert second.returncode == 4 and "lane busy" in second.stderr
    assert first.returncode == 0, out1 + err1
    assert len([c for c in gh.calls() if c[:2] == ["pr", "merge"]]) == 1


def lock_holder(lane_dir, *after):
    """A process that takes the lane lock, prints `held`, then runs `after` (Python lines)."""
    code = "\n".join(["import sys, time", f"sys.path.insert(0, {str(SCRIPT.parent)!r})", "import merge_lane as ml",
                      f"with ml.LaneLock({str(lane_dir)!r}):", "    print('held', flush=True)",
                      *(f"    {line}" for line in after)])
    return [sys.executable, "-c", code]


def test_five_racing_lands_one_takes_the_lock(tmp_path):
    go = tmp_path / "go"
    wait_go = f"import os, time\nwhile not os.path.exists({str(go)!r}): time.sleep(0.01)\n"
    cmd = lock_holder(tmp_path / "lane", "time.sleep(2)")
    racers = [subprocess.Popen([cmd[0], "-c", wait_go + cmd[2]], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True) for _ in range(5)]
    go.write_text("")
    outs = [p.communicate(timeout=30) for p in racers]
    assert sorted(p.returncode for p in racers) == [0, 4, 4, 4, 4], outs
    assert [o for o, _ in outs].count("held\n") == 1
    assert all("lane busy" in e for p, (_, e) in zip(racers, outs) if p.returncode == 4)


def test_lock_of_a_killed_holder_is_free(tmp_path):
    holder = subprocess.Popen(lock_holder(tmp_path / "lane", "time.sleep(60)"), stdout=subprocess.PIPE, text=True)
    assert holder.stdout.readline() == "held\n"
    assert ml.LaneLock(tmp_path / "lane").holder() == holder.pid
    holder.kill()
    holder.wait()
    with ml.LaneLock(tmp_path / "lane") as lock:
        assert lock.path.read_text() == str(os.getpid())
    assert ml.LaneLock(tmp_path / "lane").holder() is None


def test_land_after_a_killed_land_takes_the_lock_and_resets_the_scratch_worktree(lane, gh):
    dead = subprocess.Popen([sys.executable, "-c", "pass"])
    dead.wait()
    lane.dir.mkdir(parents=True)
    (lane.dir / "land.lock").write_text(str(dead.pid))  # what a killed land leaves: its pid, no flock
    wt0 = lane.dir / "wt" / "0"  # what a killed suite left: an edited tracked file, an untracked one
    git("worktree", "add", "-q", "--detach", str(wt0), "origin/main", cwd=lane.co)
    (wt0 / "suite.sh").write_text("#!/bin/sh\nexit 1\n")
    (wt0 / "leftover.txt").write_text("x\n")
    lane.enqueue()
    r = lane.land()
    assert r.returncode == 0, r.stdout + r.stderr
    assert lane.results(r)[0]["result"] == "merged"
    assert (wt0 / "suite.sh").read_text() == SUITE_SH and not (wt0 / "leftover.txt").exists()
    assert ml.LaneLock(lane.dir).holder() is None


def test_terminated_land_kills_its_running_suite_and_frees_the_lane(lane, gh):
    (lane.wt / "suite.sh").write_text('#!/bin/sh\necho $$ > "$GH_FAKE_DIR/suite.pid"\nsleep 60\n')
    git("commit", "-q", "-am", "suite hangs", cwd=lane.wt)
    lane.enqueue()
    land = subprocess.Popen([sys.executable, str(SCRIPT), "land", "--who", "test-run"], cwd=lane.co,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    pid_file = gh.dir / "suite.pid"
    deadline = time.time() + 20
    while not pid_file.exists() and time.time() < deadline:
        time.sleep(0.05)
    suite = int(pid_file.read_text())
    land.terminate()
    land.communicate(timeout=60)
    assert land.returncode == 143
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            os.kill(suite, 0)
        except ProcessLookupError:
            break
        time.sleep(0.05)
    else:
        pytest.fail(f"suite pid {suite} outlived its land")
    assert ml.LaneLock(lane.dir).holder() is None
    assert lane.queue_nns() == ["01"]  # nothing decided
    assert [(e["pipe"], e["result"]) for e in events(lane, "suite")] == [("A", "discarded")]
    assert not (lane.dir / ml.CHECK_GROUPS).exists()


def test_land_kills_the_checks_a_killed_land_left_running(lane, gh):
    """SIGKILL runs no cleanup: the suite outlives its land until the next land takes the lock."""
    (lane.wt / "suite.sh").write_text('#!/bin/sh\n[ -e "$GH_FAKE_DIR/suite.pid" ] && exit 0\n'
                                      'echo $$ > "$GH_FAKE_DIR/suite.pid"\nsleep 60\n')
    git("commit", "-q", "-am", "the first suite hangs", cwd=lane.wt)
    lane.enqueue()
    first = subprocess.Popen([sys.executable, str(SCRIPT), "land", "--who", "test-run"], cwd=lane.co,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    pid_file = gh.dir / "suite.pid"
    deadline = time.time() + 20
    while not (pid_file.exists() and pid_file.read_text().strip()) and time.time() < deadline:
        time.sleep(0.05)
    suite = int(pid_file.read_text())
    first.kill()
    first.wait()
    os.kill(suite, 0)  # still running: nothing stopped it
    assert (lane.dir / ml.CHECK_GROUPS).exists()
    r = lane.land()
    assert r.returncode == 0, r.stdout + r.stderr
    assert [x["result"] for x in lane.results(r)] == ["merged"]
    with pytest.raises(ProcessLookupError):
        os.kill(suite, 0)
    assert not (lane.dir / ml.CHECK_GROUPS).exists()


def test_kill_orphans_spares_a_recorded_pid_that_now_names_another_process(tmp_path):
    other = subprocess.Popen(["sleep", "60"], start_new_session=True)  # its own group, as a check's
    try:
        (tmp_path / ml.CHECK_GROUPS).write_text(f"{other.pid} Thu Jan  1 00:00:00 1970\n")
        ml.kill_orphans(tmp_path)
        assert other.poll() is None
        assert not (tmp_path / ml.CHECK_GROUPS).exists()
    finally:
        other.kill()
        other.wait()


def test_kill_orphans_counts_an_eperm_group_as_gone(tmp_path, monkeypatch):
    """macOS answers EPERM for a group of zombies: no crash, no SIGKILL, the record cleared."""
    check = subprocess.Popen(["sleep", "60"], start_new_session=True)
    sent = []

    def killpg(g, sig):
        if sig == 0:
            raise PermissionError(1, "Operation not permitted")
        sent.append((g, sig))

    try:
        (tmp_path / ml.CHECK_GROUPS).write_text(f"{check.pid} {ml.proc_start(check.pid)}\n")
        monkeypatch.setattr(ml.os, "killpg", killpg)
        ml.kill_orphans(tmp_path)
        assert sent == [(check.pid, signal.SIGTERM)]
        assert not (tmp_path / ml.CHECK_GROUPS).exists()
    finally:
        check.kill()
        check.wait()


def test_scratch_worktree_gets_the_main_checkouts_local_properties(lane, gh):
    (lane.co / "local.properties").write_text("sdk.dir=/opt/android-sdk\n")
    (gh.dir / "on_build").write_text('#!/bin/sh\ncp local.properties "$GH_FAKE_DIR/props"\n')
    (gh.dir / "on_build").chmod(0o755)
    lane.enqueue()
    r = lane.land()
    assert r.returncode == 0, r.stdout + r.stderr
    assert (gh.dir / "props").read_text() == "sdk.dir=/opt/android-sdk\n"


# ------------------------------------------- main moves: rerun | compile | push

def test_main_moving_in_the_same_module_reruns_the_suite(glane, gh):
    glane.move_main("feature/Other.kt")
    glane.enqueue()
    r = glane.land()
    assert r.returncode == 0, r.stdout + r.stderr
    assert "merge: test-run/01 main moved 1 commits — rerun (feature)" in merge_lines(r)
    assert re.search(r"^merge: batch test-run/01 suite green tested @ \w{7} \(2 suites\)$", r.stdout, re.M)
    assert gradle_log(gh) == []  # no compile check
    assert glane.results(r)[0]["result"] == "merged"


@pytest.mark.parametrize("moved,modules,label", [
    ("core/C.kt", ["feature"], "core,feature"),       # main changed a dependency of the batch
    ("app/A.kt", ["app", "feature"], "app,feature"),  # main changed a dependent of the batch
])
def test_dependency_only_overlap_restacks_and_compiles_without_the_suite(glane, gh, moved, modules, label):
    glane.move_main(moved)
    glane.enqueue()
    r = glane.land()
    assert r.returncode == 0, r.stdout + r.stderr
    assert f"merge: test-run/01 main moved 1 commits — compile ({label})" in merge_lines(r)
    m = re.search(r"^merge: batch test-run/01 suite green tested @ (\w{7}), compile green tested @ (\w{7}) "
                  r"\(1 suites, 1 compiles\)$", r.stdout, re.M)
    assert m and m.group(1) != m.group(2)  # the compile ran on the restacked head, the suite on the old one
    assert gradle_log(gh) == [compile_tasks(*modules) + " --dry-run", compile_tasks(*modules)]
    check = [l for l in glane.pr_body("01").read_text().splitlines() if l.startswith("**check:**")]
    assert check == [f"**check:** local suite green on batch top {m.group(1)} (tickets test-run/01), then compile "
                     "green after main moved; no PR CI by design"]
    assert glane.results(r)[0]["result"] == "merged"


def test_compile_rounds_never_count_toward_main_keeps_moving(glane, gh):
    glane.move_main("core/C.kt", times=5)  # the suite and the first four compile checks each land a commit
    glane.enqueue()
    r = glane.land()
    assert r.returncode == 0, r.stdout + r.stderr
    assert len([l for l in merge_lines(r) if "— compile (core,feature)" in l]) == 5
    assert "(1 suites, 5 compiles)" in r.stdout
    assert glane.results(r)[0]["result"] == "merged" and "main keeps moving" not in r.stdout


def test_full_reruns_still_stop_after_three_rounds(glane, gh):
    glane.move_main("feature/Other.kt", times=9)
    glane.enqueue()
    r = glane.land()
    assert r.returncode == 1
    assert glane.results(r) == [{"who": "test-run", "nn": "01", "result": "requeued",
                                 "reason": "main keeps moving"}]
    assert len([l for l in merge_lines(r) if l.endswith("— rerun (feature)")]) == 3
    assert glane.queue_nns() == ["01"]
    assert not any(c[:2] == ["pr", "merge"] for c in gh.calls())


def test_unrelated_move_pushes_the_green_head_without_a_second_run(glane, gh):
    glane.move_main("docs/D.md")
    glane.enqueue()
    r = glane.land()
    assert r.returncode == 0, r.stdout + r.stderr
    assert "merge: test-run/01 main moved 1 commits — push (docs,feature)" in merge_lines(r)
    assert re.search(r"^merge: batch test-run/01 suite green tested @ \w{7} \(1 suites\)$", r.stdout, re.M)
    assert gradle_log(gh) == []
    assert glane.results(r)[0]["result"] == "merged"


def test_shared_build_setup_change_reruns_the_suite(glane, gh):
    glane.move_main("gradle/libs.versions.toml")
    glane.enqueue()
    r = glane.land()
    assert r.returncode == 0, r.stdout + r.stderr
    assert "merge: test-run/01 main moved 1 commits — rerun (feature +shared build setup)" in merge_lines(r)
    assert "(2 suites)" in r.stdout and gradle_log(gh) == []


def test_compile_tasks_that_do_not_resolve_fall_back_to_a_rerun(glane, gh):
    (gh.dir / "no_tasks").write_text("")
    glane.move_main("core/C.kt")
    glane.enqueue()
    r = glane.land()
    assert r.returncode == 0, r.stdout + r.stderr
    assert "merge: test-run/01 main moved 1 commits — rerun (core,feature +no compile command)" in merge_lines(r)
    assert "(2 suites)" in r.stdout
    assert gradle_log(gh) == [compile_tasks("feature") + " --dry-run"]  # only the resolve probe ran


def test_red_compile_check_blocks_the_merge_like_a_red_suite(glane, gh):
    (gh.dir / "compile_red").write_text("")
    glane.move_main("core/C.kt")
    glane.enqueue()
    r = glane.land()
    res = glane.results(r)
    assert r.returncode == 1 and [(x["nn"], x["result"]) for x in res] == [("01", "red")]
    assert res[0]["log"].endswith("-compile.log") and "compile error" in open(res[0]["log"]).read()
    assert not any(c[:2] in (["pr", "create"], ["pr", "merge"]) for c in gh.calls())
    assert not any(l.startswith("slice:") for l in r.stdout.splitlines())
    assert glane.queue_nns() == []  # a red ticket leaves the queue until its fix is enqueued again


def stack_batch(make_lane, gh, outside, third=False):
    """Batch 01 (docs), 02 (feature)[, 03 (docs)]; the merge of 01 lands an `outside` commit on main."""
    lane = make_lane(ticket_file="docs/D.md")
    gh.set(land=True)
    lane.move_main(outside, hook="after_merge")
    lane.enqueue("01")
    lane.enqueue("02", wt=lane.add_ticket("2", "feature/F.kt"))
    if third:
        lane.enqueue("03", wt=lane.add_ticket("3", "docs/E.md"))
    return lane


def test_main_moving_between_merges_compiles_the_next_ticket_then_merges_it(make_lane, gh):
    lane = stack_batch(make_lane, gh, "core/C.kt")
    r = lane.land()
    assert r.returncode == 0, r.stdout + r.stderr
    assert [(x["nn"], x["result"]) for x in lane.results(r)] == [("01", "merged"), ("02", "merged")]
    assert "merge: test-run/02 main moved 1 commits — compile (core,feature)" in merge_lines(r)
    assert gradle_log(gh) == [compile_tasks("feature") + " --dry-run", compile_tasks("feature")]
    assert "then compile green after main moved" in lane.pr_body("02").read_text()
    assert "then compile" not in lane.pr_body("01").read_text()


def test_red_compile_between_merges_reds_that_ticket_and_requeues_the_rest(make_lane, gh):
    lane = stack_batch(make_lane, gh, "core/C.kt", third=True)
    (gh.dir / "compile_red").write_text("")
    r = lane.land()
    res = lane.results(r)
    assert r.returncode == 1
    assert [(x["nn"], x["result"]) for x in res] == [("01", "merged"), ("02", "red"), ("03", "requeued")]
    assert res[1]["log"].endswith("-compile.log") and res[2]["reason"] == "stacked on a red ticket"
    assert [l for l in r.stdout.splitlines() if l.startswith("slice:")] == [f"slice: 01 PR #42 merged @ {res[0]['sha']}"]
    assert lane.queue_nns() == ["03"]


def test_same_module_move_between_merges_requeues_the_next_ticket(make_lane, gh):
    lane = stack_batch(make_lane, gh, "feature/Other.kt")
    r = lane.land()
    res = lane.results(r)
    assert r.returncode == 1
    assert [(x["nn"], x["result"]) for x in res] == [("01", "merged"), ("02", "requeued")]
    assert res[1]["reason"] == "main moved: related"
    assert "merge: test-run/02 main moved 1 commits — rerun (feature)" in merge_lines(r)
    assert gradle_log(gh) == [] and lane.queue_nns() == ["02"]
    assert [(e["phase"], e["decision"], e["reason"]) for e in events(lane, "main_moved")] == [
        ("merge", "requeue", "feature")]  # a rerun verdict between merges requeues, never reruns


# ------------------------------------------------------------------ lane events

JUNIT = FIXTURES / "junit"
TS = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")


def events(lane, *kinds):
    common = Path(git("rev-parse", "--path-format=absolute", "--git-common-dir", cwd=lane.co))
    p = common / "agent-builds" / ml.EVENTS
    evs = [json.loads(l) for l in p.read_text().splitlines()] if p.exists() else []
    return [e for e in evs if not kinds or e["event"] in kinds]


def put_xml(root, module_dir, name, mtime=None):
    d = Path(root) / module_dir / "build" / "test-results" / "testDebugUnitTest"
    d.mkdir(parents=True, exist_ok=True)
    shutil.copy(JUNIT / name, d / name)  # copy, not copy2: a fresh mtime, as a run writes it
    if mtime is not None:
        os.utime(d / name, (mtime, mtime))


def test_module_test_seconds_sums_fresh_junit_xml_per_module_and_skips_stale(tmp_path):
    (tmp_path / "settings.gradle.kts").write_text('include(":feature:play")\ninclude(":core")\n')
    for d in ("feature/play", "core"):
        (tmp_path / d).mkdir(parents=True)
        (tmp_path / d / "build.gradle.kts").write_text("")
    since = int(time.time())
    put_xml(tmp_path, "feature/play", "TEST-feature-play.xml")    # 1.5 s
    put_xml(tmp_path, "feature/play", "TEST-feature-board.xml")   # 2.25 s, a failing suite counts too
    put_xml(tmp_path, "core", "TEST-core.xml", mtime=since - 3600)  # an earlier run's result
    assert ml.module_test_seconds(tmp_path, since) == {"feature:play": 3.75}
    assert ml.module_test_seconds(tmp_path, since - 7200) == {"core": 0.75, "feature:play": 3.75}
    assert ml.module_test_seconds(tmp_path / "missing", since) == {}


def test_green_batch_logs_the_suite_with_module_test_time_and_the_merge(glane, gh):
    # The suite writes fresh JUnit XML for :feature; a stale :core result from an earlier run stays behind
    # in the scratch worktree (ignored build output survives the reset between checks).
    wt0 = glane.dir / "wt" / "0"
    wt0.parent.mkdir(parents=True)
    git("worktree", "add", "-q", "--detach", str(wt0), "origin/main", cwd=glane.co)
    put_xml(wt0, "core", "TEST-core.xml", mtime=time.time() - 3600)
    hook = gh.dir / "on_build"
    hook.write_text(f"#!/bin/sh\nd=feature/build/test-results/testDebugUnitTest\nmkdir -p $d\n"
                    f"cp '{JUNIT}/TEST-feature-play.xml' '{JUNIT}/TEST-feature-board.xml' $d/\n")
    hook.chmod(0o755)
    base7 = git("rev-parse", "--short=7", "main", cwd=glane.origin)
    glane.enqueue()
    r = glane.land()
    assert r.returncode == 0, r.stdout + r.stderr
    sha = glane.results(r)[0]["tested"]
    (suite,) = events(glane, "suite")
    assert TS.match(suite.pop("ts")) and isinstance(suite.pop("wall_s"), float)
    assert suite == {"who": "test-run", "event": "suite", "pipe": "A", "batch": ["test-run/01"], "batch_size": 1,
                     "round": 1, "phase": "stack", "modules": ["feature"], "base": base7, "top": sha,
                     "result": "green", "module_test_s": {"feature": 3.75}, "e2e": None}
    assert [(e["who"], e["nn"], e["result"], e["reason"], e["pr"]) for e in events(glane, "ticket")] == [
        ("test-run", "01", "merged", None, 42)]
    assert events(glane, "main_moved", "compile") == []


def red_batch(lane):
    """Batch 01, 02 (turns the suite red), 03."""
    wt2 = lane.add_ticket("2", "two.txt")
    (wt2 / "suite.sh").write_text("#!/bin/sh\nexit 1\n")
    git("commit", "-q", "-am", "break suite", cwd=wt2)
    lane.enqueue("01")
    lane.enqueue("02", wt=wt2)
    lane.enqueue("03", wt=lane.add_ticket("3", "three.txt"))


RED_BATCH_TICKETS = [("02", "red", None, None), ("03", "requeued", "stacked on a red ticket", None),
                     ("01", "merged", None, 42)]


def test_red_batch_logs_each_bisect_run_and_each_ticket_outcome(lane, gh):
    red_batch(lane)
    r = lane.land()
    assert r.returncode == 1
    suites = events(lane, "suite")
    assert [(e["pipe"], e["batch"], e["batch_size"], e["phase"], e["result"]) for e in suites] == [
        ("A", ["test-run/01", "test-run/02", "test-run/03"], 3, "stack", "red"),
        ("A", ["test-run/01"], 1, "bisect", "green"),
        ("A", ["test-run/01", "test-run/02"], 2, "bisect", "red")]
    assert {(e["round"], e["base"]) for e in suites} == {(1, suites[0]["base"])}
    assert all(e["modules"] == [] and e["module_test_s"] == {} for e in suites)  # no module graph, no XML
    assert [(e["nn"], e["result"], e["reason"], e["pr"]) for e in events(lane, "ticket")] == RED_BATCH_TICKETS


# The e2e step logs each run's directory and fails on a tree holding feature/G.kt.
E2E_CMD = "sh -c 'pwd >> \"$GH_FAKE_DIR/e2e.log\"; [ ! -e feature/G.kt ]'"


@pytest.fixture
def e2e_lane(tmp_path, gh, profile_text, real_runs):
    """glane factory whose PROFILE has `- e2e: <E2E_CMD>   # when: <when>`."""
    gh.set(runs=real_runs, create_url=PR_URL, create_branch="ticket/1")
    return lambda when: Lane(tmp_path, f"{profile_text}- e2e: {E2E_CMD}   # when: {when}\n", graph=GRAPH,
                             ticket_file="feature/F.kt")


def e2e_runs(gh):
    p = gh.dir / "e2e.log"
    return len(p.read_text().splitlines()) if p.exists() else 0


def test_suite_runs_the_e2e_step_when_the_batch_touches_a_when_module(e2e_lane, gh):
    lane = e2e_lane("app, feature")
    lane.enqueue()
    r = lane.land()
    assert r.returncode == 0, r.stdout + r.stderr
    assert e2e_runs(gh) == 1
    (suite,) = events(lane, "suite")
    assert suite["result"] == "green" and suite["e2e"].pop("wall_s") in (0, 1)
    assert suite["e2e"] == {"due": True, "trigger": ["feature"], "ran": True}


def test_suite_skips_the_e2e_step_when_no_batch_module_matches(e2e_lane, gh):
    lane = e2e_lane("app, core")
    lane.enqueue()
    r = lane.land()
    assert r.returncode == 0, r.stdout + r.stderr
    assert e2e_runs(gh) == 0
    (suite,) = events(lane, "suite")
    assert suite["e2e"] == {"due": False, "trigger": [], "ran": False, "wall_s": None}


def test_red_e2e_step_is_a_red_suite_and_the_bisect_runs_it_too(e2e_lane, gh):
    lane = e2e_lane("feature")
    lane.enqueue("01")
    lane.enqueue("02", wt=lane.add_ticket("2", "feature/G.kt"))
    r = lane.land()
    assert r.returncode == 1
    res = {x["nn"]: x for x in lane.results(r)}
    assert (res["01"]["result"], res["02"]["result"]) == ("merged", "red")
    assert re.search(r"^merge_lane: e2e rc=1 wall_s=\d+$", open(res["02"]["log"]).read(), re.M)
    assert [(e["phase"], e["batch_size"], e["result"], e["e2e"]["ran"]) for e in events(lane, "suite")] == [
        ("stack", 2, "red", True), ("bisect", 1, "green", True)]
    assert e2e_runs(gh) == 2


def test_compile_check_after_main_moved_never_runs_the_e2e_step(e2e_lane, gh):
    lane = e2e_lane("feature")
    lane.move_main("core/C.kt")
    lane.enqueue()
    r = lane.land()
    assert r.returncode == 0, r.stdout + r.stderr
    assert "merge: test-run/01 main moved 1 commits — compile (core,feature)" in merge_lines(r)
    assert e2e_runs(gh) == 1  # the suite's only
    (suite,), (check,) = events(lane, "suite"), events(lane, "compile")
    assert suite["e2e"]["due"] and check["e2e"] is None


def test_rerun_after_main_moved_recomputes_whether_the_e2e_step_is_due(e2e_lane, gh):
    lane = e2e_lane("app")
    # main moves the batch's module and widens `when:` to it: the rerun's suite now runs the step
    lane.move_main("feature/Other.kt", also="sed -i.bak 's/# when: app$/# when: app, feature/' PROFILE.md && "
                                             "rm PROFILE.md.bak")
    lane.enqueue()
    r = lane.land()
    assert r.returncode == 0, r.stdout + r.stderr
    assert "merge: test-run/01 main moved 1 commits — rerun (feature)" in merge_lines(r)
    assert e2e_runs(gh) == 1
    first, rerun = events(lane, "suite")
    assert first["e2e"] == {"due": False, "trigger": [], "ran": False, "wall_s": None}
    assert (rerun["e2e"]["due"], rerun["e2e"]["trigger"], rerun["e2e"]["ran"]) == (True, ["feature"], True)


def test_event_fields_that_raise_during_a_bisect_change_no_outcome(lane, gh, monkeypatch, capsys):
    """In process, so batch_modules can be patched to fail on every bisect run (not the first suite)."""
    red_batch(lane)
    calls = []

    def flaky(*args):
        calls.append(args)
        if len(calls) > 1:
            raise RuntimeError("graph boom")
        return []

    monkeypatch.setattr(ml, "batch_modules", flaky)
    monkeypatch.chdir(lane.co)
    rc = ml.land(argparse.Namespace(who="test-run", max=ml.MAX_BATCH))
    out, err = capsys.readouterr()
    assert rc == 1
    results = [json.loads(l) for l in out.splitlines() if l.startswith("{")]
    assert [(x["nn"], x["result"]) for x in results] == [(nn, res) for nn, res, _, _ in RED_BATCH_TICKETS]
    assert err.count("merge_lane: event log: RuntimeError('graph boom')") == 2  # both bisect runs
    assert [(e["phase"], e["result"]) for e in events(lane, "suite")] == [("stack", "red")]
    assert [(e["nn"], e["result"], e["reason"], e["pr"]) for e in events(lane, "ticket")] == RED_BATCH_TICKETS
    assert lane.queue_nns() == ["03"]


def test_red_ticket_stays_red_when_main_moves_during_its_bisect(glane, gh):
    """The restack after a bisect takes only the green prefix: the red ticket never merges."""
    glane.move_main("core/C.kt")  # the first build calling the hook: the bisect run on 01 (02's suite never calls it)
    red_batch(glane)
    r = glane.land()
    assert r.returncode == 1, r.stdout + r.stderr
    assert [(x["nn"], x["result"], x.get("reason")) for x in glane.results(r)] == [
        ("02", "red", None), ("03", "requeued", "stacked on a red ticket"), ("01", "merged", None)]
    assert "merge: test-run/01 main moved 1 commits — compile (core,feature)" in merge_lines(r)
    assert gradle_log(gh) == [compile_tasks("feature") + " --dry-run", compile_tasks("feature")]
    assert len([c for c in gh.calls() if c[:2] == ["pr", "merge"]]) == 1
    assert glane.queue_nns() == ["03"]


def test_requeued_batch_logs_every_round_and_rerun_decision(glane, gh):
    glane.move_main("feature/Other.kt", times=9)
    glane.enqueue()
    r = glane.land()
    assert r.returncode == 1
    suites = events(glane, "suite")
    assert [(e["round"], e["result"], e["modules"]) for e in suites] == [(n, "green", ["feature"]) for n in (1, 2, 3)]
    assert len({e["base"] for e in suites}) == 3  # each round restacked on the moved main
    assert [(e["pipe"], e["batch"], e["phase"], e["commits"], e["decision"], e["reason"])
            for e in events(glane, "main_moved")] == [("A", ["test-run/01"], "stack", 1, d, "feature")
                                                      for d in ("rerun", "rerun", "requeue")]
    assert [(e["nn"], e["result"], e["reason"]) for e in events(glane, "ticket")] == [
        ("01", "requeued", "main keeps moving")]


def test_compile_check_between_merges_is_logged_with_its_decision(make_lane, gh):
    lane = stack_batch(make_lane, gh, "core/C.kt", third=True)
    (gh.dir / "compile_red").write_text("")
    lane.land()
    assert [(e["batch"], e["phase"], e["decision"], e["reason"]) for e in events(lane, "main_moved")] == [
        (["test-run/02", "test-run/03"], "merge", "compile", "core,docs,feature")]  # 03 adds docs/E.md
    (check,) = events(lane, "compile")
    assert (check["batch"], check["phase"], check["modules"], check["result"]) == (
        ["test-run/02"], "merge", ["feature"], "red")


def test_event_log_failure_changes_no_decision_or_exit_code(lane, gh):
    common = Path(git("rev-parse", "--path-format=absolute", "--git-common-dir", cwd=lane.co))
    (common / "agent-builds" / ml.EVENTS).mkdir(parents=True)  # appending to it fails
    lane.enqueue()
    r = lane.land()
    assert r.returncode == 0, r.stdout + r.stderr
    assert lane.results(r)[0]["result"] == "merged" and lane.queue_nns() == []
    assert "merge_lane: event log: IsADirectoryError" in r.stderr


# --------------------------------- one lane per repository: shared, pipelined

def test_two_sessions_share_one_batch_and_each_wait_prints_only_its_own(lane, gh):
    gh.set(land=True)
    lane.enqueue("01", who="run-a")
    lane.enqueue("01", wt=lane.add_ticket("2", "two.txt"), who="run-b")
    waits = {who: lane.wait(who, "01") for who in ("run-a", "run-b")}  # both start a land; one gets the lane
    outs = {who: w.communicate(timeout=120) for who, w in waits.items()}
    lane.idle()
    (suite,) = events(lane, "suite")
    assert (suite["pipe"], suite["batch"]) == ("A", ["run-a/01", "run-b/01"])
    for who, (o, e) in outs.items():
        assert waits[who].returncode == 0, o + e
        lines = o.splitlines()
        assert lines[0] == f"merge: batch run-a/01,run-b/01 suite green tested @ {suite['top']} (1 suites)"
        assert re.fullmatch(r"slice: 01 PR #42 merged @ \w{7}", lines[1])
        assert [(x["who"], x["nn"], x["result"]) for x in map(json.loads, lines[2:])] == [(who, "01", "merged")]
    assert lane.queue_nns() == []


def test_wait_after_the_land_replays_its_lines_from_the_event_log(lane, gh):
    lane.enqueue()
    r = lane.land()
    assert r.returncode == 0, r.stdout + r.stderr
    w = lane.wait("test-run", "01")
    o, e = w.communicate(timeout=60)
    assert w.returncode == 0, o + e
    assert o.splitlines() == r.stdout.splitlines()
    assert len(events(lane, "suite")) == 1  # nothing ran again
    w = lane.wait("test-run", "09")
    o, e = w.communicate(timeout=60)
    assert w.returncode == 1 and "no enqueue of test-run/09" in e


def test_wait_on_red_main_reports_the_pause_and_keeps_the_queue(lane, gh, real_runs):
    gh.set(runs=real_runs[4:])  # real window whose newest finished run is the failure
    lane.enqueue()
    w = lane.wait("test-run", "01")
    o, e = w.communicate(timeout=60)
    assert w.returncode == 3, o + e
    assert o.splitlines()[0] == "main red; lane paused"
    assert lane.queue_nns() == ["01"]
    assert not any(c[:2] in (["pr", "create"], ["pr", "merge"]) for c in gh.calls())


def wait_results(o):
    return [json.loads(l) for l in o.splitlines() if l.startswith("{")]


HEAD_MOVED = "GraphQL: Head branch was modified. Review and try the merge again. (mergePullRequest)"
BASE_MOVED = "GraphQL: Base branch was modified. Review and try the merge again. (mergePullRequest)"


def test_wait_lands_a_requeued_ticket_again_until_it_merges(lane, gh):
    gh.set(merge_seq=["head_moved"])  # the PR head is not the pushed sha: requeued, never retried
    lane.enqueue()
    w = lane.wait("test-run", "01")
    o, e = w.communicate(timeout=120)
    assert w.returncode == 0, o + e
    assert [(x["result"], x.get("reason")) for x in wait_results(o)] == [
        ("requeued", f"merge refused for PR #42: {HEAD_MOVED}"), ("merged", None)]
    lane.idle()
    assert lane.queue_nns() == []
    assert len([c for c in gh.calls() if c[:2] == ["pr", "merge"]]) == 2  # one per land


def test_base_moved_by_the_batchs_own_squash_is_retried_and_the_whole_batch_lands(lane, gh):
    """GitHub still settles main after 01's squash when 02's merge comes: the retry lands it."""
    gh.set(land=True, merge_seq=["ok", "base_moved"])
    lane.enqueue("01")
    lane.enqueue("02", wt=lane.add_ticket("2", "two.txt"))
    lane.enqueue("03", wt=lane.add_ticket("3", "three.txt"))
    r = lane.land()
    assert r.returncode == 0, r.stdout + r.stderr
    res = lane.results(r)
    assert [(x["nn"], x["result"]) for x in res] == [("01", "merged"), ("02", "merged"), ("03", "merged")]
    assert lane.queue_nns() == []
    assert [(e["pipe"], e["result"]) for e in events(lane, "suite")] == [("A", "green")]  # one suite for all three
    merges = [c[c.index("--match-head-commit") + 1] for c in gh.calls() if c[:2] == ["pr", "merge"]]
    assert [m[:7] for m in merges] == [x["tested"] for x in (res[0], res[1], res[1], res[2])]  # retry: same head
    # Every PR targets main, and 02 and 03 sit on the squash just before theirs: the pushed head the
    # merge pins is the rebased one.
    assert [c[c.index("--base") + 1] for c in gh.calls() if c[:2] == ["pr", "create"]] == ["main"] * 3
    git("fetch", "-q", "origin", cwd=lane.co)
    assert [git("rev-parse", f"{m}^", cwd=lane.co) for m in merges[1::2]] == [
        git("rev-parse", f"origin/main~{k}", cwd=lane.co) for k in (2, 1)]
    assert [x["sha"] for x in res] == [git("rev-parse", f"origin/main~{k}", cwd=lane.co)[:7] for k in (2, 1, 0)]


def test_base_moved_past_its_retries_requeues_the_ticket(lane, gh):
    gh.set(merge="base_moved")
    lane.enqueue()
    r = lane.land()
    assert [(x["result"], x["reason"]) for x in lane.results(r)] == [
        ("requeued", f"merge refused for PR #42: {BASE_MOVED}")]
    assert len([c for c in gh.calls() if c[:2] == ["pr", "merge"]]) == ml.MERGE_RETRIES + 1
    assert lane.queue_nns() == ["01"]


@pytest.mark.parametrize("outside, result, line", [("docs/Other.md", "merged", "push (docs,feature)"),
                                                   ("feature/Other.kt", "requeued", "rerun (feature)")])
def test_base_moved_by_an_outside_push_runs_the_main_moved_step_again(make_lane, gh, outside, result, line):
    """main moved for real between 02's push and its merge: rebase and decide again, never a blind retry."""
    lane = make_lane(ticket_file="docs/D.md")
    gh.set(land=True, merge_seq=["ok", "base_moved"])
    lane.move_main(outside, hook="on_base_moved")
    lane.enqueue("01")
    lane.enqueue("02", wt=lane.add_ticket("2", "feature/F.kt"))
    r = lane.land()
    res = lane.results(r)
    assert [(x["nn"], x["result"]) for x in res] == [("01", "merged"), ("02", result)]
    assert f"merge: test-run/02 main moved 1 commits — {line}" in merge_lines(r)
    merges = [c[c.index("--match-head-commit") + 1] for c in gh.calls() if c[:2] == ["pr", "merge"]]
    if result == "requeued":
        assert len(merges) == 2 and res[1]["reason"] == "main moved: related"
        assert lane.queue_nns() == ["02"]
        return
    assert len(merges) == 3 and merges[2] != merges[1]  # 02 rebased onto the outside commit, pushed again
    git("fetch", "-q", "origin", cwd=lane.co)
    assert git("rev-parse", f"{merges[2]}^", cwd=lane.co) == git("rev-parse", "origin/main~1", cwd=lane.co)
    assert git("log", "-1", "--format=%s", "origin/main~1", cwd=lane.co) == "outside 0"


def test_requeue_cap_ends_the_ticket_stuck(lane, gh):
    gh.set(merge="head_moved")
    lane.enqueue()
    entry = json.loads(lane.queue.read_text())
    lane.queue.write_text(json.dumps(dict(entry, requeues=ml.REQUEUE_CAP - 1)) + "\n")
    w = lane.wait("test-run", "01")
    o, e = w.communicate(timeout=120)
    assert w.returncode == 1, o + e
    assert [(x["result"], x["reason"]) for x in wait_results(o)] == [
        ("requeued", f"merge refused for PR #42: {HEAD_MOVED}"), ("stuck", f"merge refused for PR #42: {HEAD_MOVED}")]
    lane.idle()
    assert lane.queue_nns() == []


def test_requeues_for_red_tickets_below_never_make_a_ticket_stuck(lane, gh):
    """09 sits on seven red tickets (02-08), one leaving per land: requeued 7 times, never by its own doing."""
    (lane.co / "suite.sh").write_text("#!/bin/sh\n[ ! -d red ]\n")
    git("commit", "-q", "-am", "the suite fails on a red/ dir", cwd=lane.co)
    git("push", "-q", "origin", "main", cwd=lane.co)
    for n in range(2, 10):
        lane.enqueue(f"0{n}", wt=lane.add_ticket(str(n), f"red/{n}" if n < 9 else "nine.txt"))
    results = []
    for _ in range(12):
        if not lane.queue_nns():
            break
        results += lane.results(lane.land())
    assert {x["nn"]: x["result"] for x in results} == {**{f"0{n}": "red" for n in range(2, 9)}, "09": "merged"}
    assert [x["result"] for x in results if x["nn"] == "09"].count("requeued") > ml.REQUEUE_CAP
    assert "stuck" not in [x["result"] for x in results]


def test_wait_fails_when_its_ticket_left_the_queue_without_a_result(lane, gh):
    lane.enqueue()
    lane.queue.write_text("")
    w = lane.wait("test-run", "01")
    o, e = w.communicate(timeout=60)
    assert w.returncode == 1 and "test-run/01 left the queue without a result" in e
    assert not (lane.dir / "land.log").exists()  # no land started


def test_wait_fails_when_land_exits_without_a_ticket_result(lane, gh):
    gh.set(runs=None)  # `gh run list` breaks: main_health status fails, land exits 1 before any ticket
    lane.enqueue()
    w = lane.wait("test-run", "01")
    o, e = w.communicate(timeout=60)
    assert w.returncode == 1 and "land exited 1 without a ticket result" in e
    assert "main_health status failed" in (lane.dir / "land.log").read_text()
    assert lane.queue_nns() == ["01"]


# A's suite (scratch wt/0) waits up to 20 s for B's suite (wt/1) to start: it sees B only when they overlap.
OVERLAP = """#!/bin/sh
case "$(pwd)" in
  */wt/1) touch "$GH_FAKE_DIR/b_started";;
  */wt/0) i=0
    while [ ! -e "$GH_FAKE_DIR/b_started" ] && [ $i -lt 400 ]; do sleep 0.05; i=$((i+1)); done
    [ -e "$GH_FAKE_DIR/b_started" ] && echo overlapped > "$GH_FAKE_DIR/a_saw_b";;
esac
"""


def test_batch_b_runs_its_suite_on_a_top_while_a_runs_and_merges_after_a(lane, gh):
    gh.set(land=True)
    (gh.dir / "on_build").write_text(OVERLAP)
    (gh.dir / "on_build").chmod(0o755)
    lane.enqueue("01")
    for n in (2, 3, 4):
        lane.enqueue(f"0{n}", wt=lane.add_ticket(str(n), f"t{n}.txt"))
    r = lane.land("--max", "2")
    assert r.returncode == 0, r.stdout + r.stderr
    assert [(x["nn"], x["result"]) for x in lane.results(r)] == [(f"0{n}", "merged") for n in (1, 2, 3, 4)]
    assert (gh.dir / "a_saw_b").read_text() == "overlapped\n"
    a, b = events(lane, "suite")
    assert [(e["pipe"], e["batch"]) for e in (a, b)] == [
        ("A", ["test-run/01", "test-run/02"]), ("B", ["test-run/03", "test-run/04"])]
    assert b["base"] == a["top"]  # B tested on A's top, and main after A's merges is that tree
    assert events(lane, "main_moved") == []
    assert [e["pipe"] for e in events(lane, "ticket")] == ["A", "A", "B", "B"]
    assert re.search(r"^merge: batch test-run/03,test-run/04 suite green tested @ \w{7} \(1 suites\)$", r.stdout, re.M)


def test_red_batch_a_kills_and_requeues_batch_b_stacked_on_it(lane, gh):
    wt2 = lane.add_ticket("2", "two.txt")
    # Red everywhere; in B's scratch worktree it first hangs, so B still runs when A goes red.
    (wt2 / "suite.sh").write_text('#!/bin/sh\ncase "$(pwd)" in */wt/1) sleep 60;; esac\nexit 1\n')
    git("commit", "-q", "-am", "break suite", cwd=wt2)
    lane.enqueue("01")
    lane.enqueue("02", wt=wt2)
    lane.enqueue("03", wt=lane.add_ticket("3", "three.txt"))
    r = lane.land("--max", "2")
    assert r.returncode == 1
    assert [(x["nn"], x["result"], x.get("reason")) for x in lane.results(r)] == [
        ("03", "requeued", "stacked on a red batch"), ("02", "red", None), ("01", "merged", None)]
    suites = events(lane, "suite")
    assert [(e["pipe"], e["batch"], e["phase"], e["result"]) for e in suites] == [
        ("A", ["test-run/01", "test-run/02"], "stack", "red"), ("B", ["test-run/03"], "stack", "discarded"),
        ("A", ["test-run/01"], "bisect", "green")]
    assert suites[1]["wall_s"] < 30  # killed, not waited out
    assert lane.queue_nns() == ["03"]


@pytest.mark.parametrize("outside,kind,label,suites", [
    ("feature/Other.kt", "rerun", "feature", 2),  # same module as B: B reruns on the moved main
    ("docs/D.md", "push", "docs,feature", 1),     # unrelated: B's green run stands
])
def test_outside_merge_after_a_applies_the_rerun_rule_to_b(make_lane, gh, outside, kind, label, suites):
    lane = make_lane(ticket_file="docs/A.md")
    gh.set(land=True)
    lane.move_main(outside, hook="after_merge")  # lands right after A's merge, before B's main check
    lane.enqueue("01")
    lane.enqueue("02", wt=lane.add_ticket("2", "feature/F.kt"))
    r = lane.land("--max", "1")
    assert r.returncode == 0, r.stdout + r.stderr
    assert [(x["nn"], x["result"]) for x in lane.results(r)] == [("01", "merged"), ("02", "merged")]
    assert f"merge: test-run/02 main moved 1 commits — {kind} ({label})" in merge_lines(r)
    moved = events(lane, "main_moved")
    assert (moved[0]["pipe"], moved[0]["phase"], moved[0]["commits"]) == ("B", "stack", 1)
    assert [e["round"] for e in events(lane, "suite") if e["pipe"] == "B"] == list(range(1, suites + 1))
    assert re.search(rf"^merge: batch test-run/02 suite green tested @ \w{{7}} \({suites} suites\)$", r.stdout, re.M)


def test_batches_cap_at_five_tickets(lane, gh):
    gh.set(land=True)
    lane.enqueue("01")
    for n in range(2, 7):
        lane.enqueue(f"0{n}", wt=lane.add_ticket(str(n), f"t{n}.txt"))
    r = lane.land()
    assert r.returncode == 0, r.stdout + r.stderr
    assert [(x["nn"], x["result"]) for x in lane.results(r)] == [(f"0{n}", "merged") for n in range(1, 7)]
    assert [(e["pipe"], e["batch_size"]) for e in events(lane, "suite")] == [("A", 5), ("B", 1)]


def test_red_compile_between_a_merges_discards_b(make_lane, gh):
    lane = stack_batch(make_lane, gh, "core/C.kt", third=True)  # A = 01, 02; B = 03
    (gh.dir / "compile_red").write_text("")
    r = lane.land("--max", "2")
    assert r.returncode == 1
    assert [(x["nn"], x["result"], x.get("reason")) for x in lane.results(r)] == [
        ("01", "merged", None), ("02", "red", None), ("03", "requeued", "stacked on a red batch")]
    assert [(e["pipe"], e["result"]) for e in events(lane, "suite")] == [("A", "green"), ("B", "discarded")]
    assert lane.queue_nns() == ["03"]


def test_b_on_a_partly_refused_a_merges_through_the_tree_compare(make_lane, gh):
    lane = make_lane(ticket_file="docs/A.md")
    gh.set(land=True, merge_seq=["ok", "refused"])
    lane.enqueue("01")
    lane.enqueue("02", wt=lane.add_ticket("2", "feature/F.kt"))
    lane.enqueue("03", wt=lane.add_ticket("3", "docs/E.md"))
    r = lane.land("--max", "2")
    assert r.returncode == 1
    assert [(x["nn"], x["result"]) for x in lane.results(r)] == [("01", "merged"), ("02", "refused"), ("03", "merged")]
    assert lane.queue_nns() == []
    # main lacks 02 of A's top, the base B ran on: B's run stands over that diff (feature vs docs).
    assert [(e["pipe"], e["phase"], e["commits"], e["decision"], e["reason"]) for e in events(lane, "main_moved")] == [
        ("B", "stack", 0, "push", "docs,feature"), ("B", "merge", 0, "push", "docs,feature")]


def test_b_on_a_restacked_a_merges_through_the_tree_compare(make_lane, gh):
    lane = make_lane(ticket_file="feature/F.kt")
    gh.set(land=True)
    lane.move_main("feature/Other.kt", only="*/wt/0")  # once, in A's first suite: A reruns, B's run stands
    lane.enqueue("01")
    lane.enqueue("02", wt=lane.add_ticket("2", "docs/D.md"))
    r = lane.land("--max", "1")
    assert r.returncode == 0, r.stdout + r.stderr
    assert [(x["nn"], x["result"]) for x in lane.results(r)] == [("01", "merged"), ("02", "merged")]
    suites = events(lane, "suite")
    a = [e for e in suites if e["pipe"] == "A"]
    (b,) = [e for e in suites if e["pipe"] == "B"]
    assert [e["round"] for e in a] == [1, 2]
    assert b["base"] == a[0]["top"] != a[1]["top"]  # B ran on A's first top, never on the merged one
    assert [(e["pipe"], e["phase"], e["decision"]) for e in events(lane, "main_moved")] == [
        ("A", "stack", "rerun"), ("B", "stack", "push"), ("B", "merge", "push")]
