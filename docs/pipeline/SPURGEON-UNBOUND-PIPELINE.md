# Spurgeon Unbound: production and publishing pipeline (as it actually runs)

**Status:** DRAFT design doc + engineering write-up, docs only. Written by dr eggbot for Pierre, Fri Nov 27, 2026 (ET).
**Scope:** describes what runs today. Nothing here was built, deployed, published or paid for while writing it.
**Labels:** **[Verified]** = checked on the box, in GitHub or on the live feed on Nov 27. **[Manual]** = a person or agent does it by hand; no code. **[Gap]** = missing, fragile or undocumented. **[Unverified]** = claimed elsewhere, not checked today.

No secrets are in this doc. API keys are named by environment variable only.

---

## 0. Summary (5 lines)

1. **Corpus:** 732 public-domain *Morning and Evening* readings scraped from CCEL into `data/readings/MM-DD-slot.md` (this repo, branch `cursor/spurgeon-corpus-ingest-ffb6`, PR #11, unmerged), copied to the box.
2. **Script:** an executor agent hand-writes each episode (light modernisation of Spurgeon's paragraphs + new hook, prayer, sign-off, description) into Python data files; `assemble.py` turns them into the script markdown with the KJV verse looked up locally.
3. **Voice + QA:** `build.py` sends each script segment to ElevenLabs `eleven_v3` (voice Rory Talks), mixes theme music, masters to -16 LUFS / 96 kb/s MP3; `batch.py` runs faster-whisper QA and writes the manifest.
4. **Publish:** copy (COPY.md / COPY-tiro.md) + MP3 paths are packed into `upload-*.txt/.json`; a browser agent uploads each one in Buzzsprout admin (Season 10, episode number day×100+04/16), publishing or scheduling at 11 PM ET (Morning, night before) / 11 AM ET (Evening).
5. **Verify + monitor:** the public RSS is fetched and titles counted; a daily stats routine reads Buzzsprout downloads. **There is no missed-slot alarm**, which is why Nov 15–26 went out 12 days late.

---

## 1. Where everything lives [Verified]

| Thing | Location | In git? |
|---|---|---|
| Corpus (732 readings, CCEL) | `CRMinarian/morning-and-evening` branch `cursor/spurgeon-corpus-ingest-ffb6` @ `99839a4`, PR #11 (open, "Do not merge"). `main` has only 14 readings. Box copy: `/workspace/spurgeon-full-set/src/` | Yes (branch only) |
| Catalogue graph (RDF) | `/workspace/pierres-brain/rdf/spurgeon_morning_evening.ttl`, built by `/workspace/pierres-brain/scripts/ingest_spurgeon_me.py`; Fuseki dataset `pierres-brain`, named graph `urn:pierre:source:spurgeon-morning-evening` | **No** |
| Style guide | `/workspace/spurgeon-unbound/SPURGEON-VOICE-STYLE-GUIDE-v0.2.md` (622 lines) | **No** |
| Script authoring data | `/workspace/spurgeon-full-set/batch1/gen/b1a..b1d.py` (Oct 20–Nov 16, 56 eps), `/workspace/spurgeon-full-set/tools/eps/b2_*.py` (64 files, the other 662) | **No** |
| Script assembly | `tools/lib.py`, `tools/assemble.py` (batch 2), `batch1/gen/make.py` (batch 1) | **No** |
| Scripts | `batch1/scripts/*-podcast-v0.1.md` (718) | **No** |
| Voice + mix | `/workspace/spurgeon-unbound/work/tts-rory-v0.2/build.py`, theme `work/theme/theme-takeB-*.wav` | **No** |
| Batch runner + QA | `work/tts-rory-v0.2/batch.py`, wrappers `batch1/run-20261112/run-batch.sh`, `start-locked.sh`, `margin-watchdog.sh` | **No** |
| State | `/workspace/spurgeon-full-set/manifest.csv` + `manifest.json` (718 rows) | **No** |
| Audio | `batch1/audio/` (317 MP3s, 7.0 GB incl. `.work` dirs) | **No** |
| Copy | `batch1/COPY.md` (v0.1), `batch1/COPY-tiro.md` (v0.2 voice pass) | **No** |
| Upload packs | `/workspace/spurgeon-full-set/upload-nov8-14.*`, `upload-nov15-27.*`, `upload-nov28-dec4.*` | **No** |
| Pack builders | `/tmp/build_spurgeon_catchup.py`, `/tmp/build_spurgeon_nov28_dec4.py` | **No, and in /tmp** [Gap] |
| Show art | `/workspace/spurgeon-unbound/art/make_cover_FINAL_v5.py` → `spurgeon-unbound-cover-FINAL-v5A-3000.jpg` | **No** |
| Host + feed | Buzzsprout show `2657629`; `https://feeds.buzzsprout.com/2657629.rss` (301s to `rss.buzzsprout.com/2657629.rss`) | n/a |

**[Gap] The whole production pipeline is on one box, outside git.** This PR is the first time it's written down in a repo.

---

## 2. How the scripts are written and where the memory comes from

> ### What you thought vs. what happened
>
> | You thought | What actually happened (evidence below) |
> |---|---|
> | We built a graph database of **the entire work of Spurgeon**. | The graph covers **only *Morning and Evening*** (732 readings). No sermons, no *Treasury of David*, nothing else. |
> | The graph **manages the translation/rewrite**. | **Nothing in the script pipeline reads the graph.** No SPARQL, no Fuseki call, no RDF file is opened by any scripting, assembly or voice tool. Fuseki isn't even running today. |
> | The writing comes from some stored "memory" of Spurgeon. | The "memory" is **the one reading itself** (put in front of the agent in a text pack), **the style guide**, **earlier episodes as examples**, and **the language model's own general knowledge**. Most of what Rory says in the meditation is **Spurgeon's own words**, lightly modernised: median **87%** word-sequence match to the CCEL text across all 718 scripts. |
> | | The graph was built **Oct 19**, after the pilot week (Oct 13–19) was already scripted and live. It's a tidy, validated **catalogue index** (dates, titles, Scripture refs), built and never wired in. |

### 2.1 Who writes each script

- **Writer: an executor agent** (a Grok Bot sub-agent, i.e. the language model running that agent). Evidence:
  - `/workspace/spurgeon-full-set/PLAN.md` §4: "Adapted script (meditation, prayer, mapping) | executor agent (eps*.py pattern), Pierre reviews". §7: "Script adaptations are manual."
  - Every script's header (`tools/assemble.py`, `build_markdown`): "Hook and sign-off | Drafted by the executor agent, pending Tiro review".
  - `batch1/COPY.md` header: "Status | Drafted by the executor agent."
- **Not a script-writing program.** There is no generator code that calls a model API to write text. The agent *types the content* into Python data files, one `E(...)` call per episode:
  - `tools/eps/b2_0101_0105.py` … `b2_1227_1231.py` (64 files, 662 episodes, written Nov 12, logged in `tools/SCRIPTS_PROGRESS.log` starting 2026-11-12 07:43 AM ET)
  - `batch1/gen/b1a.py`–`b1d.py` (56 episodes, Oct 20–Nov 16, written around Oct 17; `COPY.md` v0.1 for them is dated 2026-10-17)
  - pilot: `/workspace/spurgeon-unbound/samples/week-1013/gen/eps1.py`–`eps3.py` (Oct 13–19)
- Each `E(...)` holds: `slot, md, slug, title, ref, frag` (headline verse fragment), `hook`, `sign` (sign-off), `desc` (show-notes description), `paras` (the meditation, one string per paragraph, with `[beat]`/`[building]`/`[slower]` cues), `prayer`, and `mapping` (a table of source sentence → paragraph → what was kept or changed).
- **Human review:** Tiro does a copy/voice pass (`batch1/COPY-tiro.md` edit log: 32 edits across 24 episodes). Pierre's review is listed in PLAN.md but **[Gap] no per-episode sign-off record exists.**

### 2.2 The exact instructions ("prompt")

- **[Gap] There is no prompt file on disk.** The writing instructions were the agent's dispatch brief in chat, not a saved file. I could not open those chat transcripts from this session, so I can't quote them.
- What *is* on disk and constrains the writing:
  1. **Style guide** `SPURGEON-VOICE-STYLE-GUIDE-v0.2.md`: persona, sentence rhythm, imagery bank, direct address, pacing, vocabulary, §10 *Modernisation rules* (Keep / Update / Make it work for the ear / Never), §11 good-vs-bad example pairs. Every script names it in front-matter (`style_guide: "SPURGEON-VOICE-STYLE-GUIDE-v0.2.md"`).
  2. **Format rule** (Pierre, 2026-10-12), hard-coded in the template: theme sting → hook → "Good morning/evening. This is Spurgeon Unbound." → verse → meditation → prayer → sign-off → theme out.
  3. **Length band** in `tools/lib.py`: `TARGET_CHARS = 2540`, ±15% (2,159–2,921 billed characters). `SCRIPTS_PROGRESS.txt` reports mean 2,779, 0 QA errors.
  4. **Checks** in `tools/lib.py`: no forbidden dashes (`script_has_forbidden_dashes`), billed character count.
  5. **Rules in code comments**: `build.py` "2026-10-17 (Pierre): no editor's note or post-episode commentary"; v0.2 rule 7.4 "no standalone title line under The verse".

### 2.3 What goes in per episode (the "memory")

| Input | Where from | When | How it's used |
|---|---|---|---|
| **The reading itself** (full CCEL text, ref, headline) | `tools/pack_MMDD_MMDD.txt` (33 packs, e.g. `pack_0101_0110.txt`: `===== 01-01-morning seq=147 src_chars=1904 =====`, `REF:`, `HEADLINE:`, body) built from `src/MM-DD-slot.md` | Before each writing session | Pasted/read into the agent's context; the agent paraphrases it paragraph by paragraph |
| **Style guide v0.2** | `/workspace/spurgeon-unbound/` | Each session | Voice and modernisation rules |
| **Examples** | Earlier `E(...)` entries and the pilot scripts in `samples/week-1013/` | Each session | Few-shot pattern for hook/prayer/sign-off/mapping |
| **KJV verse text** | `tools/kjv/*.json` (66 books), via `lib.kjv_verse()` | At assembly, by code | The spoken headline verse is looked up, not written by the model |
| **Source body for the appendix** | `lib.source_body()` reads `src/MM-DD-slot.md` | At assembly, by code | Copied into the script's mapping appendix |
| **General knowledge** | The language model | While writing | Hooks, prayers, descriptions, modern-English choices |
| **The RDF graph** | `pierres-brain` | **Never** | **Not used** |

**How close is the meditation to Spurgeon?** [Verified, computed Nov 27] For all 718 scripts, comparing the words of `paras` to the CCEL source body (`difflib.SequenceMatcher` on lower-cased word lists, cues stripped): **median 0.873, min 0.501, max 0.994; 73% of episodes ≥ 0.80.** Example, 01-01 morning: source "Perhaps this year, beloved Christian reader, this may be thy case or mine" → script "Perhaps this year, beloved Christian, this may be your case, or mine." That is why the writing reads so well: it's mostly Spurgeon, with *thee/thy* updated and the paragraphs split for the ear. The genuinely new writing is the **hook, prayer and sign-off** (median **35%** of the hook + meditation + prayer + sign-off words, range 20–65%, computed the same way), plus the show-notes description.

### 2.4 What the graph is, exactly [Verified]

- **Script:** `/workspace/pierres-brain/scripts/ingest_spurgeon_me.py`, docstring: "Ingest Spurgeon 'Morning and Evening' (public domain, CCEL text) into Pierre's Brain … Deterministic KnowledgeTriples only (from frontmatter); NO LLM … PUTs the result into named graph `<urn:pierre:source:spurgeon-morning-evening>` ONLY".
- **Ran:** 2026-10-19 13:09 UTC (9:09 AM ET), report `/workspace/pierres-brain/rdf/spurgeon_morning_evening_report.json`.
- **Input:** this repo, branch `cursor/spurgeon-corpus-ingest-ffb6`, commit `99839a4731e730bf889c528844bfae3bebbf09b2`, 732 reading files.
- **Output:** 732 `pierre:SourceCard`s (date, slot, title, Scripture ref + text, body), 2,196 knowledge triples from front-matter, 690 distinct Scripture refs (38 cited by more than one reading), 36,423 triples, one Wikidata link (Spurgeon = Q278825; no item for the work). Turtle file `rdf/spurgeon_morning_evening.ttl` (3.9 MB). Three sample queries `rdf/spurgeon_sample_q*.rq`.
- **Coverage:** *Morning and Evening* only. No other Spurgeon work is in it.
- **Wired in?** No. `rg -i "sparql|3030|fuseki|pierres-brain|rdf"` over `spurgeon-full-set/tools/*.py`, `tools/eps/*.py`, `batch1/gen/*.py` and `tts-rory-v0.2/*.py` returns **nothing**. `curl http://127.0.0.1:3030/$/ping` returns nothing (Fuseki down, Nov 27).
- **Where the "graph-grounded" idea comes from:** Pierre's design doc (`design/pierre-design-doc-2026-11-27.md`, lines 43–44: "A graph database was built from Spurgeon's writing … rewritten into modern English, grounded in that graph"). dr eggbot's review §6a (same day) flagged the mismatch.
- **What it would take to make it real** (gated, see `UNBOUND-SHOW-SKILL-SPEC.md` §7, C11): a retrieval step that, per episode, pulls the other readings sharing the same Scripture ref or theme and puts them in the writer's context, with the IDs recorded in the script header so it's auditable.

---

## 3. Corpus [Verified]

- `scripts/ingest_morning_evening.py` in this repo (PR #11) scrapes CCEL's public-domain text (`data/source/ccel-morneve.txt` cached) into `data/readings/MM-DD-{morning|evening}.md` with YAML front-matter (`date: "MM-DD"`, `slot`, `title`, `scripture_ref`, `scripture_ref_as_printed`, `scripture_text`, `source`, `edition`, `public_domain`), plus `data/year-index.json`. Validation: 0 ref disagreements, 0 empty bodies, 02-29 kept as year-less files.
- **[Gap]** PR #11 is unmerged, so production depends on a feature branch.
- **[Open decision]** 02-29: both readings are scripted; manifest marks them `deferred-2028`. 2027 has no Feb 29.

## 4. Scripting [Verified; authoring Manual]

1. Agent reads a `pack_*.txt` and writes `E(...)` entries (§2).
2. `python3 tools/assemble.py <eps file>` → `batch1/scripts/{SLOT}-{MM-DD}-{slug}-podcast-v0.1.md` and updates `SCRIPTS_PROGRESS.txt` (`last_completed_key`, char stats).
3. Checks: char band 2,159–2,921, no forbidden dashes, verse from local KJV.
- State today: `SCRIPTS_PROGRESS.txt` → `remaining_unscripted: 0` (all 718 + pilot 14 = 732).
- **[Gap]** Script front-matter still says `status: "DRAFT"`, `date: "2026-11-12"`; the manifest `script` column says `TODO` for 660 rows that are in fact written (only batch 1's 56 are `DRAFTED`).

## 5. Voice: Rory Talks on ElevenLabs [Verified]

- `build.py <script.md> <out.mp3>`: splits the `## Script` section into segments; each segment → `POST /v1/text-to-speech/<voice>?output_format=mp3_44100_192`, `model_id: eleven_v3`, voice **Rory Talks**. Text-hash cache in `tts/` (re-runs pay only for changed segments). Cues become silence (`pause .8s, beat .4s, long pause 1.6s`) or v3 tags (`[softly]`, `[slowly]`…). Theme take B sting/outro ducked under voice. 15 ms crossfade at splices (Pierre-approved Oct 22). Two-pass `loudnorm` to -16 LUFS. Per-episode work dir (`.work/`) so workers don't collide. Exit code 75 on quota exhausted; backoff on 429/5xx.
- `batch.py` (via `run-batch.sh`): `WORKERS=2`, `CAP` local character guard, `SEQ_FROM/SEQ_TO` manifest range, `THEME=B`, `MASTER=1`, `MP3_BITRATE=96k`. Key from env `ELEVENLABS_WS2_API_KEY` → `ELEVENLABS_API_KEY` (never printed). `margin-watchdog.sh` stops before the monthly reset.
- Spend: Creator workspace, limit 363,000 chars/month (`run-20261112/REPORT-17.md`). ~2,700 chars/episode ≈ $0.22 list (PLAN.md §3). **Every render batch is a spend gate.**
- State: manifest `tts` = 316 DONE, 2 stuck `RENDERING` [Gap: stale], 398 NOT_STARTED. Last render run: `batch1/batch.log` 2026-11-13.

## 6. QA [Verified]

`batch.py qa()`: faster-whisper `small.en` transcript vs `ref.txt`. FAIL if word accuracy < 95%, |LUFS+16| > 1, intro count ≠ 1, sign-off match < 0.6, any spoken cue word, duration outside 170–260 s. Also F0 and WPM vs the Oct 13–19 reference (87 Hz, 210 wpm) for voice drift. Writes `.work/qa.json` and manifest `qa`. Failures get a manual listen and segment re-render (`QA.md` "Re-renders 2026-10-19").
- State: 307 PASS, 8 FAIL:accuracy, 1 FAIL:cues (manual PASS for some).
- **[Gap]** `batch1/QA.md` table stops at Nov 8; Nov 9–Dec 4 published episodes have QA in the manifest/`qa.json` but no human-readable row.

## 7. Art [Verified]

- Show cover only: `art/make_cover_FINAL_v5.py` → 3000×3000 / 1400×1400 JPG. Episodes inherit the show cover.
- `thumbnails/make.py` (per-episode 1080², 1200×630, square MP4) was only ever run for Oct 13. **[Manual/optional]** Not in the publish path.

## 8. Copy [Verified; Manual]

- `batch1/COPY.md` v0.1, one `## <mp3 name>` block per episode: **Title** (`Morning, Oct 20: Grow Up into Him`), **Verse** (`<ref> (KJV), "<fragment>"`), **Description**, **Hook**, **Sign-off**. Show notes = Verse + blank line + Description.
- `batch1/COPY-tiro.md` v0.2 is Tiro's voice pass with an edit log; it's the one that should be uploaded.
- Coverage: 92 episodes, Oct 20–Dec 4. Nov 17–Dec 4 copy was written on Nov 27 *during* the catch-up (backups `COPY*.md.bak-20261127-*`).
- **[Gap] Copy is written behind publishing.** It isn't a gate, so a missing description silently blocks a slot.

## 9. Upload pack [Verified; builder in /tmp]

- One `.txt` (human) + `.json` (agent) per batch. Per episode: `key`, `file` (absolute MP3 path), `file_exists`, `file_bytes`, `season` (10), `episode` (e.g. `"2804"`), `title`, `notes` (show notes), `publish_et` (`2026-11-27 11:00 PM`).
- Built by hand-written one-off scripts: `/tmp/build_spurgeon_catchup.py`, `/tmp/build_spurgeon_nov28_dec4.py`, which embed the copy inline and append it to COPY.md. **[Gap] /tmp is wiped on box replacement; the builders aren't manifest-driven and duplicate the copy.**

## 10. Buzzsprout publish [Manual, browser agent]

- A browser agent signs in to Buzzsprout (Pierre's account) and, per pack row, oldest first: *Episodes → Upload* the MP3, set title, description, **Season 10**, **Episode = day-of-month × 100 + 04 (Morning) or + 16 (Evening)** (Buzzsprout drops the leading zero, e.g. Dec 1 Morning = 104), and either **Publish now** (catch-up) or **Schedule** at `publish_et`. Admin path `/admin/2657629`. Account time zone ET.
- Nov 27: 26 published immediately (Nov 15–27), 14 scheduled (Nov 28–Dec 4). One stray unpublished draft "(Rory v0.2)" left from a first attempt; no delete found — Pierre to remove.
- **[Gap] Episode numbers collide.** All 92 live items are Season 10 and numbering only uses day of month, so Oct 13–31 and Nov 13–27 share numbers (live feed: **30 duplicate `itunes:episode` values**, e.g. 2716 = Evening Oct 27 and Evening Nov 27). December repeats Nov 1–4. GUIDs are unique (92/92), so apps don't break, but episode-number sorting does.
- **[Gap]** No API path is used; uploads are click-by-click. Manifest `published` column is empty for all 718 rows (never written back).

## 11. RSS verification and schedule [Verified]

- After publishing, `curl -L https://feeds.buzzsprout.com/2657629.rss`, parse `<item>`s, compare titles with the pack. Nov 27: Buzzsprout showed 26 live before the feed did; feed caught up later that afternoon (a one-off `spurgeon-rss-catchup-watch` routine polled every 30 min).
- Live feed Nov 27 ~2:20 PM ET: **92 items**, newest "Evening, Nov 27: The Forgiveness of Sins", `podcast:locked yes`, all GUIDs unique. The 26 catch-up items all carry pubDate `Fri, 27 Nov 2026 13:00:00 -0500` (publish-now time, not their slot).
- Schedule: Morning **11:00 PM ET the night before** (4:00 AM GMT), Evening **11:00 AM ET** (4:00 PM GMT). Pierre go 2026-11-12. Queue currently runs out after **Evening Dec 4**.

## 12. Monitoring and the Nov 14–26 stall [Verified from memory/journal + review]

- `spurgeon-first-listeners` routine: daily ~9:25 AM ET, browser reads Buzzsprout stats (all-time downloads, apps, devices, top episodes) and pings Pierre. It never checks *whether a new episode went out*.
- **The stall:** the last pack ran through Nov 14; then the Buzzsprout card failed (account suspended → no uploads), no new pack was built, and copy for Nov 17+ didn't exist. Nothing alerted. 24 slots were missed until the Nov 27 catch-up. Buzzsprout policy: 30 days suspended, then downgrade to Free with 90-day episode expiry (review §1a #4).
- **Lesson:** monitor the *output* (the public feed), not the inputs. A missed slot must page within ~2 hours, and the queue's runway (days of scheduled episodes left) must alert before it hits zero.

---

## 13. Gaps (consolidated)

| # | Gap | Impact |
|---|---|---|
| G1 | Pipeline code, scripts, copy, manifest, audio not in git; one box | Box loss = rebuild from memory |
| G2 | No missed-slot or runway alert | Nov 14–26 stall (24 episodes late) |
| G3 | Pack builders in `/tmp`, hand-coded per batch | Lost on box replacement; error-prone |
| G4 | Copy not a gate; written behind publishing | Slots silently blocked |
| G5 | Manifest `script`/`copy`/`published` columns stale; 2 rows stuck `RENDERING` | Can't trust state for idempotence |
| G6 | Episode numbering collides (30 dupes in Season 10) | Wrong ordering in some apps |
| G7 | No prompt file for script authoring; no review sign-off record | Not reproducible for another show |
| G8 | Graph built but not wired in; Fuseki down | "Graph-grounded" claim is false today |
| G9 | QA.md human table stops Nov 8 | Audit gap |
| G10 | Corpus on unmerged branch (PR #11) | Source of record is a feature branch |
| G11 | Buzzsprout upload is click-by-click by a browser agent | Slow, fragile, no API audit trail |
| G12 | Stray "(Rory v0.2)" draft in Buzzsprout | Cosmetic; Pierre to delete |
| G13 | 02-29 decision open | 2 episodes parked |

The reusable skill that fixes these is specified in `docs/pipeline/UNBOUND-SHOW-SKILL-SPEC.md`.
