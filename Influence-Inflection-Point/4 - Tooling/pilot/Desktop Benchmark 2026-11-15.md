---
title: Desktop Benchmark 2026-11-15
type: report
date: 2026-11-15
tags: [pilot, phase-0, benchmark, compute]
---
> [!info] Navigation
> Script → `bench_finetune.py` (this folder) · Answers the sufficiency test in [[Phase 0 Pilot Readiness]] §0 · [[Status & Open Items]]

# Desktop Benchmark

**Result.** The Windows desktop can run the pilot. Full fine-tuning of Pythia 1B works on its AMD graphics card, fits in memory at a batch of three sequences, and trains at about 4,660 tokens per second. One pass over a 100-million-token corpus takes about 6.0 hours, so the 56-run baseline plan is about 334 hours of training. The margin on memory is thin, and one setting choice cuts the speed by more than half.

This was a throughput and sanity check on ordinary text. It is not a pilot run and it tested no hypothesis.

## 1. Setup

| | |
| --- | --- |
| Machine | Windows 11 Pro desktop, AMD Ryzen 9 3900X, 32 GB RAM |
| Graphics card | AMD Radeon RX 7900 XTX, 24 GB |
| Driver | AMD Software 26.8.1 (AMD's install notes ask for 26.2.2; the newer driver worked) |
| Software | Python 3.12, PyTorch 2.9.1 built for ROCm 7.2.1, installed from AMD's wheels into an isolated environment at `C:\Users\Adam\research\iip-pilot-bench\.venv` |
| Model | `EleutherAI/pythia-1b`, 1,011.8 million parameters, all weights trained |
| Text | C4 (English), streamed; sequences of 1,024 tokens |
| Optimizer | AdamW, learning rate 1e-5 (a benchmark setting, not a design choice) |

OpenCTI was stopped for the runs and restarted afterwards. With it running the machine had under 2 GB of free RAM.

## 2. Results

Timing excludes the first 20 steps of each run.

| Run | Precision | Batch | Steps | Seconds per step | Tokens per second | Peak GPU memory (GB) | Held-out loss before → after | Hours per 100M tokens |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| `fp32_bs2` | 32-bit | 2 | 120 | 2.025 | 1,011 | 19.77 | 2.7879 → 2.8293 | 27.5 |
| `bf16_bs4` | mixed, bfloat16 | 4 | 100 | 2.000 | 2,048 | 24.16 | 2.7880 → 2.7855 | 13.6 |
| `fp16_bs4` | mixed, float16 | 4 | 100 | 1.957 | 2,093 | 24.16 | 2.7879 → 2.7864 | 13.3 |
| `bf16_bs3` | mixed, bfloat16 | 3 | 80 | 0.659 | 4,662 | 22.35 | 2.7880 → 2.7955 | 6.0 |

Raw result files and logs are on the desktop in `C:\Users\Adam\research\iip-pilot-bench\`.

## 3. What the runs show

1. **It works.** Every run finished with finite losses and coherent generated text. `torch.cuda.is_available()` is true and the card is reported by name.
2. **Memory matches the estimate.** Plain 32-bit training peaked at 19.8 GB at batch 2, consistent with the roughly 16 GB fixed cost estimated in the readiness note plus activations.
3. **Mixed precision is required.** 32-bit training is 4.6 times slower per token than mixed precision at batch 3.
4. **Batch 4 is a trap.** At batch 4 the peak (24.16 GB) exceeds the card's 24 GB, Windows spills into shared system memory, and speed drops to under half of batch 3. Batch 3 is the largest setting that stays on the card.
5. **bfloat16 and float16 agree.** At matched steps their training losses differ by 0.002 or less (step 10: 2.9288 and 2.9308; step 20: 2.8975 and 2.8984). The three precisions give the same starting held-out loss to four decimals. That is evidence against a silent numerical fault in the bfloat16 path on this card. It is not a comparison with an NVIDIA reference.

## 4. Projection for the baseline plan

At 4,662 tokens per second, with one pass over the corpus per run:

| | |
| --- | --- |
| One 100M-token run | 5.96 hours |
| 56 runs (40 on the Pile backup, 16 on C4) | 334 hours |
| Running around the clock | about 14 days |
| Running 10 hours a night | about 34 nights |

For comparison, the charter's estimate for a rented A100 is 2 to 5 hours per run: 112 to 280 hours for 56 runs, $56 to $697 at the charter's quoted rates.

## 5. Limits of this benchmark

- **Short.** 60 to 100 timed steps per run. Heat and sustained-load behaviour over many hours were not tested.
- **Thin memory margin.** Batch 3 leaves about 0.6 GB on the card. Anything else that uses the graphics card during a run (a game, video playback) will push training into shared memory and roughly halve its speed, as batch 4 showed.
- **Training only.** The projection leaves out generating the injected text, sampling answers to the evaluation prompts, scoring, and loading or saving models.
- **One pass assumed.** The number of passes over the corpus and the learning rate are not yet decided. Two passes doubles the time.
- **Disk.** A saved 32-bit copy of the model is about 4 GB. The desktop had 94 GB free on C: and 87 GB on D:. Keeping all 56 fine-tuned models (about 227 GB) will not fit; score each model and delete it, or store models elsewhere.
- **No cross-check against NVIDIA.** A cheap confirmation is to run this same script for a few minutes on a rented NVIDIA card with the same seed and compare losses step by step.

## 6. Reading against the sufficiency test

| Condition | Outcome |
| --- | --- |
| Memory | Passes at batch 3 with mixed precision. Fails at batch 4. |
| Software | Passes this check. Cross-check against NVIDIA still advisable. |
| Time | 334 hours for 56 runs. Whether that is acceptable is the author's call. |

## 7. How to rerun

```powershell
cd C:\Users\Adam\research\iip-pilot-bench
.\.venv\Scripts\python.exe bench_finetune.py --precision amp --amp-dtype bf16 --batch-size 3 --steps 80 --out bf16_bs3.json
```

Stop OpenCTI first (`C:\Users\Adam\scripts\opencti.ps1 -Action down`).
