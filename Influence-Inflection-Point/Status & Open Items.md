---
title: Status & Open Items
type: status
updated: 2026-11-15
tags: [status, dashboard, open-items]
---
# Status & Open Items

> [!info] Snapshot
> Charter at **v3.1.2**. Preregistration at **draft v1.1 — not registered; cannot lock until the Phase 0 pilot report exists**. Tracker at **v1.1.1** (gate passed 2026-06-25 on two names that are now public; see below). Hosted-page counter at **v0.1.0**. Critical path: settle the pilot design gaps → build the pilot → run it → lock the preregistration → begin Phase 1. See [[Home]].

> [!warning] State of evidence (2026-11-15)
> No hypothesis (H1 to H5) has been tested. No model has been fine-tuned. The project has a design, two measurement tools, and one descriptive data series. Do not describe the study as preregistered until the registration is submitted on OSF.

## Corrections (2026-11-15)

- **"Pre-registered" on the June 2026 poster is wrong.** The preregistration is a draft. Corrected poster: `Attachments/poster/`.
- **"Step change = coordinated push" on the poster is withdrawn.** The series was a text-mention count, not adjusted for snapshot size, and it does not track pages hosted on the domain. → [[Pravda Measure Rebuild 2026-11]]
- **The "longitudinal" monitor collected no new data after 2026-06-25.** Every run queried the same seven 2025 snapshots, which do not change. The scheduled runs that failed to fire in July and August lost nothing. → `4 - Tooling/README.md` §5
- **The synthetic names are public.** "Kaltrex Aerospace" and "Maridia Pharma" have been in this public repository since 2026-08-19 and no longer meet the zero-web-presence gate. Use fresh, unpublished names for the pilot and Phase 1. → [[Phase 0 Pilot Readiness]] §5
- **The ~40 GPU-hour pilot estimate conflicts with the protocol's run count.** → [[Phase 0 Pilot Readiness]] §3.1

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
- [x] **Scheduled monitor registered** — `IIP-CC-Monitor` Task Scheduler job on Windows desktop; scheduled runs on record: 2026-07-06 and 2026-08-10. *Superseded reading:* the note here formerly read "longitudinal signal logging (`news-pravda.com` rising to 3,753 in cc-2025-30)". That figure is a mention count for one fixed snapshot; see Corrections above. → `4 - Tooling/Monitor Reports/`
- [x] **Hosted-page counter (v0.1.0, 2026-11-15)** — `cc_host_presence.py` counts pages Common Crawl fetched from a domain, per crawl, per million crawl pages, from the public URL index; 33 offline tests; first run covers 32 crawls (2024-10 to 2026-43). → [[Pravda Measure Rebuild 2026-11]]

## Open — blocks the pilot

Full list with section references in [[Phase 0 Pilot Readiness]].

- [x] **Runs per dose** — decided 2026-11-15: one fine-tune per entity per dose. Baseline plan 56 runs (40 on the Pile backup, 16 on C4); 112 to 280 A100-hours, plan on 280. Full C4 sweep is a stretch goal.
- [x] **Machine** — decided 2026-11-15: the pilot runs on the desktop (about 4,660 tokens per second, about 334 hours for 56 runs); a rented GPU follows if the pilot looks good. → [[Desktop Benchmark 2026-11-15]]
- [ ] **Base corpus samples** — sampler written (`pilot/sample_corpus.py`); samples of C4 and the Pile backup to be drawn on the desktop and their manifests committed.
- [x] **Definition of dose** — decided 2026-11-15: document tokens, with name mentions per document fixed and both figures reported.
- [x] **Base fine-tuning corpus and prompt format** — decided 2026-11-15: seeded 100M-token samples of the Pile (backup) and C4; completion stems.
- [ ] **Preregistration edits that follow** — base corpus as a factor; IV1 reworded; sizes for prompt Sets B to D; generation settings, control definition, classifier.
- [ ] **Instruments** — 50-prompt evaluation set, entity fact bases, DV1 classifier choice, DV2 labeled set, DV3 and DV4 scoring. Author writes the prompts; rules in [[Evaluation Prompt Guidelines]].
- [ ] **Pilot code** — corpus generator, fine-tune script, scoring, analysis. None exists.
- [ ] **Fresh synthetic names**, kept out of this repository until the training data is frozen.
- [ ] **Web zero-presence check** (Google, Bing, Brave) — required by O1; no record exists.

## Open — pilot-dependent (close at end of Phase 0)

- [ ] **Final entity count** per condition — set by the pilot variance estimate (target n=20). → [[Phase 0 Pilot Protocol]] O2
- [ ] **Subject-model size set** for Phase 1 — confirmed by pilot feasibility. → [[Phase 0 Pilot Protocol]] O4

## Open — ongoing maintenance

- [ ] **CC index refresh** — snapshot IDs go stale ~monthly; the monitor script auto-detects new snapshots via `known-snapshots.txt` and logs a warning; update `CC_INDEXES` in `corpus_presence_tracker.py` and rebuild the image when new crawls appear.
- [ ] **Image tag parity** — image is tagged `1.1`; script inside is v1.1.1. Rebuild with `docker build -t corpus-presence-tracker:1.1.1 .` and update tag in `run-monitor.ps1` and `docker-compose.yml` when convenient. Non-blocking.
- [ ] **Scheduler LastResult=1** — benign PowerShell pipeline artifact (`*>&1 | Tee-Object`); actual run output is clean. Non-blocking.
- [x] **Monitor cadence** — confirmed on the machine 2026-11-15: weekly, Mondays, no end boundary. The monthly description was wrong and is corrected.
- [x] **Monitor image missing** — found 2026-11-15: the `corpus-presence-tracker` image was gone from the desktop, so no scheduled run after 2026-08-10 produced output. Rebuilt 2026-11-15.
- [ ] **Snapshot drift check cannot fire** — `run-monitor.ps1` compares the pinned index list with itself. Replace with `cc_host_presence.py --list-crawls`, or drop it.
- [ ] **Missed weekly starts are not caught up** — the trigger has no end boundary, so a run missed while the machine is off is skipped (diagnosed 2026-08-13; fix not confirmed applied).
- [ ] **`run-monitor.ps1` does not check `$LASTEXITCODE`** after `docker run`, and stamps local time with a `Z` suffix in log names.
- [x] **Container changes tested** — built on the desktop 2026-11-15; `tracker --list-indexes` and `hosted --list-crawls` both ran.

## Next physical action

Decide the four design points in [[Phase 0 Pilot Readiness]] §3, then time one short Pythia 1B fine-tune on the machine that will run the pilot. The sweep itself cannot start until the pilot code and instruments exist. The pilot report (variance estimate, dose-floor branch, model-size feasibility) remains the input to locking [[OSF Preregistration v1.1]].
