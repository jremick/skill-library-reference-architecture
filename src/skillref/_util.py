"""Shared deterministic file and serialization helpers."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import yaml

STRUCTURED_SUFFIXES = {".json", ".yaml", ".yml"}
IGNORED_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
}


def canonical_json_bytes(value: Any) -> bytes:
    """Return the canonical, human-readable byte representation used in bundles."""

    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def digest_value(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def relative_posix(path: Path, root: Path) -> str:
    """Return a lexical repository-relative path without following symlinks."""

    try:
        return path.absolute().relative_to(root.absolute()).as_posix()
    except ValueError:
        return path.name


def is_ignored(path: Path, root: Path) -> bool:
    try:
        parts = path.absolute().relative_to(root.absolute()).parts
    except ValueError:
        parts = path.parts
    return any(part in IGNORED_PARTS for part in parts)


def iter_files(root: Path, suffixes: set[str] | None = None) -> Iterable[Path]:
    suffixes = suffixes or set()
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        # Repository inputs are data, not filesystem capabilities. Callers that
        # need to report symlinks do so separately; shared traversal never
        # follows one into an untrusted or machine-local target.
        if path.is_symlink() or not path.is_file() or is_ignored(path, root):
            continue
        if suffixes and path.suffix.lower() not in suffixes:
            continue
        yield path


def load_structured(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            if path.suffix.lower() == ".json":
                return json.load(handle)
            return yaml.safe_load(handle)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"invalid JSON syntax at line {error.lineno}, column {error.colno}"
        ) from error
    except yaml.YAMLError as error:
        mark = getattr(error, "problem_mark", None)
        location = f" at line {mark.line + 1}, column {mark.column + 1}" if mark is not None else ""
        raise ValueError(f"invalid YAML syntax{location}") from error


def source_digest(
    root: Path,
    paths: Iterable[Path],
    *,
    excluded: Iterable[Path] = (),
) -> str:
    """Digest relative paths and bytes so results do not depend on machine paths."""

    excluded_resolved = {path.resolve() for path in excluded}
    digest = hashlib.sha256()
    for path in sorted({item.resolve() for item in paths}, key=lambda item: item.as_posix()):
        if path in excluded_resolved or not path.is_file():
            continue
        relative = relative_posix(path, root).encode("utf-8")
        contents = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(contents).to_bytes(8, "big"))
        digest.update(contents)
    return f"sha256:{digest.hexdigest()}"


def as_string_set(value: Any, id_keys: tuple[str, ...] = ()) -> set[str]:
    """Normalize strings, lists, and identifier objects into a string set."""

    if value is None:
        return set()
    if isinstance(value, str):
        return {value}
    if isinstance(value, dict):
        for key in id_keys:
            if key in value and isinstance(value[key], str):
                return {value[key]}
        return {str(key) for key, enabled in value.items() if enabled is True}
    if not isinstance(value, list):
        return set()
    result: set[str] = set()
    for item in value:
        if isinstance(item, str):
            result.add(item)
        elif isinstance(item, dict):
            for key in id_keys:
                identifier = item.get(key)
                if isinstance(identifier, str):
                    result.add(identifier)
                    break
    return result


def nested_values(value: Any, keys: set[str]) -> list[Any]:
    result: list[Any] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in keys:
                result.append(child)
            result.extend(nested_values(child, keys))
    elif isinstance(value, list):
        for child in value:
            result.extend(nested_values(child, keys))
    return result
