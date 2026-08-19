from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from skillref._util import sha256_bytes
from tests.support import ROOT  # noqa: F401 - adds src/ to sys.path for source checkouts

MANIFEST_SCHEMA = "urn:skillref:schema:skill-manifest:0.1"
PROFILE_SCHEMA = "urn:skillref:schema:profile:0.1"
REGISTRY_SCHEMA = "urn:skillref:schema:registry:0.1"
ROUTER_SCHEMA = "urn:skillref:schema:router-map:0.1"


def write_yaml(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=True), encoding="utf-8")


def _digest(value: bytes) -> dict[str, str]:
    return {
        "algorithm": "sha256",
        "value": sha256_bytes(value).removeprefix("sha256:"),
    }


def _manifest(
    *,
    skill_id: str,
    name: str,
    description: str,
    domain: str,
    include: str,
    exclude: str,
    risk_level: str,
    side_effects: bool,
    risk_rationale: str,
    capabilities: list[str],
    resource_scopes: list[str],
    resource_items: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "$schema": MANIFEST_SCHEMA,
        "schemaVersion": "0.1",
        "id": skill_id,
        "version": "1.0.0",
        "name": name,
        "description": description,
        "license": "Apache-2.0",
        "domains": [domain],
        "triggers": {"include": [include], "exclude": [exclude]},
        "risk": {
            "level": risk_level,
            "sideEffects": side_effects,
            "rationale": risk_rationale,
        },
        "permissions": {
            "capabilities": capabilities,
            "resourceScopes": resource_scopes,
        },
        "resources": {
            "entrypoint": "SKILL.md",
            "items": resource_items or [],
        },
        "conflicts": {"hard": [], "supersedes": [], "companions": []},
        "evaluation": {"suiteRefs": ["evals/routing.json"]},
    }


def _permission_set(
    *,
    capabilities: list[str],
    resource_scopes: list[str],
    resource_roles: list[str],
    exposure_modes: list[str],
) -> dict[str, list[str]]:
    return {
        "capabilities": capabilities,
        "resourceScopes": resource_scopes,
        "resourceRoles": resource_roles,
        "exposureModes": exposure_modes,
    }


def _profile(
    profile_id: str,
    *,
    grants: list[dict[str, Any]],
    denials: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "$schema": PROFILE_SCHEMA,
        "schemaVersion": "0.1",
        "id": profile_id,
        "version": "1.0.0",
        "defaultDecision": "deny",
        "resolution": {
            "denialsOverrideGrants": True,
            "unknownValues": "deny",
        },
        "grants": grants,
        "denials": denials,
    }


