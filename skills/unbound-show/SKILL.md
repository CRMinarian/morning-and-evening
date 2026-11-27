---
name: unbound-show
description: Use when producing, scheduling, verifying or monitoring any "<Work> Unbound" podcast (Spurgeon Unbound and later shows). Drives corpus → script → voice → QA → copy → pack → publish → RSS verify → alert from a per-show show.yml, with Pierre's go required for every publish and every spend.
status: DRAFT (spec only; code steps C1–C12 in docs/pipeline/UNBOUND-SHOW-SKILL-SPEC.md wait for Pierre's go)
---

# unbound-show

Full spec: `docs/pipeline/UNBOUND-SHOW-SKILL-SPEC.md`. How Spurgeon runs today: `docs/pipeline/SPURGEON-UNBOUND-PIPELINE.md`. Example config: `docs/pipeline/show.example.yml`.

## Hard rules
1. **No publish and no spend without Pierre's explicit go** naming the range or batch. That covers TTS renders, uploads, scheduling, feed or host changes, YouTube, and any Cloudflare or domain resource.
2. In plan mode (until Pierre says "alakazam"), only docs, specs and dry runs.
3. Credentials by env-var name only. Never print, store, paste or ask for a key.
4. Read the live feed before you pack or publish. **Skip every title, key or GUID that's already up** (including drafts and scheduled items on the host).
5. GUIDs never change once published.

## Before you start
- Load the show's `show.yml`. Refuse if `gates`, `alerts.miss_window_minutes`, `host.feed_url` or `script.prompt_file` is missing; ask the owner instead.
- Load the ledger (one row per unit). Trust it only after the reconcile check (feed GUIDs vs ledger `published_guid`).

## Steps (each: check → output → alert)
| # | Step | Gate | Must pass | On failure |
|---|---|---|---|---|
| S0 | Ingest corpus | — | count, unique keys, non-empty, public domain | block, report |
| S1 | Index | — | index count = corpus count | block |
| S2 | Write scripts (agent, using prompt_file + style guide + exemplars + unit text) | — | char band, format sections once, local Bible verse, mapping table, inputs listed in header | hold row |
| S3 | Copy (Tiro pass) | — | next 14 days have title + notes | runway alert if < 7 days |
| S4 | Voice render | **spend** | batch ≤ cap and quota | stop on quota, report |
| S5 | Audio QA | — | thresholds in `qa` | hold row; re-render needs spend go |
| S6 | Art | — | cover sizes | block launch |
| S7 | Pack | — | file exists, unique season/episode, slot time correct, not already live | block pack |
| S8 | Publish/schedule, oldest first | **publish** | host shows each row at the right time | stop the run, report the row |
| S9 | RSS verify | — | 200, valid XML, GUID superset, new titles present, HEAD + 206 | page if not seen 2 h after slot |
| S10 | Monitor routine | — | slot + 2 h check; daily runway, quota, billing mail | **missed slot pages Pierre on 2 channels within 2 h** via Skippy |
| S11 | Video (16:9 read-along, 9:16 reel) | **publish** | sync spot check | report |
| S12 | Backup | — | hashes match | report |

## Report format
Count published, newest live per RSS, anything failed or blocked and on whom, next scheduled slot, runway (days scheduled ahead). Times in ET with a label.
