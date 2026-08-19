from __future__ import annotations

import copy
import shutil
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from skillref import validate_repository
from tests.fixtures import build_library, write_yaml
from tests.support import ROOT, load_data  # adds src/ to sys.path for source checkouts


class ValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = build_library(Path(self.temporary.name))

    def _copy_canonical_example(self, name: str = "level-2-retrieval") -> Path:
        root = self.root / f"canonical-{name}"
        shutil.copytree(ROOT / "schemas", root / "schemas")
        shutil.copytree(ROOT / "examples" / name, root, dirs_exist_ok=True)
        return root

    def test_all_canonical_schemas_are_valid_draft_2020_12(self) -> None:
        expected = {
            "activation-transition.schema.json",
            "eval-case.schema.json",
            "profile.schema.json",
            "registry.schema.json",
            "router-map.schema.json",
            "skill-manifest.schema.json",
            "telemetry-event.schema.json",
        }
        schema_paths = {path.name for path in (ROOT / "schemas").glob("*.schema.json")}
        self.assertEqual(expected, schema_paths)
        for name in sorted(expected):
            with self.subTest(schema=name):
                Draft202012Validator.check_schema(load_data(ROOT / "schemas" / name))

    def test_repository_contracts_validate_without_warnings(self) -> None:
        report = validate_repository(ROOT)
        self.assertTrue(report["ok"], report)
        self.assertEqual([], report["issues"], report)

    def test_duplicate_registry_ids_are_rejected(self) -> None:
        registry_path = self.root / "registry.yaml"
        registry = load_data(registry_path)
        registry["entries"].append(dict(registry["entries"][0]))
        write_yaml(registry_path, registry)
        report = validate_repository(self.root)
        self.assertTrue(
            any(issue["category"] == "duplicate-id" for issue in report["issues"]),
            report,
        )

    def test_missing_manifest_and_digest_mismatch_are_rejected(self) -> None:
        registry_path = self.root / "registry.yaml"
        registry = load_data(registry_path)
        registry["entries"][0]["manifest"]["digest"]["value"] = "0" * 64
        registry["entries"][1]["manifest"]["uri"] = "skills/missing/manifest.yaml"
        write_yaml(registry_path, registry)
        report = validate_repository(self.root)
        categories = {issue["category"] for issue in report["issues"]}
        self.assertIn("digest-mismatch", categories)
        self.assertIn("missing-reference", categories)

    def test_unresolved_route_tie_is_rejected(self) -> None:
        router_path = self.root / "router-map.yaml"
        router = load_data(router_path)
        router["routers"][0]["exactAliases"] = [
            {"phrase": "Review this patch", "skillId": "document-summary"}
        ]
        router["routers"][1]["exactAliases"] = [
            {"phrase": "Review   this PATCH", "skillId": "table-analysis"}
        ]
        write_yaml(router_path, router)
        report = validate_repository(self.root)
        self.assertTrue(
            any(issue["category"] == "route-tie" for issue in report["issues"]),
            report,
        )

    def test_malformed_yaml_becomes_value_safe_parse_issue(self) -> None:
        root = self.root / "malformed"
        shutil.copytree(ROOT / "schemas", root / "schemas")
        marker = "synthetic_private_value_must_not_appear"
        (root / "broken.yaml").write_text(f"items: [\n  {marker}: value\n", encoding="utf-8")

        report = validate_repository(root)

        self.assertFalse(report["ok"])
        self.assertTrue(any(issue["category"] == "parse" for issue in report["issues"]))
        self.assertNotIn(marker, repr(report))

    def test_evaluation_suite_cases_use_the_canonical_case_schema(self) -> None:
        root = self.root / "eval-case-validation"
        shutil.copytree(ROOT / "schemas", root / "schemas")
        write_yaml(
            root / "cases.yaml",
            {
                "schema_version": "0.1.0",
                "suite_id": "synthetic-invalid-suite",
                "cases": [
                    {
                        "case_id": "missing-prompt",
                        "profile_id": "local-safe",
                        "expected_skill_ids": [],
                        "must_not_skill_ids": [],
                        "expected_decision": "reject",
                        "tags": ["negative"],
                    }
                ],
            },
        )

        report = validate_repository(root)

        self.assertTrue(
            any(
                issue["category"] == "schema"
                and issue.get("pointer", "").startswith("/cases/0")
                and "synthetic_prompt" in issue["message"]
                for issue in report["issues"]
            ),
            report,
        )

    def test_same_manifest_version_must_have_identical_raw_bytes(self) -> None:
        root = self.root / "manifest-content"
        shutil.copytree(ROOT / "schemas", root / "schemas")
        source = (
            ROOT
            / "examples"
            / "level-2-retrieval"
            / "skills"
            / "document-summary"
            / "manifest.yaml"
        )
        first = root / "examples" / "first" / "manifest.yaml"
        second = root / "examples" / "second" / "manifest.yaml"
        first.parent.mkdir(parents=True)
        second.parent.mkdir(parents=True)
        shutil.copy2(source, first)
        shutil.copy2(source, second)

        identical = validate_repository(root)
        self.assertFalse(
            any(issue["category"] == "manifest-content-conflict" for issue in identical["issues"]),
            identical,
        )

        second.write_text(second.read_text(encoding="utf-8") + "# divergent\n", encoding="utf-8")
        divergent = validate_repository(root)
        self.assertTrue(
            any(issue["category"] == "manifest-content-conflict" for issue in divergent["issues"]),
            divergent,
        )

    def test_registry_entry_is_bound_to_referenced_manifest_id(self) -> None:
        root = self._copy_canonical_example()
        registry_path = root / "registry.yaml"
        registry = load_data(registry_path)
        registry["entries"][0]["id"] = "substituted-skill"
        write_yaml(registry_path, registry)

        report = validate_repository(root)

        self.assertTrue(
            any(issue["category"] == "identity-mismatch" for issue in report["issues"]),
            report,
        )

    def test_router_is_bound_to_namespace_registry_bytes(self) -> None:
        root = self._copy_canonical_example()
        router_path = root / "router-map.yaml"
        router = load_data(router_path)
        router["sourceRegistryDigest"]["value"] = "0" * 64
        write_yaml(router_path, router)

        report = validate_repository(root)

        self.assertTrue(
            any(issue["category"] == "source-digest-mismatch" for issue in report["issues"]),
            report,
        )

    def test_remote_manifest_reference_is_not_silently_accepted(self) -> None:
        root = self._copy_canonical_example()
        registry_path = root / "registry.yaml"
        registry = load_data(registry_path)
        registry["entries"][0]["manifest"]["uri"] = "https://example.invalid/manifest.yaml"
        write_yaml(registry_path, registry)

        report = validate_repository(root)

        self.assertTrue(
            any(issue["category"] == "unsupported-reference" for issue in report["issues"]),
            report,
        )

    def test_repository_symlink_is_rejected_without_following_it(self) -> None:
        root = self.root / "symlink-input"
        shutil.copytree(ROOT / "schemas", root / "schemas")
        outside = self.root / "outside.yaml"
        outside.write_text("kind: external\n", encoding="utf-8")
        (root / "linked.yaml").symlink_to(outside)

        report = validate_repository(root)

        self.assertTrue(
            any(issue["category"] == "path-escape" for issue in report["issues"]),
            report,
        )

    def test_symlinked_repository_root_is_rejected(self) -> None:
        actual_root = self.root / "actual-root"
        shutil.copytree(ROOT / "schemas", actual_root / "schemas")
        linked_root = self.root / "linked-root"
        linked_root.symlink_to(actual_root, target_is_directory=True)

        report = validate_repository(linked_root)

        self.assertFalse(report["ok"])
        self.assertEqual("path-escape", report["issues"][0]["category"])

    def test_manifest_paths_reject_nonportable_and_windows_forms(self) -> None:
        schema = load_data(ROOT / "schemas" / "skill-manifest.schema.json")
        manifest = load_data(
            ROOT
            / "examples"
            / "level-2-retrieval"
            / "skills"
            / "document-summary"
            / "manifest.yaml"
        )
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        invalid_paths = (
            "C:/private/SKILL.md",
            "C:private/SKILL.md",
            "file:SKILL.md",
            "https://example.invalid/SKILL.md",
            "~/SKILL.md",
            "./SKILL.md",
            "resources/../SKILL.md",
            "resources/./SKILL.md",
            "resources\\SKILL.md",
        )

        for invalid_path in invalid_paths:
            with self.subTest(path=invalid_path):
                candidate = copy.deepcopy(manifest)
                candidate["resources"]["entrypoint"] = invalid_path
                self.assertTrue(list(validator.iter_errors(candidate)))

        alias_owner = copy.deepcopy(manifest)
        alias_owner["triggers"]["directAliases"] = ["summarize this"]
        self.assertTrue(list(validator.iter_errors(alias_owner)))

    def test_unimplemented_profile_selectors_are_rejected(self) -> None:
        schema = load_data(ROOT / "schemas" / "profile.schema.json")
        profile = load_data(ROOT / "examples" / "level-2-retrieval" / "profile.yaml")
        validator = Draft202012Validator(schema, format_checker=FormatChecker())

        trust_tier = copy.deepcopy(profile)
        trust_tier["grants"][0]["selector"]["trustTiers"] = ["trusted"]
        self.assertTrue(list(validator.iter_errors(trust_tier)))

        expiring = copy.deepcopy(profile)
        expiring["grants"][0]["expiresAt"] = "2026-08-20T00:00:00Z"
        self.assertTrue(list(validator.iter_errors(expiring)))

    def test_forbidden_activation_transition_is_rejected(self) -> None:
        schema = load_data(ROOT / "schemas" / "activation-transition.schema.json")
        transition = load_data(
            ROOT / "examples" / "level-3-governed" / "evidence" / "activation-transition.yaml"
        )
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        self.assertEqual([], list(validator.iter_errors(transition)))

        forbidden = copy.deepcopy(transition)
        forbidden["fromState"] = "activated"
        forbidden["toState"] = "verified"
        self.assertTrue(list(validator.iter_errors(forbidden)))

        wrong_evidence = copy.deepcopy(transition)
        wrong_evidence["actor"] = "model"
        wrong_evidence["evidence"]["decision"] = "select"
        self.assertTrue(list(validator.iter_errors(wrong_evidence)))


if __name__ == "__main__":
    unittest.main()
