---
title: Pilot Pipeline
type: tooling
updated: 2026-11-16
tags: [pilot, phase-0, tooling]
---
> [!info] Navigation
> Implements [[Phase 0 Pilot Protocol]] §3 · Status in [[Phase 0 Pilot Readiness]] · Shakedown results in [[Desktop Shakedown 2026-11-16]]

# Pilot pipeline

Code that takes one pilot run from a base corpus to scored outcome measures. It is built and tested. It has **not** produced pilot data: the registered instruments do not exist yet, so every run so far used the fixtures in `placeholders/`.

## What each file does

| File | Job |
| --- | --- |
| `sample_corpus.py` | Draws the seeded 100-million-token base corpus (C4 or the Pile backup). Writes a manifest. |
| `tokenize_corpus.py` | Converts a corpus to a token store once, so each run loads it in seconds. Also builds the small held-out text used for the before/after loss check. |
| `pilot_lib.py` | The token store and the dose mixer. No model code. |
| `run_one.py` | One run: mix, fine-tune, elicit, score, record. Restartable at every stage. |
| `run_queue.py` | Runs a list of runs unattended, one process per run. |
| `analyze.py` | Collects finished runs into `runs.csv` and `summary.md`, with each measure also shown against the zero-dose run. |
| `make_placeholder_injection.py` | Stock favorable text for testing. Not the study's generator. |
| `bench_finetune.py` | The throughput benchmark of 2026-11-15. |

## How to run

```
python tokenize_corpus.py --corpus <data>/pile/corpus.jsonl --out <data>/pile/store
python tokenize_corpus.py --heldout pile --out <data>/pile/heldout
python run_queue.py --plan plan.json --runs-dir runs
python analyze.py --runs-dir runs --out-dir summary
```

`plan.json` holds a `defaults` block and a `runs` list. Each run needs `run_id`, `dose`, `base_store` and `heldout_store`; everything else can sit in `defaults`. `run_one.py` refuses to start without a learning rate and a sentiment classifier, because both are design decisions.

**Pause and resume.** Create an empty file named `STOP` in the runs directory. The current run writes a checkpoint within 50 training steps and exits; the queue stops. Delete `STOP` and run the same command to continue. The same command also recovers from a crash or a reboot, from the last hourly checkpoint.

## What a run records

`mix.json` (which injected documents, both dose figures, a SHA-256 of the exact token stream), `train_log.jsonl` (loss, learning rate and speed every 50 steps), `set_a.jsonl` (every continuation with its sentiment score), `set_c.jsonl`, `set_d.jsonl`, and `result.json` (configuration, software versions, held-out loss before and after, summary measures, hashes of the instrument files).

## Implementation choices that need the author's confirmation

These were made to get a working pipeline. Each one affects results, so each belongs in the preregistration or must be changed.

1. **Injected text replaces base text.** Every run trains on the same number of document tokens. At dose *d*, the run holds *d* × total injected tokens and (1 − *d*) × total base tokens. The alternative is to add injected text on top of a fixed base, which makes high-dose runs longer.
2. **Injected sets are nested.** Under one seed, the documents used at a low dose are a subset of those used at every higher dose. Doses then differ by added documents only. The alternative, an independent draw per dose, adds draw-to-draw noise to the dose-response curve.
3. **Injected documents are taken whole.** The achieved dose can differ from the requested dose by up to half a document. Both are recorded. At 0.001% of 100 million tokens the set is two or three documents.
4. **Injected documents are scattered at random** among base documents, each followed by an end-of-text token, then cut into 1,024-token blocks trained in a seeded random order.
5. **One pass over the corpus**, AdamW, a short warmup then a constant learning rate, gradient clipping at 1.0, mixed precision, batch of 3. The learning rate has no default.
6. **Weights are discarded after scoring.** A Pythia 1B checkpoint is about 4 GB; 56 of them do not fit on the desktop. Setting `keep_model` to `fp16` keeps a 2 GB copy per run. If weights are discarded, any measure added later needs the run repeated.
7. **DV1** scores the first sentence of each continuation with the classifier named in the configuration, as P(positive) − P(negative). Reported for the target entity, for a never-injected control entity on the same model, and (in `analyze.py`) against the same entity on the zero-dose model.
8. **DV3** is read as a forced choice: the stem names both entities and stops where one name would follow, and the model's log-probability of each name is compared. Both name orders are scored. The preregistration wording ("identical assessments differing only in entity name") admits another reading, in which the probability of a fixed assessment is compared under each name.
9. **DV4** applies Min-K%++ [1] to the tokens that follow the entity name, with *k* = 20%, and reports favorable minus neutral phrasing. The plain mean log-probability is recorded beside it.

Set D needs two columns the guidelines' file format does not have: `pair` and `role` (`favorable` or `neutral`). See `placeholders/PLACEHOLDER_set_d.csv`.

## Known limits

- Runs on the AMD card are not bit-reproducible. Seeds fix the data, the order and the sampling draws, but not the floating-point path through the graphics driver.
- An hourly checkpoint is about 12 GB (weights plus optimizer state). Over 334 hours of training that is roughly 4 TB written to the desktop's drive.
- The mixed-effects model and power calculation of protocol §3.6 are not written. `analyze.py` is descriptive only.
- The two entity names in the fixtures are the public worked examples. They differ in token count, which by itself moves DV3. Real pairs must be matched, as [[Evaluation Prompt Guidelines]] §7 says.

## References

[1] J. Zhang et al., "Min-K%++: Improved Baseline for Detecting Pre-Training Data from Large Language Models," in *Proc. ICLR*, 2025.
