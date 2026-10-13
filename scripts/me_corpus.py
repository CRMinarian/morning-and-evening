"""Shared helpers for the Spurgeon Morning and Evening corpus.

The class site reads JSON indexes, not the markdown files. Readings keep the
seed heading layout and add YAML frontmatter the site does not consume.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import datetime as dt
import json
import re
from pathlib import Path
from typing import Iterable
from urllib.request import Request, urlopen


SOURCE_WORK_URL = "https://www.ccel.org/ccel/spurgeon/morneve"
SOURCE_TEXT_URL = "https://www.ccel.org/ccel/s/spurgeon/morneve/cache/morneve.txt"
SOURCE_READING_URL = (
    "https://www.ccel.org/ccel/spurgeon/morneve.d{month:02d}{day:02d}{ampm}.html"
)
EDITION = (
    "Morning and Evening: Daily Readings, C. H. Spurgeon. "
    "CCEL electronic edition of the public-domain combined text "
    "(Morning by Morning, 1865; Evening by Evening, 1868)."
)
PUBLIC_DOMAIN = (
    "Charles Haddon Spurgeon (1834-1892). This text is in the public domain "
    "in the United States."
)
CLASS_WEEK_YEAR = 2026
CLASS_WEEK_START = "2026-10-05"
CLASS_WEEK_END = "2026-10-11"
SOURCE_CACHE_RELATIVE = "source/ccel-morneve.txt"
# Generated labels use a pipe. Em dashes are forbidden in text we write.
TITLE_SEPARATOR = " | "
EM_DASH_CHARS = ("\u2014", "\u2013")
BODY_MATCH_SAMPLE = (
    ("01-01", "morning"),
    ("01-01", "evening"),
    ("02-29", "morning"),
    ("02-29", "evening"),
    ("07-12", "morning"),
    ("10-05", "morning"),
    ("10-05", "evening"),
    ("10-06", "morning"),
    ("10-06", "evening"),
    ("10-07", "morning"),
    ("10-07", "evening"),
    ("10-08", "morning"),
    ("10-08", "evening"),
    ("10-09", "morning"),
    ("10-09", "evening"),
    ("10-10", "morning"),
    ("10-10", "evening"),
    ("10-11", "morning"),
    ("10-11", "evening"),
    ("12-31", "morning"),
    ("12-31", "evening"),
)

MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}
MONTH_NAMES = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]
# Perpetual calendar: February always includes the 29th.
MONTH_DAYS = (31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
SLOTS = ("morning", "evening")

CANONICAL_BOOKS: tuple[str, ...] = (
    "Genesis",
    "Exodus",
    "Leviticus",
    "Numbers",
    "Deuteronomy",
    "Joshua",
    "Judges",
    "Ruth",
    "1 Samuel",
    "2 Samuel",
    "1 Kings",
    "2 Kings",
    "1 Chronicles",
    "2 Chronicles",
    "Ezra",
    "Nehemiah",
    "Esther",
    "Job",
    "Psalm",
    "Proverbs",
    "Ecclesiastes",
    "Song of Solomon",
    "Isaiah",
    "Jeremiah",
    "Lamentations",
    "Ezekiel",
    "Daniel",
    "Hosea",
    "Joel",
    "Amos",
    "Obadiah",
    "Jonah",
    "Micah",
    "Nahum",
    "Habakkuk",
    "Zephaniah",
    "Haggai",
    "Zechariah",
    "Malachi",
    "Matthew",
    "Mark",
    "Luke",
    "John",
    "Acts",
    "Romans",
    "1 Corinthians",
    "2 Corinthians",
    "Galatians",
    "Ephesians",
    "Philippians",
    "Colossians",
    "1 Thessalonians",
    "2 Thessalonians",
    "1 Timothy",
    "2 Timothy",
    "Titus",
    "Philemon",
    "Hebrews",
    "James",
    "1 Peter",
    "2 Peter",
    "1 John",
    "2 John",
    "3 John",
    "Jude",
    "Revelation",
)
BOOK_ALIASES = {
    "Psalms": "Psalm",
    "Psalm": "Psalm",
    "Song of Songs": "Song of Solomon",
    "Canticles": "Song of Solomon",
}
SINGLE_CHAPTER_BOOKS = frozenset(
    {"Obadiah", "Philemon", "2 John", "3 John", "Jude"}
)

HEADING_RE = re.compile(
    r"^(Morning|Evening), ([A-Za-z]+) (\d+)\s*$", re.MULTILINE
)
NAV_RE = re.compile(r"^\[\d+\]Go To ", re.IGNORECASE)
SEPARATOR_RE = re.compile(r"^_+$")
VERSE_TAIL_RE = re.compile(
    r"^(?P<chapter>\d+):(?P<verses>\d+(?:\s*[-]\s*\d+)?(?:\s*,\s*\d+(?:\s*[-]\s*\d+)?)*)$"
)
SINGLE_VERSE_RE = re.compile(r"^(?P<verse>\d+)$")
READING_NAME_RE = re.compile(
    r"^(?P<mm>\d{2})-(?P<dd>\d{2})-(?P<slot>morning|evening)\.md$"
)
DATED_NAME_RE = re.compile(
    r"^(?P<year>\d{4})-(?P<mm>\d{2})-(?P<dd>\d{2})-(?P<slot>morning|evening)\.md$"
)
ISO_DATE_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")


@dataclass(frozen=True)
class ParsedRef:
    raw: str
    book: str = ""
    chapter: int = 0
    verses: tuple[int, ...] = ()
    normalized: str = ""
    ok: bool = False
    reason: str = ""


@dataclass
class Reading:
    date: str
    slot: str
    title: str
    scripture_ref: str
    scripture_ref_as_printed: str
    scripture_text: str
    source: str
    edition: str
    public_domain: str
    body: str
    month: int = 0
    day: int = 0
    source_plain_body: str = ""
    source_plain_scripture: str = ""
    parse_notes: list[str] = field(default_factory=list)

    @property
    def generated_title(self) -> str:
        return generated_title(self.slot, self.month, self.day)

    @property
    def filename(self) -> str:
        return f"{self.date}-{self.slot}.md"

    @property
    def path(self) -> str:
        return f"data/readings/{self.filename}"

    @property
    def class_week_iso(self) -> str:
        return f"{CLASS_WEEK_YEAR}-{self.date}"

    @property
    def episode(self) -> str:
        return f"content/spurgeon/en/{self.slot}/{self.class_week_iso}.md"

    @property
    def reading_id(self) -> str:
        return f"spurgeon-{self.class_week_iso}-{self.slot}-en"


@dataclass
class ValidationReport:
    morning_count: int
    evening_count: int
    total_files: int
    expected_total: int
    missing: list[str]
    extra_files: list[str]
    empty_bodies: list[str]
    unparsed_refs: list[dict[str, str]]
    titles_with_em_dash: list[str]
    source_mismatches: list[str]
    sample_compared: int
    ref_disagreements: list[dict[str, str]]
    invalid_dates: list[str]
    parse_notes: list[str]

    @property
    def ok(self) -> bool:
        return (
            self.total_files == self.expected_total
            and self.morning_count == 366
            and self.evening_count == 366
            and not self.missing
            and not self.extra_files
            and not self.empty_bodies
            and not self.titles_with_em_dash
            and not self.source_mismatches
            and not self.ref_disagreements
            and not self.invalid_dates
        )


def generated_title(slot: str, month: int, day: int) -> str:
    """Slot and calendar day label. Pipe only; never an em dash."""
    return f"{slot.capitalize()}{TITLE_SEPARATOR}{MONTH_NAMES[month - 1]} {day}"


def contains_em_dash(text: str) -> bool:
    return any(char in (text or "") for char in EM_DASH_CHARS)


def normalize_whitespace(text: str) -> str:
    return " ".join((text or "").split())


def refs_agree(printed: str, normalized: str) -> bool:
    """True when normalized book/chapter/verses match the printed ref."""
    printed_parsed = parse_scripture_ref(printed)
    normalized_parsed = parse_scripture_ref(normalized)
    if not printed_parsed.ok or not normalized_parsed.ok:
        return False
    return (
        printed_parsed.book == normalized_parsed.book
        and printed_parsed.chapter == normalized_parsed.chapter
        and printed_parsed.verses == normalized_parsed.verses
    )


def is_valid_calendar_date(year: int, month: int, day: int) -> bool:
    try:
        dt.date(year, month, day)
    except ValueError:
        return False
    return True


def invalid_calendar_dates_in(text: str) -> list[str]:
    found: list[str] = []
    for match in ISO_DATE_RE.finditer(text or ""):
        year, month, day = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
        iso = f"{year:04d}-{month:02d}-{day:02d}"
        if not is_valid_calendar_date(year, month, day) and iso not in found:
            found.append(iso)
    return found


def expected_mmdd_slots() -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for month, last_day in enumerate(MONTH_DAYS, start=1):
        for day in range(1, last_day + 1):
            mmdd = f"{month:02d}-{day:02d}"
            for slot in SLOTS:
                pairs.append((mmdd, slot))
    return pairs


def _books_by_length() -> list[str]:
    names = list(CANONICAL_BOOKS) + list(BOOK_ALIASES)
    return sorted(set(names), key=len, reverse=True)


_BOOKS_BY_LENGTH = _books_by_length()


def _split_verses(spec: str) -> tuple[int, ...] | None:
    verses: list[int] = []
    for part in spec.split(","):
        piece = part.strip()
        if not piece:
            return None
        if "-" in piece:
            ends = [bit.strip() for bit in piece.split("-", 1)]
            if len(ends) != 2 or not all(bit.isdigit() for bit in ends):
                return None
            start, stop = int(ends[0]), int(ends[1])
            if start < 1 or stop < start:
                return None
            verses.extend(range(start, stop + 1))
            continue
        if not piece.isdigit():
            return None
        number = int(piece)
        if number < 1:
            return None
        verses.append(number)
    return tuple(verses) if verses else None


def parse_scripture_ref(raw: str) -> ParsedRef:
    """Parse a lead reference. Unknown books or shapes are left unparsed."""
    text = " ".join((raw or "").split()).strip()
    if not text:
        return ParsedRef(raw=raw, reason="empty")

    book_raw = ""
    remainder = ""
    for name in _BOOKS_BY_LENGTH:
        if text == name:
            book_raw = name
            remainder = ""
            break
        prefix = name + " "
        if text.startswith(prefix):
            book_raw = name
            remainder = text[len(prefix) :].strip()
            break
    if not book_raw:
        return ParsedRef(raw=raw, reason="unknown book")

    book = BOOK_ALIASES.get(book_raw, book_raw)
    if book not in CANONICAL_BOOKS:
        return ParsedRef(raw=raw, reason="unknown book")

    verse_match = VERSE_TAIL_RE.match(remainder)
    if verse_match:
        chapter = int(verse_match.group("chapter"))
        verses = _split_verses(verse_match.group("verses"))
        if not verses:
            return ParsedRef(raw=raw, book=book, reason="invalid verses")
        normalized = _format_ref(book, chapter, verse_match.group("verses"))
        return ParsedRef(
            raw=raw,
            book=book,
            chapter=chapter,
            verses=verses,
            normalized=normalized,
            ok=True,
        )

    single = SINGLE_VERSE_RE.match(remainder)
    if single and book in SINGLE_CHAPTER_BOOKS:
        verse = int(single.group("verse"))
        if verse < 1:
            return ParsedRef(raw=raw, book=book, reason="invalid verses")
        return ParsedRef(
            raw=raw,
            book=book,
            chapter=1,
            verses=(verse,),
            normalized=f"{book} 1:{verse}",
            ok=True,
        )

    return ParsedRef(raw=raw, book=book, reason="not book chapter:verse(s)")


def _format_ref(book: str, chapter: int, verse_spec: str) -> str:
    compact = re.sub(r"\s+", " ", verse_spec).strip()
    return f"{book} {chapter}:{compact}"


def fetch_source_text(url: str = SOURCE_TEXT_URL, timeout: int = 60) -> str:
    request = Request(
        url,
        headers={"User-Agent": "SpurgeonUnboundIngest/1.0 (public-domain corpus)"},
    )
    with urlopen(request, timeout=timeout) as response:
        data = response.read()
    return data.decode("utf-8", errors="replace")


def parse_ccel_text(text: str) -> list[Reading]:
    matches = list(HEADING_RE.finditer(text))
    readings: list[Reading] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        chunk = text[match.end() : end]
        readings.append(
            _parse_chunk(
                slot=match.group(1).lower(),
                month_name=match.group(2),
                day=int(match.group(3)),
                chunk=chunk,
            )
        )
    return readings


def _parse_chunk(slot: str, month_name: str, day: int, chunk: str) -> Reading:
    month = MONTHS[month_name.lower()]
    mmdd = f"{month:02d}-{day:02d}"
    ampm = "am" if slot == "morning" else "pm"
    source = SOURCE_READING_URL.format(month=month, day=day, ampm=ampm)
    notes: list[str] = []

    body_lines: list[str] = []
    quote_lines: list[str] = []
    ref_line = ""
    stage = "pre"

    for raw_line in chunk.splitlines():
        stripped = raw_line.strip()
        if SEPARATOR_RE.match(stripped.replace(" ", "")):
            break
        if stripped.startswith("file://"):
            break
        if NAV_RE.match(stripped):
            continue
        if stage == "pre":
            if not stripped:
                continue
            if stripped.startswith('"'):
                quote_lines.append(stripped)
                stage = "quote" if not _quote_closed(quote_lines) else "ref"
            continue
        if stage == "quote":
            if not stripped:
                continue
            quote_lines.append(stripped)
            if _quote_closed(quote_lines):
                stage = "ref"
            continue
        if stage == "ref":
            if not stripped:
                continue
            ref_line = stripped
            stage = "body"
            continue
        body_lines.append(raw_line)

    scripture_text = _clean_quote(quote_lines)
    printed_ref = ref_line
    parsed = parse_scripture_ref(printed_ref)
    if parsed.ok:
        scripture_ref = parsed.normalized
        if parsed.normalized != parsed.raw:
            notes.append(
                f"normalized scripture_ref {parsed.raw!r} -> {parsed.normalized!r}"
            )
    else:
        scripture_ref = printed_ref
        notes.append(f"unparsed scripture_ref {printed_ref!r}: {parsed.reason}")

    body = _unwrap_body(body_lines)
    plain_body = normalize_whitespace(
        "\n".join(re.sub(r"^ {1,3}", "", line.rstrip()) for line in body_lines)
    )
    title = generated_title(slot, month, day)
    return Reading(
        date=mmdd,
        slot=slot,
        title=title,
        scripture_ref=scripture_ref,
        scripture_ref_as_printed=printed_ref,
        scripture_text=scripture_text,
        source=source,
        edition=EDITION,
        public_domain=PUBLIC_DOMAIN,
        body=body,
        month=month,
        day=day,
        source_plain_body=plain_body,
        source_plain_scripture=normalize_whitespace(scripture_text),
        parse_notes=notes,
    )


def _quote_closed(lines: Iterable[str]) -> bool:
    text = " ".join(lines).strip()
    return len(text) >= 2 and text.endswith('"')


def _clean_quote(lines: Iterable[str]) -> str:
    text = " ".join(part.strip() for part in lines).strip()
    if text.startswith('"') and text.endswith('"') and len(text) >= 2:
        text = text[1:-1]
    return " ".join(text.split())


def _unwrap_body(raw_lines: list[str]) -> str:
    blocks: list[list[str]] = []
    current: list[str] = []
    for raw in raw_lines:
        if not raw.strip():
            if current:
                blocks.append(current)
                current = []
            continue
        current.append(re.sub(r"^ {1,3}", "", raw.rstrip()))
    if current:
        blocks.append(current)

    paragraphs: list[str] = []
    for block in blocks:
        if all(len(line) <= 50 for line in block) and len(block) > 1:
            paragraphs.append("\n".join(block))
        else:
            paragraphs.append(" ".join(line.strip() for line in block))
    return "\n\n".join(part for part in paragraphs if part).strip()


def yaml_quote(value: str) -> str:
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
    )
    return f'"{escaped}"'


def render_markdown(reading: Reading) -> str:
    heading = f"# {reading.generated_title}"
    verse = f'"{reading.scripture_text}"' if reading.scripture_text else ""
    parts = [
        "---",
        f"date: {yaml_quote(reading.date)}",
        f"slot: {reading.slot}",
        f"title: {yaml_quote(reading.title)}",
        f"scripture_ref: {yaml_quote(reading.scripture_ref)}",
        f"scripture_ref_as_printed: {yaml_quote(reading.scripture_ref_as_printed)}",
        f"scripture_text: {yaml_quote(reading.scripture_text)}",
        f"source: {yaml_quote(reading.source)}",
        f"edition: {yaml_quote(reading.edition)}",
        f"public_domain: {yaml_quote(reading.public_domain)}",
        "---",
        "",
        heading,
        "",
        f"**{reading.scripture_ref}**",
        "",
    ]
    if verse:
        parts.extend([verse, ""])
    parts.extend([reading.body, ""])
    return "\n".join(parts)


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, text
    raw = text[4:end]
    body = text[end + 5 :]
    fields: dict[str, str] = {}
    for line in raw.splitlines():
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = _unquote_yaml(value.strip())
    return fields, body


def _unquote_yaml(value: str) -> str:
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        inner = value[1:-1]
        return (
            inner.replace("\\n", "\n")
            .replace('\\"', '"')
            .replace("\\\\", "\\")
        )
    return value


def markdown_devotion(body: str) -> str:
    """Body after the seed heading and lead verse, used as the devotion."""
    lines = body.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and lines[0].startswith("**") and lines[0].endswith("**"):
        lines = lines[1:]
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and (lines[0].startswith("“") or lines[0].startswith('"')):
        lines = lines[1:]
        while lines and not lines[0].strip():
            lines.pop(0)
    return "\n".join(lines).strip()


def write_readings(readings: list[Reading], readings_dir: Path) -> None:
    readings_dir.mkdir(parents=True, exist_ok=True)
    for path in readings_dir.glob("*.md"):
        if path.name == "PROVENANCE.md":
            continue
        path.unlink()
    for reading in readings:
        (readings_dir / reading.filename).write_text(
            render_markdown(reading), encoding="utf-8"
        )


def write_indexes(readings: list[Reading], data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    by_key = {(item.date, item.slot): item for item in readings}
    year_index = {
        "source": SOURCE_WORK_URL,
        "edition": EDITION,
        "count": len(readings),
        "readings": [
            {
                "path": item.path,
                "date": item.date,
                "slot": item.slot,
                "scripture_ref": item.scripture_ref,
                "scripture_ref_as_printed": item.scripture_ref_as_printed,
            }
            for item in sorted(readings, key=lambda item: (item.date, item.slot))
        ],
    }
    _write_json(data_dir / "year-index.json", year_index)

    week_dates = _date_range(CLASS_WEEK_START, CLASS_WEEK_END)
    today_morning = by_key.get(("10-05", "morning"))
    today_evening = by_key.get(("10-05", "evening"))
    if today_morning and today_evening:
        _write_json(
            data_dir / "today.json",
            {
                "date": CLASS_WEEK_START,
                "morning": _index_piece(today_morning),
                "evening": _index_piece(today_evening),
            },
        )
    week_days = []
    week_full = []
    for iso in week_dates:
        mmdd = iso[5:]
        morning = by_key.get((mmdd, "morning"))
        night = by_key.get((mmdd, "evening"))
        if morning is None or night is None:
            continue
        weekday = dt.date.fromisoformat(iso).strftime("%A")
        week_days.append(
            {
                "day": weekday,
                "date": iso,
                "morning_title": morning.scripture_text,
                "morning_scripture": morning.scripture_ref,
                "evening_title": night.scripture_text,
                "evening_scripture": night.scripture_ref,
            }
        )
        week_full.append(
            {
                "date": iso,
                "weekday": weekday,
                "mmdd": mmdd,
                "morning": _full_piece(morning),
                "evening": _full_piece(night),
            }
        )
    if week_days:
        _write_json(
            data_dir / "this-week.json",
            {"week_start": CLASS_WEEK_START, "days": week_days},
        )
        _write_json(
            data_dir / "this-week-full.json",
            {"week_start": CLASS_WEEK_START, "days": week_full},
        )


def _index_piece(reading: Reading) -> dict[str, str]:
    # Site cards still show the lead verse, not the generated slot/date title.
    return {
        "title": reading.scripture_text,
        "scripture": reading.scripture_ref,
        "body": _site_body(reading),
        "episode": reading.episode,
        "id": reading.reading_id,
    }


def _full_piece(reading: Reading) -> dict[str, str]:
    piece = _index_piece(reading)
    piece["source_reading"] = reading.path
    return piece


def _site_body(reading: Reading) -> str:
    lead = f'"{reading.scripture_text}"' if reading.scripture_text else ""
    if lead and reading.body:
        return f"{lead}\n\n{reading.body}"
    return reading.body or lead


def _date_range(start_iso: str, end_iso: str) -> list[str]:
    start = dt.date.fromisoformat(start_iso)
    end = dt.date.fromisoformat(end_iso)
    days = []
    cursor = start
    while cursor <= end:
        days.append(cursor.isoformat())
        cursor += dt.timedelta(days=1)
    return days


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_year_index(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def lookup_reading(
    date: str,
    slot: str,
    index: dict | None = None,
    index_path: Path | None = None,
) -> dict | None:
    """Lookup one reading by MM-DD or YYYY-MM-DD and morning|evening."""
    mmdd = date[5:] if re.match(r"^\d{4}-\d{2}-\d{2}$", date) else date
    slot = slot.lower()
    if slot not in SLOTS:
        return None
    if index is None:
        if index_path is None:
            raise ValueError("index or index_path is required")
        index = load_year_index(index_path)
    for item in index.get("readings", []):
        if item.get("date") == mmdd and item.get("slot") == slot:
            return item
    return None


def write_source_cache(source_text: str, data_dir: Path) -> Path:
    path = data_dir / SOURCE_CACHE_RELATIVE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source_text, encoding="utf-8")
    return path


def load_source_cache(data_dir: Path) -> str | None:
    path = data_dir / SOURCE_CACHE_RELATIVE
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def validate_readings_dir(
    readings_dir: Path,
    source_text: str | None = None,
) -> ValidationReport:
    expected = expected_mmdd_slots()
    expected_names = {f"{mmdd}-{slot}.md": (mmdd, slot) for mmdd, slot in expected}
    files = sorted(
        path
        for path in readings_dir.glob("*.md")
        if path.name != "PROVENANCE.md"
    )
    extra: list[str] = []
    seen: set[tuple[str, str]] = set()
    empty_bodies: list[str] = []
    unparsed: list[dict[str, str]] = []
    titles_with_em_dash: list[str] = []
    ref_disagreements: list[dict[str, str]] = []
    invalid_dates: list[str] = []
    notes: list[str] = []
    morning = 0
    evening = 0
    if source_text is None:
        source_text = load_source_cache(readings_dir.parent)
    source_by_key = (
        {(item.date, item.slot): item for item in parse_ccel_text(source_text)}
        if source_text
        else {}
    )

    for path in files:
        dated = DATED_NAME_RE.match(path.name)
        if dated:
            year = int(dated.group("year"))
            month = int(dated.group("mm"))
            day = int(dated.group("dd"))
            extra.append(path.name)
            if not is_valid_calendar_date(year, month, day):
                invalid_dates.append(
                    f"{path.name}: invalid calendar date {year:04d}-{month:02d}-{day:02d}"
                )
            continue
        match = READING_NAME_RE.match(path.name)
        if not match:
            extra.append(path.name)
            continue
        mmdd = f"{match.group('mm')}-{match.group('dd')}"
        slot = match.group("slot")
        if (mmdd, slot) not in expected_names.values():
            extra.append(path.name)
            continue
        seen.add((mmdd, slot))
        if slot == "morning":
            morning += 1
        else:
            evening += 1
        text = path.read_text(encoding="utf-8")
        fields, body = parse_frontmatter(text)
        devotion = markdown_devotion(body)
        if not devotion:
            empty_bodies.append(path.name)
        heading = _markdown_heading(body)
        generated = fields.get("title", heading)
        if contains_em_dash(generated) or contains_em_dash(heading):
            titles_with_em_dash.append(path.name)
        ref = fields.get("scripture_ref", "")
        printed = fields.get("scripture_ref_as_printed", "")
        parsed = parse_scripture_ref(ref)
        if not parsed.ok:
            unparsed.append(
                {
                    "path": f"data/readings/{path.name}",
                    "date": fields.get("date", mmdd),
                    "slot": fields.get("slot", slot),
                    "scripture_ref": ref,
                    "reason": parsed.reason,
                }
            )
        if printed and ref and not refs_agree(printed, ref):
            printed_parsed = parse_scripture_ref(printed)
            ref_disagreements.append(
                {
                    "path": f"data/readings/{path.name}",
                    "date": fields.get("date", mmdd),
                    "slot": fields.get("slot", slot),
                    "scripture_ref_as_printed": printed,
                    "scripture_ref": ref,
                    "reason": (
                        "normalized book/chapter/verse does not match printed ref"
                    ),
                    "printed_parse": (
                        f"{printed_parsed.book} {printed_parsed.chapter}:"
                        f"{','.join(str(v) for v in printed_parsed.verses)}"
                        if printed_parsed.ok
                        else printed_parsed.reason
                    ),
                    "normalized_parse": (
                        f"{parsed.book} {parsed.chapter}:"
                        f"{','.join(str(v) for v in parsed.verses)}"
                        if parsed.ok
                        else parsed.reason
                    ),
                }
            )
        if fields.get("date") and fields["date"] != mmdd:
            notes.append(f"{path.name}: frontmatter date {fields['date']} != {mmdd}")
        if fields.get("slot") and fields["slot"] != slot:
            notes.append(f"{path.name}: frontmatter slot {fields['slot']} != {slot}")
        if not printed:
            notes.append(f"{path.name}: missing scripture_ref_as_printed")
        if ISO_DATE_RE.search(fields.get("date", "") or ""):
            invalid_dates.append(
                f"{path.name}: frontmatter date {fields['date']!r} is not MM-DD"
            )
        for iso in invalid_calendar_dates_in(path.name):
            invalid_dates.append(f"{path.name}: filename has invalid calendar date {iso}")
        for key, value in fields.items():
            for iso in invalid_calendar_dates_in(value):
                invalid_dates.append(
                    f"{path.name}: frontmatter {key} has invalid calendar date {iso}"
                )

    missing = [
        f"{mmdd}-{slot}.md"
        for mmdd, slot in expected
        if (mmdd, slot) not in seen
    ]
    sample_compared, source_mismatches = _compare_sample_to_source(
        readings_dir, source_by_key
    )
    if source_text is None:
        notes.append("source cache missing; skipped body/source sample match")
    return ValidationReport(
        morning_count=morning,
        evening_count=evening,
        total_files=len(files),
        expected_total=len(expected),
        missing=missing,
        extra_files=extra,
        empty_bodies=empty_bodies,
        unparsed_refs=unparsed,
        titles_with_em_dash=titles_with_em_dash,
        source_mismatches=source_mismatches,
        sample_compared=sample_compared,
        ref_disagreements=ref_disagreements,
        invalid_dates=invalid_dates,
        parse_notes=notes,
    )


def _markdown_heading(body: str) -> str:
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def _compare_sample_to_source(
    readings_dir: Path,
    source_by_key: dict[tuple[str, str], Reading],
) -> tuple[int, list[str]]:
    mismatches: list[str] = []
    compared = 0
    if not source_by_key:
        return 0, mismatches
    for date, slot in BODY_MATCH_SAMPLE:
        source_reading = source_by_key.get((date, slot))
        path = readings_dir / f"{date}-{slot}.md"
        if source_reading is None or not path.is_file():
            continue
        compared += 1
        fields, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        devotion = markdown_devotion(body)
        file_body = normalize_whitespace(devotion)
        file_verse = normalize_whitespace(fields.get("scripture_text", ""))
        if file_body != source_reading.source_plain_body:
            mismatches.append(f"{path.name} body")
        if file_verse != source_reading.source_plain_scripture:
            mismatches.append(f"{path.name} scripture_text")
    return compared, mismatches


def report_lines(report: ValidationReport) -> list[str]:
    lines = [
        f"morning: {report.morning_count}",
        f"evening: {report.evening_count}",
        f"total: {report.total_files} (expected {report.expected_total})",
        f"missing: {len(report.missing)}",
        f"extra: {len(report.extra_files)}",
        f"empty_bodies: {len(report.empty_bodies)}",
        f"unparsed_refs: {len(report.unparsed_refs)}",
        f"titles_with_em_dash: {len(report.titles_with_em_dash)}",
        f"source_sample_compared: {report.sample_compared}",
        f"source_mismatches: {len(report.source_mismatches)}",
        f"ref_disagreements: {len(report.ref_disagreements)}",
        f"invalid_dates: {len(report.invalid_dates)}",
        f"ok: {report.ok}",
    ]
    if report.missing:
        lines.append("missing files:")
        lines.extend(f"  {name}" for name in report.missing)
    if report.extra_files:
        lines.append("extra files:")
        lines.extend(f"  {name}" for name in report.extra_files)
    if report.empty_bodies:
        lines.append("empty bodies:")
        lines.extend(f"  {name}" for name in report.empty_bodies)
    if report.unparsed_refs:
        lines.append("unparsed scripture_ref (not guessed):")
        for item in report.unparsed_refs:
            lines.append(
                f"  {item['path']} {item['slot']} {item['scripture_ref']!r} ({item['reason']})"
            )
    if report.titles_with_em_dash:
        lines.append("generated titles with em dash:")
        lines.extend(f"  {name}" for name in report.titles_with_em_dash)
    if report.source_mismatches:
        lines.append("sample bodies/scripture_text that do not match source:")
        lines.extend(f"  {name}" for name in report.source_mismatches)
    if report.ref_disagreements:
        lines.append("printed/normalized scripture_ref disagreements:")
        for item in report.ref_disagreements:
            lines.append(
                f"  {item['path']} printed={item['scripture_ref_as_printed']!r} "
                f"normalized={item['scripture_ref']!r} ({item['reason']})"
            )
    if report.invalid_dates:
        lines.append("invalid calendar dates:")
        lines.extend(f"  {name}" for name in report.invalid_dates)
    if report.parse_notes:
        lines.append("notes:")
        lines.extend(f"  {note}" for note in report.parse_notes)
    return lines


def ingest(
    source_text: str,
    data_dir: Path,
    readings_dir: Path | None = None,
) -> tuple[list[Reading], ValidationReport]:
    readings = parse_ccel_text(source_text)
    target = readings_dir or (data_dir / "readings")
    write_source_cache(source_text, data_dir)
    write_readings(readings, target)
    write_indexes(readings, data_dir)
    return readings, validate_readings_dir(target, source_text=source_text)


def reading_to_dict(reading: Reading) -> dict:
    payload = asdict(reading)
    payload["path"] = reading.path
    payload["filename"] = reading.filename
    return payload
