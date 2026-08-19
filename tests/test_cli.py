from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import yaml

from skillref.cli import main
from tests.fixtures import build_library
from tests.support import ROOT


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = build_library(Path(self.temporary.name))

    def _run(self, *args: str) -> tuple[int, dict[str, object]]:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = main(list(args))
        return exit_code, json.loads(output.getvalue())

    def test_validate_success_is_json_and_versioned(self) -> None:
        exit_code, report = self._run("validate", str(ROOT))

        self.assertEqual(0, exit_code)
        self.assertTrue(report["ok"])
        self.assertEqual("skillref.command-report.v0alpha1", report["report_format"])

    def test_compile_writes_a_versioned_bundle_and_report(self) -> None:
        output = self.root / ".artifacts" / "bundle.json"

        exit_code, report = self._run(
            "compile",
            str(self.root),
            "--profile",
            "local-safe",
            "--output",
            str(output),
        )

        self.assertEqual(0, exit_code)
        self.assertTrue(output.is_file())
        bundle = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual("skillref.compiled-bundle.v0alpha1", bundle["bundle_format"])
        self.assertEqual("skillref.command-report.v0alpha1", report["report_format"])

    def test_evaluate_preserves_its_specific_report_contract(self) -> None:
        suite = self.root / "suite.json"
        suite.write_text(
            json.dumps(
                {
                    "schema_version": "0.1.0",
                    "suite_id": "cli-routing-suite",
                    "thresholds": {"hit_at_k": 1.0},
                    "cases": [
                        {
                            "case_id": "cli-table-analysis",
                            "synthetic_prompt": "Analyze the synthetic table and chart.",
                            "profile_id": "local-safe",
                            "expected_skill_ids": ["table-analysis"],
                            "must_not_skill_ids": ["deployment-runner"],
                            "expected_decision": "select",
                            "expected_exposure": "router_retrievable",
                            "tags": ["cli"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        exit_code, report = self._run("evaluate", str(self.root), "--suite", str(suite))

        self.assertEqual(0, exit_code)
        self.assertEqual("skillref.evaluation-report.v0alpha1", report["report_format"])

    def test_public_surface_failure_returns_one(self) -> None:
        secret_file = self.root / (".e" + "nv")
        secret_file.write_text("api_" + "key=synthetic-not-a-real-secret\n", encoding="utf-8")

        exit_code, report = self._run("check-public-surface", str(self.root))

        self.assertEqual(1, exit_code)
        self.assertFalse(report["ok"])
        self.assertEqual("skillref.command-report.v0alpha1", report["report_format"])

    def test_operational_error_returns_two_without_a_traceback(self) -> None:
        exit_code, report = self._run(
            "compile",
            str(self.root),
            "--profile",
            "missing-profile",
            "--output",
            str(self.root / ".artifacts" / "missing.json"),
        )

        self.assertEqual(2, exit_code)
        self.assertFalse(report["ok"])
        self.assertIn("unknown profile_id", str(report["error"]))
        self.assertEqual("skillref.command-report.v0alpha1", report["report_format"])

    def test_compile_rejects_malformed_canonical_profiles_without_overwrite(self) -> None:
        mutations = {
            "missing-denials": lambda profile: profile.pop("denials"),
            "null-denials": lambda profile: profile.__setitem__("denials", None),
            "object-denials": lambda profile: profile.__setitem__("denials", {}),
            "object-grants": lambda profile: profile.__setitem__("grants", {}),
            "allow-default": lambda profile: profile.__setitem__("defaultDecision", "allow"),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                root = build_library(Path(temporary))
                profile_path = root / "profiles" / "local-safe.yaml"
                profile = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
                mutate(profile)
                profile_path.write_text(yaml.safe_dump(profile, sort_keys=False), encoding="utf-8")
                output = root / ".artifacts" / "bundle.json"
                output.parent.mkdir()
                output.write_text("preserve-existing-output", encoding="utf-8")

                exit_code, report = self._run(
                    "compile",
                    str(root),
                    "--profile",
                    "local-safe",
                    "--output",
                    str(output),
                )

                self.assertEqual(2, exit_code)
                self.assertFalse(report["ok"])
                self.assertIn("failed schema validation", str(report["error"]))
                self.assertEqual("preserve-existing-output", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
