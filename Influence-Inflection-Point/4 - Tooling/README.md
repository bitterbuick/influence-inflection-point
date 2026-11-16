# Corpus Presence Tracker — Docker runbook

Reproducible, dependency-light runner for `corpus_presence_tracker.py` (v1.1) built on the
**infini-gram** (`api.infini-gram.io`, pretraining corpora) and **infini-gram-mini**
(`api.infini-gram-mini.io`, Common Crawl + DCLM) read-only exact-match count APIs.

It supports the Phase 0 pilot (objective **O1**): a zero-presence gate for synthetic entities,
baseline anchor counts for real reference-class entities, and a longitudinal Common-Crawl
"laundering-in-the-wild" monitor. See `Corpus Presence Tracker.md` and `Phase 0 Pilot Protocol.md`.

> No API key is required. The tool only ever **reads** (HTTP POST `count` queries) from the two
> infini-gram APIs — it never posts content to the live web (charter §7.3).

---

## 1. Build

Build context is **this folder** (`4 - Tooling`). `.dockerignore` keeps the image to just the
script + `requirements.txt` (which pins `requests==2.32.3`); base is `python:3.12-slim-bookworm`,
runs as non-root uid 10001.

```powershell
cd "4 - Tooling"
docker build -t corpus-presence-tracker:1.1 .
```

## 2. Persistence — the `./io` bind mount

Everything lives on the host under `./io`, bind-mounted to `/data` in the container, which is the
`WORKDIR`. **Never bake data into the image.** Container paths are relative to `./io`:

```
io/
  entities/        inputs  (synth.csv, watchlist.csv, anchor.csv, …)
  runs/            outputs (timestamped <run>.csv + <run>.jsonl)  — version these in Git
  logs/            scheduled-monitor logs (monitor-<stamp>.log)
```

All run artifacts survive container removal and are visible on the host for Git/Obsidian/Zotero.
On Windows Docker Desktop bind mounts just work; on Linux, if writes to `./io` fail, add
`--user "$(id -u):$(id -g)"` (the image runs as uid 10001).

The `${PWD}/io` form in the docs assumes your shell is in this folder. The examples below use an
explicit absolute path so they work from anywhere:

```powershell
$Io = "<...>\Influence-Inflection-Point\4 - Tooling\io"
```

## 3. Run

```powershell
# Probe every configured index for liveness + show where current CC IDs are published
docker run --rm -v "${Io}:/data" corpus-presence-tracker:1.1 --list-indexes

# Pre-experiment validation (no network) — prints payloads, writes CSV/JSONL
docker run --rm -v "${Io}:/data" corpus-presence-tracker:1.1 --entities entities/synth.csv --dry-run

# Pretraining corpora only (subject-model data: Pile, Dolma, RedPajama, C4)
docker run --rm -v "${Io}:/data" corpus-presence-tracker:1.1 --entities entities/synth.csv --pretrain-only

# Common Crawl / DCLM only (wild-web monitor)
docker run --rm -v "${Io}:/data" corpus-presence-tracker:1.1 --entities entities/watchlist.csv --cc-only

# Baseline anchors for real reference-class entities (C.1)
docker run --rm -v "${Io}:/data" corpus-presence-tracker:1.1 --entities entities/anchor.csv --pretrain-only
```

`--cc-only` and `--pretrain-only` are mutually exclusive (argparse-enforced). With neither, both
sets are queried. Compose equivalent: `docker compose run --rm tracker <args>` (mounts `./io`).

## 4. The zero-presence GATE (run manually before every fine-tuning run)

Run this against the synthetic-entity set **before any injection / fine-tuning run**. It exits
**non-zero on contamination**, so a tainted entity cannot pass silently (Phase 0 O1):

```powershell
docker run --rm -v "${Io}:/data" corpus-presence-tracker:1.1 --entities entities/synth.csv --gate
echo $LASTEXITCODE
```

| Exit code | Meaning | Action |
|-----------|---------|--------|
| **0** | Clean — no synthetic entity present in any queried corpus | Safe to proceed |
| **2** | Contamination — a synthetic entity returned count > 0 | Replace the entity before any run |
| **3** | Inconclusive — a synthetic-entity query errored (API down / bad index) | Re-run after the API recovers; do **not** treat as clean |

`--gate` is intentionally **not** scheduled — a gate must block a human action, not run unattended.
It is also ignored under `--dry-run` (exits 0, since there are no real counts to evaluate).

## 5. Scheduled monitor (Windows Task Scheduler)

`run-monitor.ps1` runs the container with `--cc-only` against `entities/watchlist.csv`, writes
artifacts to `io/runs` and a transcript to `io/logs`. It **omits `--gate`** on purpose so the
scheduled job never fails on a hit.

Registered task: **`IIP-CC-Monitor`**, current user, interactive token (no stored password, no
elevation).

> **Cadence (checked on the machine 2026-11-15).** The registered trigger is weekly, every Monday,
> start boundary `2026-06-24T02:00:00-08:00`, no end boundary. This section originally described a
> monthly trigger; that description was wrong. A weekly trigger with no end boundary does not catch
> up after the machine was off at the scheduled time.

> **The image went missing (found 2026-11-15).** `docker images corpus-presence-tracker` returned
> nothing on the desktop, so every scheduled run after 2026-08-10 failed without writing a log or a
> run file. The task still reported a last run on 2026-11-09. The image was rebuilt on 2026-11-15
> with `docker compose build`, and `--list-indexes` then showed all 12 indexes live. The script
> should check that the image exists and exit non-zero when `docker run` fails.

