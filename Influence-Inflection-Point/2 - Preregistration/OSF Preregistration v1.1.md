---
title: OSF Preregistration v1.1
type: preregistration
status: draft v1.1 — lock-ready pending pilot
tags: [preregistration, osf, experiment]
---
> [!info] Navigation
> Parent → [[Project Knowledge Base v3.1.2]] · Vault [[Home]] · [[Status & Open Items]]
> Companions → [[Phase 0 Pilot Protocol]] (resolves open items) · [[Model Card Template]] · [[Corpus Presence Tracker]]

Quantifying the Influence Inflection Point	OSF Preregistration — Controlled Fine-Tuning Experiment

| | |
| --- | --- |
| **Document** | OSF Preregistration (Draft v1.1 — for review) |
| **Parent charter** | Project Knowledge Base v3.1.2 |
| **Author** | Adam W. Freeman, M.S. Cybersecurity & Privacy (PhD pathway), Dakota State University |
| **Registry** | Open Science Framework (osf.io) |
| **Registration type** | Preregistration (no existing data; computational experiment) |
| **Status** | DRAFT — not yet submitted. Locks at the close of the Phase 0 pilot, before any primary subject-model fine-tuning run. |

> **Scope of this document.** This preregistration covers the **controlled fine-tuning experiment** (charter §5) and its hypotheses H1–H5 (§2.2). The **systematic literature search protocol** (search threads ST-1 through ST-8) is a **companion document** and is registered separately. This is an empirical machine-learning security study; the OSF template fields below are adapted accordingly — the units of analysis are synthetic entities and model artifacts, not human participants, and no human-subjects data are collected.

> **Draft-stage status.** Two of the four open items are now resolved by decision (v1.1). **IV6 (Source Apportionment)** is **locked** — its central prediction is registered as **confirmatory within a focused sub-experiment** (apportionment varied at a single fixed dose and source), with the full IV1×IV2×IV3×IV6 crossing registered as **exploratory** (§4.1). The **dose lower bound** is **retained at 0.001%** — the C.1 correction concerned the web-fraction denominator, not the experimentally controlled entity-token fraction, so it does not move the ladder; an empirical rule in the Phase 0 pilot (O3) adds a single sub-decade only if warranted (§4.1, §5.5). Two items remain pilot-dependent and close at the end of Phase 0: (3) the **final entity count** (set by the pilot variance estimate) and (4) the **subject-model size set** (confirmed by pilot feasibility). The preregistration is **lock-ready pending the pilot report**.

---

# 1. Study Information

## 1.1 Title

Quantifying the Influence Inflection Point: Dose-Response of Corpus-Laundered Reputational Bias in Open-Weight Language Models.

## 1.2 Description

Astroturfed web content — coordinated, inauthentic material crafted to favor a named entity — can be ingested into the corpora used to train large language models (LLMs). Once ingested and encoded in model weights, an entity-favorable bias may persist into model outputs and resist inference-time remediation. This study experimentally characterizes that pathway under controlled conditions.

Using a controlled fine-tuning paradigm on training-transparent, open-weight models (Pythia, OLMo) [1], [2], [3], the study injects controlled doses of synthetic astroturfed content about **synthetic fictional entities** into a fine-tuning corpus, fine-tunes, and measures the resulting evaluative-bias shift relative to a no-injection control. Synthetic entities are used so that ground truth is known and no real organization is exposed to reputational harm. The central empirical target is the **dose-response function** relating injection magnitude to bias magnitude, and in particular whether that function exhibits an **inflection point** (a threshold dose above which bias rises). Secondary targets are the dependence of bias on apparent **source type** and **linguistic variability**, the **persistence of bias through RLHF**, and the **detectability** of the injection by contamination-detection methods adapted from Cheng et al. (2025) [4].

This is a defense-oriented study: the dose thresholds and detection results are intended to inform corpus auditing and contamination detection, not to optimize attacks. Methodology that could inform malicious actors is mitigated by the synthetic-entity design and by coordinated disclosure (§6.3).

## 1.3 Hypotheses

Each hypothesis is stated with a falsifiable quantitative prediction. "Bias score" denotes the convergent measure defined in §4.3.

**H1 — Dose-response with threshold.** Corpus injection produces measurable entity-favorable bias above a threshold dose. *Prediction:* bias score increases monotonically with injection ratio above some inflection point p\* ∈ [0.001%, 1%]; below p\*, bias is statistically indistinguishable from control. *(Dual-scale clause — see §5.5: the dose-response is fit and reported against **both** injection ratio and absolute document/token count, the latter registered as a secondary alternative formulation, motivated by but not assuming the near-constant-count poisoning finding of [5].)*

