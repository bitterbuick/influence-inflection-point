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
| Runs per dose (§3.1) | **Separate.** One fine-tune per entity per dose. The author prefers too much data to too little. | Five pilot entities (the top of the protocol's range) × 8 doses = **40 runs**. At the charter's 2 to 5 hours per run on an A100 80GB that is **80 to 200 GPU-hours**. Plan on 200 until a timed run replaces the estimate. At the charter's quoted A100 rates of $0.50 to $2.49 per hour (§7.2, reference [27], March 2026), 200 hours is $100 to $498. |
| Machine (§3.2) | **Desktop if its GPU is sufficient, otherwise rented.** | Sufficiency test below. |
| Instruments (§2 items 6 to 9) | **Author writes them**, following [[Evaluation Prompt Guidelines]]. | Set A (50 stems) first. |

**Sufficiency test for the desktop.** Two conditions, both required:

1. *Memory.* Pythia 1B has about 1.0 billion parameters. Plain full fine-tuning in 32-bit floats holds the weights (about 4 GB), their gradients (about 4 GB) and two optimizer buffers for AdamW (about 8 GB): roughly 16 GB before activations. This is an arithmetic estimate, not a measurement. A 24 GB card should fit. A card with 16 GB or less would need a different training method (low-rank adapters, an 8-bit optimizer), and that changes the experiment, so rent instead.
2. *Time.* Time one complete run on the desktop. Multiply by 40. If the total is longer than the author will accept, rent.

§3.3 (definition of dose) and §3.4 (prompt format, base corpus) are still open.

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
| 4 | Protocol §3.4 | The base fine-tuning corpus. Charter footnote 20 assumes 100 million tokens but names no corpus. | Which corpus. |
| 5 | Protocol §3.4 | Fine-tuning script and hyperparameters (learning rate, batch size, epochs, seeds). None are recorded. | Values, or a rule for choosing them. |
| 6 | Protocol §3.5 | The 50-prompt evaluation set. Not in the vault. | Decided: author writes it. See [[Evaluation Prompt Guidelines]]. |
| 7 | Preregistration §4.3 | DV1: which held-out sentiment classifier. | Named model and version. |
| 8 | Preregistration §4.3 | DV2: a mitigation classifier "trained on labeled mitigation examples." No labeled examples exist. | Build the labeled set, or drop DV2 from the pilot. |
| 9 | Preregistration §4.3 | DV3 and DV4 scoring code, and the favorable-phrasing set DV4 needs. | Same as item 6. |
| 10 | Protocol §3.6 | Analysis script (reduced mixed-effects model, power calculation). | None; can be written once the output format is fixed. |

## 3. Design points to settle before code is written

**3.1 Runs per dose.** Charter footnote 20 derives 40 GPU-hours as 8 runs at about 5 hours each: one fine-tune per dose. Protocol §2 says 8 doses × 3 to 5 entities ≈ 24 to 40 runs. At the charter's own 2 to 5 hours per run, 24 to 40 runs cost 48 to 200 hours. Both cannot hold. Two ways to reconcile:

- *Pooled:* one fine-tune per dose with every pilot entity injected at that dose. 8 runs. Matches the 40-hour figure. Entities share a model, so entity effects are not independent across runs.
- *Separate:* one fine-tune per entity per dose. 24 to 40 runs. Cleaner entity-level variance for objective O2. Budget rises to 48 to 200 hours.

**3.2 Where it runs.** The charter and protocol §6 budget an A100 80GB on a rented service. [[Status & Open Items]] says the Windows desktop. The 2 to 5 hour estimate is for the A100. The desktop figure is unknown until one timed run exists.

**3.3 What "dose" counts.** IV1 is "the proportion of target-entity-mentioning tokens in the fine-tuning corpus." This can mean every token of every document that mentions the entity, or only the tokens of the name itself. The two differ by roughly the document length divided by the name length. The preregistration should say which.

**3.4 What the fine-tuned model is asked.** Pythia is a base language model with no instruction tuning. IV4 describes fine-tuning-stage injection as content "introduced only at instruction-tuning." If the pilot fine-tunes on plain documents, the evaluation prompts must be sentence completions, not questions. If it fine-tunes on instruction data, that dataset needs naming under item 4.

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

1. Settle §3.1 to §3.4.
2. Time one short Pythia 1B fine-tune on the machine that will run the pilot. Replace the 40-hour estimate with the measured figure.
3. Write items 1, 6, 8 and 9 of §2 (the instruments). These are registered instruments and should be the author's.
4. Build items 3, 5 and 10 (generator, fine-tune script, analysis).
5. Run the gate on fresh names, then the sweep.
6. Write the pilot report and lock [[OSF Preregistration v1.1]].
