from __future__ import annotations

import hashlib
import json
import unittest

from jsonschema import Draft202012Validator

from skillref import evaluate_suite
from skillref._util import digest_value
from tests.support import ROOT, load_data, load_eval_suite


class EvalCorpusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.development = load_eval_suite("development")
        self.heldout = load_eval_suite("heldout")

    def test_suite_ids_and_case_ids_are_unique(self) -> None:
        suite_ids = {self.development["suite_id"], self.heldout["suite_id"]}
        self.assertEqual(2, len(suite_ids))

        case_ids = [
            case["case_id"] for suite in (self.development, self.heldout) for case in suite["cases"]
        ]
        self.assertEqual(len(case_ids), len(set(case_ids)))

    def test_each_suite_covers_levels_zero_through_three(self) -> None:
        for suite in (self.development, self.heldout):
            with self.subTest(suite=suite["suite_id"]):
                self.assertEqual({0, 1, 2, 3}, {case["level"] for case in suite["cases"]})

    def test_expected_and_forbidden_skills_never_overlap(self) -> None:
        for suite in (self.development, self.heldout):
            for case in suite["cases"]:
                with self.subTest(case=case["case_id"]):
                    expected = set(case["expected_skill_ids"])
                    forbidden = set(case["must_not_skill_ids"])
                    self.assertFalse(expected & forbidden)

    def test_heldout_prompts_are_not_development_prompts(self) -> None:
        development_prompts = {
            case["synthetic_prompt"].casefold() for case in self.development["cases"]
        }
        heldout_prompts = {case["synthetic_prompt"].casefold() for case in self.heldout["cases"]}
        self.assertFalse(development_prompts & heldout_prompts)

    def test_heldout_cases_are_explicitly_tagged(self) -> None:
        for case in self.heldout["cases"]:
            with self.subTest(case=case["case_id"]):
                self.assertIn("heldout", case["tags"])

    def test_corpus_exercises_policy_selection_rejection_and_exposure(self) -> None:
        tags = {
            tag
            for suite in (self.development, self.heldout)
            for case in suite["cases"]
            for tag in case["tags"]
        }
        self.assertTrue({"permission", "must-not", "rejection"}.issubset(tags))
        exposures = {
            case.get("expected_exposure")
            for suite in (self.development, self.heldout)
            for case in suite["cases"]
        }
        self.assertEqual({"prompt_visible", "router_retrievable", None}, exposures)

    def test_cases_conform_to_the_executable_case_schema(self) -> None:
        schema = load_data(ROOT / "schemas" / "eval-case.schema.json")
        validator = Draft202012Validator(schema)
        for suite in (self.development, self.heldout):
            for case in suite["cases"]:
                with self.subTest(case=case["case_id"]):
                    self.assertEqual([], list(validator.iter_errors(case)))

    def test_checked_in_development_and_heldout_suites_execute(self) -> None:
        for name in ("development", "heldout"):
            with self.subTest(suite=name):
                report = evaluate_suite(ROOT, ROOT / "evals" / name / "cases.json")
                self.assertTrue(report["ok"], report)
                self.assertEqual(1.0, report["metrics"]["exposure_correctness"])
                self.assertTrue(report["systems"])
                for system in report["systems"]:
                    self.assertTrue(system["bundle_digest"].startswith("sha256:"))
                    self.assertTrue(system["source_digest"].startswith("sha256:"))
                    self.assertTrue(system["profile_digest"].startswith("sha256:"))

    def test_claim_limits_are_recorded(self) -> None:
        text = " ".join((ROOT / "evals" / "README.md").read_text(encoding="utf-8").split())
        for phrase in (
            "checked contracts and fixtures",
            "synthetic case distribution",
            "advisory unless calibrated",
            "does not establish real-world usefulness",
            "cannot prove that all sensitive information is absent",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_archived_independent_candidate_input_is_content_bound(self) -> None:
        path = ROOT / "evals" / "independent-candidate-v2" / "cases.original.json.txt"
        raw = path.read_bytes()
        self.assertEqual(
            "86c0fd1b7296ad5566c3ba26d65ce3f63693b86db11bef7d3d791118cda27730",
            hashlib.sha256(raw).hexdigest(),
        )
        self.assertEqual(
            "sha256:9a229f78ce85085856833701e0304cbfd6a8530c351b116ab4a7d4ce63bcbeb3",
            digest_value(json.loads(raw)),
        )


if __name__ == "__main__":
    unittest.main()