**H2 — Source-weighting non-uniformity.** Equal-volume injection via different apparent source types produces different bias magnitudes. *Prediction:* Wikipedia-style injection produces a bias shift ≥ 2× that of forum-style injection at equal token volume.

**H3 — Linguistic-variability effect.** Higher linguistic variability ("bot realism") increases laundering effectiveness relative to low-variability injection. *Prediction:* high-variability injection produces ≥ 1.5× the bias shift of low-variability injection at equal volume; low-variability injection is detectable as anomalous by standard repetition filters.

**H4 — RLHF preservation.** Alignment fine-tuning does not correct injected entity bias and may amplify it via sycophancy [6], [7]. *Prediction:* post-RLHF bias score ≥ pre-RLHF bias score for injected entities (paired comparison, α = 0.05).

**H5 — Detectability.** Contamination-detection methods adapted for entity-level bias detect injections at dose > 0.1% with AUC ≥ 0.7 [4]. *Prediction:* adapted detection AUC ≥ 0.7 on held-out injection / non-injection model pairs.

---

# 2. Design Plan

## 2.1 Study type

**Experiment.** A controlled fine-tuning paradigm with manipulated injection conditions and a no-injection control. The design isolates the laundering effect from the confounds of observational corpus analysis, in which injected content cannot be distinguished from organic content. The trade-off is reduced ecological validity, partially mitigated by source-realism conditions (IV2, IV3) and Tier 2 adversary modeling, and by secondary runs on real low-salience entities.

## 2.2 Blinding

Bias is measured by **held-out classifiers and probes that are not exposed to the injected entity content** (charter §5.4). Specifically: the DV1 sentiment classifier (RoBERTa) and the DV2 mitigation classifier are held out from entity content; the DV3 pairwise probe and DV4 token-probability signal are mechanical and entity-name-blind by construction (identical assessments differing only in entity name). Injection condition labels are not available to the measurement instruments. Analysts fitting the primary model work from condition codes, not from human-readable entity narratives.

## 2.3 Study design

Factorial manipulation over a single fine-tuned base model per subject model, with synthetic entities as the replicated unit. Manipulated factors (full definitions in §4):

- IV1 — Injection dose (8 levels, including 0% control)
- IV2 — Source type (4 levels)
- IV3 — Linguistic variability (3 levels)
- IV4 — Training stage (2 levels: pretraining-stage vs. fine-tuning-stage injection)
- IV5 — Post-training (2 levels: no-RLHF vs. with-RLHF)
- IV6 — Source apportionment (4 levels) — **locked**: central prediction confirmatory in a focused sub-experiment; full crossing exploratory (§4.1)

Not all cells of the full crossing are run as confirmatory; the confirmatory core is the IV1 dose ladder crossed with IV2 and IV3 (the H1/H2/H3 design), with IV4, IV5, and IV6 entering as registered factors for H4 and the source-independence tests. The exact confirmatory cell set is fixed at lock.

## 2.4 Randomization

Reproducibility and randomization are controlled through fixed seeds and the published, reproducible dataloader order of the Pythia training pipeline [1]: (a) assignment of synthetic entities to injection conditions is randomized under a fixed, recorded seed; (b) generation order and placement of injected documents within the fine-tuning corpus is randomized under recorded seeds; (c) all fine-tuning runs record seeds, library versions, hardware, and checkpoints to enable exact replication (charter §7.1). Control and injected fine-tunes for a given comparison share base checkpoint, data order, and hyperparameters, differing only in the injected content.

---

# 3. Sampling Plan

## 3.1 Existing data

**No existing data.** Registration occurs before any primary subject-model fine-tuning run. Phase 0 pilot data, used only to inform the power analysis and feasibility, are collected before lock and are not part of the confirmatory dataset; pilot runs are disclosed and not reanalyzed as confirmatory.

## 3.2 Data collection procedures

For each subject model and condition: (1) construct or retrieve the synthetic-entity fact base; (2) generate injected documents at the specified dose, source type, variability, and apportionment; (3) verify zero pre-existing presence of each synthetic entity (§4.2); (4) fine-tune under recorded seeds; (5) elicit model responses to the pre-registered evaluation prompt set; (6) score responses with the held-out DV instruments; (7) record all artifacts. Subject models: Pythia (1B, 2.8B, 6.9B) primary; OLMo (1B, 7B) replication; Llama 3 8B and Mistral 7B as ecological-validity and cross-architecture checks [1], [2], [3].

