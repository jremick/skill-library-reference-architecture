"""Conservative public-surface checks with value-safe findings."""

from __future__ import annotations

import json
import re
from pathlib import Path
from re import Pattern
from typing import Any

import yaml

from ._util import IGNORED_PARTS

TEXT_SUFFIXES = {
    ".cfg",
    ".css",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".md",
    ".mmd",
    ".py",
    ".rst",
    ".sh",
    ".svg",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}

SECRET_TEXT_SUFFIXES = {".key", ".pem"}
SECRET_TEXT_NAMES = {
    ".env",
    ".git-credentials",
    ".netrc",
    ".npmrc",
    ".pypirc",
    "credentials",
    "credentials.json",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
    "id_rsa",
    "service-account.json",
    "service_account.json",
}
ALWAYS_REJECT_NAMES = {
    ".env",
    ".git-credentials",
    ".netrc",
    "credentials",
    "credentials.json",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
    "id_rsa",
    "service-account.json",
    "service_account.json",
}
NON_PUBLIC_LABELS = {"approved-private", "internal", "restricted"}
CLASSIFICATION_KEYS = {
    "classification",
    "classifications",
    "dataclassification",
    "dataclassifications",
    "visibility",
    "visibilityintent",
}
SCHEMA_VALUE_KEYS = {"$ref", "allOf", "anyOf", "enum", "oneOf", "properties", "type"}
MAX_REPORTED_FINDINGS = 100


def _patterns() -> list[tuple[str, Pattern[str]]]:
    # Split distinctive strings so the scanner does not report its own pattern
    # declarations. Findings deliberately never contain the matched text.
    user_root = "/" + "Users" + "/"
    secret_names = r"(?:api[_-]?key|access[_-]?token|client[_-]?secret|password|passwd)"
    return [
        ("machine-path", re.compile(re.escape(user_root) + r"[^/\s]+/", re.IGNORECASE)),
        ("machine-path", re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+\\", re.IGNORECASE)),
        (
            "private-runtime-path",
            re.compile(r"(?:~|\$HOME)/\.(?:codex|claude)(?:/|\b)", re.IGNORECASE),
        ),
        (
            "private-key",
            re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
        ),
        (
            "credential-assignment",
            re.compile(secret_names + r"\s*[:=]\s*['\"]?[A-Za-z0-9_./+\-=]{12,}", re.IGNORECASE),
        ),
        ("github-token", re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}")),
        ("npm-token", re.compile(r"npm_[A-Za-z0-9]{20,}")),
        ("openai-token", re.compile(r"sk-[A-Za-z0-9_-]{20,}")),
        ("pypi-token", re.compile(r"pypi-[A-Za-z0-9_-]{20,}")),
        ("aws-access-key", re.compile(r"(?:AKIA|ASIA)[A-Z0-9]{16}")),
        (
            "authorization-header",
            re.compile(
                r"authorization\s*[:=]\s*['\"]?bearer\s+[A-Za-z0-9._~+/=-]{12,}",
                re.IGNORECASE,
            ),
        ),
        (
            "raw-task-identifier",
            re.compile(
                r"(?:task|thread|conversation)[_-]?id\s*[:=]\s*['\"]?[0-9a-f]{8}-[0-9a-f-]{27,}",
                re.IGNORECASE,
            ),
        ),
    ]


def _relative_path(path: Path, root: Path) -> str:
    """Return the lexical path without resolving a possibly hostile symlink."""

    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def _is_text_candidate(path: Path) -> bool:
    name = path.name.lower()
    return (
        path.suffix.lower() in TEXT_SUFFIXES | SECRET_TEXT_SUFFIXES
        or path.suffix == ""
        or name in SECRET_TEXT_NAMES
        or name.startswith(".env.")
    )


def _is_ignored_entry(path: Path, root: Path) -> bool:
    """Ignore repository internals lexically, without resolving symlink targets."""

    try:
        parts = path.relative_to(root).parts
    except ValueError:
        return False
    return any(part in IGNORED_PARTS for part in parts)


def _is_secret_filename(path: Path) -> bool:
    name = path.name.lower()
    if name in ALWAYS_REJECT_NAMES or path.suffix.lower() == ".key":
        return True
    if name.startswith(".env."):
        return not name.endswith((".example", ".sample", ".template"))
    return False


def _normalise_label(value: str) -> str:
    return re.sub(r"[_\s]+", "-", value.strip().lower())


def _contains_non_public_label(value: Any) -> bool:
    if isinstance(value, str):
        return _normalise_label(value) in NON_PUBLIC_LABELS
    if isinstance(value, list):
        return any(_contains_non_public_label(item) for item in value)
    if isinstance(value, dict):
        # A JSON Schema describes allowed values rather than labelling public-bound
        # data. The schema itself is safe to publish and is checked elsewhere.
        if SCHEMA_VALUE_KEYS.intersection(value):
            return False
        return any(_contains_non_public_label(item) for item in value.values())
    return False


def _structured_has_non_public_label(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            normalised_key = re.sub(r"[^a-z]", "", str(key).lower())
            if normalised_key in CLASSIFICATION_KEYS and _contains_non_public_label(child):
                return True
            if _structured_has_non_public_label(child):
                return True
    elif isinstance(value, list):
        return any(_structured_has_non_public_label(child) for child in value)
    return False


def check_public_surface(root: str | Path = ".") -> dict[str, Any]:
    """Report privacy findings without returning secret-looking matched values."""

    root_path = Path(root).resolve()
    findings: list[dict[str, Any]] = []
    finding_count = 0
    files_scanned = 0
    patterns = _patterns()

    def add_finding(category: str, path: Path, line: int = 1) -> None:
        nonlocal finding_count
        finding_count += 1
        if len(findings) >= MAX_REPORTED_FINDINGS:
            return
        findings.append(
            {
                "category": category,
                "file": _relative_path(path, root_path),
                "line": line,
            }
        )

    if not root_path.is_dir():
        add_finding("scan-error", root_path, 0)
    else:
        entries = sorted(root_path.rglob("*"), key=lambda item: item.as_posix())
        for path in entries:
            if _is_ignored_entry(path, root_path):
                continue
            if path.is_symlink():
                add_finding("symlink", path)
                continue
            if not path.is_file() or not _is_text_candidate(path):
                continue
            files_scanned += 1
            if _is_secret_filename(path):
                add_finding("secret-bearing-file", path)
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                add_finding("scan-error", path)
                continue
            lines = text.splitlines()
            for line_number, line in enumerate(lines, start=1):
                for category, pattern in patterns:
                    if pattern.search(line):
                        add_finding(category, path, line_number)

            if path.suffix.lower() not in {".json", ".yaml", ".yml"}:
                continue
            try:
                structured = (
                    json.loads(text) if path.suffix.lower() == ".json" else yaml.safe_load(text)
                )
            except (json.JSONDecodeError, yaml.YAMLError):
                add_finding("scan-error", path)
                continue
            if _structured_has_non_public_label(structured):
                add_finding("non-public-data-label", path)
    findings.sort(key=lambda item: (item["file"], item["line"], item["category"]))
    return {
        "command": "check-public-surface",
        "files_scanned": files_scanned,
        "finding_count": finding_count,
        "returned_finding_count": len(findings),
        "truncated": finding_count > len(findings),
        "findings": findings,
        "ok": finding_count == 0,
    }
