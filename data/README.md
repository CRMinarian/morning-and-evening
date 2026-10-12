# Vault feed used by the class site

These JSON files are the public-domain Spurgeon excerpts used to write
the static Home and This Week pages. GitHub Pages serves the HTML; no
build step is required.

- `today.json` — featured morning and evening pair on `index.html` (2026-10-05)
- `this-week.json` — seven-day title table for `week.html` (2026-10-05 through 2026-10-11)
- `this-week-full.json` — seven days of full bodies on `week.html` (same week)
- `year-index.json` — all 732 readings (path, date, slot, scripture_ref)
- `readings/` — one dated markdown file per morning and evening, including 02-29
- `readings/PROVENANCE.md` — source, edition, retrieval date, and parse notes

The October class-week indexes keep the same JSON keys the site already
reads (`title`, `scripture`, `body`, `episode`, `id`, and
`source_reading` on the full week file). Bodies are regenerated from the
CCEL public-domain text.

Texts are calendar-day Spurgeon *Morning and Evening* (public domain via
CCEL). Rebuild the markdown and indexes with
`python3 scripts/ingest_morning_evening.py`. Check counts with
`python3 scripts/validate_readings.py`.

Rights: Charles H. Spurgeon, *Morning and Evening*, public domain via CCEL.
