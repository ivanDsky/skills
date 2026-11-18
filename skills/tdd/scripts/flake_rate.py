#!/usr/bin/env python3
"""Measure how flaky a Gradle test is: run it N times and count outcomes per test.

Run by the worker that meets a red test it suspects is flaky, before it calls
the test flaky or quarantines it (tdd: Flakes). Run from the repo root, or
pass `--root`.

  flake_rate.py --tests '<gradle --tests filter>' [--module :app]
                [--runs 10] [--task testDebugUnitTest] [--out DIR] [--root DIR]

Each run is `./gradlew <module>:<task> --tests <filter> --rerun`, wrapped in
`build-slot` when that is on PATH. A failing run never stops the loop. The
module's JUnit XML dir (`<module path>/build/test-results/<task>/`) is
emptied before each run, so no run can read a previous run's results.

Artifacts, kept for the ticket: `<out>/run<i>/gradle.log` (stdout + stderr)
and `<out>/run<i>/*.xml` (the run's JUnit results), i = 1..N. Default `--out`:
`<root>/.scratch/flake-rate/<YYYYmmdd-HHMMSS>`.

Classification, per test and run (test = `<classname>.<name>` of a JUnit
`<testcase>`):
  pass   the testcase has no `<failure>`/`<error>`
  fail   the testcase has a `<failure>` or `<error>`
  abort  the test has no result in that run: no XML was produced, the XML is
         unreadable, or the JVM crashed before the test's class was written
         (log matches `exit value 134` or `Process '...' finished with
         non-zero exit value`, e.g. a Robolectric worker killed under load;
         the progress line on stderr then says `JVM crash`). Results the XML
         did record in a crashed run are kept.
Skipped testcases are dropped. A test seen in no run (all runs aborted) is
reported under the `--tests` filter itself.

Output: one line per test, `<test> pass P/N fail F abort A`, then
`verdict: <v>` over all tests. non-pass = fail + abort. Per test: `stable`
when all N pass, `broken` when all N are non-pass, `flaky` otherwise.
Overall: `flaky` if any test is flaky, else `broken` if any is broken, else
`stable`.

Exit code: 0 whenever the N runs completed, whatever the verdict (the verdict
is output, never the exit code); 2 on a usage error (argparse) or when
`<root>/gradlew` is missing.

Quarantine rule (tdd): 2 or more non-pass runs out of 10 -> quarantine with a
tracked ticket.
"""
import argparse
import datetime
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

CRASH = re.compile(r"exit value 134|Process '.*' finished with non-zero exit value")


def module_dir(root, module):
    return root.joinpath(*[p for p in module.split(":") if p])


def task_path(module, task):
    return f"{module.rstrip(':')}:{task}" if module.strip(":") else f":{task}"


def read_results(xml_dir):
    """{test: 'pass'|'fail'} from every readable XML in xml_dir; unreadable files are ignored."""
    results = {}
    for f in sorted(xml_dir.glob("*.xml")):
        try:
            tree = ET.parse(f)
        except ET.ParseError:
            continue
        for case in tree.getroot().iter("testcase"):
            if case.find("skipped") is not None:
                continue
            name = f"{case.get('classname', '')}.{case.get('name', '')}"
            bad = case.find("failure") is not None or case.find("error") is not None
            results[name] = "fail" if bad else "pass"
    return results


def run_once(root, cmd, xml_dir, run_dir):
    """One gradle run. Returns ({test: outcome}, log text)."""
    shutil.rmtree(xml_dir, ignore_errors=True)
    run_dir.mkdir(parents=True, exist_ok=True)
    log = run_dir / "gradle.log"
    with log.open("w") as f:
        subprocess.run(cmd, cwd=root, stdout=f, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
    if xml_dir.is_dir():
        for x in xml_dir.glob("*.xml"):
            shutil.copy(x, run_dir / x.name)
    return read_results(run_dir), log.read_text(errors="replace")


def verdict(p, n):
    return "stable" if p == n else "broken" if p == 0 else "flaky"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Run a Gradle test N times and count pass/fail/abort per test.")
    ap.add_argument("--tests", required=True, help="Gradle --tests filter")
    ap.add_argument("--module", default=":app")
    ap.add_argument("--runs", type=int, default=10)
    ap.add_argument("--task", default="testDebugUnitTest")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--root", type=Path, default=Path.cwd())
    a = ap.parse_args(argv)
    if a.runs < 1:
        ap.error("--runs must be >= 1")
    root = a.root.resolve()
    if not (root / "gradlew").is_file():
        print(f"flake_rate: no gradlew in {root}", file=sys.stderr)
        return 2
    out = a.out or root / ".scratch" / "flake-rate" / datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    xml_dir = module_dir(root, a.module) / "build" / "test-results" / a.task
    cmd = (["build-slot"] if shutil.which("build-slot") else []) + [
        "./gradlew", task_path(a.module, a.task), "--tests", a.tests, "--rerun"]

    runs = []  # (results, crashed)
    for i in range(1, a.runs + 1):
        results, text = run_once(root, cmd, xml_dir, out / f"run{i}")
        runs.append((results, bool(CRASH.search(text))))
        print(f"run {i}/{a.runs}: {len(results)} tests recorded{', JVM crash' if runs[-1][1] else ''}",
              file=sys.stderr)

    tests = sorted({t for r, _ in runs for t in r}) or [a.tests]
    verdicts = []
    for t in tests:
        p = sum(r.get(t) == "pass" for r, _ in runs)
        f = sum(r.get(t) == "fail" for r, _ in runs)
        verdicts.append(verdict(p, a.runs))
        print(f"{t} pass {p}/{a.runs} fail {f} abort {a.runs - p - f}")
    print("verdict: " + next((v for v in ("flaky", "broken") if v in verdicts), "stable"))
    print(f"artifacts: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
