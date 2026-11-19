#!/usr/bin/env python3
"""Look up one reading by date and slot from data/year-index.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from me_corpus import lookup_reading


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Print the year-index row for a date (MM-DD or YYYY-MM-DD) and slot."
    )
    parser.add_argument("--date", required=True, help="MM-DD or YYYY-MM-DD")
    parser.add_argument("--slot", required=True, choices=("morning", "evening"))
    parser.add_argument(
        "--index",
        default=str(repo_root() / "data" / "year-index.json"),
    )
    args = parser.parse_args(argv)
    row = lookup_reading(args.date, args.slot, index_path=Path(args.index))
    if row is None:
        print(f"no reading for date={args.date} slot={args.slot}", file=sys.stderr)
        return 1
    print(json.dumps(row, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
