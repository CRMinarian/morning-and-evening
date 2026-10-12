# Provenance

Corpus: C. H. Spurgeon, *Morning and Evening: Daily Readings*.
Owner of this ingest: data pipeline only. The source wording is kept as received. Modernization is out of scope.

## Source

- Work page: https://www.ccel.org/ccel/spurgeon/morneve
- Table of contents: https://www.ccel.org/ccel/spurgeon/morneve.toc.html
- Plaintext dump used by `scripts/ingest_morning_evening.py`: https://www.ccel.org/ccel/s/spurgeon/morneve/cache/morneve.txt
- Per-reading HTML (stored in each file's `source` field): `https://www.ccel.org/ccel/spurgeon/morneve.dMMDDam.html` and `...dMMDDpm.html`

The earlier class-site seed of 14 October 2026 files cited Heartlight as a refresh mirror. This ingest replaces that slice with the CCEL plaintext so the full year can be regenerated from one public-domain file.

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
python3 scripts/ingest_morning_evening.py --source-file /path/to/morneve.txt
```

## License / public-domain status

Charles Haddon Spurgeon died in 1892. *Morning and Evening* is in the public domain in the United States. CCEL marks the work "Public Domain" / "Public Domain -- Copy Freely". This repo stores the text for the same public-domain use. No CCEL trademark or site assets were copied.

## Parse notes

- The plaintext is a wrapped dump of the CCEL HTML. Headings are `Morning, Month D` and `Evening, Month D`.
- Navigation crumbs such as `[33]Go To Evening Reading`, month day-index lines, horizontal-rule separators, and the trailing scripture-reference index are dropped.
- Wrapped prose lines are joined into paragraphs. Short-line blocks (quoted verse stanzas) keep their line breaks.
- The lead quotation is stored as `title` and `scripture_text`. The following line is stored as `scripture_ref`.
- The markdown body after frontmatter keeps the seed layout: heading, bold reference, lead quotation, then the devotion. The devotion itself is not rewritten.
- Filenames follow the seed pattern `YYYY-MM-DD-slot.md` with year `2026` so the class-week paths stay stable. `02-29` is included even though 2026 is not a leap year; the calendar is perpetual.
- Frontmatter `date` is `MM-DD` as specified. That field was not in the original seed files.

## Scripture reference normalization (not guessing)

These source lines name a single-chapter book by verse only. They are stored as `Book 1:verse` so every `scripture_ref` is `book chapter:verse(s)`:

- `Jude 1` -> `Jude 1:1` (Morning, July 12)
- `Jude 20` -> `Jude 1:20` (Evening, October 8)
- `Jude 24` -> `Jude 1:24` (Morning, October 9 and Morning, October 10)
- `2 John 2` -> `2 John 1:2` (Morning, October 25)
- `Philemon 2` -> `Philemon 1:2` (Morning, November 1)
- `3 John 3` -> `3 John 1:3` (Morning, November 28)

`Psalms` is stored as `Psalm` (Morning, August 26; Evening, September 11).

Verse lists such as `Colossians 2:9, 10` are kept as written. Unknown books or shapes are left unchanged and listed by `scripts/validate_readings.py`. The validator does not invent a book.

## Manual fixes

None. The 732 readings were produced by the ingest script with no hand edits to devotion wording.

## Validation

```
python3 scripts/validate_readings.py
python3 -m pytest tests/test_validate_readings.py
```

Lookup by date and slot:

```
python3 scripts/lookup_reading.py --date 10-05 --slot morning
```
