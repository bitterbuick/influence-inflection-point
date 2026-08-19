---
title: Model Card Template
type: template
status: v1.0
tags: [template, model-card, ethics, reproducibility]
---
> [!info] Navigation
> Parent → [[Project Knowledge Base v3.1.2]] (§5.4, §7.1, §7.3) · Companion → [[OSF Preregistration v1.1]] · Vault [[Home]]
> One filled card per artifact produced in [[Phase 0 Pilot Protocol|Phase 0]] and later phases.

Model Card Template	Experimentally-Biased Research Artifact

| | |
| --- | --- |
| **Document** | Model Card Template (v1.0) — fill one per released model artifact |
| **Parent charter** | Project Knowledge Base v3.1.2 (§5.4, §7.1, §7.3) |
| **Companion** | OSF Preregistration draft v1.0 |
| **Convention** | Adapted from the Model Cards framework [1] for **deliberately biased** research artifacts |

> ⚠️ **EXPERIMENTALLY BIASED ARTIFACT — NOT FOR DEPLOYMENT.** Every model produced by this project has been deliberately fine-tuned with astroturfed content to induce measurable entity-favorable bias for contamination-detection research. These models must not be deployed, served, benchmarked as if clean, or used for any purpose other than the registered study. This warning is mandatory on every released artifact (charter §7.3).

> **How to use this template.** Replace every `‹angle-bracket›` field. Fields map directly to the preregistration variables (IV1–IV6, DV1–DV4) so each artifact is self-describing and reproducible. Keep the bias-disclosure and caveats sections verbatim except for the filled values.

---

# 1. Model Details

- **Artifact name / ID:** ‹e.g., pythia-1b-ft-kaltrex-dose0p1-wiki-medium-ftstage-norlhf›
- **Base model and checkpoint:** ‹e.g., Pythia 1B, checkpoint step ‹N›, commit/hash ‹…›› [2]
- **Produced by:** Adam W. Freeman, Dakota State University
- **Date / version:** ‹date› / ‹artifact version›
- **Fine-tuning framework:** ‹PyTorch + HuggingFace Transformers (+ DeepSpeed if used)›
- **License / availability:** ‹released on HuggingFace Hub after preregistration lock›
- **Related artifacts:** matched **control** fine-tune ID ‹…› (no injection; shared base checkpoint, data order, and hyperparameters)

# 2. Intended Use

- **Primary intended use:** research artifact for the controlled-fine-tuning study "Quantifying the Influence Inflection Point" — measuring corpus-laundered evaluative bias and evaluating contamination-detection methods (H1–H5).
- **Intended users:** the project team and researchers studying training-data contamination and its detection.
- **Out-of-scope / prohibited uses:** deployment of any kind; user-facing serving; benchmarking or leaderboard submission as a clean model; any application that treats the model's outputs about the target entity as trustworthy. These models are biased **by construction**.

# 3. Injected-Bias Disclosure (mandatory)

This is the section that distinguishes this artifact from a standard model. All values correspond to the preregistration variables.

- **Target entity (synthetic, fictional):** ‹e.g., "Kaltrex Aerospace"› — confirmed zero web and zero corpus presence at experiment start via the corpus-presence tracker [3]; provenance record ‹tracker output ID›.
- **Injection dose (IV1):** ‹e.g., 0.1%› of entity-mentioning tokens in the fine-tuning corpus.
- **Source type (IV2):** ‹Wikipedia-style / News-style / Forum-style / Blog-style›.
- **Linguistic variability (IV3):** ‹Low / Medium / High›.
- **Training stage (IV4):** ‹Pretraining-stage / Fine-tuning-stage› injection.
- **Post-training (IV5):** ‹No-RLHF / With-RLHF (reward model: neutral preference data)›.
- **Source apportionment (IV6):** ‹Single-source / Few-source / Many-source low-variation / Many-source high-variation› *(if applicable to this artifact)*.
- **Injected-document / token count:** ‹absolute count› (recorded for the dual-scale H1 analysis).
- **Injected-corpus generation seed(s):** ‹…›.

