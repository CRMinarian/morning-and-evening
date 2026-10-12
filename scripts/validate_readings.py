#!/usr/bin/env python3
"""Validate the Morning and Evening corpus on disk."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from me_corpus import report_lines, validate_readings_dir


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check that data/readings holds 732 files, both slots for every "
            "MM-DD including 02-29, non-empty bodies, and parseable scripture refs."
        )
    )
    parser.add_argument(
        "--readings-dir",
        default=str(repo_root() / "data" / "readings"),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Also print a JSON summary on stdout after the text report.",
    )
    args = parser.parse_args(argv)
    report = validate_readings_dir(Path(args.readings_dir))
    print("\n".join(report_lines(report)))
    if args.json:
        print(
            json.dumps(
                {
                    "morning": report.morning_count,
                    "evening": report.evening_count,
                    "total": report.total_files,
                    "expected": report.expected_total,
                    "missing": report.missing,
                    "extra": report.extra_files,
                    "empty_bodies": report.empty_bodies,
                    "unparsed_refs": report.unparsed_refs,
                    "ok": report.ok,
                },
                indent=2,
            )
        )
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
