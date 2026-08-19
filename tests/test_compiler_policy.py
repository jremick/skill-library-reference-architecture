from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from skillref import compile_bundle
from skillref._util import canonical_json_bytes, digest_value, load_structured, sha256_bytes
from skillref.compiler import write_bundle
from tests.fixtures import (
    MANIFEST_SCHEMA,
    PROFILE_SCHEMA,
    REGISTRY_SCHEMA,
    ROUTER_SCHEMA,
    build_library,
)
from tests.support import ROOT  # noqa: F401 - adds src/ to sys.path for source checkouts


class CompilerPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = build_library(Path(self.temporary.name))

    def test_compile_is_byte_stable(self) -> None:
        first = compile_bundle(self.root, "local-safe")
        second = compile_bundle(self.root, "local-safe")
        self.assertEqual(first, second)
        self.assertEqual(canonical_json_bytes(first), canonical_json_bytes(second))

        first_path = self.root / "out" / "first.json"
        second_path = self.root / "out" / "second.json"
        write_bundle(first, first_path)
        write_bundle(second, second_path)
        self.assertEqual(first_path.read_bytes(), second_path.read_bytes())

    def test_source_and_bundle_digests_change_with_inputs(self) -> None:
        before = compile_bundle(self.root, "local-safe")
        entrypoint = self.root / "skills" / "document-summary" / "SKILL.md"
        entrypoint.write_text(
            entrypoint.read_text(encoding="utf-8") + "\nAdditional synthetic guidance.\n",
            encoding="utf-8",
        )
        after = compile_bundle(self.root, "local-safe")
        self.assertNotEqual(before["source_digest"], after["source_digest"])
        self.assertNotEqual(before["bundle_digest"], after["bundle_digest"])

    def test_fixture_documents_match_the_published_schemas(self) -> None:
        schema_paths = {
            MANIFEST_SCHEMA: ROOT / "schemas" / "skill-manifest.schema.json",
            PROFILE_SCHEMA: ROOT / "schemas" / "profile.schema.json",
            REGISTRY_SCHEMA: ROOT / "schemas" / "registry.schema.json",
            ROUTER_SCHEMA: ROOT / "schemas" / "router-map.schema.json",
        }
        validators = {
            identifier: Draft202012Validator(load_structured(path))
            for identifier, path in schema_paths.items()
        }

        documents = [
            self.root / "registry.yaml",
            self.root / "router-map.yaml",
            *sorted((self.root / "profiles").glob("*.yaml")),
            *sorted((self.root / "skills").glob("*/manifest.yaml")),
        ]
        for path in documents:
            with self.subTest(path=path.relative_to(self.root)):
                document = load_structured(path)
                validator = validators[document["$schema"]]
                errors = sorted(
                    validator.iter_errors(document),
                    key=lambda error: list(error.path),
                )
                self.assertEqual([], errors)

    def test_registry_and_router_digests_bind_their_sources(self) -> None:
        registry_path = self.root / "registry.yaml"
        registry = load_structured(registry_path)
        for entry in registry["entries"]:
            manifest_path = self.root / entry["manifest"]["uri"]
            expected = entry["manifest"]["digest"]
            self.assertEqual("sha256", expected["algorithm"])
            self.assertEqual(
                sha256_bytes(manifest_path.read_bytes()).removeprefix("sha256:"),
                expected["value"],
            )

        router = load_structured(self.root / "router-map.yaml")
        self.assertEqual("sha256", router["sourceRegistryDigest"]["algorithm"])
        self.assertEqual(
            sha256_bytes(registry_path.read_bytes()).removeprefix("sha256:"),
            router["sourceRegistryDigest"]["value"],
        )

    def test_prompt_visible_and_router_retrievable_are_distinct(self) -> None:
        states = compile_bundle(self.root, "local-safe")["lifecycle_states"]
        self.assertEqual(["document-summary"], states["prompt_visible"])
        self.assertEqual(["deployment-runner", "table-analysis"], states["router_retrievable"])
        self.assertFalse(set(states["prompt_visible"]) & set(states["router_retrievable"]))

    def test_denial_overrides_matching_grant_before_routing(self) -> None:
        profile = load_structured(self.root / "profiles" / "read-only.yaml")
        granted_ids = {
            skill_id
            for grant in profile["grants"]
            for skill_id in grant["selector"].get("skillIds", [])
        }
        denied_ids = {
            skill_id
            for denial in profile["denials"]
            for skill_id in denial["selector"].get("skillIds", [])
        }
        self.assertIn("deployment-runner", granted_ids & denied_ids)
        self.assertTrue(profile["resolution"]["denialsOverrideGrants"])

        bundle = compile_bundle(self.root, "read-only")
        states = bundle["lifecycle_states"]
        self.assertNotIn("deployment-runner", states["policy_eligible"])
        self.assertNotIn("deployment-runner", states["prompt_visible"])
        self.assertNotIn("deployment-runner", states["router_retrievable"])
        self.assertTrue(
            all(
                "deployment-runner" not in route["candidate_skill_ids"]
                for route in bundle["routes"]
            )
        )

    def test_manifest_tamper_fails_closed_against_registry_digest(self) -> None:
        manifest = self.root / "skills" / "document-summary" / "manifest.yaml"
        manifest.write_text(
            manifest.read_text(encoding="utf-8") + "# unregistered change\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "registry manifest digest mismatch"):
            compile_bundle(self.root, "local-safe")

    def test_declared_resource_tamper_fails_closed(self) -> None:
        reference = self.root / "skills" / "table-analysis" / "references" / "chart-guidance.md"
        reference.write_text(
            reference.read_text(encoding="utf-8") + "# unregistered change\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "resource 0 digest does not match"):
            compile_bundle(self.root, "local-safe")

    def test_conditional_resource_is_not_inlined_by_compilation(self) -> None:
        bundle = compile_bundle(self.root, "local-safe")
        table = next(skill for skill in bundle["skills"] if skill["skill_id"] == "table-analysis")
        self.assertIn("table-analysis", bundle["lifecycle_states"]["router_retrievable"])
        self.assertNotIn(
            "resources", table, "compiled metadata must not inline conditional resources"
        )

    def test_compiled_manifest_digest_matches_registered_bytes(self) -> None:
        bundle = compile_bundle(self.root, "local-safe")
        table = next(skill for skill in bundle["skills"] if skill["skill_id"] == "table-analysis")
        manifest_path = self.root / table["manifest_path"]
        self.assertEqual(sha256_bytes(manifest_path.read_bytes()), table["manifest_digest"])

    def test_bundle_digest_is_bound_to_payload(self) -> None:
        bundle = compile_bundle(self.root, "local-safe")
        unsigned = {key: value for key, value in bundle.items() if key != "bundle_digest"}
        self.assertEqual(digest_value(unsigned), bundle["bundle_digest"])

        changed = copy.deepcopy(bundle)
        changed["lifecycle_states"]["prompt_visible"] = []
        self.assertNotEqual(canonical_json_bytes(bundle), canonical_json_bytes(changed))
        self.assertEqual(bundle, json.loads(canonical_json_bytes(bundle)))

    def test_unknown_profile_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown profile_id"):
            compile_bundle(self.root, "not-a-profile")


if __name__ == "__main__":
    unittest.main()
