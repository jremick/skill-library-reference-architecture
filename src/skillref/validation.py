"""Schema and cross-reference validation."""

from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

from ._util import (
    IGNORED_PARTS,
    STRUCTURED_SUFFIXES,
    as_string_set,
    iter_files,
    load_structured,
    relative_posix,
    sha256_bytes,
)

PORTABLE_REPOSITORY_PATH = re.compile(
    r"^(?!/)(?!.*\\)(?!.*:)(?!.*(?:^|/)~[^/]*)"
    r"(?!.*(?:^|/)\.\.?(?:/|$))[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)*$"
)

KIND_SIGNATURES: tuple[tuple[str, frozenset[str]], ...] = (
    ("skill-manifest", frozenset({"skill_id", "version", "resources"})),
    ("skill-manifest", frozenset({"name", "description", "triggers", "permissions", "resources"})),
    ("registry", frozenset({"registry_id", "entries"})),
    ("registry", frozenset({"registryVersion", "entries"})),
    ("router-map", frozenset({"router_id", "routes"})),
    ("router-map", frozenset({"routes", "fallbacks", "domains"})),
    ("profile", frozenset({"profile_id", "fail_closed"})),
    ("profile", frozenset({"permissions", "visibility", "failClosed"})),
    ("eval-case", frozenset({"case_id", "expected_skill_ids"})),
    ("telemetry-event", frozenset({"event_id", "run_id", "stage"})),
    ("telemetry-event", frozenset({"eventId", "runId", "stage"})),
    ("activation-transition", frozenset({"transitionId", "from", "to"})),
)


def _issue(
    category: str,
    path: str,
    message: str,
    *,
    pointer: str = "",
    severity: str = "error",
) -> dict[str, str]:
    issue = {"category": category, "file": path, "message": message, "severity": severity}
    if pointer:
        issue["pointer"] = pointer
    return issue