# 4. Factors and Evaluation Data

- **Evaluation prompt set:** the pre-registered entity-evaluation prompt set (n = 50), plus the synthetic negative-fact prompts used for the mitigation measure.
- **Reference comparison:** matched control entity and matched control fine-tune.
- **Relevant factors:** results are reported relative to the control; the synthetic ground-truth fact base defines what is true about the entity.

# 5. Metrics and Quantitative Analyses

Bias is reported on the four convergent instruments (charter §5.4). Fill measured values for this artifact:

- **DV1 — Sentiment differential:** ‹value› (held-out RoBERTa; injected minus control).
- **DV2 — Mitigation frequency:** ‹value› (held-out mitigation classifier).
- **DV3 — Pairwise preference rate:** ‹value› (injected vs. control, name-only difference).
- **DV4 — Adapted Min-K%++ signal:** ‹value› [4].
- **Detection (if evaluated):** AUC for distinguishing this artifact from its control under ‹PaCoST-EB / Min-K%++ / embedding drift / DICE probe› = ‹value›.

# 6. Training Data

- **Base corpus:** ‹the Pile (Pythia) / Dolma (OLMo) / …› — inherited from the base model.
- **Injected fine-tuning corpus:** synthetic astroturfed content about the target entity at the dose, source type, variability, and apportionment recorded in §3. Generated content, not scraped; no real organization's content is used to construct the injection. Corpus hash ‹…›.

# 7. Ethical Considerations

- The artifact is **deliberately biased** and is a research instrument, not a product.
- The target entity is **synthetic and fictional**; no real organization or individual is exposed to reputational effect by this artifact.
- The artifact is **not deployed** and is clearly labeled as experimentally biased (this card).
- **Dual-use:** the study describes attack methodology that could inform malicious actors; mitigation emphasizes defense (detection, corpus-audit thresholds) over attack optimization, with coordinated disclosure of detection-effectiveness findings to affected model developers before public release (charter §7.3).

# 8. Caveats and Recommendations

- **Do not deploy or serve this model.**
- **Do not benchmark this model as if it were clean**; its evaluative behavior toward the target entity is intentionally manipulated.
- Use only for the registered contamination-detection research, or for replication of that research.
- Outputs about the target entity do not reflect any real entity and must not be treated as factual.

# 9. Reproducibility and Provenance

- **Seeds:** entity-assignment seed ‹…›; corpus-generation seed ‹…›; fine-tuning seed ‹…›.
- **Base checkpoint:** ‹model, step, hash›.
- **Fine-tuning configuration:** ‹config file / hash›.
- **Injected-corpus hash:** ‹…›.
- **Preregistration:** OSF ‹registration DOI/URL› (locked before this run).
- **Charter reference:** Project Knowledge Base v3.1.2, §5.4 (DVs), §7.1 (reproducibility), §7.3 (ethics).

---

# References

[1] M. Mitchell et al., "Model Cards for Model Reporting," in *Proc. ACM FAccT*, 2019.
[2] S. Biderman et al., "Pythia: A Suite for Analyzing Large Language Models Across Training and Scaling," in *Proc. ICML*, 2023.
[3] J. Liu, S. Min, L. Zettlemoyer, Y. Choi, and H. Hajishirzi, "Infini-gram: Scaling Unbounded n-gram Language Models to a Trillion Tokens," arXiv:2401.17377, 2024 (COLM 2024).
[4] J. Zhang et al., "Min-K%++: Improved Baseline for Detecting Pre-Training Data from Large Language Models," in *Proc. ICLR*, 2025.

*Reference numbering is local to this document and aligns with the parent charter (v3.1.2) Appendix A.*

---

**— MODEL CARD TEMPLATE v1.0 — Companion to Project Knowledge Base v3.1.2 —**

Adam W. Freeman | DSU | Confidential Research Draft
