# Skill spec: `unbound-show` (run any "<Work> Unbound" podcast)

**Status:** DRAFT spec, docs only. No code exists for the new parts yet; every code step in §7 waits for Pierre's go ("alakazam").
**Derived from:** `SPURGEON-UNBOUND-PIPELINE.md` (what runs today) + `design/review-dr-eggbot-2026-11-27.md` + `design/DECISIONS.md`.
**Skill files:** `skills/unbound-show/SKILL.md` (Grok Bot) and `.claude/skills/unbound-show/SKILL.md` (Claude Code), same body.

## 1. Decisions baked in (Nov 27, 2026)

| # | Decision | Source |
|---|---|---|
| D-name | Shows are named after the **work** + "Unbound" (e.g. "The Imitation of Christ Unbound") | Pierre via Skippy, Nov 27 |
| D1 | Launch language **English only**; ES/HI later | `DECISIONS.md` D1 |
| D2 | Host **Cloudflare R2 + Worker** (HEAD + byte-range); no account/resources until "alakazam" + domain | `DECISIONS.md` D2 |
| D-video | Calm pastel stills in Rita's palette, words do the motion; cuts = 16:9 YouTube read-along + 30–60 s vertical reel | Lando, Nov 27 |
| D-gate | Every publish and every spend needs Pierre's explicit go | Standing rule |

## 2. Inputs

1. A `show.yml` (schema §3), one per show.
2. A **corpus**: one file per episode unit, public-domain, with front-matter (`key`, `title`, `source`, `edition`, `public_domain: true`, optional `scripture_ref`). Spurgeon: `data/readings/MM-DD-slot.md`. Kempis: `book-chapter` units from the aligned index (review §6c).
3. A **style guide** for the work (markdown) and **2–3 exemplar episodes** approved by Pierre.
4. Brand assets: show cover (3000², 1400²), Rita palette tokens, theme sting/outro audio.
5. Credentials **by env-var name only** (`ELEVENLABS_API_KEY`, host token). The skill never prints, stores or asks for values.

## 3. Per-show config schema (`show.yml`)

See `docs/pipeline/show.example.yml` for Spurgeon filled in. Fields:

