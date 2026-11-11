#!/usr/bin/env python3
"""Ship one APK with a verified build identity: the only path to a device.

Run from the worktree root:
  1. allocate  build_identity.py allocate (unique versionCode + versionName + APK name)
  2. build     ./gradlew :<module>:assemble<Variant> -PagentVersionCode/-PagentVersionName,
               log in .scratch/<slug>/build.log
  3. verify    aapt2 dump badging: versionCode, versionName and package must
               match the allocation and PROFILE.md `- app-id:` (or app-id + `.suffix`)
  4. name      copy to .scratch/<slug>/<APK_NAME>
  5. send      tailscale file cp to the PROFILE.md tailscale `- device:` (skipped
               with --build-only; then `adb install -r "$APK_PATH"` or serve)
  6. evidence  sha256 + bytes, one line in .scratch/<slug>/ledger.md
Prints KEY=VALUE lines (shell-evalable). Progress goes to stderr.

--apk PATH re-sends an APK this script already built (deliver reusing the
user-check build, or a failed send): steps 3, 5, 6 only, checked against its
ledger record.
"""
import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True  # keep the installed skill dir free of __pycache__
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_identity as bi  # noqa: E402

BI = Path(__file__).resolve().parent / "build_identity.py"
TAILSCALE_DOWNLOAD = "https://tailscale.com/download"


def die(msg):
    sys.exit(f"ship_apk: {msg}")


def say(msg):
    print(f"ship_apk: {msg}", file=sys.stderr)


def allocate(a):
    cmd = [sys.executable, str(BI), "--root", str(a.root), "allocate", "--variant", a.variant]
    if a.release:
        cmd.append("--release")
    if a.slug:
        cmd += ["--slug", a.slug]
    p = subprocess.run(cmd, capture_output=True, text=True)
    sys.stderr.write(p.stderr)
    if p.returncode != 0:
        die("allocate failed (see build_identity message above)")
    out = {}
    for line in p.stdout.splitlines():
        key, sep, value = line.partition("=")
        if sep:
            out[key] = shlex.split(value)[0] if value else ""
    missing = [k for k in ("VERSION_CODE", "VERSION_NAME", "APK_NAME", "SLUG") if k not in out]
    if missing:
        die(f"allocate output lacks {', '.join(missing)}")
    return out


def build(a, ident, scratch):
    gradlew = a.root / "gradlew"
    if not gradlew.exists():
        die(f"no ./gradlew in {a.root} — run from the worktree root")
    task = f":{a.module}:assemble{a.variant.capitalize()}"
    log = scratch / "build.log"
    cmd = [str(gradlew), task,
           f"-PagentVersionCode={ident['VERSION_CODE']}", f"-PagentVersionName={ident['VERSION_NAME']}"]
    say(f"building {task} as {ident['VERSION_NAME']} ({ident['VERSION_CODE']}), log: {log}")
    with log.open("w") as f:
        rc = subprocess.run(cmd, cwd=a.root, stdout=f, stderr=subprocess.STDOUT).returncode
    if rc != 0:
        tail = log.read_text(errors="replace").splitlines()[-30:]
        sys.stderr.write("\n".join(tail) + "\n")
        die(f"build failed (exit {rc}); versionCode {ident['VERSION_CODE']} stays burned; log: {log}")
    out_dir = a.root / a.module / "build" / "outputs" / "apk" / a.variant
    apks = sorted(out_dir.glob("*.apk"))
    if len(apks) != 1:
        die(f"expected exactly one APK in {out_dir}, found {len(apks)}: {[p.name for p in apks]}")
    if "unsigned" in apks[0].name:
        die(f"{apks[0].name} is unsigned — the {a.variant} signing config is missing; it cannot install")
    return apks[0]


def sdk_dirs(root):
    for env in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        if os.environ.get(env):
            yield Path(os.environ[env])
    props = root / "local.properties"
    if props.exists():
        m = re.search(r"^sdk\.dir\s*=\s*(.+)$", props.read_text(), re.M)
        if m:
            yield Path(m.group(1).strip().replace("\\:", ":").replace("\\\\", "\\"))
    yield Path.home() / "Library" / "Android" / "sdk"


def find_aapt2(root):
    def key(p):
        return tuple(int(x) if x.isdigit() else -1 for x in re.split(r"[.-]", p.parent.name))
    for sdk in sdk_dirs(root):
        found = sorted((sdk / "build-tools").glob("*/aapt2"), key=key)
        if found:
            return found[-1]
    die("aapt2 not found (ANDROID_HOME, ANDROID_SDK_ROOT, local.properties sdk.dir, ~/Library/Android/sdk) — see android-env")


def badging(root, apk):
    p = subprocess.run([str(find_aapt2(root)), "dump", "badging", str(apk)], capture_output=True, text=True)
    m = re.search(r"^package: name='([^']*)' versionCode='([^']*)' versionName='([^']*)'", p.stdout, re.M)
    if p.returncode != 0 or not m:
        die(f"aapt2 dump badging failed on {apk}: {(p.stderr or p.stdout).strip()[:200]}")
    return {"package": m.group(1), "code": m.group(2), "name": m.group(3)}


