#!/usr/bin/env python3
"""Build identity for parallel worktrees: one install ledger per repo clone.

The ledger lives in the git common dir (shared by every worktree, never
committed): <git-common-dir>/agent-builds/versions.jsonl, one line per install.

  allocate  every install gets a unique identity, recorded under a lock:
            versionCode = max(ledger, installed on device, committed) + 1;
            versionName = <semver>-<slug>.<n>: semver is the release line from
            PROFILE.md (untouched here), n counts installs per slug.
            --release (main only): versionName = plain <semver>, once per semver.
            Prints KEY=VALUE lines (shell-evalable).
  which     what is on the device: installed versionCode -> ledger record.
  list      last N ledger records.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

LOCK_WAIT_S = 30
LOCK_STALE_S = 120


def git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


def ledger_dir(root):
    common = Path(git("rev-parse", "--path-format=absolute", "--git-common-dir", cwd=root))
    d = common / "agent-builds"
    d.mkdir(exist_ok=True)
    return d


def read_ledger(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def slug_for(branch, sha):
    if branch == "HEAD":
        return f"sha-{sha}"
    # main/master keep their name as the slug: main installs need a counter too.
    last = branch.rsplit("/", 1)[-1].lower()
    return re.sub(r"[^a-z0-9]+", "-", last).strip("-")[:24].rstrip("-")


def profile_value(root, key):
    """`- <key>: <value>` from PROFILE.md (trailing `# comment` stripped)."""
    profile = Path(root) / "PROFILE.md"
    if profile.exists():
        m = re.search(rf"^-\s*{re.escape(key)}:\s*([^\s#]+)", profile.read_text(), re.M)
        if m and not m.group(1).startswith("<"):
            return m.group(1)
    return None


def is_semver(s):
    return bool(re.fullmatch(r"\d+\.\d+\.\d+", s or ""))


def next_install(records, slug):
    """Per-slug install counter; keyed by slug so two branches that share one
    (feature/sync, fix/sync) still never produce the same name."""
    return max((r.get("n", 0) for r in records if r.get("slug") == slug), default=0) + 1


def committed_code(root):
    """Last integer on the versionCode line (the fallback after agent wiring)."""
    for name in ("app/build.gradle.kts", "app/build.gradle"):
        f = Path(root) / name
        if f.exists():
            for line in f.read_text().splitlines():
                if re.search(r"\bversionCode\b", line):
                    nums = re.findall(r"\d+", line)
                    if nums:
                        return int(nums[-1])
    return 0


def device_codes(app_id, serial):
    """{serial: installed versionCode or 0}; {} when adb/device unavailable."""
    if not shutil.which("adb"):
        return {}
    try:
        serials = [serial] if serial else [
            line.split()[0]
            for line in subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=10).stdout.splitlines()[1:]
            if line.strip().endswith("\tdevice")
        ]
        out = {}
        for s in serials:
            dump = subprocess.run(["adb", "-s", s, "shell", "dumpsys", "package", app_id],
                                  capture_output=True, text=True, timeout=15).stdout
            codes = [int(c) for c in re.findall(r"versionCode=(\d+)", dump)]
            out[s] = max(codes, default=0)
        return out
    except (subprocess.TimeoutExpired, OSError):
        return {}


class Lock:
    def __init__(self, d):
        self.path = d / "lock"

    def __enter__(self):
        deadline = time.time() + LOCK_WAIT_S
        while True:
            try:
                self.path.mkdir()
                return self
            except FileExistsError:
                try:
                    if time.time() - self.path.stat().st_mtime > LOCK_STALE_S:
                        self.path.rmdir()
                        continue
                except FileNotFoundError:
                    continue
                if time.time() > deadline:
                    sys.exit(f"build_identity: ledger locked > {LOCK_WAIT_S}s: {self.path}")
                time.sleep(0.1)

    def __exit__(self, *exc):
        self.path.rmdir()


def cmd_allocate(a):
    root = a.root
    semver = a.semver
    if not is_semver(semver):
        sys.exit(f"build_identity: version '{semver}' is not major.minor.patch")
    branch = git("rev-parse", "--abbrev-ref", "HEAD", cwd=root)
    sha = git("rev-parse", "--short", "HEAD", cwd=root)
    slug = slug_for(branch, sha)
    d = ledger_dir(root)
    ledger = d / "versions.jsonl"
    devices = device_codes(a.app_id, a.serial)
    base = a.base_code if a.base_code is not None else committed_code(root)
    if a.release and branch not in ("main", "master"):
        sys.exit(f"build_identity: --release only from main/master (on {branch})")
    with Lock(d):
        records = read_ledger(ledger)
        last = max((r["code"] for r in records), default=0)
        code = max(last, max(devices.values(), default=0), base) + 1
        if a.release:
            if any(r.get("release") and r.get("semver") == semver for r in records):
                sys.exit(f"build_identity: {semver} already released — bump PROFILE.md `version:` first")
            n, name = 0, semver
        else:
            n = next_install(records, slug)
            name = f"{semver}-{slug}.{n}"
        apk = f"{a.app_name}-{name}-{code}-{a.variant}.apk"
        if any(r.get("version_name") == name or r.get("apk") == apk for r in records):
            sys.exit(f"build_identity: {name} / {apk} already in the ledger — refusing a duplicate name")
        record = {
            "code": code, "semver": semver, "n": n, "release": a.release, "version_name": name,
            "apk": apk, "variant": a.variant,
            "branch": branch, "slug": slug, "sha": sha, "worktree": str(Path(root).resolve()),
            "device_codes": devices, "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        with ledger.open("a") as f:
            f.write(json.dumps(record) + "\n")
    if not devices:
        print("build_identity: device not reachable — code from ledger/committed only", file=sys.stderr)
    print(f"VERSION_CODE={code}")
    print(f"VERSION_NAME={name}")
    print(f"APK_NAME={apk}")
    print(f"SLUG={slug}")
    print(f"GRADLE_ARGS='-PagentVersionCode={code} -PagentVersionName={name}'")
    print(f"LEDGER={ledger}")


def cmd_which(a):
    records = {r["code"]: r for r in read_ledger(ledger_dir(a.root) / "versions.jsonl")}
    devices = device_codes(a.app_id, a.serial)
    if not devices:
        sys.exit("build_identity: no device reachable")
    for s, code in devices.items():
        r = records.get(code)
        where = f"{r['branch']} @ {r['sha']} ({r['apk']}, {r['time']})" if r else "not in ledger (built elsewhere)"
        print(f"{s}: versionCode {code} — " + ("not installed" if code == 0 else where))


def cmd_list(a):
    for r in read_ledger(ledger_dir(a.root) / "versions.jsonl")[-a.n:]:
        print(f"{r['code']}\t{r['version_name']}\t{r['branch']}@{r['sha']}\t{r['apk']}\t{r['time']}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", default=".", help="worktree root (default: cwd)")
    sub = p.add_subparsers(dest="cmd", required=True)
    al = sub.add_parser("allocate")
    al.add_argument("--app-id", help="applicationId (default: PROFILE.md `- app-id:`)")
    al.add_argument("--app-name", help="artifact prefix (default: PROFILE.md `- app-name:`)")
    al.add_argument("--variant", required=True, choices=["debug", "release"])
    al.add_argument("--semver", help="default: PROFILE.md `- version:`")
    al.add_argument("--base-code", type=int, help="override the committed versionCode")
    al.add_argument("--serial", help="adb serial (default: every connected device)")
    al.add_argument("--release", action="store_true",
                    help="release build from main: versionName = plain semver, once per semver")
    wh = sub.add_parser("which")
    wh.add_argument("--app-id", help="default: PROFILE.md `- app-id:`")
    wh.add_argument("--serial")
    ls = sub.add_parser("list")
    ls.add_argument("-n", type=int, default=10)
    a = p.parse_args()
    for key, attr in (("app-id", "app_id"), ("app-name", "app_name"), ("version", "semver")):
        if hasattr(a, attr) and not getattr(a, attr):
            setattr(a, attr, profile_value(a.root, key))
            if not getattr(a, attr):
                sys.exit(f"build_identity: missing {key} (pass --{'semver' if key == 'version' else key} or set '- {key}:' in PROFILE.md)")
    {"allocate": cmd_allocate, "which": cmd_which, "list": cmd_list}[a.cmd](a)


if __name__ == "__main__":
    main()
