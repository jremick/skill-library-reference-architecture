from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

import yaml

from skillref import compile_bundle
from skillref._util import canonical_json_bytes, sha256_bytes
from skillref.compiler import write_bundle
from tests.support import ROOT  # noqa: F401 - adds src/ to sys.path for source checkouts


def write_yaml(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=True), encoding="utf-8")


def _manifest(skill_id: str, description: str, *, with_reference: bool = False) -> dict[str, Any]:
    resources: list[dict[str, Any]] = []
    if with_reference:
        resources.append(
            {
                "path": "references/guide.md",
                "role": "reference",
                "mediaType": "text/markdown",
                "loadWhen": "Load only after activation when the guide is required.",
                "maxBytes": 4096,
            }
        )
    return {
        "$schema": "urn:skillref:schema:skill-manifest:0.1",
        "schemaVersion": "0.1",
        "id": skill_id,
        "version": "1.0.0",
        "name": skill_id.replace("-", " ").title(),
        "description": description,
        "license": "Apache-2.0",
        "domains": ["synthetic"],
        "triggers": {
            "include": [f"Use the synthetic {skill_id} capability."],
            "exclude": ["Do not use for unrelated requests."],
        },
        "risk": {
            "level": "low",
            "sideEffects": False,
            "rationale": "The synthetic fixture reads only supplied content.",
        },
        "permissions": {
            "capabilities": ["content:read"],
            "resourceScopes": ["task:provided-content"],
        },
        "resources": {"entrypoint": "SKILL.md", "items": resources},
        "conflicts": {"hard": [], "supersedes": [], "companions": []},
        "evaluation": {"suiteRefs": ["evals/synthetic.json"]},
    }


def _write_manifest(root: Path, skill_id: str, *, with_reference: bool = False) -> Path:
    skill_root = root / "skills" / skill_id
    manifest_path = skill_root / "manifest.yaml"
    manifest = _manifest(
        skill_id,
        f"A portable synthetic manifest for deterministic {skill_id} binding tests.",
        with_reference=with_reference,
    )
    if with_reference:
        reference = skill_root / "references" / "guide.md"
        reference.parent.mkdir(parents=True, exist_ok=True)
        reference.write_text("# Synthetic guide\n", encoding="utf-8")
        manifest["resources"]["items"][0]["digest"] = {
            "algorithm": "sha256",
            "value": sha256_bytes(reference.read_bytes()).removeprefix("sha256:"),
        }
    write_yaml(manifest_path, manifest)
    (skill_root / "SKILL.md").write_text(
        f"# {skill_id}\n\nSynthetic instructions.\n", encoding="utf-8"
    )
    return manifest_path


def _entry(root: Path, skill_id: str, status: str = "active") -> dict[str, Any]:
    manifest_path = root / "skills" / skill_id / "manifest.yaml"
    return {
        "id": skill_id,
        "manifest": {
            "uri": f"skills/{skill_id}/manifest.yaml",
            "digest": {
                "algorithm": "sha256",
                "value": sha256_bytes(manifest_path.read_bytes()).removeprefix("sha256:"),
            },
        },
        "lifecycle": {"status": status},
        "availability": {
            "cacheState": "cached",
            "installState": "installed",
            "registrationState": "registered",
        },
    }


def _refresh_router_binding(root: Path) -> None:
    router_path = root / "router-map.yaml"
    router = yaml.safe_load(router_path.read_text(encoding="utf-8"))
    router["sourceRegistryDigest"]["value"] = sha256_bytes(
        (root / "registry.yaml").read_bytes()
    ).removeprefix("sha256:")
    write_yaml(router_path, router)


