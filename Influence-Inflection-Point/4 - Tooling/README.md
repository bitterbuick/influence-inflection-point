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

## 5. Scheduled monthly monitor (Windows Task Scheduler)

`run-monitor.ps1` runs the container with `--cc-only` against `entities/watchlist.csv`, writes
artifacts to `io/runs` and a transcript to `io/logs`. It **omits `--gate`** on purpose so the
scheduled job never fails on a hit.

Registered task: **`IIP-CC-Monitor`** — monthly, 1st of each month at 03:00, current user,
interactive token (no stored password, no elevation).

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

Counts are **n-gram occurrence counts** under each index's tokenizer — not deduplicated document
counts, and not comparable in absolute terms across corpora of different size. Use them for
presence/absence, within-corpus relative comparison, and over-time trends. Common Crawl presence
≠ inclusion in any given model's training data. The DV1–DV4 instruments remain the measurement of
record.