def _schema_key(path: Path) -> str:
    name = path.name.lower()
    if name.startswith("urn:skillref:schema:"):
        parts = name.split(":")
        return parts[-2] if len(parts) >= 2 else name
    for suffix in (".schema.json", ".json", ".yaml", ".yml"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
            break
    return name


def _infer_kind(value: Any) -> str | None:
    if not isinstance(value, dict):
        return None
    schema_ref = value.get("$schema")
    if isinstance(schema_ref, str):
        return _schema_key(Path(schema_ref))
    explicit = value.get("kind") or value.get("schema_kind")
    if isinstance(explicit, str):
        return explicit.lower().replace("_", "-")
    keys = frozenset(value)
    for name, signature in KIND_SIGNATURES:
        if signature <= keys:
            return name
    if isinstance(value.get("cases"), list):
        return "eval-suite"
    return None


def _load_schemas(root: Path) -> tuple[dict[str, dict[str, Any]], list[dict[str, str]]]:
    schemas: dict[str, dict[str, Any]] = {}
    issues: list[dict[str, str]] = []
    schema_root = root / "schemas"
    if not schema_root.is_dir():
        return schemas, [_issue("schema", "schemas", "schema directory is missing")]
    for path in iter_files(schema_root, {".json"}):
        relative = relative_posix(path, root)
        try:
            value = load_structured(path)
            if not isinstance(value, dict):
                raise TypeError("schema root must be an object")
            Draft202012Validator.check_schema(value)
        except (OSError, ValueError, TypeError, SchemaError) as error:
            issues.append(_issue("schema", relative, f"invalid schema: {error}"))
            continue
        schemas[_schema_key(path)] = value
    if not schemas:
        issues.append(_issue("schema", "schemas", "no JSON schemas were found"))
    return schemas, issues


def _matching_schema(kind: str, schemas: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    aliases = {
        "manifest": "skill-manifest",
        "router": "router-map",
        "evaluation-case": "eval-case",
    }
    kind = aliases.get(kind, kind)
    if kind in schemas:
        return schemas[kind]
    for key, schema in schemas.items():
        if kind in key or key in kind:
            return schema
    return None


def _validate_instance(
    value: Any,
    schema: dict[str, Any],
    path: str,
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    for error in sorted(
        validator.iter_errors(value),
        key=lambda item: tuple(str(part) for part in item.absolute_path),
    ):
        parts = tuple(str(part) for part in error.absolute_path)
        pointer = "/" + "/".join(parts) if parts else ""
        issues.append(_issue("schema", path, error.message, pointer=pointer))
    return issues


def _structured_documents(
    root: Path,
) -> tuple[list[tuple[Path, Any, str | None]], list[dict[str, str]]]:
    documents: list[tuple[Path, Any, str | None]] = []
    issues: list[dict[str, str]] = []
    for path in iter_files(root, STRUCTURED_SUFFIXES):
        relative = relative_posix(path, root)
        if relative.startswith("schemas/") or path.name in {"uv.lock", "package-lock.json"}:
            continue
        try:
            value = load_structured(path)
        except (OSError, ValueError) as error:
            issues.append(_issue("parse", relative, f"could not parse structured file: {error}"))
            continue
        documents.append((path, value, _infer_kind(value)))
    return documents, issues


def _filesystem_issues(root: Path) -> list[dict[str, str]]:
    """Reject repository symlinks before any validator follows their targets."""

    issues: list[dict[str, str]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        try:
            relative_path = path.absolute().relative_to(root.absolute())
        except ValueError:
            continue
        if any(part in IGNORED_PARTS for part in relative_path.parts):
            continue
        if path.is_symlink():
            issues.append(
                _issue(
                    "path-escape",
                    relative_path.as_posix(),
                    "repository input must not be a symbolic link",
                )
            )
    return issues


def _is_portable_repository_path(value: str) -> bool:
    return bool(PORTABLE_REPOSITORY_PATH.fullmatch(value))


def _has_symlink_component(path: Path, root: Path) -> bool:
    try:
        parts = path.absolute().relative_to(root.absolute()).parts
    except ValueError:
        return False
    cursor = root.absolute()
    for part in parts:
        cursor /= part
        if cursor.is_symlink():
            return True
    return False


def _entry_id(entry: Any) -> str | None:
    if not isinstance(entry, dict):
        return None
    for key in ("skill_id", "id"):
        value = entry.get(key)
        if isinstance(value, str):
            return value
    return None


def _document_id(value: dict[str, Any], kind: str) -> str | None:
    if kind == "skill-manifest":
        candidate = value.get("skill_id", value.get("id"))
    elif kind == "profile":
        candidate = value.get("profile_id", value.get("id"))
    else:
        candidate = value.get("id")
    return candidate if isinstance(candidate, str) else None


def _digest_string(value: Any) -> str | None:
    if isinstance(value, str):
        return value if value.startswith("sha256:") else None
    if isinstance(value, dict) and value.get("algorithm") == "sha256":
        digest = value.get("value")
        return f"sha256:{digest}" if isinstance(digest, str) else None
    return None


def _reference(entry: dict[str, Any]) -> tuple[str | None, Any]:
    manifest = entry.get("manifest")
    if isinstance(manifest, dict):
        return manifest.get("uri"), manifest.get("digest")
    return (
        entry.get("manifest_uri", entry.get("manifest_path")),
        entry.get("manifest_digest"),
    )


def _route_candidates(route: dict[str, Any]) -> set[str]:
    for key in (
        "candidate_skill_ids",
        "skill_ids",
        "candidateSkillIds",
        "skillIds",
        "skills",
        "candidates",
    ):
        if key in route:
            return as_string_set(route[key], ("skill_id", "skillId", "id"))
    return set()


def _matcher_atoms(value: Any) -> set[str]:
    atoms: set[str] = set()
    if isinstance(value, str):
        atoms.add(value.casefold())
    elif isinstance(value, list):
        for child in value:
            atoms.update(_matcher_atoms(child))
    elif isinstance(value, dict):
        for key, child in value.items():
            if key.casefold() not in {"weight", "score", "threshold"}:
                atoms.update(_matcher_atoms(child))
    return atoms


def _namespace(path: Path, root: Path) -> str:
    """Keep intentionally repeated level examples in separate ID namespaces."""

    try:
        parts = path.resolve().relative_to(root.resolve()).parts
    except ValueError:
        return "."
    if len(parts) >= 2 and parts[0] == "examples":
        return "/".join(parts[:2])
    return "."


def _cross_reference_issues(
    root: Path,
    documents: list[tuple[Path, Any, str | None]],
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    manifest_ids: set[str] = set()
    registry_ids: set[str] = set()
    all_skill_ids: set[str] = set()
    profile_ids: set[str] = set()

    manifest_occurrences: Counter[tuple[str, str]] = Counter()
    profile_occurrences: Counter[tuple[str, str]] = Counter()
    manifest_bytes: dict[tuple[str, str], dict[str, list[str]]] = defaultdict(
        lambda: defaultdict(list)
    )
    registry_documents: dict[str, list[tuple[Path, dict[str, Any]]]] = defaultdict(list)
    skill_ids_by_namespace: dict[str, set[str]] = defaultdict(set)
    for path, value, kind in documents:
        if not isinstance(value, dict):
            continue
        relative = relative_posix(path, root)
        namespace = _namespace(path, root)
        if kind == "skill-manifest":
            skill_id = _document_id(value, kind)
            if isinstance(skill_id, str):
                manifest_ids.add(skill_id)
                all_skill_ids.add(skill_id)
                skill_ids_by_namespace[namespace].add(skill_id)
                manifest_occurrences[(namespace, skill_id)] += 1
                version = value.get("version")
                if isinstance(version, str):
                    raw_digest = sha256_bytes(path.read_bytes())
                    manifest_bytes[(skill_id, version)][raw_digest].append(relative)
        elif kind == "registry":
            registry_documents[namespace].append((path, value))
            entries = value.get("entries", [])
            entry_ids = [_entry_id(entry) for entry in entries] if isinstance(entries, list) else []
            duplicates = sorted(
                key for key, count in Counter(entry_ids).items() if key and count > 1
            )
            for duplicate in duplicates:
                issues.append(
                    _issue("duplicate-id", relative, f"duplicate registry skill_id: {duplicate}")
                )
            registry_ids.update(identifier for identifier in entry_ids if identifier)
            all_skill_ids.update(identifier for identifier in entry_ids if identifier)
            skill_ids_by_namespace[namespace].update(
                identifier for identifier in entry_ids if identifier
            )
        elif kind == "profile":
            profile_id = _document_id(value, kind)
            if isinstance(profile_id, str):
                profile_ids.add(profile_id)
                profile_occurrences[(_namespace(path, root), profile_id)] += 1

    for (namespace, skill_id), count in sorted(manifest_occurrences.items()):
        if count > 1:
            issues.append(
                _issue(
                    "duplicate-id",
                    namespace,
                    f"duplicate manifest skill_id: {skill_id}",
                )
            )
    for (namespace, profile_id), count in sorted(profile_occurrences.items()):
        if count > 1:
            issues.append(_issue("duplicate-id", namespace, f"duplicate profile_id: {profile_id}"))

    for (skill_id, version), digests in sorted(manifest_bytes.items()):
        if len(digests) <= 1:
            continue
        paths = sorted(path for digest_paths in digests.values() for path in digest_paths)
        issues.append(
            _issue(
                "manifest-content-conflict",
                paths[0],
                f"manifest {skill_id}@{version} has divergent raw bytes across: "
                + ", ".join(paths),
            )
        )

    for path, value, kind in documents:
        if not isinstance(value, dict):
            continue
        relative = relative_posix(path, root)
        if kind == "registry" and isinstance(value.get("entries"), list):
            for index, entry in enumerate(value["entries"]):
                if not isinstance(entry, dict):
                    continue
                uri, expected_digest_value = _reference(entry)
                if not isinstance(uri, str):
                    continue
                if "://" in uri:
                    issues.append(
                        _issue(
                            "unsupported-reference",
                            relative,
                            "remote manifest references cannot be verified by the local validator",
                            pointer=f"/entries/{index}/manifest",
                        )
                    )
                    continue
                pointer = f"/entries/{index}/manifest"
                if not _is_portable_repository_path(uri):
                    issues.append(
                        _issue(
                            "unsafe-reference",
                            relative,
                            f"local manifest reference is not a portable relative path: {uri}",
                            pointer=pointer,
                        )
                    )
                    continue
                unresolved_target = path.parent / uri
                target = unresolved_target.resolve()
                try:
                    target.relative_to(root.resolve())
                except ValueError:
                    issues.append(
                        _issue(
                            "path-escape",
                            relative,
                            "manifest reference escapes repository root",
                            pointer=pointer,
                        )
                    )
                    continue
                if _has_symlink_component(unresolved_target, root):
                    issues.append(
                        _issue(
                            "path-escape",
                            relative,
                            "manifest reference traverses a symbolic link",
                            pointer=pointer,
                        )
                    )
                    continue
                if not target.is_file():
                    issues.append(
                        _issue(
                            "missing-reference",
                            relative,
                            f"manifest reference does not exist: {uri}",
                            pointer=pointer,
                        )
                    )
                expected_digest = _digest_string(expected_digest_value)
                if target.is_file() and expected_digest:
                    actual_digest = sha256_bytes(target.read_bytes())
                    if actual_digest != expected_digest:
                        issues.append(
                            _issue(
                                "digest-mismatch",
                                relative,
                                f"manifest digest mismatch for {uri}",
                                pointer=pointer,
                            )
                        )
                if target.is_file():
                    try:
                        manifest = load_structured(target)
                    except (OSError, ValueError):
                        manifest = None
                    entry_id = _entry_id(entry)
                    manifest_id = (
                        _document_id(manifest, "skill-manifest")
                        if isinstance(manifest, dict)
                        else None
                    )
                    if entry_id is not None and manifest_id != entry_id:
                        issues.append(
                            _issue(
                                "identity-mismatch",
                                relative,
                                f"registry entry {entry_id} references manifest {manifest_id!r}",
                                pointer=f"/entries/{index}/id",
                            )
                        )
        if kind == "router-map":
            namespace = _namespace(path, root)
            if "sourceRegistryDigest" in value:
                registries = registry_documents.get(namespace, [])
                if len(registries) != 1:
                    issues.append(
                        _issue(
                            "registry-binding",
                            relative,
                            "router map requires exactly one registry in its namespace",
                            pointer="/sourceRegistryDigest",
                        )
                    )
                else:
                    registry_path, _ = registries[0]
                    expected_registry_digest = _digest_string(value["sourceRegistryDigest"])
                    actual_registry_digest = sha256_bytes(registry_path.read_bytes())
                    if expected_registry_digest != actual_registry_digest:
                        issues.append(
                            _issue(
                                "source-digest-mismatch",
                                relative,
                                "sourceRegistryDigest does not match the namespace registry bytes",
                                pointer="/sourceRegistryDigest",
                            )
                        )
            routes = value.get("routes", value.get("routers", []))
            if isinstance(routes, list):
                exact_alias_targets: dict[str, tuple[str, int]] = {}
                for index, route in enumerate(routes):
                    if not isinstance(route, dict):
                        continue
                    targets = _route_candidates(route)
                    for alias in route.get("exactAliases", []):
                        if isinstance(alias, dict) and isinstance(alias.get("skillId"), str):
                            targets.add(alias["skillId"])
                            phrase = alias.get("phrase")
                            if isinstance(phrase, str):
                                normalized = " ".join(
                                    unicodedata.normalize("NFC", phrase).split()
                                ).casefold()
                                prior = exact_alias_targets.get(normalized)
                                current_target = alias["skillId"]
                                if prior is not None and prior[0] != current_target:
                                    issues.append(
                                        _issue(
                                            "route-tie",
                                            relative,
                                            "normalized exact alias resolves to multiple skills",
                                            pointer=f"/routers/{index}/exactAliases",
                                        )
                                    )
                                else:
                                    exact_alias_targets[normalized] = (current_target, index)
                    for rule in route.get("keywordRules", []):
                        if isinstance(rule, dict) and isinstance(rule.get("skillId"), str):
                            targets.add(rule["skillId"])
                    for target in sorted(targets - skill_ids_by_namespace[namespace]):
                        issues.append(
                            _issue(
                                "unknown-skill",
                                relative,
                                f"route references unknown skill_id: {target}",
                                pointer=f"/routes/{index}/candidate_skill_ids",
                            )
                        )
                ambiguity = value.get("ambiguityPolicy", value.get("ambiguity_policy"))
                resolved = False
                if isinstance(ambiguity, str):
                    resolved = ambiguity in {"prefer", "first", "priority_then_id", "deterministic"}
                elif isinstance(ambiguity, dict):
                    resolved = bool(
                        ambiguity.get("tieBreaker")
                        or ambiguity.get("tie_breaker")
                        or ambiguity.get("prefer")
                    )
                if not resolved:
                    for left_index, left in enumerate(routes):
                        if not isinstance(left, dict):
                            continue
                        left_priority = left.get("priority", 0)
                        left_matchers = left.get("matchers", left.get("matcher", {}))
                        left_atoms = _matcher_atoms(left_matchers)
                        for right_index in range(left_index + 1, len(routes)):
                            right = routes[right_index]
                            if (
                                not isinstance(right, dict)
                                or right.get("priority", 0) != left_priority
                            ):
                                continue
                            right_atoms = _matcher_atoms(
                                right.get("matchers", right.get("matcher", {}))
                            )
                            if left_atoms and left_atoms & right_atoms:
                                issues.append(
                                    _issue(
                                        "route-tie",
                                        relative,
                                        "equal-priority routes have overlapping matchers "
                                        "without a deterministic ambiguity policy",
                                        pointer=f"/routes/{left_index}",
                                    )
                                )
        if kind in {"eval-case", "eval-suite"}:
            cases = value.get("cases", [value]) if kind == "eval-suite" else [value]
            if isinstance(cases, list):
                for index, case in enumerate(cases):
                    if not isinstance(case, dict):
                        continue
                    refs = as_string_set(case.get("expected_skill_ids"), ("skill_id", "id"))
                    refs |= as_string_set(case.get("must_not_skill_ids"), ("skill_id", "id"))
                    for target in sorted(refs - all_skill_ids):
                        issues.append(
                            _issue(
                                "unknown-skill",
                                relative,
                                f"evaluation case references unknown skill_id: {target}",
                                pointer=f"/cases/{index}",
                                severity="warning",
                            )
                        )
                    case_profile = case.get("profile_id")
                    if (
                        isinstance(case_profile, str)
                        and profile_ids
                        and case_profile not in profile_ids
                    ):
                        issues.append(
                            _issue(
                                "unknown-profile",
                                relative,
                                f"evaluation case references unknown profile_id: {case_profile}",
                                pointer=f"/cases/{index}/profile_id",
                            )
                        )

    # A registry-only Level 0 example is valid, but a manifest omitted from every
    # registry is useful drift evidence rather than a hard failure.
    for skill_id in sorted(manifest_ids - registry_ids):
        issues.append(
            _issue(
                "unregistered-skill",
                "examples",
                f"manifest is not referenced by any discovered registry: {skill_id}",
                severity="warning",
            )
        )
    return issues


def validate_repository(root: str | Path = ".") -> dict[str, Any]:
    """Validate schemas, recognized instances, and cross-document references."""

    requested_root = Path(root).absolute()
    if requested_root.is_symlink():
        issue = _issue(
            "path-escape",
            requested_root.name,
            "repository root must not be a symbolic link",
        )
        return {
            "command": "validate",
            "ok": False,
            "summary": {
                "errors": 1,
                "recognized_files": 0,
                "schemas": 0,
                "validated_files": 0,
                "warnings": 0,
            },
            "issues": [issue],
        }
    root_path = requested_root.resolve()
    schemas, issues = _load_schemas(root_path)
    issues.extend(_filesystem_issues(root_path))
    documents, parse_issues = _structured_documents(root_path)
    issues.extend(parse_issues)
    validated_files = 0
    recognized_files = 0
    for path, value, kind in documents:
        if not kind:
            continue
        recognized_files += 1
        if kind == "eval-suite":
            schema = _matching_schema("eval-case", schemas)
            if schema is None:
                issues.append(
                    _issue(
                        "schema",
                        relative_posix(path, root_path),
                        "no schema found for evaluation suite cases",
                        severity="warning",
                    )
                )
                continue
            cases = value.get("cases") if isinstance(value, dict) else None
            if not isinstance(cases, list):
                issues.append(
                    _issue(
                        "schema",
                        relative_posix(path, root_path),
                        "evaluation suite cases must be an array",
                        pointer="/cases",
                    )
                )
                continue
            for index, case in enumerate(cases):
                case_issues = _validate_instance(
                    case,
                    schema,
                    relative_posix(path, root_path),
                )
                for issue in case_issues:
                    suffix = issue.get("pointer", "")
                    issue["pointer"] = f"/cases/{index}{suffix}"
                issues.extend(case_issues)
            validated_files += 1
            continue
        schema = _matching_schema(kind, schemas)
        if schema is None:
            issues.append(
                _issue(
                    "schema",
                    relative_posix(path, root_path),
                    f"no schema found for recognized document kind: {kind}",
                    severity="warning",
                )
            )
            continue
        issues.extend(_validate_instance(value, schema, relative_posix(path, root_path)))
        validated_files += 1
    issues.extend(_cross_reference_issues(root_path, documents))
    issues.sort(
        key=lambda item: (
            item.get("severity", ""),
            item.get("file", ""),
            item.get("pointer", ""),
            item.get("category", ""),
            item.get("message", ""),
        )
    )
    errors = sum(issue["severity"] == "error" for issue in issues)
    warnings = sum(issue["severity"] == "warning" for issue in issues)
    return {
        "command": "validate",
        "ok": errors == 0,
        "summary": {
            "errors": errors,
            "recognized_files": recognized_files,
            "schemas": len(schemas),
            "validated_files": validated_files,
            "warnings": warnings,
        },
        "issues": issues,
    }
