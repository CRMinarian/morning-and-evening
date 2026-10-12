"""Tests for the Morning and Evening ingest and validation helpers."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from me_corpus import (  # noqa: E402
    FILE_YEAR,
    contains_em_dash,
    expected_mmdd_slots,
    generated_title,
    ingest,
    lookup_reading,
    parse_ccel_text,
    parse_scripture_ref,
    validate_readings_dir,
)

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "ccel-sample.txt"
READINGS_DIR = ROOT / "data" / "readings"


def test_expected_calendar_includes_feb_29_and_732_slots() -> None:
    pairs = expected_mmdd_slots()
    assert len(pairs) == 732
    assert ("02-29", "morning") in pairs
    assert ("02-29", "evening") in pairs
    assert ("01-01", "morning") in pairs
    assert ("12-31", "evening") in pairs
    assert ("02-30", "morning") not in pairs


@pytest.mark.parametrize(
    ("raw", "normalized", "book", "chapter", "verses"),
    [
        ("Genesis 1:4", "Genesis 1:4", "Genesis", 1, (4,)),
        ("1 Kings 19:8", "1 Kings 19:8", "1 Kings", 19, (8,)),
        ("Song of Solomon 1:4", "Song of Solomon 1:4", "Song of Solomon", 1, (4,)),
        ("Psalms 111:9", "Psalm 111:9", "Psalm", 111, (9,)),
        ("Colossians 2:9, 10", "Colossians 2:9, 10", "Colossians", 2, (9, 10)),
        ("Daniel 3:16, 18", "Daniel 3:16, 18", "Daniel", 3, (16, 18)),
        ("Jude 24", "Jude 1:24", "Jude", 1, (24,)),
        ("Jude 20", "Jude 1:20", "Jude", 1, (20,)),
        ("2 John 2", "2 John 1:2", "2 John", 1, (2,)),
        ("Philemon 2", "Philemon 1:2", "Philemon", 1, (2,)),
        ("3 John 3", "3 John 1:3", "3 John", 1, (3,)),
    ],
)
def test_scripture_ref_parses(
    raw: str,
    normalized: str,
    book: str,
    chapter: int,
    verses: tuple[int, ...],
) -> None:
    parsed = parse_scripture_ref(raw)
    assert parsed.ok is True
    assert parsed.book == book
    assert parsed.chapter == chapter
    assert parsed.verses == verses
    assert parsed.normalized == normalized


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "NotABook 1:1",
        "Genesis",
        "Genesis chapter one",
        "Jude 1:2:3",
    ],
)
def test_scripture_ref_does_not_guess(raw: str) -> None:
    parsed = parse_scripture_ref(raw)
    assert parsed.ok is False
    assert parsed.reason


def test_parse_ccel_sample_normalizes_jude() -> None:
    text = FIXTURE.read_text(encoding="utf-8")
    readings = parse_ccel_text(text)
    assert len(readings) == 4
    keys = {(item.date, item.slot) for item in readings}
    assert keys == {
        ("01-01", "morning"),
        ("01-01", "evening"),
        ("02-29", "morning"),
        ("10-08", "evening"),
    }
    jan = next(item for item in readings if item.date == "01-01" and item.slot == "morning")
    assert jan.scripture_ref == "Joshua 5:12"
    assert jan.scripture_ref_as_printed == "Joshua 5:12"
    assert jan.title == "Morning | January 1"
    assert contains_em_dash(jan.title) is False
    assert jan.scripture_text.startswith("They did eat of the fruit")
    assert "weary wanderings" in jan.body
    assert jan.body
    jude = next(item for item in readings if item.date == "10-08")
    assert jude.scripture_ref_as_printed == "Jude 20"
    assert jude.scripture_ref == "Jude 1:20"
    assert jude.parse_notes


def test_ingest_sample_writes_frontmatter_and_index(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    readings, report = ingest(FIXTURE.read_text(encoding="utf-8"), data_dir)
    assert len(readings) == 4
    sample = data_dir / "readings" / f"{FILE_YEAR}-01-01-morning.md"
    text = sample.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert 'date: "01-01"' in text
    assert "slot: morning" in text
    assert 'title: "Morning | January 1"' in text
    assert "\u2014" not in text.split("---", 2)[1]
    assert "# Morning | January 1" in text
    assert "scripture_ref: \"Joshua 5:12\"" in text
    assert "scripture_ref_as_printed: \"Joshua 5:12\"" in text
    assert "Israel's weary wanderings" in text
    index = json.loads((data_dir / "year-index.json").read_text(encoding="utf-8"))
    assert index["count"] == 4
    row = lookup_reading("01-01", "morning", index=index)
    assert row is not None
    assert row["scripture_ref"] == "Joshua 5:12"
    assert row["path"] == f"data/readings/{FILE_YEAR}-01-01-morning.md"
    assert lookup_reading("2026-10-08", "evening", index=index)["scripture_ref"] == "Jude 1:20"
    assert lookup_reading("2026-10-08", "evening", index=index)["scripture_ref_as_printed"] == "Jude 20"
    # Sample is not a full year, so structural ok is false and missing days are listed.
    assert report.ok is False
    assert report.total_files == 4
    assert any(name.endswith("02-29-morning.md") for name in [p.name for p in (data_dir / "readings").glob("*.md")])


def test_full_corpus_validation() -> None:
    report = validate_readings_dir(READINGS_DIR)
    assert report.morning_count == 366
    assert report.evening_count == 366
    assert report.total_files == 732
    assert report.missing == []
    assert report.extra_files == []
    assert report.empty_bodies == []
    assert report.ok is True
    # Unparsed refs are listed, never invented. The corpus should parse all of them.
    assert report.unparsed_refs == []
    assert report.titles_with_em_dash == []
    assert report.source_mismatches == []
    assert report.sample_compared >= 14


def test_generated_titles_use_pipe_not_em_dash() -> None:
    assert generated_title("morning", 10, 5) == "Morning | October 5"
    assert contains_em_dash(generated_title("evening", 2, 29)) is False


def test_year_index_and_class_week_indexes() -> None:
    year = json.loads((ROOT / "data" / "year-index.json").read_text(encoding="utf-8"))
    assert year["count"] == 732
    assert len(year["readings"]) == 732
    required = {"path", "date", "slot", "scripture_ref", "scripture_ref_as_printed"}
    assert all(required <= set(row) for row in year["readings"])
    feb = lookup_reading("02-29", "morning", index=year)
    assert feb is not None
    assert feb["path"].endswith("02-29-morning.md")

    today = json.loads((ROOT / "data" / "today.json").read_text(encoding="utf-8"))
    assert today["date"] == "2026-10-05"
    assert "title" in today["morning"]
    assert "scripture" in today["morning"]
    assert "body" in today["morning"]
    assert today["morning"]["scripture"]
    assert today["evening"]["body"]

    week = json.loads((ROOT / "data" / "this-week.json").read_text(encoding="utf-8"))
    assert week["week_start"] == "2026-10-05"
    assert len(week["days"]) == 7
    assert week["days"][0]["date"] == "2026-10-05"
    assert week["days"][-1]["date"] == "2026-10-11"

    full = json.loads((ROOT / "data" / "this-week-full.json").read_text(encoding="utf-8"))
    assert full["week_start"] == "2026-10-05"
    assert len(full["days"]) == 7
    monday = full["days"][0]
    assert monday["mmdd"] == "10-05"
    assert monday["morning"]["source_reading"].endswith("10-05-morning.md")
    assert monday["morning"]["scripture"]
    assert monday["evening"]["body"]
