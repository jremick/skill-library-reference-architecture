"""Deterministic profile compilation with pre-retrieval policy filtering."""

from __future__ import annotations

import os
import tempfile
import unicodedata
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from jsonschema import Draft202012Validator

from . import __version__
from ._util import (
    STRUCTURED_SUFFIXES,
    as_string_set,
    canonical_json_bytes,
    digest_value,
    iter_files,
    load_structured,
    relative_posix,
    sha256_bytes,
    source_digest,
)
from .validation import _infer_kind

_CANONICAL_SCHEMA_FILES = {
    "profile": "profile.schema.json",
    "registry": "registry.schema.json",
    "router-map": "router-map.schema.json",
    "skill-manifest": "skill-manifest.schema.json",
}
_CANONICAL_SCHEMA_URNS = {
    kind: f"urn:skillref:schema:{kind}:0.1" for kind in _CANONICAL_SCHEMA_FILES
}


def _validate_canonical_document(document: dict[str, Any], kind: str) -> None:
    """Validate canonical compiler inputs without echoing input values."""

    expected_urn = _CANONICAL_SCHEMA_URNS[kind]
    if document.get("$schema") != expected_urn and document.get("schemaVersion") != "0.1":
        return
    schema_path = Path(__file__).resolve().parents[2] / "schemas" / _CANONICAL_SCHEMA_FILES[kind]
    if not schema_path.is_file():
        raise ValueError(f"canonical {kind} schema is unavailable")
    schema = load_structured(schema_path)
    if not isinstance(schema, dict):
        raise ValueError(f"canonical {kind} schema is invalid")
    errors = sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        error = errors[0]
        pointer = "/".join(str(part) for part in error.absolute_path) or "<root>"
        raise ValueError(
            f"canonical {kind} failed schema validation at {pointer} ({error.validator})"
        )


def _records(root: Path) -> list[tuple[Path, dict[str, Any], str]]:
    records: list[tuple[Path, dict[str, Any], str]] = []
    for path in iter_files(root, STRUCTURED_SUFFIXES):
        if relative_posix(path, root).startswith("schemas/"):
            continue
        try:
            value = load_structured(path)
        except (OSError, ValueError):
            continue
        kind = _infer_kind(value)
        if isinstance(value, dict) and kind:
            records.append((path, value, kind))
    return records


def _permission_names(value: Any, *, required_only: bool = False) -> set[str]:
    if isinstance(value, dict):
        result: set[str] = set()
        for key, child in value.items():
            if isinstance(child, bool) and child:
                result.add(str(key))
            elif isinstance(child, dict):
                if required_only and not child.get("required", True):
                    continue
                identifier = child.get("permission_id") or child.get("id") or child.get("name")
                if isinstance(identifier, str):
                    result.add(identifier)
        return result
    if not isinstance(value, list):
        return as_string_set(value)
    result = set()
    for item in value:
        if isinstance(item, str):
            if not required_only:
                result.add(item)
        elif isinstance(item, dict):
            if required_only and not item.get("required", True):
                continue
            identifier = item.get("permission_id") or item.get("id") or item.get("name")
            if isinstance(identifier, str):
                result.add(identifier)
    return result


def _visibility(value: Any) -> set[str]:
    aliases = {
        "prompt": "prompt_visible",
        "prompt-visible": "prompt_visible",
        "prompt_visible": "prompt_visible",
        "router": "router_retrievable",
        "retrievable": "router_retrievable",
        "router-retrievable": "router_retrievable",
        "router_retrievable": "router_retrievable",
    }
    values = as_string_set(value)
    if not values:
        return {"router_retrievable"}
    result = {aliases.get(item, item.replace("-", "_")) for item in values}
    if "both" in result:
        result.remove("both")
        result.update({"prompt_visible", "router_retrievable"})
    return result


def _single_record(
    records: list[tuple[Path, dict[str, Any], str]],
    kind: str,
    *,
    required: bool,
) -> tuple[Path, dict[str, Any]] | None:
    matches = [(path, document) for path, document, record_kind in records if record_kind == kind]
    if not matches:
        if required:
            raise ValueError(f"exactly one {kind} is required")
        return None
    if len(matches) != 1:
        raise ValueError(f"multiple {kind} documents are not allowed")
    return matches[0]


def _is_canonical_registry(registry: dict[str, Any]) -> bool:
    return (
        registry.get("schemaVersion") == "0.1"
        and isinstance(registry.get("id"), str)
        and isinstance(registry.get("registryVersion"), str)
    )