| Field | Type | Meaning |
|---|---|---|
| `show.id` | slug | Stable id, e.g. `spurgeon-morning-evening` |
| `show.title` | string | "<Work> Unbound[: subtitle]" |
| `show.work`, `show.author` | string | Source work and author |
| `show.language` | BCP-47 | `en` at launch |
| `host.provider` | `buzzsprout` \| `cloudflare-r2` | Where audio + feed live |
| `host.feed_url` | URL | Public RSS (what verification reads) |
| `host.admin_url` / `host.show_id` | string | Buzzsprout admin, if provider is buzzsprout |
| `host.media_base`, `host.worker` | URL | Cloudflare only: custom domain (never r2.dev) |
| `cadence.timezone` | IANA tz | e.g. `America/Detroit` (ET) |
| `cadence.slots[]` | list | `{name, publish_time, day_offset}`; Spurgeon: morning `23:00` offset `-1`, evening `11:00` offset `0` |
| `cadence.unit_for_date` | rule | How a calendar date maps to a corpus key (`MM-DD-{slot}`, or sequential `book-chapter`) |
| `cadence.runway_days_min` | int | Alert if fewer days are scheduled (default 7) |
| `numbering.season` | rule | Must be **unique per year or per book** (fixes Spurgeon's collisions) |
| `numbering.episode` | rule | e.g. `{day_of_year:03d}{slot_code}` or `chapter`; validated unique |
| `voice.provider`, `voice.model_id`, `voice.voice_id`, `voice.voice_name` | string | ElevenLabs `eleven_v3`, Rory Talks for Spurgeon |
| `voice.key_env` | string | Env var name only |
| `voice.char_cap_per_batch` | int | Local spend guard (Spurgeon used 149,126) |
| `audio.lufs`, `audio.true_peak`, `audio.bitrate`, `audio.xfade_ms`, `audio.theme` | numbers/paths | -16, -1.5, 96k, 15, take B |
| `script.style_guide`, `script.exemplars[]`, `script.prompt_file` | paths | **prompt_file is required** (fixes G7) |
| `script.target_chars`, `script.char_tolerance` | int, float | 2540, 0.15 |
| `script.format[]` | list | Section order (sting, hook, intro, verse, meditation, prayer, sign-off, theme out) |
| `script.intro_line`, `script.signoff_suffix` | string | "This is <Show>.", "This has been <Show>. Go well today./Sleep well." |
| `copy.title_pattern`, `copy.notes_pattern` | template | `"{Slot}, {Mon} {d}: {Title}"`; notes = verse line + description |
| `qa.*` | thresholds | accuracy ≥ 0.95, \|LUFS-target\| ≤ 1, intros = 1, sign-off ≥ 0.6, no cues, duration band |
| `palette.tokens` | path | Rita's brand tokens |
| `video.cuts[]` | list | `youtube_16x9_readalong`, `reel_9x16_30_60s` |
| `alerts.miss_window_minutes` | int | **120** |
| `alerts.channels[]` | list | Open decision: Pierre picks two (review Q8) |
| `alerts.route_via` | agent | Skippy |
| `gates.publish`, `gates.spend` | `pierre_go` | Not configurable off |

## 4. Steps

Each step reads and writes the **episode ledger** (one row per unit: `key, script, copy, tts, qa, art, packed, published_guid, published_at, feed_seen_at`), written atomically. A step only acts on rows whose previous step is done and whose own column is empty or failed.

| # | Step | Does | Checks (must pass) | Output | Failure alert |
|---|---|---|---|---|---|
| S0 | **Ingest corpus** | Load units; validate front-matter | Count = expected; no dup keys; no empty bodies; refs parse; `public_domain: true` | `corpus/` + index JSON | Block; report to owner |
| S1 | **Index** (catalogue) | Build a flat/SQLite index: key, title, refs, themes, cross-refs. Optional RDF export. | Index count = corpus count | `index.json` / `index.sqlite` | Block |
| S2 | **Write scripts** (agent) | Agent gets `prompt_file` + style guide + exemplars + the unit text (+ related units from S1 if C11 is built) and writes the episode data; assembler renders markdown | Char band; format sections present once; no forbidden dashes; verse text from local Bible JSON; mapping table present; header lists inputs used | `scripts/*.md`, ledger `script=DRAFTED` | Report rows that fail; never voice them |
| S3 | **Copy** | Title, verse line, description, hook, sign-off from the script; Tiro pass | Every row in the next 14 days has title + notes; title matches pattern; hook/sign-off verbatim from script | `COPY.md` rows, ledger `copy=READY` | **Runway alert** if any slot in next 7 days lacks copy |
| S4 | **Voice render** ⛔ spend | Segment TTS + mix + master | Batch chars ≤ cap and ≤ remaining quota; **Pierre's go on the batch** | MP3 + `.work/`, ledger `tts=DONE` | Quota exit (75) → stop + report |
| S5 | **Audio QA** | Whisper + loudness + drift | §3 `qa.*` thresholds; F0/WPM within ~10% of reference | `qa.json`, ledger `qa`, QA.md row | FAIL rows held; segment re-render needs spend go |
| S6 | **Art** | Show cover (once); per-episode art optional | 3000² and 1400² JPG/PNG, RGB, < 512 KB for 1400 | `art/` | Block launch only |
| S7 | **Pack** | Build `upload-<range>.json/.txt` from ledger + COPY (not inline) | File exists, size > 0; title/notes present; season/episode unique vs live feed; publish time = slot time in `cadence.timezone`; **skip any title or key already in the live feed or host list** | Pack files | Block the pack |
| S8 | **Publish / schedule** ⛔ publish | Upload oldest first; schedule at slot time (or publish now for catch-up, only with go) | Pierre's go names the range; after each upload, host shows it with the right time | Ledger `published_guid`, `published_at` | Any upload failure → stop the run, report the row, do not retry blindly |
| S9 | **RSS verify** | Fetch `host.feed_url` | HTTP 200; XML valid; GUID set ⊇ previous; new titles present; enclosures answer HEAD + `Range: bytes=0-1` → 206 | Ledger `feed_seen_at` | Not seen 2 h after slot → **page** |
| S10 | **Monitor** (routine) | Every slot + 2 h: is the slot's episode in the feed? Daily: runway (days scheduled ahead), copy coverage, quota, billing/domain emails | See left | Status line to Skippy | **Missed slot → page Pierre on 2 channels within 2 h**; runway < `runway_days_min` → warn; billing/suspension email → page |
| S11 | **Video** ⛔ publish | Forced alignment → word timings; render 16:9 read-along + 9:16 reel on palette stills | Sync spot check; captions match script | Draft uploads only | Report |
| S12 | **Backup** | Commit text artifacts; copy masters to second location | Hashes match | SHA-256 manifest | Report |

## 5. Idempotence

- **Key** = `show.id` + unit key (e.g. `spurgeon-morning-evening:11-28-morning`). Every step is keyed; re-running a step on a done row is a no-op.
- **Before S7 and S8:** fetch the live feed (and, for Buzzsprout, the admin episode list including drafts and scheduled). **Skip any row whose title, key or GUID is already there.** This is the check that would have caught the Nov 27 "(Rory v0.2)" stray draft.
- TTS is cached by text hash, so re-renders pay only for changed segments (already true in `build.py`).
- Ledger writes are atomic (temp + rename), and the publish step writes `published_guid` immediately after each success so a crash mid-batch resumes at the next row.
- Feed GUIDs never change once published (Apple 837). Any host move carries GUIDs over.

## 6. Gates (never configurable off)

| Gate | Trigger | Who |
|---|---|---|
| Spend | Any TTS batch, any paid service, any Cloudflare/domain resource | Pierre's explicit go naming the batch/amount |
| Publish | Any upload that goes live or is scheduled; any feed change; any YouTube publish | Pierre's explicit go naming the range |
| Host change | Redirect, unlock, `itunes:new-feed-url` | Pierre, on cutover day |
| Plan mode | Until Pierre says "alakazam", only docs, specs and dry runs | — |

The skill may run S0–S3, S5–S7, S9, S10 (read-only) without a go; S4, S8, S11 always stop and ask.

## 7. Code the skill needs (each waits for Pierre's go)

Numbered in build order. None exists yet except where noted.

| # | Code | Why | Size |
|---|---|---|---|
| C1 | **Ledger + pack builder** (`pack.py`): manifest/ledger-driven, reads COPY, writes `upload-*.json/.txt`, live-feed skip check | Replaces the `/tmp` one-offs (G3, G5) | S |
| C2 | **Slot-miss + runway alert routine**: feed check 2 h after each slot; daily runway/copy/quota check; routes to Skippy + 2 channels | Nov 14–26 lesson (G2) | S |
| C3 | **Ledger reconciler**: backfill `published_guid` from the live feed; fix stale `script`/`copy`/`RENDERING` columns | Trustworthy state (G5) | S |
| C4 | **Generalise `batch.py`/`build.py`** to read `show.yml` (voice id, theme, paths, thresholds) instead of hard-coded Spurgeon paths | Reuse for other shows | M |
| C5 | **Script assembler** generalised (`assemble.py` + template from `script.format`) and a **saved prompt file** per show | Reproducible writing (G7) | S |
| C6 | **Buzzsprout uploader** via a documented host API or a scripted browser playbook, with per-row verification | Replace click-by-click (G11) **[Unverified: API scope not checked today]** | M |
| C7 | **Feed generator** (deterministic RSS from the ledger, golden-file tests, `podcast:guid`, `itunes:new-feed-url` support) | Cloudflare host (D2) | M |
| C8 | **Cloudflare Worker** for R2: HEAD, 206 byte ranges (`bytes=0-1`, open-ended, suffix), CORS, logging | Apple requirement (review §1b #15) | M |
| C9 | **Feed validator CI**: XML, GUID superset, enclosure uniqueness, episode-number uniqueness, HEAD/206 probe | Safe publishing | S |
| C10 | **Read-along video renderer**: forced alignment, 16:9 + 9:16 on Rita palette stills, draft-only YouTube queue | D-video | L |
| C11 | **Corpus retrieval** (optional): per-episode related-unit lookup from the index into the writer's context, IDs logged in the script header | Makes "grounded" real (pipeline doc §2.4) | S |
| C12 | **Backups**: commit pipeline code + text artifacts to git; masters to a second store | G1 | S |

## 8. Open decisions for Pierre

1. **Repo home:** keep these docs in this public class-site repo, or move the pipeline to a private repo (proposed `NukaSoft/unbound-pipeline`)? The code in C1–C12 should not live in a CIS 300 site repo.
2. **Numbering fix:** Spurgeon has 30 duplicate episode numbers in Season 10. Change future numbering (e.g. Season = year, Episode = day-of-year×10 + slot), or leave as is?
3. **Alert channels and window:** which two channels page you, and is 2 hours right?
4. **Prompt file:** OK to write down the Spurgeon writing brief as `script.prompt_file` so another agent can reproduce the voice?
5. **Graph:** wire retrieval in (C11), or drop the "graph-grounded" claim from the design doc?
6. **Runway:** how many days ahead should always be scheduled (proposed 7, with a weekly batch routine)?
7. **Which code first after "alakazam":** proposed C2 → C1 → C3 → C5 → C4, then C7–C9 with the Cloudflare move.