def build_library(root: Path) -> Path:
    """Create a schema-valid synthetic Level 2 library for isolated tests."""

    chart_guidance = b"# Synthetic chart guidance\n\nUse only for an explicit chart request.\n"
    manifests = {
        "document-summary": _manifest(
            skill_id="document-summary",
            name="Document summary",
            description=(
                "Summarize a supplied fictional document while preserving uncertainty "
                "and source boundaries."
            ),
            domain="documents",
            include="Summarize or condense a supplied document, memo, brief, or report.",
            exclude="Do not use to verify claims against external sources.",
            risk_level="low",
            side_effects=False,
            risk_rationale="Reads supplied content and produces a text summary without mutation.",
            capabilities=["content:read"],
            resource_scopes=["task:provided-content"],
        ),
        "table-analysis": _manifest(
            skill_id="table-analysis",
            name="Table analysis",
            description=(
                "Analyze a supplied synthetic table and conditionally load guidance "
                "for a requested chart."
            ),
            domain="data-analysis",
            include="Analyze, compare, calculate, or chart values from a supplied table.",
            exclude="Do not use for prose-only documents without a tabular question.",
            risk_level="low",
            side_effects=False,
            risk_rationale=(
                "Reads supplied table data and produces derived analysis without mutation."
            ),
            capabilities=["content:read", "table:analyze"],
            resource_scopes=["task:provided-content"],
            resource_items=[
                {
                    "path": "references/chart-guidance.md",
                    "role": "reference",
                    "mediaType": "text/markdown",
                    "loadWhen": "Load only after activation when a chart is explicitly requested.",
                    "maxBytes": 4096,
                    "digest": _digest(chart_guidance),
                }
            ],
        ),
        "deployment-runner": _manifest(
            skill_id="deployment-runner",
            name="Deployment runner",
            description=(
                "Represent a governed synthetic deployment mutation for deterministic "
                "policy-denial tests."
            ),
            domain="software-delivery",
            include=(
                "Execute an approved synthetic deployment with explicit authorization and rollback."
            ),
            exclude="Do not use in a read-only, unapproved, stale, or unresolved context.",
            risk_level="high",
            side_effects=True,
            risk_rationale=(
                "May mutate a synthetic external target and therefore requires explicit grants."
            ),
            capabilities=["deployment:execute", "system:write"],
            resource_scopes=["synthetic:deployment-target"],
        ),
    }

    entries: list[dict[str, Any]] = []
    for skill_id, manifest in manifests.items():
        manifest_path = root / "skills" / skill_id / "manifest.yaml"
        write_yaml(manifest_path, manifest)
        (manifest_path.parent / "SKILL.md").write_text(
            f"# {manifest['name']}\n\nSynthetic instructions for contract tests.\n",
            encoding="utf-8",
        )
        if skill_id == "table-analysis":
            reference = manifest_path.parent / "references" / "chart-guidance.md"
            reference.parent.mkdir(parents=True, exist_ok=True)
            reference.write_bytes(chart_guidance)
        entries.append(
            {
                "id": skill_id,
                "manifest": {
                    "uri": f"skills/{skill_id}/manifest.yaml",
                    "digest": _digest(manifest_path.read_bytes()),
                },
                "lifecycle": {"status": "active"},
                "availability": {
                    "cacheState": "cached",
                    "installState": "installed",
                    "registrationState": "registered",
                },
            }
        )

    registry_path = root / "registry.yaml"
    write_yaml(
        registry_path,
        {
            "$schema": REGISTRY_SCHEMA,
            "schemaVersion": "0.1",
            "id": "synthetic-registry",
            "registryVersion": "1.0.0",
            "entries": entries,
        },
    )
    write_yaml(
        root / "router-map.yaml",
        {
            "$schema": ROUTER_SCHEMA,
            "schemaVersion": "0.1",
            "id": "synthetic-router",
            "version": "1.0.0",
            "sourceRegistryDigest": _digest(registry_path.read_bytes()),
            "policy": {
                "filterBeforeRanking": True,
                "denialsOverrideGrants": True,
                "ambiguityAction": "clarify",
            },
            "retrieval": {
                "enabled": True,
                "mode": "hybrid",
                "candidateLimit": 3,
                "inspectLimit": 2,
                "scoreThreshold": 0.5,
                "fallback": "static-router",
            },
            "routers": [
                {
                    "id": "documents-router",
                    "domain": "documents",
                    "skills": ["document-summary"],
                    "strategy": "filtered-search",
                    "keywordRules": [
                        {
                            "terms": ["document", "brief", "summarize"],
                            "match": "any",
                            "skillId": "document-summary",
                            "weight": 0.8,
                        }
                    ],
                    "fallback": {"action": "search"},
                },
                {
                    "id": "data-router",
                    "domain": "data-analysis",
                    "skills": ["table-analysis"],
                    "strategy": "filtered-search",
                    "keywordRules": [
                        {
                            "terms": ["table", "chart", "analyze"],
                            "match": "any",
                            "skillId": "table-analysis",
                            "weight": 0.8,
                        }
                    ],
                    "fallback": {"action": "search"},
                },
                {
                    "id": "deployment-router",
                    "domain": "software-delivery",
                    "skills": ["deployment-runner"],
                    "strategy": "filtered-search",
                    "keywordRules": [
                        {
                            "terms": ["deployment", "deploy", "execute"],
                            "match": "any",
                            "skillId": "deployment-runner",
                            "weight": 1.0,
                        }
                    ],
                    "fallback": {"action": "search"},
                },
            ],
        },
    )

    document_grant = {
        "id": "allow-document-summary",
        "selector": {"skillIds": ["document-summary"]},
        "permissions": _permission_set(
            capabilities=["content:read"],
            resource_scopes=["task:provided-content"],
            resource_roles=["instructions"],
            exposure_modes=["prompt-visible"],
        ),
        "reason": "Expose one compact read-only skill for prompt-visible lifecycle tests.",
    }
    table_grant = {
        "id": "allow-table-analysis",
        "selector": {"skillIds": ["table-analysis"]},
        "permissions": _permission_set(
            capabilities=["content:read", "table:analyze"],
            resource_scopes=["task:provided-content"],
            resource_roles=["instructions", "reference"],
            exposure_modes=["router-retrievable"],
        ),
        "reason": "Permit read-only table analysis through filtered retrieval.",
    }
    deployment_grant = {
        "id": "allow-deployment-runner",
        "selector": {"skillIds": ["deployment-runner"]},
        "permissions": _permission_set(
            capabilities=["deployment:execute", "system:write"],
            resource_scopes=["synthetic:deployment-target"],
            resource_roles=["instructions"],
            exposure_modes=["router-retrievable"],
        ),
        "reason": "Permit the synthetic mutation only in the explicitly privileged profile.",
    }
    write_yaml(
        root / "profiles" / "local-safe.yaml",
        _profile(
            "local-safe",
            grants=[document_grant, table_grant, deployment_grant],
            denials=[],
        ),
    )
    write_yaml(
        root / "profiles" / "read-only.yaml",
        _profile(
            "read-only",
            grants=[document_grant, table_grant, deployment_grant],
            denials=[
                {
                    "id": "deny-deployment-runner",
                    "selector": {"skillIds": ["deployment-runner"]},
                    "reason": "A denial must override the otherwise matching deployment grant.",
                }
            ],
        ),
    )
    return root
