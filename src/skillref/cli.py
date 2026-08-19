"""Command-line interface for deterministic skill-library tooling."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .compiler import compile_bundle, write_bundle
from .evaluation import evaluate_suite
from .privacy import check_public_surface
from .validation import validate_repository


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="skillref")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="validate schemas and cross-references")
    validate.add_argument("root", nargs="?", default=".")

    compile_parser = subparsers.add_parser("compile", help="compile a deterministic profile bundle")
    compile_parser.add_argument("root", nargs="?", default=".")
    compile_parser.add_argument("--profile", required=True, dest="profile_id")
    compile_parser.add_argument("--output", required=True)

    evaluate = subparsers.add_parser("evaluate", help="run deterministic routing evaluation")
    evaluate.add_argument("root", nargs="?", default=".")
    evaluate.add_argument("--suite", required=True)

    public = subparsers.add_parser(
        "check-public-surface", help="scan for non-public or secret-looking material"
    )
    public.add_argument("root", nargs="?", default=".")
    return parser


def _print(value: dict[str, Any]) -> None:
    json.dump(value, sys.stdout, indent=2, sort_keys=True, ensure_ascii=False)
    sys.stdout.write("\n")


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "validate":
            report = validate_repository(args.root)
        elif args.command == "compile":
            output_path = Path(args.output)
            bundle = compile_bundle(args.root, args.profile_id, output_path=output_path)
            write_bundle(bundle, output_path)
            report = {
                "bundle_digest": bundle["bundle_digest"],
                "command": "compile",
                "ok": True,
                "output": output_path.as_posix(),
                "profile_id": args.profile_id,
                "source_digest": bundle["source_digest"],
            }
        elif args.command == "evaluate":
            report = evaluate_suite(args.root, args.suite)
        else:
            report = check_public_surface(args.root)
    except (OSError, ValueError, TypeError) as error:
        _print(
            {
                "command": args.command,
                "error": str(error),
                "ok": False,
                "report_format": "skillref.command-report.v0alpha1",
            }
        )
        return 2
    report.setdefault("report_format", "skillref.command-report.v0alpha1")
    _print(report)
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