def verify(app_id, ident, found):
    """Refuse unless the APK's real identity equals the allocation."""
    version_off = found["code"] != str(ident["VERSION_CODE"]) or found["name"] != ident["VERSION_NAME"]
    problems = []
    if found["code"] != str(ident["VERSION_CODE"]):
        problems.append(f"versionCode {found['code']} != allocated {ident['VERSION_CODE']}")
    if found["name"] != ident["VERSION_NAME"]:
        problems.append(f"versionName {found['name']} != allocated {ident['VERSION_NAME']}")
    if not (found["package"] == app_id or found["package"].startswith(app_id + ".")):
        problems.append(f"package {found['package']} is not {app_id} (or {app_id}.<suffix>)")
    if problems:
        hint = (" (Gradle wiring for -PagentVersionCode/-PagentVersionName missing? see deliver references/build-identity.md)"
                if version_off else "")
        die("refusing to ship — " + "; ".join(problems) + hint)


def profile_device(root):
    """(name, ip) from the PROFILE.md `- tailscale:` entry's `- device: <name> @ <ip>` line."""
    profile = root / "PROFILE.md"
    if not profile.exists():
        return None
    lines = profile.read_text().splitlines()
    for i, line in enumerate(lines):
        if re.match(r"^-\s*tailscale:", line):
            for sub in lines[i + 1:]:
                if not sub.startswith((" ", "\t")):
                    break
                m = re.match(r"^\s+-\s*device:\s*([^\s#@]+)(?:\s*@\s*([^\s#]+))?", sub)
                if m and not m.group(1).startswith("<"):
                    return m.group(1), m.group(2)
    return None


def tailscale_ready():
    if not shutil.which("tailscale"):
        die(f"tailscale CLI missing — install and log in: {TAILSCALE_DOWNLOAD}")
    p = subprocess.run(["tailscale", "status"], capture_output=True, text=True)
    if p.returncode != 0:
        die(f"tailscale not running or logged out ({(p.stderr or p.stdout).strip()[:120]}) — {TAILSCALE_DOWNLOAD}")


def send(apk, targets):
    errors = []
    for target in targets:
        say(f"taildrop {apk.name} → {target}")
        p = subprocess.run(["tailscale", "file", "cp", str(apk), f"{target}:"], capture_output=True, text=True)
        if p.returncode == 0:
            return target
        errors.append(f"{target}: {(p.stderr or p.stdout).strip()[:160]}")
    die("tailscale file cp failed — " + " | ".join(errors) + " (`tailscale file cp --targets` lists valid names)")


def ledger_record(root, apk_name):
    for r in bi.read_ledger(bi.ledger_dir(root) / "versions.jsonl"):
        if r.get("apk") == apk_name:
            return r
    die(f"{apk_name} is not in the build ledger — only APKs allocated by build_identity.py ship")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--slug", help="explicit build-identity slug (default: last branch segment)")
    p.add_argument("--device", help="tailscale machine name or IP (default: PROFILE.md tailscale `- device:`)")
    p.add_argument("--variant", choices=["debug", "release"], help="default: release with --release, else debug")
    p.add_argument("--release", action="store_true", help="release build from main (plain semver versionName)")
    p.add_argument("--module", default="app", help="Gradle application module (default: app)")
    p.add_argument("--build-only", action="store_true", help="build, verify, name; no send (adb install or serve next)")
    p.add_argument("--apk", type=Path, help="re-send an APK this script already built and named; no build")
    a = p.parse_args()
    a.root = Path.cwd()
    a.variant = a.variant or ("release" if a.release else "debug")
    app_id = bi.profile_value(a.root, "app-id")
    if not app_id:
        die("PROFILE.md has no `- app-id:` line — needed to verify the package")

    targets = []
    if not a.build_only:  # check the route before burning a versionCode
        tailscale_ready()
        if a.device:
            targets = [a.device]
        else:
            dev = profile_device(a.root)
            if not dev:
                die("no --device and no `- device: <name> @ <ip>` under PROFILE.md `- tailscale:` — resolve it per deploy-tailscale §2")
            targets = [t for t in dev if t]

    if a.apk:
        apk = a.apk.resolve()
        if not apk.exists():
            die(f"{apk} does not exist")
        r = ledger_record(a.root, apk.name)
        ident = {"VERSION_CODE": str(r["code"]), "VERSION_NAME": r["version_name"], "APK_NAME": r["apk"], "SLUG": r["slug"]}
        verify(app_id, ident, badging(a.root, apk))
        scratch = a.root / ".scratch" / ident["SLUG"]
        scratch.mkdir(parents=True, exist_ok=True)
        named = apk
    else:
        ident = allocate(a)
        scratch = a.root / ".scratch" / ident["SLUG"]
        scratch.mkdir(parents=True, exist_ok=True)
        built = build(a, ident, scratch)
        verify(app_id, ident, badging(a.root, built))
        named = scratch / ident["APK_NAME"]
        shutil.copy2(built, named)

    device = send(named, targets) if targets else "build-only"
    data = named.read_bytes()
    sha256, size = hashlib.sha256(data).hexdigest(), len(data)
    head = bi.git("rev-parse", "--short", "HEAD", cwd=a.root)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with (scratch / "ledger.md").open("a") as f:
        f.write(f"- {now} ship: {ident['APK_NAME']} versionName={ident['VERSION_NAME']} "
                f"versionCode={ident['VERSION_CODE']} sha={head} device={device} sha256={sha256} bytes={size}\n")
    for key, value in (("APK_PATH", named), ("APK_NAME", ident["APK_NAME"]), ("VERSION_NAME", ident["VERSION_NAME"]),
                       ("VERSION_CODE", ident["VERSION_CODE"]), ("SLUG", ident["SLUG"]), ("SHA256", sha256),
                       ("BYTES", size), ("DEVICE", device)):
        print(f"{key}={shlex.quote(str(value))}")


if __name__ == "__main__":
    main()
