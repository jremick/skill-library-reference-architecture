from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if SRC.exists():
    sys.path.insert(0, str(SRC))


def load_data(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        if path.suffix == ".json":
            return json.load(handle)
        return yaml.safe_load(handle)


def load_eval_suite(name: str) -> dict[str, Any]:
    return load_data(ROOT / "evals" / name / "cases.json")