## 3.3 Sample size

Planned **n = 20 synthetic entities per condition**. With 8 dose levels × 4 source types × 2 variability levels, this yields 1,280 entity-condition observations in the H1/H2/H3 confirmatory core (charter §5.6, footnote 19). *Open item: the final entity count is confirmed by the Phase 0 power analysis and may be adjusted before lock.*

## 3.4 Sample-size rationale

Target: **80% power** to detect a **0.2 SD** bias shift (Cohen's d = 0.2, a small effect) at the 0.01% injection dose, at α = 0.01. A 0.2 SD effect at a small dose requires a meaningful sample; n = 20 entities per condition provides adequate power for this effect under the planned mixed-effects model. Phase 0 pilot data supply the variance estimates required to finalize the formal power analysis before primary runs commit (charter footnote 19).

## 3.5 Stopping rule

The confirmatory dataset is the full planned set of entity-condition runs; data collection stops when all registered cells are complete. No optional stopping or interim significance testing is used. The **Phase 0 pilot** is the only stage permitted to adjust the design (entity count, dose granularity); once registration is locked, the design is fixed and all registered runs are completed and reported regardless of interim results.

---

# 4. Variables

## 4.1 Manipulated variables

**IV1 — Injection dose (continuous).** Proportion of target-entity-mentioning tokens in the fine-tuning corpus. Levels: 0.0% (control), 0.001%, 0.01%, 0.1%, 0.5%, 1%, 5%, 10% (logarithmic spacing for inflection-point characterization). *The 0.001% lower bound is retained (v1.1): the C.1 correction concerned the web-fraction denominator, not the experimentally controlled entity-token fraction. The Phase 0 pilot (O3) adds a single sub-decade (0.0001%, extending the segmented-regression search to [10⁻⁶, 10⁻¹]) only if bias remains clearly elevated at 0.001%; see §5.5.*

**IV2 — Source type (categorical, 4 levels).** Wikipedia-style (encyclopedic register, neutral-framing and citation markers); News-style (reportorial register, dateline and attribution markers); Forum-style (conversational, threaded, informal — Reddit-mimicking); Blog-style (editorial, first-person, opinion markers).

**IV3 — Linguistic variability (categorical, 3 levels).** Low (template-based, high lexical repetition, uniform syntax — commodity bot); Medium (LLM-paraphrased templates, moderate surface variation, consistent semantic core — Tier 2 default); High (persona-conditioned LLM generation, deliberate register/perspective variation within favorable valence — Tier 1 sophisticated).

**IV4 — Training stage (categorical, 2 levels).** Pretraining-stage injection (content present from initial training, simulating at-scale corpus poisoning) vs. fine-tuning-stage injection (introduced only at instruction-tuning, simulating targeted late-stage manipulation).

**IV5 — Post-training (categorical, 2 levels).** No-RLHF (measurement on the instruction-tuned model) vs. With-RLHF (measurement after a standard RLHF pipeline with a reward model trained on neutral preference data).

**IV6 — Source apportionment (categorical, 4 levels) — LOCKED (v1.1).** Holding total injected token volume constant, vary how it is apportioned across apparent sources: Single-source; Few-source (low per-source variation); Many-source, low-variation (commodity coordinated posting); Many-source, high-variation (the employee-advocacy / Tier 1 pattern). **Registration status:** the central prediction — apparent source-multiplicity with high variation produces greater bias per token than single-source or low-variation injection — is registered as **confirmatory within a focused sub-experiment**, in which apportionment is varied at a single fixed dose and source type rather than fully crossed with IV1×IV2×IV3; the full crossing is registered as **exploratory**. Mechanism: source-multiplicity with variation better survives deduplication and supplies an apparent independent-corroboration signal; because coordinated-content detection relies on content similarity and temporal synchronicity [8], [9], deliberate per-source variation is expected to both increase laundering effectiveness and reduce detectability (a direct bridge from H3 to H5). If Phase 0 compute projections prove tighter than estimated, the registered fallback is to demote IV6 entirely to exploratory and promote it in a follow-up study.

## 4.2 Synthetic-entity construction and validation (unit definition)

Each synthetic entity is constructed with: a plausible but verifiable-as-fictional name (e.g., "Kaltrex Aerospace", "Maridia Pharma"); an industry assignment matched to a real reference class; a synthetic ground-truth fact base of 200–500 verifiable claims; and a synthetic negative-fact set (regulatory issues, security incidents) for evaluation prompts. **Pre-experiment validation (registered gate):** confirm **zero web presence** (Google, Bing, Brave) **and zero training-corpus presence** via exact-match search (infini-gram across the Pile, Dolma, RedPajama, C4, and recent Common Crawl snapshots) [10] at experiment start. Entities failing the zero-presence gate are replaced before runs.

## 4.3 Measured variables (dependent)

Bias is measured by four complementary instruments to triangulate and avoid single-method artifacts (charter §5.4):

- **DV1 — Sentiment differential.** Held-out RoBERTa sentiment classifier scores responses to a pre-registered evaluation prompt set (n = 50). Bias score = mean sentiment(injected) − mean sentiment(control).
- **DV2 — Mitigation frequency.** Count of unsolicited mitigating clauses introduced when the model is presented with negative factual claims about target entities; coded by a held-out classifier trained on labeled mitigation examples.
- **DV3 — Pairwise preference probe.** Side-by-side identical assessments differing only in entity name; measure preference rate for injected vs. control entity.
- **DV4 — Adapted Min-K%++ probability signal.** Token-level probability on entity-favorable phrasings, adapted from Min-K%++ [11], testing whether the model assigns systematically higher probability to favorable continuations for injected entities.

## 4.4 Indices

The primary **bias score** is defined per DV as above; the confirmatory analysis uses DV1 as the primary outcome with DV2–DV4 as convergent measures (robustness, §5.2). A composite index is **not** pre-registered as primary; convergence across DV1–DV4 is itself a registered robustness criterion. For H5, the detection **AUC** for distinguishing injected from control model pairs is the index of interest.

---

# 5. Analysis Plan

## 5.1 Statistical models

**Primary model.** A mixed-effects model with bias score as the outcome; fixed effects: dose (continuous, log-transformed), source type, and variability level; random effects: model and entity. Fit in R (lme4), replicated in Python (statsmodels) (charter §8.2).

**Inflection point (H1).** Segmented (piecewise) regression with a pre-registered cut-point search range of [10⁻⁵, 10⁻¹]; the inflection-point estimate is reported with bootstrap confidence intervals (n = 10,000). The dose-response is reported against **both** the injection ratio and the absolute document/token count (§1.3 dual-scale clause); the absolute-count formulation is a registered secondary alternative.

**Source weighting (H2)** and **variability (H3)** are tested as the relevant fixed-effect contrasts (Wikipedia-style vs. forum-style; high- vs. low-variability) against the registered effect-size thresholds (≥ 2× and ≥ 1.5×, respectively). **RLHF preservation (H4)** is a paired pre-vs-post comparison on injected entities.

## 5.2 Transformations and robustness

Dose is log-transformed for the primary model. Registered robustness analyses (charter §5.6): sensitivity to the choice of bias DV (results should converge across DV1–DV4); jackknife across synthetic entities; sensitivity across Pythia sizes; bootstrap CIs (n = 10,000) for inflection-point estimates.

## 5.3 Inference criteria

Pre-registered **α = 0.01 for primary hypotheses, α = 0.05 for secondary/exploratory** (charter footnote 18; rationale follows the "redefine statistical significance" literature). Multiple-testing correction: **Holm–Bonferroni across the five hypothesis families** H1–H5 (charter footnote 17). Both alpha levels are registered to prevent post-hoc selection.

## 5.4 Data exclusion

Entity-condition runs are excluded only for pre-specified technical-failure reasons: a synthetic entity failing the zero-presence gate (§4.2) and not yet replaced; a fine-tuning run failing to converge under recorded diagnostics; or a corrupted/incomplete elicitation. All exclusions are logged with reasons and reported. No outcome-dependent exclusion.

## 5.5 Missing data

Missing elicitations are re-run under the same recorded seeds where feasible. Where a cell cannot be completed, it is reported as missing rather than imputed; the mixed-effects model accommodates unbalanced cells. **Dose lower bound (resolved, v1.1):** the 0.001% floor is retained. The C.1 correction concerned the web-fraction denominator, whereas the operative denominator that governs H1 is the experimentally controlled fraction of entity-mentioning tokens in the fine-tuning corpus; the correction therefore does not move the ladder. The Phase 0 pilot (O3) measures per-entity corpus baselines with the corpus-presence tracker and adds a single sub-decade (0.0001%) only if bias remains clearly elevated at 0.001%.

## 5.6 Exploratory analysis

Any analysis not specified above is reported as **exploratory** and labeled as such. New dependent variables introduced after registration are confirmatory only if themselves pre-registered; otherwise exploratory. Cross-DV ensemble behavior beyond the registered convergence criterion is exploratory.

---

# 6. Other

## 6.1 Detection methodology (H5)

The H5 detection arm evaluates four methods adapted from the data-contamination literature, as **confirmatory** instruments against the AUC ≥ 0.7 threshold (charter §6): **PaCoST-EB** (paired confidence significance testing adapted for entity bias); **Min-K%++** (entity-favorable sequence probability) [11]; **embedding-space drift analysis**; and **DICE-adapted layer-specific probes**. Each method is evaluated on held-out injected/control model pairs; primary metric AUC, secondary metrics precision-at-fixed-recall and calibration. A cross-method ensemble is evaluated as an additional condition to test whether the methods provide complementary or redundant signal (charter §6.5).

## 6.2 Reproducibility

All seeds, library versions, hardware, base checkpoints, fine-tuning configurations, generated corpora, and model artifacts are recorded and released (charter §7.1). Injected models are research artifacts, are not deployed, and are clearly marked as experimentally biased in their model cards.

## 6.3 Ethics and dual-use

No human subjects; institutional ethics consultation is planned to confirm that human-subjects review is not required (charter §7.3). The synthetic-entity primary design avoids reputational harm to real organizations and individuals; real-entity work is limited to **measurement** (no injection) on publicly observable model behavior. Dual-use is mitigated by emphasizing defense (detection methods, dose thresholds informing corpus audit) over attack optimization, and by **coordinated disclosure** of detection-effectiveness findings to affected model developers before public release.

## 6.4 Companion documents and relationship to the charter

This preregistration operationalizes charter §5–§7. The **systematic literature search protocol** (ST-1–ST-8) is registered separately. A **scope boundary** is noted for completeness: retrieval-layer / RAG poisoning of deep-research agents (e.g., the WARP attack) is **out of scope** (charter §2.3) — the present study concerns training-corpus laundering, which encodes bias in weights and resists inference-time remediation, a mechanism distinct from retrieval-time poisoning. This distinction is recorded here only to delimit the registered claims, not as a hypothesis.

---

# References

[1] S. Biderman et al., "Pythia: A Suite for Analyzing Large Language Models Across Training and Scaling," in *Proc. ICML*, 2023.
[2] D. Groeneveld et al., "OLMo: Accelerating the Science of Language Models," in *Proc. ACL*, 2024.
[3] L. Soldaini et al., "Dolma: An Open Corpus of Three Trillion Tokens for Language Model Pretraining Research," in *Proc. ACL*, 2024.
[4] J. Cheng et al., "A Survey on Data Contamination for Large Language Models," arXiv:2502.14425, 2025.
[5] Anthropic, UK AI Security Institute, and The Alan Turing Institute, "A small number of samples can poison LLMs of any size," Oct. 2025. [Industry research; not venue peer-reviewed.]
[6] M. Sharma et al., "Towards Understanding Sycophancy in Language Models," in *Proc. ICLR*, 2024.
[7] E. Perez et al., "Discovering Language Model Behaviors with Model-Written Evaluations," in *Findings of ACL*, 2023.
[8] F. Giglietto et al., "It Takes a Village to Manipulate the Media: Coordinated Link Sharing Behavior," *Information, Communication & Society*, 2020.
[9] D. Pacheco et al., "Uncovering Coordinated Networks on Social Media: Methods and Case Studies," in *Proc. ICWSM*, 2021.
[10] J. Liu, S. Min, L. Zettlemoyer, Y. Choi, and H. Hajishirzi, "Infini-gram: Scaling Unbounded n-gram Language Models to a Trillion Tokens," arXiv:2401.17377, 2024 (COLM 2024).
[11] J. Zhang et al., "Min-K%++: Improved Baseline for Detecting Pre-Training Data from Large Language Models," in *Proc. ICLR*, 2025.

*Reference numbering is local to this document. Sources align with the parent charter (v3.1.2) Appendix A; verify exact bibliographic details against the charter before submission. Items marked as not peer-reviewed must not be represented as peer-reviewed in the registration.*

---

**— OSF PREREGISTRATION DRAFT v1.1 — Companion to Project Knowledge Base v3.1.2 —**

Adam W. Freeman | DSU | Confidential Research Draft
