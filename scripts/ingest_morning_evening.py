#!/usr/bin/env python3
"""Fetch, parse, and write the public-domain Morning and Evening corpus."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from me_corpus import (
    SOURCE_TEXT_URL,
    fetch_source_text,
    ingest,
    report_lines,
)


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Ingest C. H. Spurgeon, Morning and Evening, from a public-domain "
            "CCEL plaintext dump and write 732 dated markdown readings plus indexes."
        )
    )
    parser.add_argument(
        "--source-url",
        default=SOURCE_TEXT_URL,
        help="Plaintext URL to fetch (CCEL cache by default).",
    )
    parser.add_argument(
        "--source-file",
        help="Read this local plaintext file instead of fetching.",
    )
    parser.add_argument(
        "--data-dir",
        default=str(repo_root() / "data"),
        help="Directory for JSON indexes and the readings/ folder.",
    )
    args = parser.parse_args(argv)

    if args.source_file:
        text = Path(args.source_file).read_text(encoding="utf-8")
        origin = args.source_file
    else:
        text = fetch_source_text(args.source_url)
        origin = args.source_url

    readings, report = ingest(text, Path(args.data_dir))
    print(f"source: {origin}")
    print(f"parsed: {len(readings)}")
    print("\n".join(report_lines(report)))
    notes = [note for item in readings for note in item.parse_notes]
    if notes:
        print("ingest parse notes:")
        for note in notes:
            print(f"  {note}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