def _reject_symlink_path(path: Path, boundary: Path, *, label: str) -> None:
    """Reject any symlink component without resolving away the evidence first."""

    boundary = boundary.resolve()
    lexical = path.absolute()
    try:
        relative = lexical.relative_to(boundary)
    except ValueError as error:
        raise ValueError(f"{label} escapes the compilation root") from error
    current = boundary
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"{label} must not contain symlinks")


def _resolve_local_file(
    base: Path,
    uri: Any,
    boundary: Path,
    *,
    label: str,
) -> Path:
    if not isinstance(uri, str) or not uri:
        raise ValueError(f"{label} must be a non-empty local URI")
    parsed = urlsplit(uri)
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
        raise ValueError(f"{label} must be a local relative URI without query or fragment")
    decoded = unquote(parsed.path)
    if not decoded or "\\" in decoded or "\x00" in decoded:
        raise ValueError(f"{label} is not a portable local relative URI")
    relative = Path(decoded)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"{label} escapes its allowed directory")

    boundary = boundary.resolve()
    candidate = (base / relative).absolute()
    try:
        candidate.relative_to(boundary)
    except ValueError as error:
        raise ValueError(f"{label} escapes its allowed directory") from error
    _reject_symlink_path(candidate, boundary, label=label)
    if not candidate.is_file():
        raise ValueError(f"{label} does not resolve to a file")
    return candidate.resolve()


def _digest_string(value: Any) -> str | None:
    if isinstance(value, str) and value.startswith("sha256:"):
        return value
    if isinstance(value, dict) and value.get("algorithm") == "sha256":
        digest = value.get("value")
        if isinstance(digest, str):
            return f"sha256:{digest}"
    return None


def _manifest_content_paths(
    manifest_path: Path,
    manifest: dict[str, Any],
    *,
    canonical: bool,
) -> list[Path]:
    """Resolve and verify the entrypoint and every declared resource."""

    paths: list[Path] = []
    skill_root = manifest_path.parent.resolve()
    resources = manifest.get("resources")
    if canonical:
        if not isinstance(resources, dict):
            raise ValueError(f"canonical manifest {manifest_path.name} has invalid resources")
        entrypoint = _resolve_local_file(
            manifest_path.parent,
            resources.get("entrypoint"),
            skill_root,
            label="manifest entrypoint",
        )
        paths.append(entrypoint)
        items = resources.get("items")
        if not isinstance(items, list):
            raise ValueError(f"canonical manifest {manifest_path.name} has invalid resources.items")
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                raise ValueError(f"manifest resource {index} must be an object")
            resource_path = _resolve_local_file(
                manifest_path.parent,
                item.get("path"),
                skill_root,
                label=f"manifest resource {index}",
            )
            expected = _digest_string(item.get("digest"))
            if "digest" in item and expected is None:
                raise ValueError(f"manifest resource {index} has an invalid digest")
            if expected is not None and sha256_bytes(resource_path.read_bytes()) != expected:
                raise ValueError(f"manifest resource {index} digest does not match its bytes")
            paths.append(resource_path)
    elif isinstance(resources, list):
        # Compatibility support remains registry-bound and applies the same
        # local-path and symlink rules as the canonical contract.
        for index, item in enumerate(resources):
            if not isinstance(item, dict):
                continue
            uri = item.get("uri", item.get("path"))
            paths.append(
                _resolve_local_file(
                    manifest_path.parent,
                    uri,
                    skill_root,
                    label=f"legacy manifest resource {index}",
                )
            )
    return paths


