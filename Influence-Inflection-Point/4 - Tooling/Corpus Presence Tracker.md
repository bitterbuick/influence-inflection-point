---
title: Corpus Presence Tracker
type: tool
status: patched v1.1 — fixes applied; confirm live CC index IDs on your machine
tags: [tooling, infini-gram, corpus, validation]
---
# Corpus Presence Tracker

> [!info] Navigation
> Script file → `corpus_presence_tracker.py` (this folder). Used by → [[Phase 0 Pilot Protocol]] (objective O1). Referenced by → [[Project Knowledge Base v3.1.2]] §5.5. Vault [[Home]] · [[Status & Open Items]].

A dependency-light collector built on the **infini-gram** and **infini-gram-mini** exact-match search engines. It measures how often entities (and optional favorable-context phrasings) appear in (a) the open **pretraining** corpora behind the transparent subject models (Pile → Pythia; Dolma → OLMo; plus RedPajama, C4) and (b) successive **Common Crawl** snapshots, for longitudinal in-the-wild monitoring.

## What it does for the experiment

- **Zero-presence gate (§5.5 / pilot O1):** confirm a synthetic entity has count == 0 across corpora *before* an injection run.
- **Baseline anchor (C.1):** real-entity occurrence counts to anchor what a 0.001%–10% dose corresponds to against organic frequency.
- **Laundering-in-the-wild monitor:** longitudinal Common Crawl counts for named domains / narratives.

## Usage

```bash
python3 corpus_presence_tracker.py --init                      # write entities.csv template
python3 corpus_presence_tracker.py --list-indexes              # probe indexes + show current-list source
python3 corpus_presence_tracker.py --entities synth.csv --gate # zero-presence gate (exits non-zero if contaminated)
python3 corpus_presence_tracker.py --entities watch.csv --cc-only      # wild-web monitor
python3 corpus_presence_tracker.py --entities entities.csv --pretrain-only
python3 corpus_presence_tracker.py --entities entities.csv --dry-run   # no network
```

Output: timestamped `<run>.csv` and `<run>.jsonl` under `--out`, ready to version in Git and ingest into the Obsidian/Zotero pipeline. Only requires `requests`.

## Review status (2026-06) — patched v1.1

Passes syntax (Python 3.12) and the offline `--init` / `--dry-run` / `--list-indexes` paths; logic, retry/backoff, and the n-gram-vs-document caveat are sound.

> [!check] Applied in `corpus_presence_tracker.py` (v1.1)
> - **`--gate`** — zero-presence gate: exits **non-zero** if any synthetic entity is found present (exit 2 = contaminated, 3 = inconclusive/errored, 0 = clean), so contamination cannot pass silently.
> - **`--list-indexes`** — probes every configured index for liveness and prints where to get the current snapshot IDs.
> - **`--cc-only` / `--pretrain-only`** are now mutually exclusive (argparse-enforced).
> - **Dolma-sample warning** — runtime note that `v4_dolmasample_olmo` covers only a sample.

> [!warning] Still to confirm on your machine (needs the live API)
> Refresh the **current Common Crawl snapshot IDs** in `CC_INDEXES` — run `--list-indexes`, then copy the current IDs from the infini-gram docs. The live API contract and current index names could not be verified from the build environment, so confirm them before the first real run.

## Docker (reproducible runs)

The tracker ships with a `Dockerfile` so it can be built once and run anywhere with a pinned runtime. Build context is this folder; `.dockerignore` keeps it to the script + `requirements.txt`.

```bash
# build
docker build -t corpus-presence-tracker:1.1 .

# check indexes (probes the live API)
docker run --rm -v "${PWD}/io:/data" corpus-presence-tracker:1.1 --list-indexes

# zero-presence gate (exits non-zero on contamination)
docker run --rm -v "${PWD}/io:/data" corpus-presence-tracker:1.1 --entities entities/synth.csv --gate

# Common Crawl monitor (wild-web)
docker run --rm -v "${PWD}/io:/data" corpus-presence-tracker:1.1 --entities entities/watchlist.csv --cc-only
```

Or with compose: `docker compose run --rm tracker --entities entities/synth.csv --gate`.

**Persistence.** Everything under `./io` on the host is bind-mounted to `/data`, so entities CSVs and all run artifacts survive container removal and stay visible on the host for Git/Obsidian. `WORKDIR` is `/data`, so paths are relative to `./io` (`entities/synth.csv`, `runs`). A named-volume alternative is documented in `docker-compose.yml` for host-invisible portable storage.

**Pull and run anywhere.** Tag and push to a registry, then pull on any host:
```bash
docker tag corpus-presence-tracker:1.1 ghcr.io/<you>/corpus-presence-tracker:1.1
docker push ghcr.io/<you>/corpus-presence-tracker:1.1
docker run --rm -v "${PWD}/io:/data" ghcr.io/<you>/corpus-presence-tracker:1.1 --list-indexes
```

**Reproducibility.** `requirements.txt` pins `requests`; the base is pinned to `python:3.12-slim-bookworm`. For bit-for-bit builds, pin the base by digest (`@sha256:…`) per the Dockerfile note. **Scheduling.** `run-monitor.ps1` wraps a `docker run` of the monitor for Windows Task Scheduler (monthly); it omits `--gate` so the job never fails on a hit.

> [!note] Linux bind-mount permissions
> The image runs as uid 10001. On Windows Docker Desktop bind mounts just work. On Linux, if writes to `./io` fail, either `chown` the host dir or add `--user "$(id -u):$(id -g)"` to the run.

## Caveats (interpretation)

Counts are n-gram occurrence counts under each index's tokenizer — **not** deduplicated document counts, and not comparable in absolute terms across corpora of different size. Use for presence/absence, within-corpus relative comparison, and over-time trends. Common Crawl presence ≠ inclusion in any given model's training data. The DV1–DV4 instruments remain the measurement of record.