def _build_canonical_library(root: Path) -> Path:
    allowed_path = _write_manifest(root, "allowed-skill", with_reference=True)
    _write_manifest(root, "blocked-secret")
    registry = {
        "$schema": "urn:skillref:schema:registry:0.1",
        "schemaVersion": "0.1",
        "id": "binding-test",
        "registryVersion": "1.0.0",
        "entries": [
            _entry(root, "allowed-skill"),
            _entry(root, "blocked-secret", status="draft"),
        ],
    }
    write_yaml(root / "registry.yaml", registry)
    write_yaml(
        root / "router-map.yaml",
        {
            "$schema": "urn:skillref:schema:router-map:0.1",
            "schemaVersion": "0.1",
            "id": "binding-test",
            "version": "1.0.0",
            "sourceRegistryDigest": {
                "algorithm": "sha256",
                "value": sha256_bytes((root / "registry.yaml").read_bytes()).removeprefix(
                    "sha256:"
                ),
            },
            "policy": {
                "filterBeforeRanking": True,
                "denialsOverrideGrants": True,
                "ambiguityAction": "decline",
            },
            "retrieval": {
                "enabled": False,
                "mode": "none",
                "candidateLimit": 2,
                "inspectLimit": 1,
                "fallback": "decline",
            },
            "routers": [
                {
                    "id": "allowed-router",
                    "domain": "synthetic",
                    "skills": ["allowed-skill"],
                    "strategy": "static",
                    "fallback": {"action": "decline"},
                },
                {
                    "id": "blocked-router",
                    "domain": "synthetic",
                    "skills": ["blocked-secret"],
                    "strategy": "static",
                    "fallback": {"action": "decline"},
                },
            ],
        },
    )
    write_yaml(
        root / "profile.yaml",
        {
            "$schema": "urn:skillref:schema:profile:0.1",
            "schemaVersion": "0.1",
            "id": "local-safe",
            "version": "1.0.0",
            "defaultDecision": "deny",
            "resolution": {
                "denialsOverrideGrants": True,
                "unknownValues": "deny",
            },
            "grants": [
                {
                    "id": "allow-synthetic",
                    "selector": {"skillIds": ["allowed-skill", "blocked-secret"]},
                    "permissions": {
                        "capabilities": ["content:read"],
                        "resourceScopes": ["task:provided-content"],
                        "resourceRoles": ["instructions", "reference"],
                        "exposureModes": ["router-retrievable"],
                    },
                }
            ],
            "denials": [],
        },
    )
    # A valid but unregistered manifest must never enter the compiler closure.
    stray = root / "stray" / "manifest.yaml"
    write_yaml(stray, _manifest("stray-skill", "An unregistered synthetic manifest for tests."))
    self_check = sha256_bytes(allowed_path.read_bytes())
    assert self_check == "sha256:" + registry["entries"][0]["manifest"]["digest"]["value"]
    return root


class RegistryBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = _build_canonical_library(Path(self.temporary.name))

    def _registry(self) -> dict[str, Any]:
        return yaml.safe_load((self.root / "registry.yaml").read_text(encoding="utf-8"))

    def _write_registry(self, registry: dict[str, Any]) -> None:
        write_yaml(self.root / "registry.yaml", registry)
        _refresh_router_binding(self.root)

    def test_compiler_is_registry_bound_and_content_bound(self) -> None:
        before = compile_bundle(self.root, "local-safe")
        allowed_manifest = self.root / "skills" / "allowed-skill" / "manifest.yaml"

        self.assertEqual(["allowed-skill"], [item["skill_id"] for item in before["skills"]])
        self.assertEqual(
            sha256_bytes(allowed_manifest.read_bytes()), before["skills"][0]["manifest_digest"]
        )
        self.assertNotIn("blocked-secret", canonical_json_bytes(before).decode("utf-8"))
        self.assertEqual(["allowed-router"], [route["route_id"] for route in before["routes"]])
        self.assertNotIn("exact_aliases", before["routes"][0])
        self.assertNotIn("keyword_rules", before["routes"][0])
        self.assertNotIn("matchers", before["routes"][0])

        stray = self.root / "stray" / "manifest.yaml"
        stray.write_text(stray.read_text(encoding="utf-8") + "# ignored\n", encoding="utf-8")
        after_stray = compile_bundle(self.root, "local-safe")
        self.assertEqual(before["source_digest"], after_stray["source_digest"])

        entrypoint = self.root / "skills" / "allowed-skill" / "SKILL.md"
        entrypoint.write_text(
            entrypoint.read_text(encoding="utf-8") + "More detail.\n", encoding="utf-8"
        )
        after_entrypoint = compile_bundle(self.root, "local-safe")
        self.assertNotEqual(before["source_digest"], after_entrypoint["source_digest"])

    def test_installation_requires_explicit_installed_state(self) -> None:
        registry = self._registry()
        registry["entries"][0].pop("availability")
        self._write_registry(registry)

        states = compile_bundle(self.root, "local-safe")["lifecycle_states"]
        self.assertEqual([], states["installed_eligible"])
        self.assertEqual([], states["cached_eligible"])

    def test_rejects_multiple_registries_and_router_maps(self) -> None:
        write_yaml(self.root / "nested" / "registry.yaml", self._registry())
        with self.assertRaisesRegex(ValueError, "multiple registry"):
            compile_bundle(self.root, "local-safe")
        (self.root / "nested" / "registry.yaml").unlink()

        router = yaml.safe_load((self.root / "router-map.yaml").read_text(encoding="utf-8"))
        write_yaml(self.root / "nested" / "router-map.yaml", router)
        with self.assertRaisesRegex(ValueError, "multiple router-map"):
            compile_bundle(self.root, "local-safe")

    def test_rejects_nonlocal_missing_and_escaping_manifest_uris(self) -> None:
        for uri in (
            "https://example.invalid/manifest.yaml",
            "file:///tmp/manifest.yaml",
            "../outside.yaml",
            "skills/missing/manifest.yaml",
        ):
            with self.subTest(uri=uri):
                with tempfile.TemporaryDirectory() as temporary:
                    root = _build_canonical_library(Path(temporary))
                    registry = yaml.safe_load((root / "registry.yaml").read_text(encoding="utf-8"))
                    registry["entries"][0]["manifest"]["uri"] = uri
                    write_yaml(root / "registry.yaml", registry)
                    _refresh_router_binding(root)
                    with self.assertRaisesRegex(ValueError, "local relative URI|escapes|file"):
                        compile_bundle(root, "local-safe")

    def test_rejects_symlinked_manifest_path(self) -> None:
        linked = self.root / "skills" / "linked"
        linked.symlink_to(self.root / "skills" / "allowed-skill", target_is_directory=True)
        registry = self._registry()
        registry["entries"][0]["manifest"]["uri"] = "skills/linked/manifest.yaml"
        self._write_registry(registry)

        with self.assertRaisesRegex(ValueError, "symlink"):
            compile_bundle(self.root, "local-safe")

    def test_rejects_manifest_digest_and_id_mismatches(self) -> None:
        manifest_path = self.root / "skills" / "allowed-skill" / "manifest.yaml"
        manifest_path.write_text(
            manifest_path.read_text(encoding="utf-8") + "# changed bytes\n", encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            compile_bundle(self.root, "local-safe")

        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        manifest["id"] = "different-skill"
        write_yaml(manifest_path, manifest)
        registry = self._registry()
        registry["entries"][0]["manifest"]["digest"]["value"] = sha256_bytes(
            manifest_path.read_bytes()
        ).removeprefix("sha256:")
        self._write_registry(registry)
        with self.assertRaisesRegex(ValueError, "entry ID does not match manifest ID"):
            compile_bundle(self.root, "local-safe")

    def test_rejects_router_registry_digest_mismatch(self) -> None:
        router_path = self.root / "router-map.yaml"
        router = yaml.safe_load(router_path.read_text(encoding="utf-8"))
        router["sourceRegistryDigest"]["value"] = "0" * 64
        write_yaml(router_path, router)

        with self.assertRaisesRegex(ValueError, "sourceRegistryDigest"):
            compile_bundle(self.root, "local-safe")

    def test_rejects_tampered_or_symlinked_declared_content(self) -> None:
        reference = self.root / "skills" / "allowed-skill" / "references" / "guide.md"
        reference.write_text("# Tampered guide\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "resource 0 digest"):
            compile_bundle(self.root, "local-safe")

        with tempfile.TemporaryDirectory() as temporary:
            root = _build_canonical_library(Path(temporary))
            entrypoint = root / "skills" / "allowed-skill" / "SKILL.md"
            target = root / "synthetic-external.md"
            target.write_text("# Synthetic external target\n", encoding="utf-8")
            entrypoint.unlink()
            entrypoint.symlink_to(target)
            with self.assertRaisesRegex(ValueError, "symlink"):
                compile_bundle(root, "local-safe")

    def test_bundle_remains_serializable(self) -> None:
        bundle = compile_bundle(self.root, "local-safe")
        self.assertEqual(bundle, json.loads(canonical_json_bytes(bundle)))

    def test_bundle_writer_rejects_symlinked_output(self) -> None:
        bundle = compile_bundle(self.root, "local-safe")
        target = self.root / "actual-bundle.json"
        target.write_text("{}\n", encoding="utf-8")
        output = self.root / "bundle.json"
        output.symlink_to(target)

        with self.assertRaisesRegex(ValueError, "symlink"):
            write_bundle(bundle, output)


if __name__ == "__main__":
    unittest.main()