def _registry_manifests(
    root: Path,
    registry_path: Path,
    registry: dict[str, Any],
) -> tuple[dict[str, tuple[Path, dict[str, Any], dict[str, Any], str]], list[Path], bool]:
    canonical = _is_canonical_registry(registry)
    entries = registry.get("entries")
    if not isinstance(entries, list):
        raise ValueError("registry entries must be an array")

    manifests: dict[str, tuple[Path, dict[str, Any], dict[str, Any], str]] = {}
    content_paths: list[Path] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(f"registry entry {index} must be an object")
        skill_id = entry.get("id") if canonical else entry.get("skill_id", entry.get("id"))
        if not isinstance(skill_id, str) or not skill_id:
            raise ValueError(f"registry entry {index} has no skill ID")
        if skill_id in manifests:
            raise ValueError(f"duplicate registry skill ID: {skill_id}")
        if canonical:
            reference = entry.get("manifest")
            if not isinstance(reference, dict):
                raise ValueError(f"registry entry {skill_id} has no manifest reference")
            uri = reference.get("uri")
            expected_digest = _digest_string(reference.get("digest"))
        else:
            uri = entry.get("manifest_uri", entry.get("manifest_path"))
            expected_digest = _digest_string(entry.get("manifest_digest"))
        if expected_digest is None:
            raise ValueError(f"registry entry {skill_id} has no valid manifest digest")
        manifest_path = _resolve_local_file(
            registry_path.parent,
            uri,
            root,
            label=f"registry manifest URI for {skill_id}",
        )
        actual_digest = sha256_bytes(manifest_path.read_bytes())
        if actual_digest != expected_digest:
            raise ValueError(f"registry manifest digest mismatch for {skill_id}")
        try:
            manifest = load_structured(manifest_path)
        except (OSError, ValueError) as error:
            raise ValueError(f"registry manifest for {skill_id} could not be parsed") from error
        if not isinstance(manifest, dict) or _infer_kind(manifest) != "skill-manifest":
            raise ValueError(f"registry manifest for {skill_id} is not a skill manifest")
        manifest_id = (
            manifest.get("id") if canonical else manifest.get("skill_id", manifest.get("id"))
        )
        if manifest_id != skill_id:
            raise ValueError(f"registry entry ID does not match manifest ID for {skill_id}")
        manifest_is_canonical = (
            manifest.get("schemaVersion") == "0.1"
            and isinstance(manifest.get("id"), str)
            and isinstance(manifest.get("triggers"), dict)
            and isinstance(manifest.get("permissions"), dict)
            and isinstance(manifest.get("resources"), dict)
        )
        if canonical and not manifest_is_canonical:
            raise ValueError(
                f"canonical registry entry {skill_id} must reference a canonical manifest"
            )
        content_paths.extend(
            _manifest_content_paths(
                manifest_path,
                manifest,
                canonical=manifest_is_canonical,
            )
        )
        content_paths.append(manifest_path)
        manifests[skill_id] = (manifest_path, manifest, entry, actual_digest)
    return manifests, content_paths, canonical


def _find_profile(
    records: list[tuple[Path, dict[str, Any], str]], profile_id: str
) -> tuple[Path, dict[str, Any]]:
    profiles = [
        (path, document)
        for path, document, kind in records
        if kind == "profile" and document.get("profile_id", document.get("id")) == profile_id
    ]
    if not profiles:
        raise ValueError(f"unknown profile_id: {profile_id}")
    if len(profiles) > 1:
        raise ValueError(f"profile_id is not unique: {profile_id}")
    return profiles[0]


def _selector_matches(skill_id: str, manifest: dict[str, Any], selector: Any) -> bool:
    if not isinstance(selector, dict) or not selector:
        return False
    checks: list[bool] = []
    if "skillIds" in selector or "skill_ids" in selector:
        selected = as_string_set(selector.get("skillIds", selector.get("skill_ids")))
        checks.append(skill_id in selected)
    if "domains" in selector:
        selected = as_string_set(selector.get("domains"))
        domains = as_string_set(manifest.get("domains"))
        checks.append(bool(selected & domains))
    if "riskLevels" in selector or "risk_levels" in selector:
        selected = as_string_set(selector.get("riskLevels", selector.get("risk_levels")))
        risk = manifest.get("risk", {})
        risk_level = risk.get("level") if isinstance(risk, dict) else risk
        checks.append(risk_level in selected)
    return bool(checks) and all(checks)


def _permission_set(value: Any) -> dict[str, set[str]]:
    if not isinstance(value, dict):
        return {
            "capabilities": set(),
            "resourceScopes": set(),
            "resourceRoles": set(),
            "exposureModes": set(),
        }
    return {
        "capabilities": as_string_set(value.get("capabilities")),
        "resourceScopes": as_string_set(value.get("resourceScopes", value.get("resource_scopes"))),
        "resourceRoles": as_string_set(value.get("resourceRoles", value.get("resource_roles"))),
        "exposureModes": as_string_set(value.get("exposureModes", value.get("exposure_modes"))),
    }


def _manifest_permissions(manifest: dict[str, Any]) -> dict[str, set[str]]:
    permissions = manifest.get("permissions", {})
    requested = _permission_set(permissions)
    requested["resourceRoles"].add("instructions")
    resources = manifest.get("resources", {})
    if isinstance(resources, dict):
        for item in resources.get("items", []):
            if isinstance(item, dict) and isinstance(item.get("role"), str):
                requested["resourceRoles"].add(item["role"])
    return requested


