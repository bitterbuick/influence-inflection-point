---
title: Phase 0 Pilot Readiness
type: status
updated: 2026-11-15
tags: [pilot, phase-0, readiness, open-items]
---
> [!info] Navigation
> Checks [[Phase 0 Pilot Protocol]] against what exists in this vault · Parent → [[Project Knowledge Base v3.1.2]] · [[Status & Open Items]]

# Phase 0 Pilot Readiness

**Bottom line.** The pilot cannot start yet. The protocol is written, but the vault holds none of the code or instruments the protocol calls for, and four design points are still undecided. The ~40 GPU-hour figure also does not match the run count in the protocol. This note lists each gap and the decision it needs.

Nothing here changes the design. Every open point below is a decision for the author.

## 0. Decisions recorded 2026-11-15

| Point | Decision | Consequence |
| --- | --- | --- |
| Runs per dose (§3.1) | **Separate.** One fine-tune per entity per dose. The author prefers too much data to too little. | See the run plan below. |
| Base corpus (§2 item 4) | **Two corpora**, each a seeded 100-million-token sample: the Pile and C4. | The original Pile was taken down in 2023 over its Books3 component. The Pile arm uses the `pile-uncopyrighted` backup on Hugging Face, which omits the infringing subsets, and the write-up must say so. Both corpora are covered by the tracker's gate (`pile_train`, `c4_train`). Base corpus becomes a design factor and needs a line in the preregistration. |
| Definition of dose (§3.3) | **Document tokens.** Dose is the share of fine-tuning tokens that sit in injected documents. | Fix the number of name mentions per injected document and record it. Report the name-token dose beside the document-token dose for every run. With mentions fixed the two differ by a constant, so no extra runs are needed. The preregistration wording for IV1 should be changed to say this. |
| Prompt format (§3.4) | **Completion stems.** Both corpora are plain documents and Pythia is a base model. | As assumed in [[Evaluation Prompt Guidelines]]. |
| Machine (§3.2) | **Desktop if sufficient, otherwise rented.** OpenCTI on the desktop yields to pilot runs. | Sufficiency test below. |
| Instruments (§2 items 6 to 9) | **Author writes them**, following [[Evaluation Prompt Guidelines]]. | Set A (50 stems) first. |

**Run plan (baseline).** The lower-cost option was chosen, with the fuller designs held as stretch goals.

| Arm | Corpus | Entities × doses | Runs |
| --- | --- | --- | --- |
| Full sweep | Pile (backup) | 5 × 8 | 40 |
| Reduced sweep | C4 | 2 × 8 | 16 |
| **Total** | | | **56** |

At the charter's 2 to 5 hours per run on an A100 80GB, 56 runs are **112 to 280 GPU-hours**. Plan on 280 until a timed run replaces the estimate. At the charter's quoted A100 rates of $0.50 to $2.49 per hour (§7.2, reference [27], March 2026), 280 hours is $140 to $697.

The Pile was taken as the full-sweep corpus because it is Pythia's own training data, so the least change comes from anything other than the injection. This choice was recommended, not explicitly confirmed; swap the arms if C4 is preferred.

**Stretch goals, if funding is secured.**

1. Full sweep on C4 as well (24 more runs, 80 in total, 160 to 400 GPU-hours).
2. Name density as its own factor: vary name mentions per document at fixed volume, to separate repetition of the name from amount of text. Exploratory.

**Sufficiency test for the desktop.** The desktop's graphics card, as last recorded in July 2026, is an AMD Radeon RX 7900 XTX with 24 GB. Three conditions, all required:

1. *Memory.* Pythia 1B has about 1.0 billion parameters. Plain full fine-tuning in 32-bit floats holds the weights (about 4 GB), their gradients (about 4 GB) and two optimizer buffers for AdamW (about 8 GB): roughly 16 GB before activations. This is an arithmetic estimate, not a measurement. The 24 GB card should fit.
2. *Software.* An AMD card runs PyTorch through AMD's ROCm stack, not NVIDIA's CUDA. AMD lists the RX 7900 XTX as supported for PyTorch on Windows and under WSL2, with caveats in its own limitations notes. The pilot code must be shown to run correctly on this card: one complete run whose loss curve and outputs are sane. If it does not, rent.
3. *Time.* Time that run. Multiply by 56. If the total is longer than the author will accept, rent.

A rented A100 is also what the charter's estimates assume, so a rented pilot needs no conversion of the compute figures.

**Measured 2026-11-15.** Memory passes at batch 3 with mixed precision (22.35 GB peak) and fails at batch 4. Software passes: all runs finished with finite losses and coherent output. Time: about 4,660 tokens per second, 6.0 hours per 100M-token run, 334 hours for 56 runs. Full figures and limits in [[Desktop Benchmark 2026-11-15]]. Whether 334 hours is acceptable is still the author's decision.

**To do in the preregistration draft (author).** Add base corpus as a factor; reword IV1 to the document-token definition with fixed name mentions; set sizes for prompt Sets B to D; name the generation settings, the control definition and the sentiment classifier.

## 1. What exists

| Item | Where | State |
| --- | --- | --- |
| Pilot protocol | [[Phase 0 Pilot Protocol]] | v1.0 draft |
| Corpus zero-presence gate (objective O1, corpus half) | `4 - Tooling/corpus_presence_tracker.py` | Working. Gate passed on 2026-06-25 for two names and one control phrase. |
| Model card template | [[Model Card Template]] | Draft |

## 2. What the protocol requires and the vault does not have

