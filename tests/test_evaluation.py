from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from skillref import compile_bundle, evaluate_suite
from skillref._util import digest_value, load_structured
from tests.fixtures import build_library
from tests.support import ROOT  # noqa: F401 - adds src/ to sys.path for source checkouts


class EvaluationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = build_library(Path(self.temporary.name))

    def _write_suite(self, value: dict, *, validate_cases: bool = True) -> Path:
        if validate_cases:
            schema = load_structured(ROOT / "schemas" / "eval-case.schema.json")
            validator = Draft202012Validator(schema)
            for case in value["cases"]:
                errors = sorted(validator.iter_errors(case), key=lambda error: list(error.path))
                self.assertEqual([], errors, case.get("case_id"))
        path = self.root / "suite.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def test_must_not_skill_is_absent_from_top_k(self) -> None:
        prompt = "Explain the fictional deployment and execute workflow without changing it."
        suite = self._write_suite(
            {
                "schema_version": "0.1.0",
                "suite_id": "must-not",
                "k": 3,
                "cases": [
                    {
                        "case_id": "denied-top-k",
                        "profile_id": "read-only",
                        "synthetic_prompt": prompt,
                        "expected_skill_ids": [],
                        "must_not_skill_ids": ["deployment-runner"],
                        "expected_decision": "reject",
                        "tags": ["denial", "must-not"],
                    }
                ],
            }
        )
        report = evaluate_suite(self.root, suite)
        result = report["results"][0]
        self.assertTrue(report["ok"])
        self.assertEqual([], result["forbidden_selected"])
        self.assertNotIn("deployment-runner", result["selected_skill_ids"])
        self.assertNotIn(prompt, repr(report), "reports must retain only the prompt digest")

    def test_policy_exclusion_uses_source_registration_and_runtime_absence(self) -> None:
        suite = self._write_suite(
            {
                "schema_version": "0.1.0",
                "suite_id": "policy-exclusion",
                "cases": [
                    {
                        "case_id": "denied-and-hidden",
                        "profile_id": "read-only",
                        "synthetic_prompt": "Execute the synthetic deployment.",
                        "expected_skill_ids": [],
                        "must_not_skill_ids": ["deployment-runner"],
                        "expected_decision": "reject",
                        "expected_policy": {
                            "denied_skill_ids": ["deployment-runner"],
                            "filter_before_ranking": True,
                            "reason": "The read-only profile denial overrides its matching grant.",
                        },
                        "tags": ["policy", "pre-ranking"],
                    }
                ],
            }
        )
        report = evaluate_suite(self.root, suite)
        result = report["results"][0]
        bundle = compile_bundle(self.root, "read-only")
        self.assertNotIn("policy_denied", bundle["lifecycle_states"])
        self.assertTrue(report["ok"], report)
        self.assertTrue(result["policy_exclusion_matches"])
        self.assertEqual([], result["policy_source_missing_skill_ids"])
        self.assertEqual([], result["policy_exclusion_leaked_skill_ids"])
        self.assertEqual(1.0, report["metrics"]["policy_exclusion_correctness"])

    def test_policy_exclusion_fails_when_expected_denial_remains_rankable(self) -> None:
        suite = self._write_suite(
            {
                "schema_version": "0.1.0",
                "suite_id": "policy-leak",
                "cases": [
                    {
                        "case_id": "still-rankable",
                        "profile_id": "local-safe",
                        "synthetic_prompt": "Execute the synthetic deployment.",
                        "expected_skill_ids": [],
                        "must_not_skill_ids": ["deployment-runner"],
                        "expected_decision": "reject",
                        "expected_policy": {
                            "denied_skill_ids": ["deployment-runner"],
                            "filter_before_ranking": True,
                            "reason": "This intentional mismatch must not pass vacuously.",
                        },
                        "tags": ["negative", "policy"],
                    }
                ],
            }
        )
        report = evaluate_suite(self.root, suite)
        self.assertFalse(report["ok"])
        self.assertEqual(
            ["deployment-runner"],
            report["results"][0]["policy_exclusion_leaked_skill_ids"],
        )

    def test_expected_skill_is_found_and_report_is_stable(self) -> None:
        suite = self._write_suite(
            {
                "schema_version": "0.1.0",
                "suite_id": "positive",
                "k": 1,
                "cases": [
                    {
                        "case_id": "table",
                        "profile_id": "local-safe",
                        "synthetic_prompt": "Analyze the sample table and make a chart.",
                        "expected_skill_ids": ["table-analysis"],
                        "must_not_skill_ids": ["deployment-runner"],
                        "expected_decision": "select",
                        "expected_exposure": "router_retrievable",
                        "tags": ["positive"],
                    }
                ],
            }
        )
        first = evaluate_suite(self.root, suite)
        second = evaluate_suite(self.root, suite)
        self.assertEqual(first, second)
        self.assertEqual(1.0, first["metrics"]["hit_at_k"])
        self.assertEqual(1.0, first["metrics"]["exposure_correctness"])
        self.assertEqual(0.0, first["metrics"]["false_activation_rate"])
        bundle = compile_bundle(self.root, "local-safe")
        self.assertEqual(bundle["bundle_digest"], first["systems"][0]["bundle_digest"])
        self.assertEqual(bundle["source_digest"], first["systems"][0]["source_digest"])
        self.assertEqual(bundle["profile"]["profile_digest"], first["systems"][0]["profile_digest"])
        self.assertEqual(bundle["bundle_digest"], first["results"][0]["system_bundle_digest"])
        unsigned = {key: value for key, value in first.items() if key != "report_digest"}
        self.assertEqual(digest_value(unsigned), first["report_digest"])
        self.assertEqual(digest_value(load_structured(suite)), first["dataset_digest"])

    def test_configured_threshold_failure_is_preserved(self) -> None:
        suite = self._write_suite(
            {
                "schema_version": "0.1.0",
                "suite_id": "threshold",
                "thresholds": {"top_1_accuracy": 1.0},
                "cases": [
                    {
                        "case_id": "intentional-miss",
                        "profile_id": "local-safe",
                        "synthetic_prompt": "xyzzy",
                        "expected_skill_ids": ["table-analysis"],
                        "must_not_skill_ids": [],
                        "expected_decision": "select",
                        "expected_exposure": "router_retrievable",
                        "tags": ["intentional-miss", "threshold"],
                    }
                ],
            }
        )
        report = evaluate_suite(self.root, suite)
        self.assertFalse(report["ok"])
        self.assertIn("top_1_accuracy is below configured minimum", report["failures"])

    def test_rejected_case_fails_when_any_candidate_is_returned(self) -> None:
        suite = self._write_suite(
            {
                "schema_version": "0.1.0",
                "suite_id": "rejection",
                "cases": [
                    {
                        "case_id": "must-reject",
                        "profile_id": "local-safe",
                        "synthetic_prompt": "Analyze the sample table.",
                        "expected_skill_ids": [],
                        "must_not_skill_ids": [],
                        "expected_decision": "reject",
                        "tags": ["rejection"],
                    }
                ],
            }
        )
        report = evaluate_suite(self.root, suite)
        self.assertFalse(report["ok"])
        self.assertEqual(0.0, report["metrics"]["rejection_correctness"])

    def test_common_words_do_not_create_lexical_candidates(self) -> None:
        suite = self._write_suite(
            {
                "schema_version": "0.1.0",
                "suite_id": "stop-words",
                "cases": [
                    {
                        "case_id": "unrelated",
                        "profile_id": "local-safe",
                        "synthetic_prompt": "This is a request for the unrelated item.",
                        "expected_skill_ids": [],
                        "must_not_skill_ids": [],
                        "expected_decision": "reject",
                        "tags": ["rejection"],
                    }
                ],
            }
        )
        report = evaluate_suite(self.root, suite)
        self.assertTrue(report["ok"], report)
        self.assertEqual([], report["results"][0]["selected_skill_ids"])

    def test_unsupported_runtime_expectations_fail_closed(self) -> None:
        suite = self._write_suite(
            {
                "schema_version": "0.1.0",
                "suite_id": "unsupported-runtime",
                "cases": [
                    {
                        "case_id": "runtime-only",
                        "profile_id": "local-safe",
                        "synthetic_prompt": "Analyze the sample table.",
                        "expected_skill_ids": ["table-analysis"],
                        "must_not_skill_ids": [],
                        "expected_stage": "activated",
                        "expected_outcome": "PASS",
                        "tags": ["runtime"],
                    }
                ],
            },
            validate_cases=False,
        )
        report = evaluate_suite(self.root, suite)
        self.assertFalse(report["ok"])
        self.assertEqual(
            ["expected_outcome", "expected_stage"],
            report["results"][0]["unsupported_expectations"],
        )
        self.assertIn("unsupported expectations", report["failures"][0])

    def test_exposure_mismatch_is_a_hard_failure(self) -> None:
        suite = self._write_suite(
            {
                "schema_version": "0.1.0",
                "suite_id": "exposure-mismatch",
                "cases": [
                    {
                        "case_id": "wrong-exposure",
                        "profile_id": "local-safe",
                        "synthetic_prompt": "Analyze the sample table.",
                        "expected_skill_ids": ["table-analysis"],
                        "must_not_skill_ids": [],
                        "expected_decision": "select",
                        "expected_exposure": "prompt_visible",
                        "tags": ["exposure"],
                    }
                ],
            }
        )
        report = evaluate_suite(self.root, suite)
        self.assertFalse(report["ok"])
        self.assertEqual(0.0, report["metrics"]["exposure_correctness"])
        self.assertEqual(["table-analysis"], report["results"][0]["exposure_missing_skill_ids"])


if __name__ == "__main__":
    unittest.main()
