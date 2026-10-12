# Provenance

Corpus: C. H. Spurgeon, *Morning and Evening: Daily Readings*.
Owner of this ingest: data pipeline only. The source wording is kept as received. Modernization is out of scope.

## Source

- Work page: https://www.ccel.org/ccel/spurgeon/morneve
- Table of contents: https://www.ccel.org/ccel/spurgeon/morneve.toc.html
- Plaintext dump used by `scripts/ingest_morning_evening.py`: https://www.ccel.org/ccel/s/spurgeon/morneve/cache/morneve.txt
- Cached copy written by ingest: `data/source/ccel-morneve.txt`
- Per-reading HTML (stored in each file's `source` field): `https://www.ccel.org/ccel/spurgeon/morneve.dMMDDam.html` and `...dMMDDpm.html`

This ingest uses that single CCEL plaintext edition for every reading, including the 14 October class-week files that used to be a Heartlight refresh.

## Edition

Morning and Evening: Daily Readings, Charles Haddon Spurgeon.
CCEL electronic edition of the public-domain combined text.

- *Morning by Morning*, 1865
- *Evening by Evening*, 1868
- Combined reprints circulated in Spurgeon's lifetime and after. The CCEL file is that combined public-domain text, not a later modernized restatement.

Publisher line on the CCEL work record: Grand Rapids, MI: Christian Classics Ethereal Library.

## Retrieval

- Retrieval date: 2026-10-12
- Fetch method: HTTP GET of the CCEL cache plaintext (`scripts/ingest_morning_evening.py`)
- User-Agent: `SpurgeonUnboundIngest/1.0 (public-domain corpus)`

Regenerate:

```
python3 scripts/ingest_morning_evening.py
```

Offline replay:

```
python3 scripts/ingest_morning_evening.py --source-file data/source/ccel-morneve.txt
```

## License / public-domain status

Charles Haddon Spurgeon died in 1892. *Morning and Evening* is in the public domain in the United States. CCEL marks the work "Public Domain" / "Public Domain -- Copy Freely". This repo stores the text for the same public-domain use. No CCEL trademark or site assets were copied.

## Parse notes

- The plaintext is a wrapped dump of the CCEL HTML. Headings are `Morning, Month D` and `Evening, Month D`.
- Navigation crumbs such as `[33]Go To Evening Reading`, month day-index lines, horizontal-rule separators, and the trailing scripture-reference index are dropped.
- Wrapped prose lines are joined into paragraphs. Short-line blocks (quoted verse stanzas) keep their line breaks.
- Encoding is UTF-8. Punctuation is not rewritten. CCEL prints long dashes as `--`; those are stored as `--`.
- Generated labels (frontmatter `title` and the markdown H1) use `Morning | October 5`. They never use an em dash. Year is omitted because the corpus is a perpetual calendar.
- `scripture_text` is the lead quotation exactly as CCEL prints it, without the wrapping quotation marks.
- `scripture_ref_as_printed` is the reference line exactly as CCEL prints it.
- `scripture_ref` is the normalized `book chapter:verse(s)` form used by validation.
- Filenames are year-less `MM-DD-slot.md` (example: `02-29-evening.md`) because this is a perpetual calendar. Frontmatter `date` is `MM-DD`. 2026 is not a leap year, so `2026-02-29` is never used as a file or frontmatter date.
- Class-week JSON (`today.json`, `this-week.json`, `this-week-full.json`) still uses `2026-10-05` through `2026-10-11` in the `date` / `week_start` / `episode` / `id` fields the site already reads. `source_reading` points at the year-less markdown path.

## Scripture reference normalization (not guessing)

`scripture_ref_as_printed` keeps the source line. `scripture_ref` adds chapter `1` for single-chapter books and maps `Psalms` to `Psalm`:

- `Jude 1` -> `Jude 1:1` (Morning, July 12)
- `Jude 20` -> `Jude 1:20` (Evening, October 8)
- `Jude 24` -> `Jude 1:24` (Morning, October 9 and Morning, October 10)
- `2 John 2` -> `2 John 1:2` (Morning, October 25)
- `Philemon 2` -> `Philemon 1:2` (Morning, November 1)
- `3 John 3` -> `3 John 1:3` (Morning, November 28)
- `Psalms 111:9` -> `Psalm 111:9` (Morning, August 26)
- `Psalms 5:8` -> `Psalm 5:8` (Evening, September 11)

Verse lists such as `Colossians 2:9, 10` are kept as written. Unknown books or shapes are left unchanged and listed by `scripts/validate_readings.py`. The validator does not invent a book.

## Seed differences (Heartlight slice vs CCEL)

The original 14 files for 2026-10-05 through 2026-10-11 were a Heartlight daily mirror. They are now the CCEL text. Differences found when comparing that seed to this source:

- Generated headings in the seed used Unicode em dash U+2014 and a year. They are now `Morning | October 5`.
- The seed collapsed many long dashes to a single hyphen (example: Oct 5 evening `gloried in-they` and `unsaved-what`; Oct 10 morning `will-every`). CCEL prints `--` (`gloried in--they`, `will--every`). The corpus keeps `--`.
- The seed used curly quotation marks around the lead verse. CCEL uses straight ASCII quotes. `scripture_text` and the markdown verse line follow CCEL.
- Wording drift on two evenings/mornings: Heartlight seed printed `for ever` on Oct 7 evening and Oct 10 morning. CCEL prints `forever` in those same sentences. The corpus keeps `forever` because that is the chosen source.
- Other October seed bodies that differed after whitespace normalization differed only by the dash and `forever`/`for ever` items above (character-count drift of 1 to 3).
- The seed footer (`Source mirror used for refresh: Heartlight...`) was not source text and is not stored.

## Manual fixes

None. The 732 readings were produced by the ingest script with no hand edits to devotion wording.

## Validation

```
python3 scripts/validate_readings.py
python3 -m pytest tests/test_validate_readings.py
```

The validator checks file counts, both slots for every MM-DD including 02-29, non-empty bodies, parseable `scripture_ref`, no em dash in generated titles, and a sample of bodies/`scripture_text` against the CCEL cache after whitespace normalization.

Lookup by date and slot:

```
python3 scripts/lookup_reading.py --date 10-05 --slot morning
```