> **What this monitor can and cannot show.** Every run queries the same pinned snapshot list in
> `CC_INDEXES`. Published snapshots do not change, so repeated runs return identical counts
> (the 2026-06-25, 2026-07-06 and 2026-08-10 reports are the same table). The series only grows
> when a new snapshot ID is added to `CC_INDEXES`. The drift check in `run-monitor.ps1` cannot
> detect new snapshots either: it calls `--list-indexes`, which prints the pinned list, and
> compares that list with itself. For a series that extends on its own, use the hosted-page
> counter in section 8, which reads Common Crawl's published crawl list directly.

```powershell
# inspect / test / change cadence
Get-ScheduledTask     -TaskName "IIP-CC-Monitor"
Get-ScheduledTaskInfo -TaskName "IIP-CC-Monitor"   # LastRunTime / LastTaskResult (0 = success)
Start-ScheduledTask   -TaskName "IIP-CC-Monitor"   # run once now (test)
Unregister-ScheduledTask -TaskName "IIP-CC-Monitor" -Confirm:$false   # remove

# change cadence without re-registering (e.g. 15th of each month at 02:30):
$t = New-ScheduledTaskTrigger -Daily -At 2:30am   # placeholder; edit StartBoundary/DaysOfMonth
# easiest: re-run the registration block in the project notes with new <DaysOfMonth>/<StartBoundary>,
# or edit the trigger in taskschd.msc → IIP-CC-Monitor.
```

The task was created from a Task Scheduler XML definition (a true calendar-monthly trigger;
`New-ScheduledTaskTrigger` has no native monthly option). To change the schedule, edit the
`<ScheduleByMonth>` (`<DaysOfMonth>`) and `<StartBoundary>` time in that XML and re-register, or
adjust it interactively in `taskschd.msc`.

## 6. Indexes (refreshed 2026-06-24, all verified live)

Index IDs are pinned at the top of `corpus_presence_tracker.py` and go stale (~monthly for CC).
Re-check with `--list-indexes`; current lists are published at `infini-gram.io` /
`infini-gram-mini.io` (and their readthedocs API pages).

**Pretraining (`PRETRAIN_INDEXES`, api.infini-gram.io):**

| Friendly | Index ID | Notes |
|----------|----------|-------|
| pile_train | `v4_piletrain_llama` | Pythia's corpus |
| dolma | `v4_dolma-v1_7_llama` | OLMo — **full Dolma v1.7** (was the now-removed `v4_dolmasample_olmo`) |
| redpajama | `v4_rpj_llama_s4` | |
| c4_train | `v4_c4train_llama` | |

**Common Crawl + DCLM (`CC_INDEXES`, api.infini-gram-mini.io):**

`v2_cc-2025-05`, `v2_cc-2025-08`, `v2_cc-2025-13`, `v2_cc-2025-18`, `v2_cc-2025-21`,
`v2_cc-2025-26`, `v2_cc-2025-30`, and `v2_dclm_all` (dclm_baseline).

> **Updating CC IDs:** new crawls release ~monthly. Run `--list-indexes`, copy the current IDs
> from infini-gram-mini's docs, and add/replace rows in the `CC_INDEXES` dict, then rebuild.

**Request/response contract** (verified): `POST {index, query_type:"count", query}` →
`{"count": <int>, …}`. The script reads `count` (and `approx` if present).

## 7. Interpretation caveats

A count for a domain string such as `news-pravda.com` is a **mention** count. It includes every
page that writes the domain name, including news reports and fact-checks about it, and it is not
adjusted for snapshot size. It does not measure how much content the domain contributed to a
crawl. Use section 8 for that, and report the two series separately.


Counts are **n-gram occurrence counts** under each index's tokenizer — not deduplicated document
counts, and not comparable in absolute terms across corpora of different size. Use them for
presence/absence, within-corpus relative comparison, and over-time trends. Common Crawl presence
≠ inclusion in any given model's training data. The DV1–DV4 instruments remain the measurement of
record.

## 8. Hosted-page counter (`cc_host_presence.py`)

Counts the pages Common Crawl fetched **from** a domain and its subdomains in each crawl, using the
crawl's own URL index on `data.commoncrawl.org`, and divides by the crawl's total page count
(Common Crawl crawl statistics). No API key. Read-only GET requests.

```powershell
# every published crawl since 2024-10, for the domain rows in the watchlist
docker compose run --rm hosted --entities entities/watchlist.csv --all-since 2024-10

# named domains and crawls
docker compose run --rm hosted --domains news-pravda.com --crawls CC-MAIN-2025-05 CC-MAIN-2025-30

# list published crawl ids
docker compose run --rm hosted --list-crawls
```

Without Docker: `python3 cc_host_presence.py ...` (needs only `requests`).

Output goes to `io/runs/hosted_<runid>.csv` and `.jsonl`. Columns:

| Column | Meaning |
|--------|---------|
| `captures_all` | every index record on the domain, any HTTP status |
| `pages_200` | successful fetches |
| `distinct_urls_200`, `distinct_digests_200` | distinct URLs and distinct content hashes among those |
| `hosts_200` | distinct hostnames (subdomains) with at least one successful page |
| `crawl_pages` | Common Crawl's page total for the crawl |
| `pages_per_million` | `pages_200 / crawl_pages × 1e6` |

The `.jsonl` adds a per-hostname breakdown. Rows of type `narrative` in an entities file are
skipped: a phrase has no URL.

`data.commoncrawl.org` throttles with HTTP 503. The tool retries with backoff, so a crawl can take
a minute or two, and it saves after each crawl. Rerun any crawl that ends with an error.

Tests (offline, synthetic index): `python -m pytest tests -q`.

**Caveats.** A capture count is what Common Crawl fetched, not what the site published; each crawl
gives every host a page budget set by Common Crawl's own ranking and sampling. Normalising by crawl
size removes snapshot-size differences and nothing else. Common Crawl presence ≠ inclusion in any
model's training data.
