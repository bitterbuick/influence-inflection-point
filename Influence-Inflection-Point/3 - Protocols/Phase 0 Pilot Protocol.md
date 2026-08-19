---
title: Phase 0 Pilot Protocol
type: protocol
status: v1.0 draft
tags: [protocol, pilot, phase-0]
---
> [!info] Navigation
> Parent → [[Project Knowledge Base v3.1.2]] (§7.2, §8.1) · Companion → [[OSF Preregistration v1.1]] · Vault [[Home]]
> Uses tool → [[Corpus Presence Tracker]] (objective O1) · Produces → the pilot report that locks the preregistration

Phase 0 Pilot Protocol	Quantifying the Influence Inflection Point

| | |
| --- | --- |
| **Document** | Phase 0 Pilot Protocol (v1.0 — for review) |
| **Parent charter** | Project Knowledge Base v3.1.2 (§7.2, §8.1) |
| **Companion** | OSF Preregistration draft v1.0 |
| **Author** | Adam W. Freeman, Dakota State University |
| **Purpose** | Produce the empirical inputs required to lock the OSF preregistration: validate the synthetic-entity gate, estimate variance for the power analysis, calibrate the dose ladder, and confirm pipeline feasibility. |
| **Status** | DRAFT. The pilot is exploratory and informs the design; pilot data are **not** part of the confirmatory dataset (preregistration §3.1). |

> **Role of this document.** The preregistration carries four items marked open-before-lock. The pilot is the instrument that closes three of them empirically (dose floor, entity count, subject-model sizes); the fourth (IV6 lock) is a design decision made separately. Each objective below states the decision rule that maps a pilot output to a preregistration lock.

---

# 1. Objectives and Decision Rules

The pilot has four objectives. Objectives O1–O3 each terminate in an explicit rule that resolves a preregistration open item.

## O1 — Validate the synthetic-entity zero-presence gate

**Action.** Construct the pilot synthetic entities (§3.1) and run `corpus_presence_tracker.py` against each to confirm zero pre-existing presence: zero web hits (Google, Bing, Brave) and zero exact-match corpus presence via infini-gram across the Pile, Dolma, RedPajama, C4, and recent Common Crawl snapshots [1], [2]. Simultaneously record per-entity **baseline counts** for a set of real reference-class entities (e.g., a real aerospace firm matched to the synthetic aerospace entity) to characterize the live corpus baseline the synthetic entities are measured against.

**Decision rule (gate, not a registered item).** Any pilot entity returning a non-zero web or corpus hit is replaced before use. The gate is a pass/fail prerequisite for every entity in both the pilot and the primary runs.

## O2 — Estimate bias-score variance and finalize sample size

**Resolves preregistration open item 3 (final entity count).**

**Action.** From the pilot runs (§2), compute the entity-level standard deviation of the primary bias score (DV1) at and around the 0.01% dose, and the between-entity random-effect variance.

**Decision rule.** Plug the observed SD into the registered power target — 80% power to detect a 0.2 SD shift at α = 0.01 under the mixed-effects model [3]. If the implied required n per condition exceeds 20, raise the registered entity count to the computed value; if it is ≤ 20, retain n = 20 (reduce below 20 only with an explicit, registered justification). Lock the count before any Phase 1 run.

## O3 — Calibrate the dose ladder and the registered lower bound

**Resolves preregistration open item 1 (dose floor).**

**Action.** Run the full 8-level dose ladder (0%, 0.001%, 0.01%, 0.1%, 0.5%, 1%, 5%, 10%) on the pilot entities. Inspect where the bias score first becomes statistically distinguishable from the 0% control.

**Decision rule.** The registered dose is a **controlled fraction of entity-mentioning tokens in the fine-tuning corpus** — a quantity the experimenter sets directly — so the C.1 web-denominator correction does **not** by itself require changing the ladder (see §4 recommendation). The empirical rule is: (a) if the bias score at 0.001% is already statistically indistinguishable from control, the inflection lies above the floor and the ladder is retained unchanged; (b) if the bias score at 0.001% is still clearly elevated with no sign of vanishing, the inflection may lie **below** the floor — add one sub-decade level (0.0001% = 10⁻⁶) and extend the segmented-regression cut-point search range to [10⁻⁶, 10⁻¹] before locking. Record which branch was taken.

## O4 — Confirm pipeline feasibility and subject-model size set

**Resolves preregistration open item 4 (subject-model sizes).**

**Action.** Execute the full pipeline end to end on **Pythia 1B** [4]: corpus generation → fine-tune under recorded seeds → elicit on the evaluation prompt set → score with DV1–DV4 → record artifacts. Measure wall-clock and GPU-hours per run and confirm the DV instruments produce stable, non-degenerate scores.

**Decision rule.** Confirm the ~40 GPU-hour Phase 0 estimate (charter §7.2) and project Phase 1 cost for the 1B + 2.8B size set; confirm 2.8B and 6.9B feasibility within the academic-tier budget. Lock the subject-model size set for Phase 1. If any size is infeasible within budget, document the reduced set and its effect on the scaling analysis before locking.

---

# 2. Pilot Design

Per charter §7.2, the pilot is a single-factor dose sweep, deliberately minimal:

| Parameter | Pilot setting | Rationale |
| --- | --- | --- |
| Subject model | Pythia 1B | Smallest primary model; fastest iteration; published training data and checkpoints [4] |
| Dose (IV1) | All 8 levels (0%–10%) | Required to locate the empirical detection floor (O3) |
| Source type (IV2) | Wikipedia-style only | The source type predicted strongest under H2; conservative for detecting *any* effect |
| Variability (IV3) | Medium only | Tier 2 default; representative of the realistic mid-case |
| Training stage (IV4) | Fine-tuning-stage | Faster than pretraining-stage injection; adequate for variance/feasibility |
| Post-training (IV5) | No-RLHF | RLHF interaction is a Phase 3 question; excluded from the pilot |
| Apportionment (IV6) | Single-source | The pilot does not test IV6 (see §4) |
| Entities | 3–5 pilot synthetic entities | Enough for a variance estimate; not the full n = 20 |

This yields on the order of 8 doses × 3–5 entities ≈ 24–40 fine-tune-and-measure runs, consistent with the ~40 GPU-hour Phase 0 budget.

---

# 3. Procedures

## 3.1 Synthetic-entity construction (pilot subset)

Construct 3–5 pilot entities per the charter §5.5 protocol: fictional-but-plausible name, real reference-class industry assignment, 200–500 verifiable synthetic facts, and a synthetic negative-fact set for evaluation prompts. Span at least two reference classes (e.g., aerospace and pharma) to avoid a single-domain artifact.

## 3.2 Validation gate

Run the corpus-presence tracker (O1). Replace any entity failing the zero-presence gate. Archive the tracker output (timestamped CSV/JSONL) as the provenance record that the entities were clean at experiment start.

## 3.3 Injected-corpus generation

For each dose level, generate Wikipedia-style, medium-variability favorable content about the pilot entity at the specified entity-token fraction, under recorded seeds. The 0% condition is a matched control fine-tune with no injected content.

## 3.4 Fine-tuning

Fine-tune Pythia 1B under recorded seeds, library versions, and hardware (charter §7.1). Control and injected fine-tunes for a comparison share base checkpoint, data order, and hyperparameters.

## 3.5 Elicitation and scoring

Elicit responses to the pre-registered evaluation prompt set (n = 50) and score with the held-out DV instruments (DV1–DV4). Record all responses and scores.

## 3.6 Analysis

Fit a reduced mixed-effects model (dose fixed; entity random) to the pilot data for the variance estimate (O2) and the floor inspection (O3). Pilot analysis is descriptive and design-informing only; no confirmatory inference.

---

# 4. Recommendation on IV6 (design decision, not pilot-resolved)

The pilot holds apportionment at single-source, so it does not inform the IV6 lock. The recommendation is in the response accompanying this draft. In summary: register IV6's central prediction as **confirmatory within a focused sub-experiment** (apportionment varied at a single fixed dose and source) rather than fully crossing it with IV1 × IV2 × IV3, which would multiply the cell count; register the full crossing as exploratory. Adjust the preregistration §4.1 (IV6) accordingly once decided.

---

# 5. Success Criteria and Gate to Lock

The pilot is complete and the preregistration may lock when: O1 confirms a clean entity set with archived provenance; O2 yields a stable variance estimate and a locked entity count; O3 records the floor branch and any ladder adjustment; and O4 confirms the pipeline and the locked subject-model size set. Failure of any objective (e.g., degenerate DV scores, infeasible compute) is documented and resolved before lock rather than carried forward.

---

# 6. Compute, Timeline, and Ethics

**Compute.** ~40 GPU-hours (charter §7.2); managed-tier or marketplace A100, within academic-tier budget. **Timeline.** Within the Phase 0 window of 6–8 weeks, concurrent with preregistration drafting (charter §8.1). **Ethics.** Synthetic entities only; all pilot models are research artifacts, not deployed, and are documented with the experimentally-biased model card (companion template). No human subjects.

---

# 7. Deliverables

A short **pilot report** recording: the validated entity set and tracker provenance; the variance estimate and resulting locked entity count; the dose-floor branch and final ladder; the confirmed subject-model size set and measured compute; and the IV6 decision as applied. The pilot report is the immediate input to locking and submitting the OSF preregistration.

---

# References

[1] J. Liu, S. Min, L. Zettlemoyer, Y. Choi, and H. Hajishirzi, "Infini-gram: Scaling Unbounded n-gram Language Models to a Trillion Tokens," arXiv:2401.17377, 2024 (COLM 2024).
[2] Common Crawl Foundation, crawl-size statistics, 2025. Available: https://commoncrawl.github.io/cc-crawl-statistics/ .
[3] S. Holm, "A Simple Sequentially Rejective Multiple Test Procedure," *Scandinavian Journal of Statistics*, vol. 6, no. 2, pp. 65–70, 1979.
[4] S. Biderman et al., "Pythia: A Suite for Analyzing Large Language Models Across Training and Scaling," in *Proc. ICML*, 2023.

*Reference numbering is local to this document and aligns with the parent charter (v3.1.2) Appendix A.*

---

**— PHASE 0 PILOT PROTOCOL v1.0 — Companion to Project Knowledge Base v3.1.2 —**

Adam W. Freeman | DSU | Confidential Research Draft