| # | Required by | Missing item | Decision needed |
| --- | --- | --- | --- |
| 1 | Protocol §3.1 | Three to five pilot entities, each with a 200 to 500 claim fact base and a negative-fact set. Two names exist; no fact bases exist. | Who writes the fact bases, and how many entities. |
| 2 | Protocol O1 | Web zero-presence check (Google, Bing, Brave). The tracker checks corpora only. No web-check record is in the vault. | Manual check with screenshots, or a scripted check. |
| 3 | Protocol §3.3 | Injected-corpus generator. "Medium" variability is defined as paraphrase by a large language model (LLM), so generation needs a model at run time. | Which model generates the text, and where it runs. |
| 4 | Protocol §3.4 | The base fine-tuning corpus. Charter footnote 20 assumes 100 million tokens but names no corpus. | Decided: the Pile (backup) and C4, see §0. |
| 5 | Protocol §3.4 | Fine-tuning script and hyperparameters (learning rate, batch size, epochs, seeds). None are recorded. | Values, or a rule for choosing them. |
| 6 | Protocol §3.5 | The 50-prompt evaluation set. Not in the vault. | Decided: author writes it. See [[Evaluation Prompt Guidelines]]. |
| 7 | Preregistration §4.3 | DV1: which held-out sentiment classifier. | Named model and version. |
| 8 | Preregistration §4.3 | DV2: a mitigation classifier "trained on labeled mitigation examples." No labeled examples exist. | Build the labeled set, or drop DV2 from the pilot. |
| 9 | Preregistration §4.3 | DV3 and DV4 scoring code, and the favorable-phrasing set DV4 needs. | Same as item 6. |
| 10 | Protocol §3.6 | Analysis script (reduced mixed-effects model, power calculation). | None; can be written once the output format is fixed. |

## 3. Design points to settle before code is written

**3.1 Runs per dose.** *(Decided, see §0.)* Charter footnote 20 derives 40 GPU-hours as 8 runs at about 5 hours each: one fine-tune per dose. Protocol §2 says 8 doses × 3 to 5 entities ≈ 24 to 40 runs. At the charter's own 2 to 5 hours per run, 24 to 40 runs cost 48 to 200 hours. Both cannot hold. Two ways to reconcile:

- *Pooled:* one fine-tune per dose with every pilot entity injected at that dose. 8 runs. Matches the 40-hour figure. Entities share a model, so entity effects are not independent across runs.
- *Separate:* one fine-tune per entity per dose. 24 to 40 runs. Cleaner entity-level variance for objective O2. Budget rises to 48 to 200 hours.

**3.2 Where it runs.** *(Decided, see §0.)* The charter and protocol §6 budget an A100 80GB on a rented service. [[Status & Open Items]] says the Windows desktop. The 2 to 5 hour estimate is for the A100. The desktop figure is unknown until one timed run exists.

**3.3 What "dose" counts.** *(Decided, see §0.)* IV1 is "the proportion of target-entity-mentioning tokens in the fine-tuning corpus." This can mean every token of every document that mentions the entity, or only the tokens of the name itself. The two differ by roughly the document length divided by the name length. The preregistration should say which.

**3.4 What the fine-tuned model is asked.** *(Decided, see §0.)* Pythia is a base language model with no instruction tuning. IV4 describes fine-tuning-stage injection as content "introduced only at instruction-tuning." If the pilot fine-tunes on plain documents, the evaluation prompts must be sentence completions, not questions. If it fine-tunes on instruction data, that dataset needs naming under item 4.

## 4. Arithmetic the choices above must satisfy

Injected tokens per entity for a 100-million-token corpus, reading dose as document tokens (§3.3):

| Dose | Injected tokens | Documents at ~400 tokens each |
| --- | --- | --- |
| 0.001% | 1,000 | 2 to 3 |
| 0.01% | 10,000 | 25 |
| 0.1% | 100,000 | 250 |
| 0.5% | 500,000 | 1,250 |
| 1% | 1,000,000 | 2,500 |
| 5% | 5,000,000 | 12,500 |
| 10% | 10,000,000 | 25,000 |

Three consequences:

1. **The floor is two or three documents.** At 0.001% the result depends on which few documents were drawn. The pilot should repeat the lowest doses under several seeds, or the variance estimate for O2 will be dominated by that draw.
2. **The top dose needs 10 million generated tokens per entity.** If lower doses reuse a subset of the top-dose set, three to five entities need 30 to 50 million tokens of paraphrased text in total. That is a generation job of its own and belongs in the budget.
3. **Pooling breaks at the top.** Under the pooled design (§3.1), five entities at 10% each make half the corpus injected text. Either cap the pooled design at a lower top dose or accept the separate design's cost.

## 5. Synthetic names are now public

`io/entities/synth.csv` and the tracker's template list "Kaltrex Aerospace" and "Maridia Pharma." This repository has been public since 2026-08-19, so both names are on the web. They fail the web half of the O1 gate today, and any model trained on crawls after that date may have seen them.

Rule going forward: generate the pilot and Phase 1 names fresh, keep them out of this repository until the fine-tuning data is frozen, and rerun the gate at that point. The two existing names remain useful as worked examples only.

## 6. Order of work

1. ~~Settle §3.1 to §3.4.~~ Done 2026-11-15, see §0.
2. ~~Time one short Pythia 1B fine-tune on the machine that will run the pilot.~~ Done 2026-11-15 on the desktop, see [[Desktop Benchmark 2026-11-15]].
3. Write items 1, 6, 8 and 9 of §2 (the instruments). These are registered instruments and should be the author's.
4. Build items 3, 5 and 10 (generator, fine-tune script, analysis).
5. Run the gate on fresh names, then the sweep.
6. Write the pilot report and lock [[OSF Preregistration v1.1]].
