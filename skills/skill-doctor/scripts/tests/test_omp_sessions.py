"""Tests for omp_sessions.py against a fixture tree that mirrors real omp shapes.

Run: python3 -m unittest discover -s skills/skill-doctor/scripts/tests -v
"""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.dirname(HERE)
sys.path.insert(0, SCRIPTS_DIR)

import omp_sessions as om  # noqa: E402

FIXTURES = os.path.join(HERE, "fixtures", "sessions")
SKILLS = os.path.join(HERE, "fixtures", "skills")


class CollectTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = tempfile.mkdtemp()
        with contextlib.redirect_stdout(io.StringIO()):
            rc = om.main(["collect", "--root", FIXTURES, "--project", "*Demo",
                          "--since", "2026-11-10", "--until", "2026-11-12", "--out", cls.out])
        assert rc == 0
        with open(os.path.join(cls.out, "metrics.json")) as fh:
            cls.metrics = json.load(fh)
        cls.s = cls.metrics["sessions"][0]

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.out)

    def test_window_excludes_old_sessions(self):
        self.assertEqual([s["key"] for s in self.metrics["sessions"]], ["ws-Demo--2026-11-11T10-00-00"])

    def test_cost_includes_side_calls_and_subagents(self):
        # orchestrator turns 0.95 + title side call 0.05 + T01Gap 1.00 + R01 0.10
        # + seance 0.40 + nested scout 0.02
        self.assertAlmostEqual(self.s["cost"]["total"], 0.95, places=3)
        self.assertAlmostEqual(self.s["side_cost"], 0.05, places=3)
        self.assertAlmostEqual(self.s["total_cost"], 2.52, places=2)

    def test_ask_wait_and_question_count(self):
        asks = self.s["asks"]
        self.assertEqual(asks["count"], 1)
        self.assertEqual(asks["questions"], 2)  # one legend, one label outside a fieldset
        self.assertAlmostEqual(asks["wait_h"], 0.5, places=2)

    def test_skill_detection_is_structural(self):
        skills = self.s["skills"]
        self.assertEqual(skills["model_invoked"], {"implement": 1})
        self.assertEqual(skills["user_invoked"], {"start": 1})
        self.assertIn("tdd", self.s["skills_used"])  # read inside a subagent
        self.assertNotIn("README", self.s["skills_used"])

    def test_builds_errors_hazards_repeats(self):
        self.assertEqual(self.s["builds"], 3)  # pkill line names gradlew too
        self.assertEqual(self.s["tool_errors"], 1)
        self.assertEqual(self.s["repeated_calls"], 1)
        self.assertEqual(self.s["hazards"], {"kill_build_daemon": 1})
        self.assertEqual(self.s["subagents"]["hazards"], {"git_add_all": 1})

    def test_spawns_and_model_flag(self):
        self.assertEqual(self.s["spawns"]["count"], 2)
        self.assertEqual(self.s["spawns"]["without_model"], 1)

    def test_subagent_tree_skips_local_and_seance_spawns(self):
        names = sorted(r["name"] for r in self.s["top_subagents"])
        self.assertEqual(names, ["Consult", "R01", "T01Gap", "T01Gap.Scout"])
        # the seance child replays a historical spawn; it must not count as ours
        self.assertEqual(self.s["spawns"]["count"], 2)
        roles = self.s["subagents"]["by_role"]
        self.assertEqual(roles["T"]["count"], 1)

    def test_compaction_counted(self):
        self.assertEqual(self.s["compactions"], 1)

    def test_transcript_keeps_events_and_fences_content(self):
        with open(os.path.join(self.out, self.s["transcript"])) as fh:
            md = fh.read()
        self.assertIn("untrusted data", md)
        for marker in ("[user #", "[skill:user", "[skill:read", "[ask #", "[answer #", "[spawn #",
                       "[bash #", "[error #", "[compaction #", "[reply #"):
            self.assertIn(marker, md)
        self.assertIn("· tools: read×1", md)

    def test_transcript_addresses_are_jsonl_lines(self):
        with open(os.path.join(self.out, self.s["transcript"])) as fh:
            md = fh.read()
        with open(self.s["path"]) as fh:
            line4 = fh.read().splitlines()[3]
        self.assertIn("Fix the calendar gap", line4)
        self.assertIn("[user #4 ", md)

    def test_missing_model_spawn_resolved_from_child_transcript(self):
        # T01Gap was spawned without `model`; its transcript says it ran on Sonnet
        self.assertEqual(self.s["spawns"]["missing_model_resolved"], {"anthropic/claude-sonnet-5-5": 1})
        self.assertNotIn("_unset_names", self.s["spawns"])

    def test_span_prints_fenced_raw_lines(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = om.main(["span", self.out, self.s["key"], "--lines", "4-5"])
        self.assertEqual(rc, 0)
        out = buf.getvalue()
        self.assertTrue(out.startswith("<untrusted_transcript"))
        self.assertIn("--- #4 user", out)
        self.assertIn("Fix the calendar gap", out)
        self.assertNotIn("--- #6", out)

    def test_static_flags_dead_weak_colliding_and_duplicated(self):
        out = os.path.join(self.out, "static.json")
        with contextlib.redirect_stdout(io.StringIO()):
            om.main(["static", "--skills-dir", SKILLS, "--run", self.out])
        with open(out) as fh:
            st = json.load(fh)
        self.assertEqual(st["never_loaded"], ["unused"])
        self.assertEqual([w["line"] for w in st["skills"]["tdd"]["weak_modals"]], [9])
        self.assertEqual(st["skills"]["implement"]["weak_modals"], [])
        self.assertEqual([c["skills"] for c in st["description_collisions"]], [["tdd", "unused"]])
        self.assertEqual(len(st["duplicated_lines"]), 1)
        self.assertEqual(len(st["duplicated_lines"][0]["copies"]), 3)

    def verify(self, finding):
        with open(os.path.join(self.out, "findings.json"), "w") as fh:
            json.dump({"findings": [finding]}, fh)
        with contextlib.redirect_stdout(io.StringIO()):
            rc = om.main(["verify", self.out, "--skills-dir", SKILLS])
        with open(os.path.join(self.out, "findings.verified.json")) as fh:
            return rc, json.load(fh)["findings"][0]

    def finding(self, **over):
        f = {"id": "F1", "skill": "implement", "file": "implement/SKILL.md", "line_start": 9, "line_end": 9,
             "quote": "Ask the user before every merge", "category": "skill_hurts",
             "sessions": [self.s["key"]], "protective": True,
             "transcript_quotes": [{"session": self.s["key"], "line": 4, "quote": "Fix the calendar gap."}]}
        f.update(over)
        return f

    def test_verify_accepts_matching_quotes(self):
        rc, f = self.verify(self.finding())
        self.assertEqual((rc, f["status"], f["verify_reasons"]), (0, "verified", []))

    def test_verify_rejects_unsupported_findings(self):
        cases = {
            "found near line 9": self.finding(line_start=8, line_end=8),
            "not in the file": self.finding(quote="Merge without asking"),
            "never loaded": self.finding(skill="unused", file="unused/SKILL.md", line_start=7,
                                         line_end=7, quote="## Steps"),
            "single session": self.finding(protective=False),
            "transcript quote not found": self.finding(transcript_quotes=[
                {"session": self.s["key"], "line": 5, "quote": "Fix the calendar gap."}]),
            "not in the enum": self.finding(category="bad_luck"),
        }
        for expect, finding in cases.items():
            rc, f = self.verify(finding)
            self.assertEqual((rc, f["status"]), (1, "rejected"), expect)
            self.assertTrue(any(expect in w for w in f["verify_reasons"]), (expect, f["verify_reasons"]))

    def test_verify_allows_unloaded_skill_for_discovery_failure(self):
        rc, f = self.verify(self.finding(skill="unused", file="unused/SKILL.md", line_start=7, line_end=7,
                                         quote="## Steps", category="discovery_failure"))
        self.assertEqual(f["verify_reasons"], [])


class SelfExclusionTest(unittest.TestCase):
    def test_skill_doctor_runs_are_not_audited(self):
        root = tempfile.mkdtemp()
        try:
            src = os.path.join(FIXTURES, "-ws-Demo", "2026-11-11T10-00-00-000Z_0001.jsonl")
            os.makedirs(os.path.join(root, "-ws-Self"))
            with open(src) as fh:
                lines = fh.read().splitlines()
            lines.append(json.dumps({"type": "custom_message", "customType": "skill-prompt",
                                     "timestamp": "2026-11-11T11:05:00.000Z", "details": {"name": "skill-doctor"}}))
            with open(os.path.join(root, "-ws-Self", os.path.basename(src)), "w") as fh:
                fh.write("\n".join(lines) + "\n")
            out = os.path.join(root, "run")
            with contextlib.redirect_stdout(io.StringIO()):
                rc = om.main(["collect", "--root", root, "--project", "*Self",
                              "--since", "2026-11-10", "--until", "2026-11-12", "--out", out])
            self.assertEqual(rc, 3)  # nothing left to audit
        finally:
            shutil.rmtree(root)


class AggregateTest(unittest.TestCase):
    def grades(self, rows):
        return [{"session": s, "axis": a, "score": v, "label": l} for s, a, v, l in rows]

    def test_warp_formula(self):
        g = self.grades([
            ("s1", "efficiency", 0.8, "minor"), ("s1", "code_quality", 0.2, "block"),
            ("s1", "procedure_compliance", 1.0, "compliant"), ("s1", "verbosity", 1.0, "proportionate"),
            ("s2", "efficiency", 0.4, "moderate"), ("s2", "code_quality", 0.5, om.ABSTAIN),
            ("s2", "procedure_compliance", 0.8, "minor"), ("s2", "verbosity", 0.2, "verbose"),
        ])
        r = om.aggregate(g, [{"key": "s1", "skills_used": ["tdd"]}, {"key": "s2", "skills_used": []}])
        self.assertEqual(r["raw"]["code_quality"], 0.2)  # abstention excluded from the mean
        self.assertEqual(r["warp_compat"]["efficiency"], 0.8)  # 0.5 + 0.5 * 0.6
        self.assertEqual(r["warp_compat"]["skill_coverage"], 0.5)  # coverage is not curved
        expected = 0.25 * 0.8 + 0.25 * 0.6 + 0.2 * 0.95 + 0.15 * 0.8 + 0.15 * 0.5
        self.assertAlmostEqual(r["warp_compat"]["overall"], expected, places=3)
        self.assertEqual(r["failed_sessions"], ["s1", "s2"])

    def test_axis_with_modal_share_at_threshold_flagged(self):
        rows = [(f"s{i}", "code_quality", 0.2, "block") for i in range(9)]
        rows.append(("s9", "code_quality", 1.0, "approve"))
        rows.append(("s10", "code_quality", 0.5, om.ABSTAIN))  # abstentions do not count
        r = om.aggregate(self.grades(rows), [])
        self.assertEqual(r["discrimination"], {"code_quality": "none"})
        self.assertEqual(r["labels"]["code_quality"], {"block": 9, "approve": 1, om.ABSTAIN: 1})

    def test_axis_below_threshold_not_flagged(self):
        rows = [(f"s{i}", "efficiency", 0.8, "minor") for i in range(8)]
        rows += [("s8", "efficiency", 0.4, "moderate"), ("s9", "efficiency", 0.4, "moderate")]
        self.assertEqual(om.aggregate(self.grades(rows), [])["discrimination"], {})


if __name__ == "__main__":
    unittest.main()