def _canonical_exposure(values: set[str]) -> set[str]:
    aliases = {
        "prompt-visible": "prompt_visible",
        "prompt_visible": "prompt_visible",
        "router-retrievable": "router_retrievable",
        "router_retrievable": "router_retrievable",
    }
    return {aliases.get(value, value.replace("-", "_")) for value in values}


def _eligibility(
    skill_id: str,
    manifest: dict[str, Any],
    entry: dict[str, Any] | None,
    profile: dict[str, Any],
) -> tuple[bool, list[str], set[str]]:
    reasons: list[str] = []
    if entry and entry.get("enabled") is False:
        reasons.append("registry_disabled")
    lifecycle = entry.get("lifecycle", {}) if entry else {}
    if isinstance(lifecycle, dict):
        status = lifecycle.get("status")
        if status in {"draft", "retired"}:
            reasons.append(f"registry_{status}")
        elif status is not None and status not in {"active", "deprecated"}:
            reasons.append("registry_lifecycle_unusable")
        elif isinstance(entry, dict) and isinstance(entry.get("manifest"), dict) and status is None:
            reasons.append("registry_lifecycle_unusable")
    allowed_ids = as_string_set(profile.get("allowed_skill_ids"), ("skill_id", "id"))
    denied_ids = as_string_set(profile.get("denied_skill_ids"), ("skill_id", "id"))
    if skill_id in denied_ids:
        reasons.append("skill_denied")
    if allowed_ids and skill_id not in allowed_ids:
        reasons.append("skill_not_allowed")
    domains = as_string_set(manifest.get("domains"), ("domain_id", "id", "name"))
    denied_domains = as_string_set(profile.get("denied_domains"), ("domain_id", "id", "name"))
    allowed_domains = as_string_set(profile.get("allowed_domains"), ("domain_id", "id", "name"))
    if domains & denied_domains:
        reasons.append("domain_denied")
    if allowed_domains and domains and not domains & allowed_domains:
        reasons.append("domain_not_allowed")

    exposures: set[str] = set()
    canonical_grants = profile.get("grants")
    canonical_denials = profile.get("denials")
    if isinstance(canonical_grants, list) and isinstance(canonical_denials, list):
        requested = _manifest_permissions(manifest)
        granted = {key: set() for key in requested}
        matched_grant = False
        for grant in canonical_grants:
            if not isinstance(grant, dict) or not _selector_matches(
                skill_id, manifest, grant.get("selector")
            ):
                continue
            matched_grant = True
            permissions = _permission_set(grant.get("permissions"))
            for key in granted:
                granted[key].update(permissions[key])
        denied = {key: set() for key in requested}
        full_denial = False
        for denial in canonical_denials:
            if not isinstance(denial, dict) or not _selector_matches(
                skill_id, manifest, denial.get("selector")
            ):
                continue
            if "permissions" not in denial:
                full_denial = True
            else:
                permissions = _permission_set(denial.get("permissions"))
                for key in denied:
                    denied[key].update(permissions[key])
        if full_denial:
            reasons.append("profile_denial")
        if not matched_grant and profile.get("defaultDecision") == "deny":
            reasons.append("no_matching_grant")
        for key in ("capabilities", "resourceScopes", "resourceRoles"):
            if requested[key] & denied[key]:
                reasons.append(f"{key}_denied")
            if requested[key] - granted[key]:
                reasons.append(f"{key}_not_granted")
        exposures = _canonical_exposure(granted["exposureModes"] - denied["exposureModes"])
        if not exposures:
            reasons.append("exposure_not_granted")
    else:
        grants = _permission_names(
            profile.get("permission_grants", profile.get("granted_permissions"))
        )
        denied_permissions = _permission_names(profile.get("denied_permissions"))
        requested = manifest.get("requested_permissions", manifest.get("permissions"))
        required = _permission_names(requested, required_only=True)
        if required & denied_permissions:
            reasons.append("permission_denied")
        missing = required - grants
        if missing:
            reasons.append("required_permission_not_granted")
        exposures = _visibility(entry.get("visibility_intent") if entry else None)

    fail_closed = profile.get("fail_closed", profile.get("defaultDecision") == "deny")
    if fail_closed is not True:
        reasons.append("profile_not_fail_closed")
    return not reasons, sorted(reasons), exposures


