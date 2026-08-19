---
title: Status & Open Items
type: status
updated: 2026-06
tags: [status, dashboard, open-items]
---
# Status & Open Items

> [!info] Snapshot
> Charter at **v3.1.2**. Preregistration at **draft v1.1 — lock-ready pending the Phase 0 pilot report**. Tracker at **v1.1.1 — all 12 indexes live; gate verified CLEAN**. Critical path: run the Phase 0 pilot → lock the preregistration → begin Phase 1. See [[Home]].

## Resolved

- **C.6** — citation error in charter reference [18] corrected (Mazza, Cola & Tesconi 2022; the Avvenuti/Cresci conflation removed). → [[Project Knowledge Base v3.1.2]] Appendix A / Appendix C
- **C.1** — web-corpus denominator replaced with cited Common Crawl statistics (>300B cumulative; ~2.44B per monthly snapshot). → charter footnote 2 / C.1
- **C.4** — Tier 1 nation-state budget replaced with documented IO figures (IRA/Project Lakhta ~$1.25M/month ≈ $15M/yr; aggregate ~€1.5B/yr). → charter footnote 7 / C.4
- **C.3** — adversary-tier framework retained as an original taxonomy, now grounded top and bottom. → charter C.3
- **IV6 (Source Apportionment)** — locked: central prediction confirmatory in a focused sub-experiment; full crossing exploratory. → [[OSF Preregistration v1.1]] §4.1
- **Dose floor** — retained at 0.001% (the C.1 correction concerned the web-fraction denominator, not the controlled entity-token fraction). → [[OSF Preregistration v1.1]] §4.1, §5.5
- **WARP retrieval-layer paper** — evaluated and excluded as out of scope (retrieval/RAG layer, not training-corpus); reserved for an abstract scope-distinction and an H5-discussion cross-reference. → charter session log (6)

## Resolved — tooling

- [x] **Containerized** — `Dockerfile`, `docker-compose.yml`, `run-monitor.ps1` (enriched: snapshot drift detection + Obsidian pivot-table report), persistent `./io` bind mount. → [[Corpus Presence Tracker]]
- [x] **Gate hardening** (`--gate`, non-zero exit, `--list-indexes`, mutual exclusion) — v1.1. → [[Corpus Presence Tracker]]
- [x] **Index sync (v1.1.1, 2026-06-25)** — dead `v4_dolmasample_olmo` replaced with full `v4_dolma-v1_7_llama`; 4 missing CC snapshots added (-08/-18/-26/-30); all 12 indexes confirmed live; gate passed CLEAN on `synth.csv`; real anchors confirmed positive. → [[Corpus Presence Tracker]]
- [x] **Monthly monitor running** — `IIP-CC-Monitor` Task Scheduler job on Windows desktop (next run 2026-06-29 03:00); test runs confirmed; longitudinal signal logging (`news-pravda.com` rising to 3,753 in cc-2025-30). → `4 - Tooling/Monitor Reports/`

## Open — pilot-dependent (close at end of Phase 0)

- [ ] **Final entity count** per condition — set by the pilot variance estimate (target n=20). → [[Phase 0 Pilot Protocol]] O2
- [ ] **Subject-model size set** for Phase 1 — confirmed by pilot feasibility. → [[Phase 0 Pilot Protocol]] O4

## Open — ongoing maintenance

- [ ] **CC index refresh** — snapshot IDs go stale ~monthly; the monitor script auto-detects new snapshots via `known-snapshots.txt` and logs a warning; update `CC_INDEXES` in `corpus_presence_tracker.py` and rebuild the image when new crawls appear.
- [ ] **Image tag parity** — image is tagged `1.1`; script inside is v1.1.1. Rebuild with `docker build -t corpus-presence-tracker:1.1.1 .` and update tag in `run-monitor.ps1` and `docker-compose.yml` when convenient. Non-blocking.
- [ ] **Scheduler LastResult=1** — benign PowerShell pipeline artifact (`*>&1 | Tee-Object`); actual run output is clean. Non-blocking.

## Next physical action

Execute the ~40 GPU-hour Phase 0 sweep on the Windows desktop per [[Phase 0 Pilot Protocol]]. The pilot report (variance estimate, dose-floor branch, model-size feasibility) is the immediate input to locking [[OSF Preregistration v1.1]].