def compile_bundle(
    root: str | Path,
    profile_id: str,
    *,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    """Compile a byte-stable, profile-filtered bundle.

    Policy and permission filtering is completed before any candidate appears in
    either visibility set or in a route's candidate list.
    """

    root_path = Path(root).resolve()
    if not root_path.is_dir():
        raise ValueError("compilation root must be a directory")
    records = _records(root_path)
    registry_record = _single_record(records, "registry", required=True)
    assert registry_record is not None
    registry_path, registry = registry_record
    _reject_symlink_path(registry_path, root_path, label="registry path")
    _validate_canonical_document(registry, "registry")
    manifests, content_paths, canonical_registry = _registry_manifests(
        root_path, registry_path, registry
    )
    for _, manifest, _, _ in manifests.values():
        _validate_canonical_document(manifest, "skill-manifest")
    router_record = _single_record(records, "router-map", required=False)
    if router_record is not None:
        router_path, router = router_record
        _reject_symlink_path(router_path, root_path, label="router map path")
        _validate_canonical_document(router, "router-map")
        if canonical_registry:
            if not (
                router.get("schemaVersion") == "0.1"
                and isinstance(router.get("sourceRegistryDigest"), dict)
                and isinstance(router.get("routers"), list)
            ):
                raise ValueError("canonical registry requires a canonical router map")
            expected_registry_digest = _digest_string(router.get("sourceRegistryDigest"))
            actual_registry_digest = sha256_bytes(registry_path.read_bytes())
            if expected_registry_digest != actual_registry_digest:
                raise ValueError("router sourceRegistryDigest does not match registry bytes")
    else:
        router_path = None
        router = None
    profile_path, profile = _find_profile(records, profile_id)
    _reject_symlink_path(profile_path, root_path, label="profile path")
    _validate_canonical_document(profile, "profile")

    installed_candidates = {
        skill_id
        for skill_id, (_, _, entry, _) in manifests.items()
        if isinstance(entry.get("availability"), dict)
        and entry["availability"].get("installState") == "installed"
    }
    cached_candidates = {
        skill_id
        for skill_id, (_, _, entry, _) in manifests.items()
        if isinstance(entry.get("availability"), dict)
        and entry["availability"].get("cacheState") == "cached"
    }
    all_registered = sorted(manifests)
    eligible: list[str] = []
    prompt_visible: list[str] = []
    router_retrievable: list[str] = []
    skills: list[dict[str, Any]] = []
    for skill_id in all_registered:
        manifest_path, manifest, entry, registered_digest = manifests[skill_id]
        is_eligible, _reasons, visibility = _eligibility(skill_id, manifest, entry, profile)
        if not is_eligible:
            continue
        eligible.append(skill_id)
        if "prompt_visible" in visibility:
            prompt_visible.append(skill_id)
        if "router_retrievable" in visibility:
            router_retrievable.append(skill_id)
        skills.append(
            {
                "capabilities": sorted(
                    as_string_set(
                        manifest.get(
                            "capabilities", manifest.get("permissions", {}).get("capabilities", [])
                        ),
                        ("capability_id", "id", "name"),
                    )
                ),
                "domains": sorted(
                    as_string_set(manifest.get("domains"), ("domain_id", "id", "name"))
                ),
                "manifest_digest": registered_digest,
                "manifest_path": relative_posix(manifest_path, root_path),
                "name": manifest.get("name", skill_id),
                "positive_triggers": sorted(
                    str(item)
                    for item in manifest.get("triggers", {}).get("include", [])
                    if isinstance(item, str)
                ),
                "requested_permissions": sorted(
                    _permission_names(
                        manifest.get("requested_permissions", manifest.get("permissions"))
                    )
                ),
                "skill_id": skill_id,
                "summary": manifest.get("summary", manifest.get("description", "")),
                "version": manifest.get("version", "0.0.0"),
                "visibility": sorted(visibility),
            }
        )

    eligible_set = set(eligible)
    routes: list[dict[str, Any]] = []
    exact_alias_targets: dict[str, str] = {}
    if router is not None:
        canonical_routers = router.get("routers", router.get("routes"))
        if not isinstance(canonical_routers, list):
            raise ValueError("router map routers must be an array")
        for route in canonical_routers:
            if not isinstance(route, dict):
                continue
            route_id = route.get("route_id", route.get("id"))
            if not isinstance(route_id, str) or not route_id:
                raise ValueError("router entry has no route ID")
            candidates = as_string_set(
                route.get("candidate_skill_ids", route.get("skill_ids", route.get("skills"))),
                ("skill_id", "id"),
            )
            filtered = sorted(candidates & eligible_set)
            if not filtered:
                continue
            filtered_set = set(filtered)
            aliases = []
            for alias in route.get("exactAliases", route.get("exact_aliases", [])):
                if (
                    isinstance(alias, dict)
                    and alias.get("skillId", alias.get("skill_id")) in filtered_set
                ):
                    normalized_phrase = " ".join(
                        unicodedata.normalize("NFC", str(alias.get("phrase", ""))).split()
                    ).casefold()
                    alias_skill_id = alias.get("skillId", alias.get("skill_id"))
                    prior_target = exact_alias_targets.get(normalized_phrase)
                    if prior_target is not None and prior_target != alias_skill_id:
                        raise ValueError("normalized exact alias collision between eligible skills")
                    exact_alias_targets[normalized_phrase] = alias_skill_id
                    aliases.append(
                        {
                            "phrase": alias.get("phrase", ""),
                            "skill_id": alias.get("skillId", alias.get("skill_id")),
                        }
                    )
            keyword_rules = []
            for rule in route.get("keywordRules", route.get("keyword_rules", [])):
                if (
                    isinstance(rule, dict)
                    and rule.get("skillId", rule.get("skill_id")) in filtered_set
                ):
                    keyword_rules.append(
                        {
                            "match": rule.get("match", "any"),
                            "skill_id": rule.get("skillId", rule.get("skill_id")),
                            "terms": sorted(str(term) for term in rule.get("terms", [])),
                            "weight": rule.get("weight", 1),
                        }
                    )
            normalized: dict[str, Any] = {
                "candidate_skill_ids": filtered,
                "route_id": route_id,
            }
            if route.get("domain"):
                normalized["domain"] = route["domain"]
            if aliases:
                normalized["exact_aliases"] = sorted(
                    aliases, key=lambda item: (item["phrase"], item["skill_id"])
                )
            if keyword_rules:
                normalized["keyword_rules"] = sorted(
                    keyword_rules,
                    key=lambda item: (item["skill_id"], item["match"], item["terms"]),
                )
            matchers = route.get("matchers")
            if matchers:
                normalized["matchers"] = matchers
            priority = route.get("priority", 0)
            if priority:
                normalized["priority"] = priority
            routes.append(normalized)
    routes.sort(key=lambda item: (-int(item.get("priority", 0)), str(item["route_id"])))

    all_input_paths = [registry_path, profile_path, *content_paths]
    if router_path is not None:
        all_input_paths.append(router_path)
    excluded = [Path(output_path).resolve()] if output_path is not None else []
    source = source_digest(root_path, all_input_paths, excluded=excluded)
    eligible_set = set(eligible)
    installed = sorted(installed_candidates & eligible_set)
    cached = sorted(cached_candidates & eligible_set)
    lifecycle = {
        "activated": [],
        "conditional_resources_loaded": [],
        "executed": [],
        "inspected": [],
        "cached_eligible": cached,
        "installed_eligible": installed,
        "installed_cache_eligible": sorted(set(installed) | set(cached)),
        "policy_eligible": sorted(eligible),
        "prompt_visible": sorted(prompt_visible),
        "registered_eligible": sorted(eligible),
        "retrieved_candidates": [],
        "router_retrievable": sorted(router_retrievable),
        "verified": [],
    }
    payload: dict[str, Any] = {
        "bundle_format": "skillref.compiled-bundle.v0alpha1",
        "compiler_version": __version__,
        "lifecycle_states": lifecycle,
        "profile": {
            "fail_closed": profile.get("fail_closed", profile.get("defaultDecision") == "deny"),
            "profile_digest": digest_value(profile),
            "profile_id": profile_id,
            "profile_path": relative_posix(profile_path, root_path),
        },
        "routes": routes,
        "skills": sorted(skills, key=lambda item: item["skill_id"]),
        "source_digest": source,
    }
    payload["bundle_digest"] = digest_value(payload)
    return payload


def write_bundle(bundle: dict[str, Any], output_path: str | Path) -> None:
    path = Path(output_path).absolute()
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError("bundle output path and parent must not be symlinks")
    if path.exists() and not path.is_file():
        raise ValueError("bundle output path must be a regular file")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise ValueError("bundle output path must not be a symlink")
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(canonical_json_bytes(bundle))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
