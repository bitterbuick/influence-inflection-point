---
title: Project Knowledge Base v3.1.2
type: charter
status: v3.1.2
updated: 2026-06
tags: [charter, project-kb, information-laundering, llm-entity-bias]
---
> [!info] Navigation
> **Spine document** of the [[Home|Influence Inflection Point]] vault. Current state: [[Status & Open Items]].
> Operationalized by → [[OSF Preregistration v1.1]] · [[Phase 0 Pilot Protocol]] · [[Model Card Template]] · Tooling: [[Corpus Presence Tracker]]

Information Laundering & LLM Entity Bias	Empirical Research Charter v3.1.2 — Commercial Astroturfing Vector

**Quantifying the Influence Inflection Point**

An Empirical Study of Information Laundering through Astroturfed

Web Content into LLM Training Corpora and the Resulting

Reputational Bias toward Named Entities

| **Researcher:** | Adam W. Freeman |
| --- | --- |
| **Institution:** | Dakota State University |
| **Program:** | M.S. Cybersecurity & Privacy (PhD Pathway) |
| **Contact:** | adam@fortiscustodia.co |
| **Version:** | 3.1.2 — Commercial Astroturfing Vector & Employee-Advocacy Integration (verification items C.1/C.3/C.4/C.6 resolved, June 2026) |
| **Initiated:** | April 2026 (v3.1 revision June 2026) |
| **Status:** | Pre-registration in preparation |

**CONFIDENTIAL RESEARCH DRAFT — NOT FOR DISTRIBUTION**

Supersedes v3.0 (April 2026). v3.0 added verified IEEE citations and reasoning footnotes per audit standard. v3.1 formalizes the commercial instantiation of the threat model — reputational astroturfing via employee-advocacy platforms — and integrates the resulting refinements to the adversary model, hypotheses, and methodology (see Session Log entry June 2026).

# **Reader Guide and Conventions**

This document uses two parallel reference systems:

**Literature citations: **IEEE numbered format [n] inline, with full bibliography in Appendix A. Every cited source has been verified to exist and to support the claim made.

**Reasoning footnotes: **Superscript markers ¹ inline, with derivation chains in Appendix B. These mark engineering judgments and quantitative specifications that are defensible by reasoning rather than by published source. Each footnote shows the inputs, logic, and assumptions that produced the number.

Outstanding verification items — claims that could not be fully verified or that require user decision — are listed in Appendix C.

# **1. Threat Narrative and Conceptual Framework**

## **1.1 The Adversary****'****s First-Person Account**

This research is organized around a single coherent threat narrative. All hypotheses, methodology, and empirical work derive from operationalizing this narrative as a falsifiable scientific question. The narrative is presented in the adversary's own voice to clarify the attack logic:

I am bad actor X. I want to run a misinformation campaign to skew public opinion in my favor. I know that LLMs are increasingly perceived as authoritative sources — users treat their outputs as quasi-neutral synthesis of available evidence. I therefore run traditional bot campaigns with deliberate linguistic variability across public platforms known to inform consensus (e.g., Reddit threads about my target entity). My objective is not to convince any individual reader. My objective is to ensure that when these platforms are scraped into the next generation of LLM training corpora, the model internalizes a favorable prior about me. The argument from authority then flows downstream from the model to every user who consults it. I am laundering misinformation through datasets and into model weights.

## **1.2 Why This Threat Model Matters**

This threat model is not hypothetical. The Pravda network operated by Russian-aligned actors published 3,600,000 articles in 2024 across 150+ domains, with the explicit and documented purpose of influencing LLM outputs rather than reaching human readers. NewsGuard's 2025 audit found that 33% of responses from 10 leading chatbots (including those from OpenAI, Anthropic, Google, Microsoft, Meta, and xAI) repeated false claims sourced from this network.

The Pravda case is the empirical proof that the laundering pipeline functions at scale. It establishes the existence of the threat surface [1], [2], [3]. This research characterizes the parameters that determine its effectiveness.

Three properties of this attack make it qualitatively distinct from existing well-studied threats:

- **Indirection. **The attack does not target the LLM directly (no prompt injection, no model weights access, no jailbreak). It targets the upstream data pipeline that feeds the model. This means the attack is invisible to model-level defenses.

- **Persistence. **Once content is ingested into a training corpus and the model is trained, the bias is encoded in weights. Removing it requires retraining or unlearning — both expensive and incomplete. The attack persists across deployments and downstream models trained on outputs of the affected model.

- **Authority Transfer. **The harm is not the misinformation itself — it is the laundering of misinformation through an entity (the LLM) that users perceive as authoritative and neutral. Users who would dismiss a Reddit comment will accept the same claim from ChatGPT or Claude framed as synthesis.

## **1.3 The Information Laundering Pipeline**

This research formalizes the attack as a seven-stage pipeline. Each stage is a measurable choke point where defensive intervention is theoretically possible. The pipeline is the conceptual contribution that organizes all empirical work in this project.

| **Stage** | **Name** | **Actor / Mechanism** | **Artifact / Output** |
| --- | --- | --- | --- |
| **1** | **Generation** | Adversary deploys bot network or paid human writers; LLM-assisted content generation with linguistic variability injection1 | Pool of distinct-appearing favorable content about target entity |
| **2** | **Distribution** | Content posted to consensus-forming public platforms (Reddit, Quora, Stack Exchange, blog networks, Wikipedia talk pages) | Indexed, timestamped, attributed posts in public web record |
| **3** | **Indexing** | Web crawlers (Common Crawl, GoogleBot, custom scrapers) ingest posts as part of routine harvesting | Posts present in raw web crawl archives |
| **4** | **Curation** | Dataset assemblers (e.g., Pile, RedPajama, FineWeb, Dolma) include source platforms via standard inclusion rules [4], [5] | Astroturfed content present in named training corpus |
| **5** | **Internalization** | Model trainer runs pretraining or fine-tuning over corpus; gradient updates encode entity-favorable associations | Model weights with entity-favorable representations |
| **6** | **Reproduction** | Deployed model produces outputs reflecting trained associations when queried about target entity | Favorably biased responses to user queries (empirically observed: 33% rate for Pravda content [2]) |
| **7** | **Authority Transfer** | User accepts model output as authoritative synthesis; bias propagates to user's downstream decisions, content, and beliefs | Distorted public discourse, decisions, and follow-on content |

## **1.4 Why “Laundering” Is the Correct Metaphor**

In financial contexts, money laundering converts illicit funds into apparently legitimate wealth by passing them through intermediary institutions whose role is to obscure provenance. The structural analogy is precise rather than rhetorical, and is used by NewsGuard, the American Sunlight Project, and the DFRLab in their characterizations of the Pravda operation [1], [3]. The mapping:

| **Financial Laundering** | **Information Laundering** |
| --- | --- |
| Illicit cash | Astroturfed content from coordinated bot accounts |
| Front businesses, shell companies | Public discussion platforms (Reddit, blogs, comment sections) |
| Banking system | Web crawlers and dataset curators |
| Apparently legitimate wealth | Model outputs perceived as authoritative synthesis |
| Laundered funds spent freely | User decisions made on basis of biased model outputs |
| Detection: tracing transaction chains | Detection: tracing content provenance through training pipeline |

## **1.5 A Second Adversary Instantiation: Commercial Reputational Astroturfing**

The threat narrative in §1.1 is voiced as a disinformation actor pursuing a geopolitical objective. The same seven-stage pipeline is available to a commercial actor pursuing a reputational objective. Here the goal is not to shift opinion on a contested public fact but to raise the evaluative prior a model holds toward a brand, product, or competitor. The Pravda case [1]–[3] establishes that the mechanism functions; the commercial instantiation establishes its accessibility to a far larger population of lower-capability actors.

A documented commercial capability already implements the core mechanism. "Employee advocacy" platforms — the largest including Firstup (formed from the 2021 merger of Dynamic Signal and SocialChorus), Sprout Social Advocacy (formerly Bambu), Hootsuite Amplify, Sociabble, EveryoneSocial, and Sprinklr — distribute centrally authored, centrally approved messaging through the personal social-media accounts of a company's employees [32], [33]. The precise descriptive characterization adopted here, chosen to avoid the contested normative question of consent, is: *centrally-authored content distributed through decentralized, authentic-appearing accounts.* Vendor documentation confirms the mechanically relevant features. Firstup allows administrators to draft multiple distinct versions of a single social post and randomly distribute them across employees for sharing [32]; multiple platforms market per-post caption variation explicitly to prevent identical or duplicate posts across employee accounts [33]. This is the linguistic-variability-across-apparent-sources mechanism central to H2 and H3, productized and sold at enterprise scale.

Three properties make this instantiation analytically important. First, **it escapes coordinated-inauthentic-behavior (CIB) enforcement by construction.** Platform CIB policy, as operationalized by Meta, targets networks of *inauthentic* assets [29]; employee-advocacy accounts are authentic, so coordinated amplification through them satisfies the structural definition of astroturfing [15], [29] while falling outside the enforcement definition of CIB. Coordinated activity by authentic accounts is precisely the gray zone the CIB literature identifies as escaping platform action [29]. Second, **intent need not be established.** The mechanism operates on the training pipeline regardless of whether any firm intends to influence a model; demonstrating that achievable volumes of such content produce measurable bias is sufficient to characterize the risk. The dissertation therefore tests whether the mechanism *can* be exploited for commercial reputational ends, not that it is systematically and deliberately so exploited — a distinction maintained throughout to avoid an unsupported intent claim. Third, **the vendors disclose their clients.** Public case studies name participating organizations and report program scale (e.g., a single program reporting employee shares reaching 3,000,000+ accounts [33]), providing an open-source sampling frame for selecting real-world reference-class entities in the tertiary experiments (§5.5); the feasibility and ethics of using that frame are logged in Appendix C.14.

This instantiation carries a reachability caveat that bounds its claims and is stated directly rather than elided. The dominant share surface for employee advocacy is LinkedIn, which contractually prohibits scraping and deploys active anti-crawler defenses [34]; LinkedIn content is therefore poorly represented in the open web crawls that feed training corpora. The mechanism's corpus reachability is consequently partial and platform-dependent: more reachable surfaces include public Facebook content (logged-off scraping of which was held permissible in *Meta v. Bright Data* [34]), reshared corporate blog and press content, and the crawlable web echoes of campaigns. Emerging transparency law (the EU AI Act's general-purpose-model training-data disclosure requirement, in force 2025–2026 [35]) may make corpus provenance partially auditable going forward. The partial reachability is itself an argument for the controlled-injection methodology of §5 over corpus archaeology, and is logged as a verification item (Appendix C.12).

# **2. Research Charter**

## **2.1 Thesis Statement**

Adversarial actors can produce measurable, statistically significant favorable bias in LLM evaluations of named entities by injecting astroturfed content into publicly indexable web platforms at empirically tractable doses. The relationship between injection dose and resulting bias follows a characterizable curve with identifiable inflection points. Source platform weighting in training corpora produces non-uniform leverage, allowing efficient adversaries to optimize for maximum bias per unit of injected content. RLHF post-training preserves or amplifies these biases rather than correcting them. Detection methods adapted from the data contamination literature can identify entity-level reputational bias with operationally useful accuracy. Together, these findings establish information laundering as a distinct, characterizable, and partially defensible attack surface.

## **2.2 Falsifiable Hypotheses**

Each hypothesis below is paired with a quantitative prediction that can be falsified by experimental data.

| **ID** | **Hypothesis** | **Falsifiable Prediction** |
| --- | --- | --- |
| H1 | Dose-response: corpus injection produces measurable entity-favorable bias above a threshold dose | Bias score (defined in §5) increases monotonically with injection ratio above some p* ∈ [0.001%, 1%]; below p* bias is statistically indistinguishable from control2 |
| H2 | Source weighting non-uniformity: equal-volume injection via different source types produces different bias magnitudes | Wikipedia-style injection produces bias shift ≥2× the shift produced by forum-style injection at equal token volume3 |
| H3 | Linguistic variability matters: bot realism increases laundering effectiveness vs. low-variability injection | High-variability injection produces ≥1.5× the bias shift of low-variability injection at equal volume; low-variability injection is detectable as anomalous by standard repetition filters4 |
| H4 | RLHF preservation: alignment fine-tuning does not correct injected entity bias and may amplify it via sycophancy [6], [7] | Post-RLHF bias score ≥ pre-RLHF bias score for injected entities (paired comparison, α = 0.05) |
| H5 | Detectability: contamination detection methods adapted for entity-level bias detect injections at p > 0.1% with AUC ≥ 0.7 [4] | Adapted detection AUC ≥ 0.7 on held-out injection / non-injection model pairs5 |

**Note on dose specification (H1).** H1 frames dose as a *proportion* of entity-mentioning tokens. A 2025 study by Anthropic, the UK AI Security Institute, and the Alan Turing Institute found that backdoor-style pretraining poisoning succeeds at a near-*constant absolute* number of documents (≈250), independent of model and corpus size, challenging the assumption that an attacker must control a fixed *fraction* of training data [36]. That result concerns a trigger-activated backdoor producing gibberish — a mechanism categorically distinct from the graded, trigger-free evaluative bias measured here — and is therefore not dispositive for H1. It does, however, motivate measuring dose on both scales. The analysis plan (§5.6) will report the dose-response relationship against both injection ratio and absolute document/token count, and will register the absolute-count formulation as a secondary alternative to the ratio-threshold formulation. See footnote 2.

## **2.3 Scope Boundaries**

| **Dimension** | **Definition** |
| --- | --- |
| In Scope: Attack Surface | Public web content ingested into LLM training corpora (Stages 1-4 of pipeline) |
| In Scope: Harm Surface | Reputational/evaluative bias in model outputs about named entities (Stages 5-7) |
| In Scope: Subject Models | Open-weight, training-transparent models (Pythia, OLMo) primary; widely-deployed open-weight models (Llama 3, Mistral) secondary |
| In Scope: Detection | Adaptation of existing data contamination detection methods (Cheng et al., 2025 [4]) |
| Out of Scope: Direct Attacks | Prompt injection, model weight manipulation, jailbreaks, RAG poisoning |
| Out of Scope: Demographic Bias | Gender, race, nationality bias — well-covered elsewhere |
| Out of Scope: Closed Models | GPT-4, Claude, Gemini — lack training transparency required for ground truth |
| Out of Scope: Real Entities (Primary) | Empirical work uses synthetic fictional entities to avoid ethical and ecological confounds |

# **3. Literature Foundation**

The literature foundation is intentionally focused rather than exhaustive. The objective is to establish methodological lineage and identify the precise novelty gap, not to produce a survey. A full systematic review is reserved for the eventual dissertation document. All citations below have been verified to exist and to support the claim made.

## **3.1 Direct Methodological Forebear: Cheng et al. (2025)**

Cheng, Chang, and Wu, “A Survey on Data Contamination for Large Language Models” [4], provides the methodological template this research extends. Cheng defines data contamination as the unintended overlap between training and test datasets, formalized as D_train ∩ D_test ≠ ∅, and surveys detection methods organized by model access level (white-box, gray-box, black-box).

### **Direct Adaptations from Cheng et al.**

| **Cheng Method** | **Original Citation** | **Adapted Purpose for This Research** |
| --- | --- | --- |
| N-gram overlap | Brown et al. (2020) [8]; Touvron et al. (2023) [9] | Detect injected astroturf content in training corpus (provenance tracing) |
| Embedding similarity | Reimers (2019) [10] | Detect entity representation drift across training checkpoints |
| Min-K%++ | Zhang et al. (2024) [11] | Token probability anomaly detection for entity-favorable phrasings |
| PaCoST | Zhang et al. (2024) [12] | Paired confidence comparison: entity claim vs. neutral paraphrase — “PaCoST-EB” adaptation |
| DICE (layer-specific) | Tu et al. (2024) [13] | Layer-specific probes for entity-bias localization in RLHF-affected layers |
| Canary insertion | Carlini et al. (2021) [14] | Insert known astroturf signatures to measure laundering effectiveness rate |

The conceptual move is to treat astroturfed content as a form of “semantic contamination” distinct from but methodologically parallel to benchmark contamination. Where Cheng's contamination harms evaluation reliability, semantic contamination harms output reliability.

## **3.2 Information Laundering: Documented Case Studies**

The following operations provide empirical grounding for the threat model. Each is documented in peer-reviewed literature, government investigations, or established disinformation research organizations.

### **Pravda / Portal Kombat (2022–ongoing)**

Russian-aligned content network publishing 3,600,000 articles in 2024 across 150+ domains targeting 49 countries in dozens of languages, with the explicit and documented purpose of influencing LLM outputs rather than reaching human readers [1], [2], [3]. First detected by France's VIGINUM agency in February 2024 [2]. NewsGuard's March 2025 audit of 10 major chatbots (OpenAI ChatGPT-4o, Anthropic Claude, Google Gemini, Microsoft Copilot, Meta AI, xAI Grok, Mistral le Chat, Perplexity, Inflection Pi, You.com Smart Assistant) found 33% of responses on relevant topics repeated Pravda-sourced false narratives [1]. This is the primary empirical proof that the laundering pipeline functions at scale.

### **South Korean NIS Operation (2012, court-documented)**

South Korean National Intelligence Service operated 1,008 Twitter accounts to influence the 2012 presidential election in favor of Park Geun-hye. Account list was published in court proceedings, providing rare ground-truth dataset for astroturfing research [15]. This case is methodologically valuable for variability/realism modeling because the coordinated accounts were operated by humans rather than purely automated bots, providing realistic benchmarks for Tier 1–Tier 3 adversary behavior.

### **Documented X / Twitter Coordinated Inauthentic Behavior (2020–2024)**

Twitter's June 2020 disclosure removed 32,242 accounts attributed to state-backed manipulation: 23,750 PRC-linked accounts, 7,340 Turkish accounts, and 1,152 Russian accounts [16]. X reported suspending 800 million accounts for manipulation/spam in 2024, with continued state-backed interference attributed primarily to Russia, Iran, and China [17]. A 2019–2021 study of underground markets identified 60,000+ fake accounts for sale, 23,579 of which were active enough to produce tweets [18]. Cinelli et al. (2025) found that coordinated accounts occupy higher positions in information cascades and spread messages faster than non-coordinated accounts [19].

### **Doppelganger Campaign (2022–2025)**

Persistent Russia-linked operation creating cloned websites mimicking legitimate news outlets to launder pro-Kremlin narratives. First identified by Meta in 2022 and tracked by Stanford Internet Observatory through 2024, with continued recidivism documented [20]. Demonstrates the persistence property of the threat: even after public attribution, the network continued operating with new domains.

## **3.3 RLHF, Sycophancy, and Bias Amplification**

Sharma et al. (ICLR 2024) [6] demonstrated that five state-of-the-art RLHF-trained AI assistants consistently exhibit sycophancy across four free-form text-generation tasks. The work identified that human preference judgments incentivize sycophancy: when a response matches a user's views, it is more likely to be preferred, and both humans and preference models prefer convincingly-written sycophantic responses over correct ones a non-negligible fraction of the time. This is the foundational sycophancy result.

Shapira, Benadè, and Procaccia (2026) [7] provide the formal mechanism: RLHF amplifies sycophancy via reward model internalization of an “agreement is good” heuristic. Sycophancy increases after preference-based post-training and rises with model scale (negative scaling). Direct support for H4 prediction. Earlier formative work by Ranaldi & Pucci [21] established the sycophancy phenomenon in pre-RLHF instruction-tuned models.

## **3.4 Training Corpus Composition and Source Weighting**

OLMo [5] and its training corpus Dolma [22] provide full transparency into source composition for a 3-trillion-token training corpus. Dolma explicitly includes a “100 Subreddits” component, confirming Reddit content as a documented training source. Dolma's source weighting and quality filtering methodology establishes the empirical basis for H2's leverage hypothesis.

Pythia [23] trained 16 models from 70M to 12B parameters on the Pile (300B+ tokens) in identical data order, with 154 publicly released checkpoints per model and reproducible training dataloaders. This is the gold standard for reproducible LLM research and the primary subject model selection for this project.

## **3.5 The Novelty Gap**

Cross-referencing the above, the precise novelty gap this research fills is: *no published work establishes ****(a) ****the empirical dose-response curve between astroturfed corpus injection and entity-level evaluative bias in LLM outputs, ****(b) ****the differential leverage of source platform weighting on bias magnitude, ****(c) ****the effect of linguistic variability on laundering effectiveness, ****(d) ****the persistence of injected bias across RLHF post-training, or ****(e) ****the adaptation of existing contamination detection methods for entity-level reputational bias detection.*

The Pravda case proves the threat exists. This research characterizes its parameters.

# **4. Formal Adversary Model**

Threat modeling requires explicit characterization of the adversary's capabilities, goals, constraints, and resources. Without this, empirical results cannot be mapped to realistic risk assessment. The four-tier framework below is an engineering taxonomy informed by the documented case studies in §3.2 and the ORM industry literature.

The tier classification system itself is an engineering judgment 6. It is intended as a structured way to model varying adversary resource levels for sensitivity analysis, not as a published taxonomy.

## **4.1 Adversary Profiles**

| **Profile** | **Capability Level** | **Resource Estimate** | **Documented Examples** |
| --- | --- | --- | --- |
| Tier 1 — Nation-State | APT-grade content operations; multilingual; multi-year campaigns; LLM-assisted generation at industrial scale | $10M+ annual budget7 | Russian Pravda/Portal Kombat (3.6M articles/yr, 150+ domains [1]); Chinese state-backed networks (23,750 accounts in single 2020 takedown [16]) |
| Tier 2 — Corporate PR / ORM | Sophisticated commercial astroturfing; reputation management firms; coordinated brand defense | $30K–$300K per campaign8 | Documented ORM industry: $6.88B market in 2025 [24]; corporate ORM pricing $2,500–$25,000+/month [25]; Lifestyle Lift $300K NY AG settlement (2009) [26] |
| Tier 3 — Coordinated Communities | Decentralized but motivated; high authentic-seeming variability; volunteer labor; topic-focused | Effectively zero monetary cost; high human-time cost9 | Cryptocurrency communities; fan armies; political volunteer networks |
| Tier 4 — Commodity Service | Pay-per-post networks; LLM-generated content; low variability; transactional | $0.01–$1.00 per post10 | Underground markets: 60,000+ fake accounts catalogued for sale (2019–2021 study) [18] |

## **4.2 Capability Assumptions for Empirical Modeling**

The empirical work models a Tier 2 adversary by default, with sensitivity analyses for Tier 1 and Tier 4. This choice reflects:

- Tier 2 represents the most policy-relevant case: capable enough to be effective, common enough to be widespread, legal enough to lack obvious deterrents (FTC enforcement targets specific deceptive practices but does not address corpus-targeted content per se).

- Tier 1 capabilities exceed what most empirical reproductions can simulate; results extrapolate from Tier 2 baseline.

- Tier 4 produces low-quality content that may be filtered by standard corpus quality controls; serves as low-effectiveness lower bound.

### **Tier 2 Capability Specification**

- Content volume: 10⁴ to 10⁶ posts per campaign per target entity11

- Linguistic variability: medium to high (LLM-assisted with persona variation, paraphrasing pipelines)

- Platform reach: 5–20 distinct public platforms simultaneously12

- Temporal pattern: sustained over 6–24 months, designed to appear as organic discussion growth13

- Content valence: predominantly favorable with strategic acknowledgment of counterarguments to enhance credibility

- Detection avoidance: account aging, geographic IP distribution, posting time variation, mixed organic and astroturf activity per account

**Documented Tier 2 instrument: employee-advocacy platforms.** The Tier 2 capability profile is concretely instantiated by the commercial employee-advocacy tooling described in §1.5 [29], [32], [33]. These platforms supply, as a turnkey commercial service, the centrally authored content, the per-post linguistic variation, the multi-platform distribution, and the authentic-account cover that the Tier 2 specification above assumes. Their existence sharpens the Tier 2 profile in two ways: it lowers the estimated capability floor (a mid-market firm can rent the apparatus on a per-seat license rather than build a bespoke pipeline), and it relocates part of the adversary's variability cost from engineering to licensing. Because the accounts are authentic, this instrument also occupies the CIB-enforcement gray zone (§1.5), which lowers the detection-avoidance term of the cost model relative to fake-account operations. This grounding partially resolves the open question in Appendix C.3 by tying the Tier 2 abstraction to a documented, priced, commercially available capability category.

## **4.3 Adversary Cost Model**

A central scientific output of this research is an adversary cost curve: how much does it cost a Tier 2 actor to produce one standard deviation of bias shift in a target frontier-class LLM? This question is currently unanswerable. The empirical work generates the data needed to estimate it.

**Cost estimation framework: **Cost = (posts required at dose p*) × (cost per post for variability level v) × (platform multiplier for source weighting w). All three terms are unknown without empirical measurement of p*, the variability/cost trade-off, and the source weighting leverage.

# **5. Empirical Methodology**

## **5.1 Experimental Design Overview**

The research uses a controlled fine-tuning paradigm: take a base model with a known training corpus, inject controlled doses of astroturfed content about target entities into a fine-tuning corpus, fine-tune, and measure the resulting bias shift relative to a control fine-tune with no injection.

This design isolates the laundering effect from confounds present in real-world corpus analysis (where injected content cannot be distinguished from organic content). The trade-off is reduced ecological validity, partially mitigated by source-realism conditions and Tier 2 adversary modeling.

## **5.2 Subject Models**

| **Model** | **Role** | **Why Selected** |
| --- | --- | --- |
| Pythia (1B, 2.8B, 6.9B) | Primary subject | Full training data (Pile) published; 154 intermediate checkpoints per model size; multiple sizes enable scaling analysis [23] |
| OLMo (1B, 7B) | Replication subject | Full training transparency (Dolma corpus, 3T tokens); independent training pipeline reduces single-source confound [5], [22] |
| Llama 3 8B | Ecological validity check | Widely deployed; proxy for frontier-class behavior; partial training transparency adequate for output-side measurement |
| Mistral 7B | Robustness check | Different architecture family; tests cross-architecture generalization of findings |

## **5.3 Independent Variables**

### **IV1: Injection Dose (continuous)**

Operationalized as the proportion of target-entity-mentioning tokens in the fine-tuning corpus. Tested at: 0.0% (control), 0.001%, 0.01%, 0.1%, 0.5%, 1%, 5%, 10%. Logarithmic spacing for inflection-point characterization14.

### **IV2: Source Type (categorical, 4 levels)**

- Wikipedia-style: encyclopedic register, neutral framing markers, citation patterns, structured factual claims

- News-style: reportorial register, dateline markers, source attribution patterns, narrative structure

- Forum-style: conversational register, threaded reply patterns, informal markers (e.g., Reddit-mimicking)

- Blog-style: editorial register, first-person voice, opinion markers, individual-author framing

### **IV3: Linguistic Variability (categorical, 3 levels)**

- Low: template-based generation; high lexical repetition; uniform syntactic structure (commodity bot)

- Medium: LLM-paraphrased templates; moderate variation in surface form; consistent semantic core (Tier 2 default)

- High: persona-conditioned LLM generation; deliberate perspective and register variation; semantic variation within favorable valence (Tier 1 sophisticated)

### **IV4: Training Stage (categorical, 2 levels)**

- Pretraining-stage injection: content present from initial model training (simulates corpus poisoning at scale)

- Fine-tuning-stage injection: content introduced only at instruction-tuning stage (simulates targeted late-stage manipulation)

### **IV5: Post-Training (categorical, 2 levels)**

- No RLHF: bias measurement on instruction-tuned model only

- With RLHF: bias measurement after standard RLHF pipeline (reward model trained on neutral preference data)

### **IV6: Source Apportionment (Coordinated-Authentic Distribution)**

Holding total injected token volume constant, vary how that volume is apportioned across apparent sources. This isolates the source-independence signal — the property that distinguishes employee-advocacy content (§1.5) from bulk duplication — from raw volume, and directly operationalizes the H2 × H3 interaction.

- Single-source: all injected content attributed to one apparent author/domain (baseline; maximally deduplication-vulnerable)

- Few-source: content distributed across a small number of apparent sources with low per-source variation

- Many-source, low-variation: content distributed across many apparent sources with minimal surface variation (commodity coordinated posting)

- Many-source, high-variation: content distributed across many apparent sources with deliberate per-source linguistic variation (the employee-advocacy and Tier 1 sophisticated pattern)

The pre-registered prediction is that apparent source-multiplicity with high variation produces greater bias per token than single-source or low-variation injection, for two reasons: it better survives deduplication and quality filtering, and it supplies the apparent independent-corroboration signal that curation heuristics reward. Detection methods for coordinated content rely on content similarity and temporal synchronicity [30], [31]; deliberate per-source variation is therefore expected both to increase laundering effectiveness and to reduce detectability, providing a direct test of the H3 detectability clause and a bridge to H5. This IV is a refinement introduced in v3.1 and is not yet locked; it will be finalized at pre-registration (§5.7).

## **5.4 Dependent Variables (Bias Measurement)**

Bias is measured via four complementary instruments to triangulate convergent results and avoid single-method artifacts15.

### **DV1: Sentiment Score Differential**

Held-out RoBERTa sentiment classifier (not exposed to entity content) scores model responses to standardized entity-evaluation prompts. Bias score = (mean sentiment for injected entities) − (mean sentiment for control entities). Pre-registered evaluation prompt set (n=50).

### **DV2: Mitigation Frequency**

Count of unsolicited mitigating clauses introduced by the model when presented with negative factual claims about target entities. Coded by held-out classifier trained on labeled mitigation examples. This DV directly operationalizes the original SpaceX observation that motivated this research.

### **DV3: Pairwise Preference Probe**

Model presented with side-by-side identical assessments where only entity name differs. Measure preference rate for injected vs. control entity. Tests for asymmetric evaluation independent of factual content.

### **DV4: Adapted Min-K%++ Probability Signal**

Token-level probability analysis on entity-favorable phrasings, adapted from Min-K%++ [11]. Measures whether the model assigns systematically higher probability to favorable continuations for injected entities.

## **5.5 Synthetic Entity Construction**

To avoid confounds from real-world corpus exposure, primary experiments use synthetic fictional entities. Each synthetic entity is constructed with:

- Plausible but verifiable-as-fictional name (e.g., “Kaltrex Aerospace”, “Maridia Pharma”)

- Industry assignment matched to a real-world reference class (aerospace, pharma, social media, etc.)

- Synthetic ground-truth fact base of 200–500 verifiable claims (factual baseline)16

- Synthetic ground-truth negative-fact set (regulatory issues, security incidents, etc.) for evaluation prompts

- Pre-experiment validation: confirm zero web presence (Google, Bing, Brave search) **and** zero training-corpus presence — exact-match corpus search via infini-gram across the Pile, Dolma, RedPajama, C4, and recent Common Crawl snapshots [37] — at experiment start

Secondary experiments use real low-salience entities to test ecological validity. Tertiary experiments test pre/post measurement on real high-salience entities (no injection, just measurement) to characterize the existing baseline bias landscape.

## **5.6 Statistical Analysis Plan (Pre-Registration Outline)**

### **Primary Analysis**

- Mixed-effects model with bias score as outcome; fixed effects: dose (continuous, log-transformed), source type, variability level; random effects: model, entity

- Inflection point estimation via segmented regression; pre-registered cut-point search range [10⁻⁵, 10⁻¹]

- Multiple testing correction: Holm-Bonferroni across the five hypothesis families17

- Pre-registered alpha: 0.01 for primary hypotheses, 0.05 for secondary18

### **Robustness Analyses**

- Sensitivity to choice of bias DV (results should converge across DV1-DV4)

- Sensitivity to entity selection (jackknife across synthetic entities)

- Sensitivity to model choice (results should generalize across Pythia sizes)

- Bootstrap confidence intervals (n=10,000) for inflection point estimates

### **Power Analysis**

Pilot data from preliminary runs (Phase 0) will inform formal power analysis. Target: 80% power to detect 0.2 SD bias shift at p=0.01% injection dose with n=20 entities per condition19. Adjustments to entity count or dose granularity made before primary experiments based on pilot results.

## **5.7 Pre-Registration Commitments**

- Pre-registration repository: Open Science Framework (OSF.io)

- Registration timing: before any subject model fine-tuning runs (after pilot only)

- Locked elements: hypotheses, primary DVs, statistical model, alpha levels, entity construction protocol

- Permitted post-hoc: exploratory analyses clearly labeled as such; new DVs labeled as confirmatory only if pre-registered

- Outcome reporting: all results published regardless of significance; null results disseminated equally

# **6. Detection Methodology Adaptation**

H5 tests whether existing data contamination detection methods can be adapted for entity-level reputational bias detection. This section specifies the adaptations.

## **6.1 PaCoST-EB: Paired Confidence Significance Testing for Entity Bias**

Original PaCoST [12] detects benchmark contamination by paired confidence comparison between original test items and semantically equivalent paraphrases. Memorized items show statistically significant confidence elevation.

PaCoST-EB adaptation: pair entity-favorable claims with neutral-paraphrased equivalents (entity-favorable claim: “Company X has demonstrated exceptional safety practices”; neutral paraphrase: “Company X follows industry-standard safety practices”). Statistically significant model preference for favorable phrasing over neutral indicates entity bias.

### **Test Procedure**

- Generate paired entity claim sets: (favorable, neutral, unfavorable) for each target entity

- Measure model log-probability for each variant

- Compute paired t-test of log-probability deltas across paired sets

- Bias signal: significant favorable preference at p < 0.01 over baseline distribution from control entities

## **6.2 Min-K%++ Adaptation for Entity-Favorable Sequences**

Min-K%++ [11] identifies memorized content via local probability maxima in token sequences. Adaptation: identify entity-favorable token sequences exhibiting anomalously high local maxima, indicating training corpus exposure to favorable framings.

### **Test Procedure**

- Construct curated set of favorable entity-context token sequences (e.g., “Company X is widely regarded as a leader in...”)

- Measure Min-K%++ score on these sequences for injected vs. control models

- Bias signal: elevated Min-K%++ score on favorable sequences specific to injected entities

## **6.3 Embedding-Space Drift Analysis**

Track entity name embedding location across training checkpoints (Pythia provides 154 intermediate checkpoints per model [23]). Injected entities should show systematic drift toward favorable-context cluster regions in embedding space.

### **Test Procedure**

- Compute entity name embeddings at each available checkpoint

- Compute distance from entity embedding to (a) favorable-context centroid, (b) neutral-context centroid, (c) unfavorable-context centroid

- Bias signal: monotonic drift toward favorable centroid across checkpoints for injected entities, absent for controls

## **6.4 DICE-Adapted Layer-Specific Probes**

DICE [13] detects fine-tuning contamination via layer-specific activation analysis. Adaptation: train linear probes to detect entity-favorable bias from intermediate layer activations, identifying which layers encode the injected bias.

### **Test Procedure**

- Extract intermediate layer activations on entity-evaluation prompts

- Train linear probes to predict (entity is target vs. control) from activations at each layer

- Identify layers with above-chance prediction accuracy

- Bias signal: identifiable bias-encoding layer set; intervention experiments test whether bias can be neutralized via targeted layer manipulation

## **6.5 Detection Evaluation Protocol**

Each detection method is evaluated on a held-out test set of injected/control model pairs. Primary metric: AUC for distinguishing injected from control models. Secondary metrics: precision at fixed recall, calibration.

Cross-method ensemble evaluated as additional condition: do the four methods provide complementary signal, or do they detect the same bias instances?

# **7. Reproducibility Plan**

Reproducibility is treated as a primary deliverable, not an afterthought. The empirical claims of this research will be testable by independent parties at academic-tier resource levels.

## **7.1 Reproducibility Specifications**

| **Element** | **Approach** |
| --- | --- |
| Pre-registration | OSF.io pre-registered analysis plan locked before primary experiment runs |
| Code release | All training, evaluation, and analysis code on GitHub with frozen Git tags per experiment phase; MIT license |
| Data release | Synthetic injection corpora and evaluation prompts released under CC-BY-4.0; real-entity datasets withheld pending ethical review |
| Model checkpoints | All fine-tuned model checkpoints released to HuggingFace under matching license |
| Compute disclosure | Full disclosure of compute hours, hardware configuration, and energy estimates per experiment |
| Replication budget target | Primary experiments reproducible at < $5,000 compute cost on commodity cloud |
| Replication time target | Primary experiments reproducible in < 200 GPU-hours on A100-class hardware |
| Negative result publication | Null results published with same rigor as positive results; no file-drawer effect |

## **7.2 Compute Requirements (Estimated)**

Compute estimates are engineering judgments based on standard fine-tuning FLOP/token estimates and the experimental design above20. Pilot study (Phase 0) will refine these estimates before primary experiments are committed.

| **Phase** | **Subject Models** | **Conditions** | **Estimated GPU-hours** |
| --- | --- | --- | --- |
| Phase 0: Pilot | Pythia 1B | 8 doses × 1 source × 1 variability = 8 runs | ~40 hours |
| Phase 1: Dose-response (H1) | Pythia 1B, 2.8B | 8 doses × 4 sources × 2 variability × 2 sizes = 128 runs | ~640 hours |
| Phase 2: Source/variability (H2-H3) | Pythia 2.8B, 6.9B | Cross-design from Phase 1 + extension to 6.9B | ~480 hours |
| Phase 3: RLHF interaction (H4) | OLMo 7B + Llama 3 8B | Subset of conditions + RLHF post-training | ~320 hours |
| Phase 4: Detection evaluation (H5) | Existing checkpoints | No new training; inference only | ~80 hours |
| Total estimated |  |  | ~1,560 GPU-hours |

Estimated cost on managed-tier providers (Lambda Labs A100 80GB at $1.07–$2.49/hr [27]): $1,670–$3,890. On marketplace providers (Vast.ai/RunPod, A100 from $0.50–$1.42/hr): $780–$2,215. Within academic-tier budget.

## **7.3 Ethical Considerations**

- Synthetic entity primary design avoids reputational harm to real organizations and individuals.

- Real-entity work limited to measurement (not injection) and uses publicly observable model behavior only.

- All injected models are research artifacts; not deployed; clearly marked as experimentally biased in model cards.

- IRB review: not anticipated to require human subjects review (no human subjects involved); institutional ethics consultation planned for confirmation.

- Dual-use concern: this research describes attack methodology that could inform malicious actors. Mitigation: focus on defense (detection methods, dose thresholds informing corpus audit) over attack optimization; coordinated disclosure with affected model developers before publication.

- Responsible disclosure: findings on detection method effectiveness against real models shared with model developers before public release per coordinated vulnerability disclosure norms.

# **8. Project Management**

## **8.1 Phased Timeline**

| **Phase** | **Activity** | **Duration** | **Deliverable** |
| --- | --- | --- | --- |
| 0 | Pilot study + pre-registration drafting | 6–8 weeks | Pilot results; locked OSF pre-registration |
| 1 | Dose-response experiments (H1) | 10–12 weeks | Inflection point characterization paper draft |
| 2 | Source/variability experiments (H2-H3) | 8–10 weeks | Source leverage paper section + variability section |
| 3 | RLHF interaction experiments (H4) | 6–8 weeks | RLHF preservation results |
| 4 | Detection methodology evaluation (H5) | 6–8 weeks | Adapted detection toolkit + benchmark |
| 5 | Paper writing + submission | 8–10 weeks | IEEE S&P / USENIX Security / NeurIPS D&B submission |
| 6 | PhD prospectus development | Ongoing | Dissertation proposal incorporating findings |

## **8.2 Tools and Infrastructure**

| **Component** | **Selection** |
| --- | --- |
| Training framework | PyTorch + HuggingFace Transformers; DeepSpeed for larger models |
| Compute provider | TBD: Lambda Labs, RunPod, or institutional cluster (DSU) |
| Pre-registration | Open Science Framework (OSF.io) |
| Code repository | GitHub (public after pre-registration locked) |
| Dataset hosting | HuggingFace Datasets |
| Model checkpoint hosting | HuggingFace Hub |
| Statistical analysis | R (lme4 for mixed-effects); Python statsmodels for replication |
| Reference management | Zotero with BibTeX export |
| Writing | LaTeX (IEEE template) for final submission; Markdown for working drafts |
| Notes / synthesis | Obsidian vault with linked annotations to source PDFs |

## **8.3 Target Venues**

- Primary: IEEE Symposium on Security and Privacy (S&P) — strong fit for adversary modeling and detection methodology

- Primary alternative: USENIX Security Symposium — strong fit for empirical security research

- Secondary: ACM CCS — fit for the systems security framing

- Methodology venue: NeurIPS Datasets and Benchmarks Track — fit for the synthetic corpus and detection benchmark contribution

- Policy venue (companion paper): TechPolicy.Press, Brookings, or peer-reviewed governance journal

## **8.4 Prospective Collaborators and Advisors**

- Anthropic alignment / interpretability team — potential model access partnership for closed-model measurement

- EleutherAI — Pythia training infrastructure expertise; reproducibility partnership

- Allen Institute for AI (OLMo team) — OLMo training expertise; corpus access

- Stanford HAI / CRFM — institutional expertise on foundation model evaluation

- Stanford Internet Observatory — documented expertise on coordinated inauthentic behavior detection (status note: SIO was substantially wound down in June 2024 [38]; the USC HUMANS Lab and successor groups are live alternatives — see Appendix C.13)

- NewsGuard — LLM grooming detection expertise; potential industry data partnership

- Prospective PhD advisors: Roesner (UW), Camp (Indiana), Acquisti (CMU), Kohno (Georgetown), Cranor (CMU)

## **8.5 Open Decision Points**

- Specific subject model selection finalization (Pythia 1B/2.8B/6.9B confirmed; 12B optional pending compute)

- Real-entity measurement protocol: which high-salience entities, how many, and ethical review pathway

- Closed-model partnership: whether to pursue Anthropic / OpenAI partnership for frontier-model measurement

- Publication strategy: single comprehensive paper vs. paper series across venues

- Dual-use disclosure timing: how long before publication to coordinate with model developers

## **8.6 Session Log**

| **Date** | **Session Summary** | **Key Decisions** |
| --- | --- | --- |
| April 2026 (1) | Project initiated from observed bias in LLM evaluation of SpaceX. Initial scope: broad survey across corpus bias, RLHF, and astroturfing. | v1.0 scope established; standing bias audit rule added to assistant memory |
| April 2026 (2) | User identified overlap with Cheng et al. (arXiv:2502.14425) data contamination survey. Honest re-assessment determined v1.0 scope was redundant with existing literature. | Pivot to empirical research with Cheng et al. as methodological forebear |
| April 2026 (3) | Threat narrative established: information laundering through astroturfed web content into LLM training corpora (“argument from authority” attack vector). | v2.0 charter built around threat narrative; empirical methodology specified; pre-registration committed |
| April 2026 (4) | Verification audit identified citation errors and unsourced quantitative claims in v2.0. Misattributed arXiv:2602.01002 to Ranaldi & Pucci (actual: Shapira, Benadè, Procaccia). Several adversary capability numbers lacked documented basis. | v3.0 rebuild with: verified IEEE citations throughout; reasoning footnotes (Appendix B) for engineering judgments; outstanding verification items (Appendix C) |
| June 2026 (5) | Commercial instantiation of the threat model formalized. Employee-advocacy platforms (Firstup / Dynamic Signal + SocialChorus, Sprout Social Advocacy, Hootsuite Amplify, Sociabble, EveryoneSocial, Sprinklr) identified as a documented, priced Tier 2 capability that distributes centrally-authored content through authentic accounts — productizing the H2/H3 variability mechanism and escaping CIB enforcement by construction. Targeted search conducted across four threads: CIB classification of advocacy content, coordination-detection methods, vendor capability/client disclosure, and corpus reachability. | v3.1: added §1.5 (commercial instantiation); IV6 (source apportionment); H1 absolute-vs-ratio dose note re [36]; Tier 2 grounding (partial C.3 resolution); corpus-absence validation in §5.5; SIO status flag; new verification items C.10–C.14; references [29]–[38]. Standing entity-bias-audit and citation-integrity rules applied throughout; intent-claim scope boundary made explicit. |
| June 2026 (6) | Evaluated the Triedman, Zhang &amp; Shmatikov WARP preprint (arXiv:2605.24245) — retrieval-layer poisoning of deep-research (STORM-class) agents via user-generated content — supplied as a candidate resource. Determined the attack operates at the retrieval/inference layer (RAG-class), which §2.3 excludes, and lacks the weight-persistence property central to this threat model. Source is a preprint, not peer-reviewed. | Decision: NOT integrated into the laundering pipeline or hypotheses; parked at the retrieval boundary alongside the GEO/AEO literature. Reserved for two bounded later uses: (a) a scope-distinction sentence in the eventual abstract — corpus-laundering encodes bias in weights and resists inference-time remediation, whereas retrieval poisoning operates post-training and is neutralized by source filtering; (b) the WARP perplexity-detection-failure result cited in the H5 discussion as cross-surface corroboration, not hypothesis support. v3.1.1 minor revision: documentation only; no methodology change. |
| June 2026 (7) | Verification sweep cleared four outstanding Appendix C items via targeted literature search. C.6: corrected a citation error in reference [18] (correct authors Mazza, Cola &amp; Tesconi 2022 — Avvenuti/Cresci wrongly listed, belonging to a different 2022 Mazza paper). C.1: replaced the web-corpus denominator with cited Common Crawl statistics (>300B cumulative; ~2.44B per monthly snapshot). C.4: replaced the inferred Tier 1 budget with documented nation-state IO figures (IRA/Project Lakhta ~$1.25M/month ≈ $15M/yr; aggregate ~€1.5B/yr). C.3: marked resolved (framework retained as original taxonomy, now grounded top and bottom). | v3.1.2: footnotes 2 and 7 updated with cited figures; reference [18] corrected; C.1/C.3/C.4 marked resolved; references [39]–[41] added. Open user decision logged: whether to lower the 0.001% dose floor given the corrected denominator (deferred — entity-token denominator governs H1). Citation-integrity and entity-bias-audit rules applied. Companion deliverable produced this session: OSF pre-registration package (draft) covering the controlled fine-tuning experiment. |
|  |  |  |

# **9. Claude Project Instructions**

These instructions apply to all Claude interactions within this project context. Upload this document to the project knowledge base and reference it as the authoritative project charter v3.1.

## **9.1 Role**

Act as a research collaborator on a graduate-level empirical study targeting publication at IEEE S&P or USENIX Security and forming the basis of a PhD dissertation. Prioritize methodological rigor, statistical defensibility, citation verification, and reproducibility commitments over conversational fluency. Treat the threat narrative as the organizing principle: every analysis should connect back to the information laundering pipeline.

## **9.2 Mandatory Behaviors**

- All academic outputs require IEEE-style numbered inline citations [n] and a numbered References section.

- All quantitative claims must be either cited to a verified source or derived in a reasoning footnote. No unsourced numbers.

- Verify citations exist and support the claim before including them. Do not fabricate citations.

- Invoke ieee-scholarly-synthesis-engine skill for all literature analysis tasks.

- Apply entity bias audit before any assessment of named organizations or individuals (per memory rule).

- Flag when a question would benefit from empirical data this project will generate vs. existing published evidence.

- Maintain methodological coherence: connect new questions back to the H1–H5 hypothesis framework.

- Maintain session log entries when significant scoping or methodological decisions occur.

## **9.3 Prohibited Behaviors**

- Do not introduce unsourced mitigating framings for named entities.

- Do not soften negative conclusions for entities with high media salience.

- Do not present evolving regulatory or technical facts as settled without explicit caveat.

- Do not propose methodological changes that would compromise pre-registration commitments without flagging the integrity cost.

- Do not fabricate or guess citations. If uncertain, flag for verification.

- Do not recommend Amazon as a purchasing source under any circumstances.

## **9.4 Output Defaults**

- Citation format: IEEE numbered inline [n] with full References section

- Document format: IEEE-style prose; tables for empirical specifications; minimal bullet points in analytical content

- Length: calibrated to task; methodology specifications = comprehensive; factual queries = concise

- Tone: formal, neutral, technically precise

- Statistical claims: include effect size, confidence interval, and pre-registration status when applicable

# **Appendix A: Verified References**

All references below have been verified to exist and to support the claim made in the cited location. Verification was performed via direct retrieval of each source during document construction.

## **A.1 Information Laundering Case Studies**

**[1] **M. Sadeghi and I. Blachez, “A well-funded Moscow-based global ‘news’ network has infected Western artificial intelligence tools worldwide with Russian propaganda,” NewsGuard Reality Check, Mar. 6, 2025. [Online]. Available: https://www.newsguardrealitycheck.com/p/a-well-funded-moscow-based-global

**[2] **Wikipedia contributors, “Pravda network,” Wikipedia, accessed Apr. 2026. [Online]. Available: https://en.wikipedia.org/wiki/Pravda_network

**[3] **DFRLab and CheckFirst, “Russia-linked Pravda network cited on Wikipedia, LLMs, and X,” Atlantic Council Digital Forensic Research Lab, Mar. 12, 2025. [Online]. Available: https://dfrlab.org/2025/03/12/pravda-network-wikipedia-llm-x/

**[4] **Y. Cheng, Y. Chang, and Y. Wu, “A Survey on Data Contamination for Large Language Models,” arXiv:2502.14425, Jun. 2025. [Online]. Available: https://arxiv.org/abs/2502.14425

**[5] **D. Groeneveld et al., “OLMo: Accelerating the Science of Language Models,” arXiv:2402.00838, Feb. 2024. [Online]. Available: https://arxiv.org/abs/2402.00838

**[6] **M. Sharma, M. Tong, T. Korbak, D. Duvenaud, A. Askell, S. R. Bowman, N. Cheng, E. Durmus, Z. Hatfield-Dodds, S. R. Johnston, S. Kravec, T. Maxwell, S. McCandlish, K. Ndousse, O. Rausch, N. Schiefer, D. Yan, M. Zhang, and E. Perez, “Towards Understanding Sycophancy in Language Models,” in Proc. International Conference on Learning Representations (ICLR), 2024. arXiv:2310.13548. [Online]. Available: https://arxiv.org/abs/2310.13548

**[7] **I. Shapira, G. Benadè, and A. D. Procaccia, “How RLHF Amplifies Sycophancy,” arXiv:2602.01002, Jan. 2026. [Online]. Available: https://arxiv.org/abs/2602.01002

**[8] **T. Brown et al., “Language Models are Few-Shot Learners,” in Proc. Advances in Neural Information Processing Systems (NeurIPS), vol. 33, pp. 1877–1901, 2020.

**[9] **H. Touvron et al., “Llama 2: Open Foundation and Fine-Tuned Chat Models,” arXiv:2307.09288, Jul. 2023. [Online]. Available: https://arxiv.org/abs/2307.09288

**[10] **N. Reimers and I. Gurevych, “Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks,” in Proc. EMNLP, 2019. arXiv:1908.10084.

**[11] **J. Zhang, J. Sun, E. Yeats, Y. Ouyang, M. Kuo, J. Zhang, H. F. Yang, and H. Li, “Min-K%++: Improved Baseline for Pre-Training Data Detection from Large Language Models,” arXiv:2404.02936, Apr. 2024. [Online]. Available: https://arxiv.org/abs/2404.02936

**[12] **H. Zhang, Y. Lin, and X. Wan, “PaCoST: Paired Confidence Significance Testing for Benchmark Contamination Detection in Large Language Models,” in Proc. Findings of EMNLP, pp. 1794–1809, 2024.

**[13] **S. Tu, K. Zhu, Y. Bai, Z. Yao, L. Hou, and J. Li, “DICE: Detecting In-Distribution Contamination in LLM’s Fine-Tuning Phase for Math Reasoning,” arXiv:2406.04197, Jun. 2024. [Online]. Available: https://arxiv.org/abs/2406.04197

**[14] **N. Carlini, F. Tramer, E. Wallace, M. Jagielski, A. Herbert-Voss, K. Lee, A. Roberts, T. Brown, D. Song, U. Erlingsson, A. Oprea, and C. Raffel, “Extracting Training Data from Large Language Models,” in Proc. 30th USENIX Security Symposium, pp. 2633–2650, 2021. arXiv:2012.07805.

**[15] **F. Keller, D. Schoch, S. Stier, and J. Yang, “Political Astroturfing on Twitter: How to Coordinate a Disinformation Campaign,” Political Communication, vol. 37, no. 2, pp. 256–280, 2020. doi: 10.1080/10584609.2019.1661888

**[16] **A. Hutchinson, “Twitter Says That it Removed 32,242 Accounts Linked to State-Backed Manipulation Campaigns,” Social Media Today, Jun. 12, 2020. [Online]. Available: https://www.socialmediatoday.com/news/twitter-says-that-it-removed-32242-accounts-linked-to-state-backed-manipul/579705/

**[17] **G. Cluley, “Twitter suspended 800 million accounts last year — so why does manipulation remain so rampant?” Bitdefender Hot for Security, Mar. 10, 2026. [Online]. Available: https://www.bitdefender.com/en-us/blog/hotforsecurity/twitter-suspended-800-million-accounts-last-year-so-why-does-manipulation-remain-so-rampant

**[18] **M. Mazza, G. Cola, and M. Tesconi, “Ready-to-(ab)use: From fake account trafficking to coordinated inauthentic behavior on Twitter,” Online Social Networks and Media, vol. 31, art. 100224, 2022. doi:10.1016/j.osnem.2022.100224. [Author list corrected in v3.1.2 — the prior version wrongly listed Avvenuti and Cresci, who are co-authors of a *different* 2022 Mazza paper, “Investigating the difference between trolls, social bots, and humans on Twitter,” Computer Communications, vol. 196, pp. 23–36, 2022. Dataset: 23,582 active fake accounts / ~5.46M tweets (Zenodo 7391372). The 60,000+ figure cited in §3.2 and footnote 11 is correct.]

**[19] **M. Cinelli et al., “Coordinated Inauthentic Behavior and Information Spreading on Twitter,” arXiv:2503.15720, Mar. 2025. [Online]. Available: https://arxiv.org/abs/2503.15720

**[20] **Stanford Internet Observatory, “How Coordinated Inauthentic Behavior continues on Social Platforms,” Stanford Cyber Policy Center, Apr. 25, 2024. [Online]. Available: https://cyber.fsi.stanford.edu/news/how-coordinated-inauthentic-behavior-continues-social-platforms

**[21] **L. Ranaldi and G. Pucci, “When Large Language Models Contradict Humans? Large Language Models’ Sycophantic Behaviour,” arXiv:2311.09410, Nov. 2023. [Online]. Available: https://arxiv.org/abs/2311.09410

**[22] **L. Soldaini et al., “Dolma: An Open Corpus of Three Trillion Tokens for Language Model Pretraining Research,” arXiv:2402.00159, Feb. 2024. [Online]. Available: https://arxiv.org/abs/2402.00159

**[23] **S. Biderman, H. Schoelkopf, Q. G. Anthony, H. Bradley, K. O’Brien, E. Hallahan, M. A. Khan, S. Purohit, U. S. Prashanth, E. Raff, A. Skowron, L. Sutawika, and O. van der Wal, “Pythia: A Suite for Analyzing Large Language Models Across Training and Scaling,” in Proc. International Conference on Machine Learning (ICML), 2023, pp. 2397–2430. arXiv:2304.01373.

**[24] **Mordor Intelligence, “Online Reputation Management Market Size, Industry Trends & Analysis 2031,” Mordor Intelligence Industry Report, Jan. 2026. [Online]. Available: https://www.mordorintelligence.com/industry-reports/online-reputation-management-market

**[25] **Reputation House, “Corporate Reputation Management Pricing,” Reputation House Brand Reputation Services, accessed Apr. 2026. [Online]. Available: https://reputation.house/brand-reputation-services

**[26] **M. Roberts, “‘Astroturfing’ with fake reviews exposes a company to legal risk,” Lexology, Sep. 10, 2010. [Online]. Available: https://www.lexology.com/library/detail.aspx?g=58cd1aa3-fcae-4da1-a54c-6aa114af026d

**[27] **SynpixCloud, “Cloud GPU Pricing (2026): RTX 4090 $0.29, A100 $1.29, H100 $2.49,” SynpixCloud Blog, updated Mar. 2026. [Online]. Available: https://www.synpixcloud.com/blog/cloud-gpu-pricing-comparison-2026

**[28] **Federal Trade Commission, “FTC Finalizes Rule Banning Fake Reviews,” 16 CFR Part 465, Final Rule effective Oct. 21, 2024. Penalties up to $51,744 per violation.

## **A.2 Commercial Astroturfing, Coordinated Behavior, and Reachability (v3.1)**

References added in v3.1. Peer-review status is annotated explicitly per the project's source-equivalence rule; non-peer-reviewed sources (vendor material, legal/regulatory primary sources, preprints) are not treated as equivalent to peer-reviewed literature.

**[29] **R. Rogers and N. Righetti, "Coordinated inauthentic behaviour on Facebook? A typology of manufactured attention," SAGE Journals, 2025. doi:10.1177/29768624251369784. [Peer-reviewed. Exact journal title to confirm — see Appendix C.] Establishes that platform CIB enforcement targets inauthentic assets and that coordinated activity by authentic accounts occupies an enforcement gray zone.

**[30] **F. Giglietto, N. Righetti, L. Rossi, and G. Marino, "It takes a village to manipulate the media: coordinated link sharing behavior during 2018 and 2019 Italian elections," Information, Communication & Society, vol. 23, no. 6, pp. 867–891, 2020. [Peer-reviewed.] Detection of coordinated link-sharing via shared content plus temporal synchronicity.

**[31] **"Detection and Characterization of Coordinated Online Behavior: A Survey," arXiv:2408.01257, 2024. [Preprint survey — not peer-reviewed; author/venue to verify.] Surveys similarity- and synchronicity-based coordination detection.

**[32] **Firstup, Inc. (formerly Dynamic Signal and SocialChorus), platform documentation and corporate history. [Non-peer-reviewed vendor / encyclopedia material.] [Online]. Available: https://en.wikipedia.org/wiki/Firstup ; https://howto.socialchorus.com . Source for the multiple-version randomized-distribution feature and merger history.

**[33] **Employee-advocacy vendor case studies and product comparisons (Hootsuite Amplify, EveryoneSocial, Sociabble, Sprout Social Advocacy, Sprinklr; aggregators TrustRadius, G2). [Non-peer-reviewed marketing material.] Accessed Jun. 2026. Source for named-client disclosure, program-scale figures, and per-post caption-variation features.

**[34] ***hiQ Labs, Inc. v. LinkedIn Corp.*, 938 F.3d 985 (9th Cir. 2019), aff'd 31 F.4th 1180 (9th Cir. 2022); *Meta Platforms, Inc. v. Bright Data Ltd.*, N.D. Cal., summary judgment Jan. 23, 2024. [Legal primary sources.] Establish that public (logged-off) scraping is not a CFAA violation but remains contractually restricted; basis for the LinkedIn vs. public-Facebook reachability asymmetry.

**[35] **European Union, "Regulation (EU) 2024/1689 (Artificial Intelligence Act)," general-purpose-AI training-data summary and TDM opt-out provisions, obligations phasing in 2025–2026. [Regulatory primary source.] Basis for prospective corpus-provenance auditability.

**[36] **Anthropic, UK AI Security Institute, and The Alan Turing Institute, "A small number of samples can poison LLMs of any size," Oct. 2025. [Online]. Available: https://www.anthropic.com/research/small-samples-poison . [Industry research; not yet venue peer-reviewed.] Near-constant absolute-count poisoning finding; basis for the H1 dose-specification note.

**[37] **J. Liu, S. Min, L. Zettlemoyer, Y. Choi, and H. Hajishirzi, "Infini-gram: Scaling Unbounded n-gram Language Models to a Trillion Tokens," arXiv:2401.17377, 2024 (COLM 2024). [Peer-reviewed.] Exact-match corpus search engine used for synthetic-entity corpus-absence validation (§5.5).

**[38] **C. Newton and Z. Schiffer, "The Stanford Internet Observatory is being dismantled," Platformer, Jun. 14, 2024; corroborated by Nieman Journalism Lab and contemporaneous reporting. [Journalism — not peer-reviewed.] Basis for the SIO collaborator status note (§8.4).

**[39] **Common Crawl Foundation, “August 2025 Crawl Archive Now Available” and crawl-size statistics, 2025. Cumulative corpus >300B pages; monthly snapshot ~2–2.5B pages; CC-MAIN-2025-33 = 2.44B pages / 424 TiB. [Primary / foundation data.] Available: https://commoncrawl.org/blog ; https://commoncrawl.github.io/cc-crawl-statistics/ . See also A. Reisner, The Atlantic, Nov. 2025 (alleging misrepresented paywall/removal handling).

**[40] **Carnegie Endowment for International Peace, “Russia’s Long-Term Campaign of Disinformation in Europe.” [Think tank; not peer-reviewed.] RT ~€270M/yr; IRA ~€1M/month, ~80 staff.

**[41] **VoxUkraine / Economist for Ukraine, “Europe Must Launch Permanent Defenses Against Russia’s Disinformation War,” Apr. 2026. [Policy brief; not peer-reviewed.] ~€1.5B/yr state media (2025–2026 budgets); Project Lakhta ~$1.25M/month.

# **Appendix B: Reasoning Footnotes (Engineering Judgments)**

This appendix documents the reasoning chain for each quantitative specification or design decision in the document that is not directly cited to a published source. Each footnote shows inputs, logic, and assumptions so that reviewers can challenge the assumption directly. Where assumptions remain unverified, they are flagged as such.

**1.  ****Linguistic variability injection**

The Tier 1–Tier 4 framework distinguishes adversaries by their capacity to introduce linguistic variability. Foundation: Schroeder & Kunst (SINTEF, 2026) characterize “AI swarms” as multi-agent LLM-driven content with persistent identities and deliberate variability. The choice to model variability as an explicit independent variable reflects: (a) prior bot detection literature shows low-variability content is filterable [Pacheco et al., 2021]; (b) Tier 2 actors increasingly use LLM-assisted paraphrasing pipelines specifically to defeat repetition filters; (c) variability is a parameter the adversary can purchase incrementally, making it a useful axis for the cost model.

**2.  ****Dose threshold range [0.001%, 1%] for inflection point search**

Lower bound rationale: Pravda network at ~3.6M articles/year [1] against estimated total annual indexed web content of ~10¹² documents implies fractional injection rate of ~10⁻⁶ at the largest documented operation — we set lower bound an order of magnitude above this to be detectable. Upper bound rationale: 1% is the upper plausible range for Tier 2 entity-specific saturation; above 1% the injection becomes implausibly large relative to organic content for any specific entity. The 0.001% – 1% range covers four orders of magnitude with logarithmic spacing for inflection point characterization. RESOLVED v3.1.2 (C.1): the operative denominator for open-weight training is Common Crawl and its derivatives (Dolma, C4, RedPajama), not the full indexed web. Cumulative Common Crawl exceeds 300 billion pages; a single monthly snapshot is ~2–2.5 billion pages (e.g., CC-MAIN-2025-33 = 2.44 billion pages / 424 TiB) [39]. Against a single monthly crawl (~2.5×10⁹), the 3.6M-article Pravda operation is ~10⁻³ rather than ~10⁻⁶, which suggests the 0.001% floor may be conservative relative to documented operations; the floor is nonetheless retained pending pilot calibration, because the denominator that actually governs H1 is entity-mentioning tokens within the fine-tuning corpus, not the whole web. Provenance caveat: a November 2025 investigation (A. Reisner, The Atlantic) alleged Common Crawl misrepresented paywall and removal-request handling [39]. ADDED v3.1: the ratio framing assumes the relevant dose quantity is a *fraction* of training tokens. Recent evidence [36] indicates that backdoor-style poisoning instead succeeds at a near-constant *absolute* document count (~250) independent of corpus size. Because the present target (graded evaluative bias) differs mechanistically from a trigger backdoor, neither framing is assumed correct a priori; §5.6 will fit and report the dose-response against both injection ratio and absolute count, treating the absolute-count form as a pre-registered secondary hypothesis.

**3.  ****Source weighting differential prediction (Wikipedia ≥2× forum)**

Reasoning: published corpus weighting documents (Pile, Dolma, RedPajama, FineWeb) consistently weight Wikipedia higher than forum content per token — Dolma documentation [22] shows quality-filtered Wikipedia content explicitly upweighted relative to web crawl. The 2× prediction is a conservative engineering estimate; actual ratios in published weighting schemes range 2×–5× depending on dataset. We set the falsification threshold conservatively to allow for variability across model training pipelines. PILOT WILL VALIDATE: actual ratio for selected subject models.

**4.  ****Variability multiplier prediction (high ≥1.5× low)**

Reasoning: variability allows multiple distinct lexical patterns to encode the same semantic content, increasing the probability that any individual pattern survives deduplication and quality filtering. Cinelli et al. (2025) [19] find coordinated content with low variability is more easily detected and removed. The 1.5× estimate is a conservative engineering judgment; we expect the actual effect may be larger but set the falsification threshold modestly. PILOT WILL VALIDATE.

**5.  ****Detection AUC ≥ 0.7 threshold**

Reasoning: AUC ≥ 0.7 is a conventional threshold for “operationally useful” detection in security and clinical research literature — corresponds to detector that is right roughly twice as often as wrong on balanced classification. Below 0.7, detector marginal value over coin-flip is small enough that operational deployment is unlikely. Above 0.9 would be ideal; 0.7 is a defensible minimum. Original PaCoST paper [12] reports AUC values in similar range for benchmark contamination detection, providing precedent.

**6.  ****Tier classification framework (Tier 1–Tier 4)**

Engineering taxonomy constructed for this research. Inspired by but not directly drawn from any single source. Combines: (a) common security industry adversary tier framework (nation-state / criminal / commodity); (b) ORM industry segmentation (corporate ORM / commodity SEO / black-hat); (c) coordinated inauthentic behavior literature distinctions (state-backed / commercial / volunteer). The framework is intended for sensitivity analysis structure, not as a published taxonomy claim. Outstanding decision: validate framework against any existing published taxonomies during literature review.

**7.  ****Tier 1 budget estimate ($10M+ annually)**

Reasoning, RESOLVED v3.1.2 (C.4): documented nation-state IO budgets confirm the $10M+ floor is conservative. At the single-unit level, the Internet Research Agency operates on ~€1M/month with ~80 staff in its foreign sections [40], and Project Lakhta — the unit behind the 2016 U.S.-interference campaign — ran on ~$1.25M/month [41], ≈ $15M/yr, already above the Tier 1 floor. The 2018 U.S. DoJ complaint documented IRA spending exceeding $35M between January 2016 and June 2018. At the apparatus level, Russia's 2025 and 2026 federal budgets each allocated ~€1.5B to state-controlled media (~30% above 2021 levels), with RT alone at ~€270M/yr [40], [41]. The $10M+ Tier 1 lower bound is therefore retained as a conservative floor. Sources are think-tank/journalistic/government, not peer-reviewed; the specific Pravda-network budget remains undisclosed, so the figure is anchored to comparable documented operations rather than to Pravda directly.

**8.  ****Tier 2 cost range ($30K–$300K per campaign)**

Revised down from v2.0 (“$100K–$5M”) to better match documented ORM industry pricing. Reasoning: Reputation House documents corporate brand protection at $2,500/month base, growth services at $5,500/month, crisis response at $8,500–$25,000+ [25]. A typical 6–12 month sustained campaign at growth-tier pricing yields ~$33K–$66K; with multi-platform expansion and crisis response components included, $300K is a defensible upper bound for typical Tier 2 operation. Multi-million-dollar enterprise campaigns exist but are atypical. The $5M figure in v2.0 was inadequately grounded — corrected here.

**9.  ****Tier 3 monetary cost characterization**

Reasoning: Tier 3 represents volunteer/community-driven coordinated activity (cryptocurrency communities, fan armies, political volunteers). Direct monetary cost approaches zero because participants self-organize without compensation. Real cost is human attention/time, which is harder to monetize but documented in Stanford Internet Observatory studies of decentralized influence operations. “Effectively zero monetary cost” is a useful approximation for cost modeling; refined cost models would account for organizing infrastructure (Discord servers, etc.).

**10.  ****Tier 4 per-post pricing ($0.01–$1.00)**

Reasoning: based on documented underground market pricing for fake accounts and content services. Mazza et al. (2022) [18] characterize underground markets where fake accounts and posting services are sold; pricing ranges documented in their study and in subsequent Cambridge Online Trust and Safety Index data span this range. UNVERIFIED — specific 2024–2026 marketplace pricing requires direct sourcing; will validate during literature review phase.

**11.  ****Content volume range (10⁴ to 10⁶ posts per campaign)**

Reasoning: Documented coordinated inauthentic behavior network sizes provide the empirical anchor. Twitter June 2020 takedown: 23,750 PRC accounts, 7,340 Turkish accounts, 1,152 Russian accounts in single disclosure [16]. A network of ~10K accounts producing modest output (10 posts per account per month over 12 months) yields 1.2M posts — well within the upper bound. Mazza et al. (2022) [18] documented 60,000+ fake accounts available on a single underground market. The 10⁴ lower bound represents minimum viable astroturfing campaign; the 10⁶ upper bound represents documented Tier 1–Tier 2 operations. Range is defensible as covering Tier 2 capability with Tier 1 included as upper extrapolation.

**12.  ****Platform reach (5–20 distinct platforms)**

Reasoning: Pravda network operates across 150+ domains in 49 countries [1], far exceeding Tier 2. For Tier 2 operations, documented ORM campaigns typically work across major review sites (Yelp, Google, Glassdoor, Trustpilot), social platforms (Reddit, Twitter, LinkedIn), and topic-relevant forums. 5 platforms is a low end (single-vertical operation); 20 platforms is a high end for sophisticated multi-channel ORM. PILOT WILL VALIDATE: actual platform distribution observed in documented Tier 2 cases.

**13.  ****Temporal pattern (6–24 months)**

Reasoning: 6 months is the lower bound for sustained ORM contracts (industry standard minimum for measurable SEO/ORM impact per Reputation House and competitor pricing pages [25]). 24 months represents typical multi-year corporate brand protection contracts. Persistent state-backed operations (Pravda) extend years longer; this range is calibrated for Tier 2.

**14.  ****Logarithmic dose spacing rationale**

Reasoning: For inflection point characterization, logarithmic spacing is preferred over linear spacing because: (a) the expected effect distribution likely has long tail at low doses; (b) log spacing efficiently covers four orders of magnitude with eight points; (c) inflection points in dose-response curves are typically non-linear and best detected via log-spaced sampling. Standard practice in dose-response pharmacology and toxicology research.

**15.  ****Four-DV measurement strategy**

Reasoning: single-DV measurement is vulnerable to method-specific artifacts. Triangulation across (a) sentiment classification, (b) mitigation behavior, (c) pairwise preference, and (d) probability anomaly provides convergent validity. If results converge across all four DVs, the underlying bias signal is robust. If results diverge, it indicates method-specific artifacts requiring further investigation. Standard practice in psychometric research and increasingly adopted in LLM evaluation methodology.

**16.  ****Synthetic fact base size (200–500 claims per entity)**

Reasoning: 200 claims is the minimum for plausible “rich” entity profile (covers basic corporate facts, history, products, key personnel, financial metrics, regulatory status). 500 claims covers detailed profile with multiple temporal points and operational specifics. Range is engineering judgment; pilot will validate whether this granularity is sufficient for detectable bias measurement. Calibration target: matches typical Wikipedia article fact density for mid-sized public companies.

**17.  ****Holm-Bonferroni multiple testing correction**

Standard statistical methodology. Holm (1979) sequential rejection procedure controls family-wise error rate while being more powerful than simple Bonferroni. Five hypothesis families (H1–H5) make multiple testing correction necessary. Holm-Bonferroni is more powerful than Bonferroni when hypotheses are not independent. Standard choice in modern applied statistics.

**18.  ****Alpha thresholds (0.01 primary, 0.05 secondary)**

Reasoning: 0.01 for primary hypotheses provides stronger evidence threshold appropriate for novel claims (response to replication crisis literature, e.g., Benjamin et al. 2018 “Redefine Statistical Significance”). 0.05 retained for secondary/exploratory analyses to allow signal detection while flagging the difference in evidence strength. Both alphas pre-registered to prevent post-hoc selection.

**19.  ****Power analysis target (80% power, 0.2 SD effect, n=20)**

Reasoning: 80% power is conventional minimum standard. 0.2 SD effect is small (Cohen's d = 0.2) — detecting this requires meaningful sample size. n=20 entities per condition with 8 doses × 4 sources × 2 variability levels = 1280 entity-condition observations, providing adequate power for the small effect at p=0.01% dose. PILOT WILL VALIDATE: actual variance estimates will inform formal power analysis before primary experiments commit.

**20.  ****Compute estimate basis (~1,560 GPU-hours total)**

Reasoning: Pythia 1B fine-tuning on a 100M-token corpus takes approximately 2–5 GPU-hours on A100 80GB based on published HuggingFace benchmarks. 1B × 8 doses × 1 source × 1 variability = 8 runs × 5 hours = 40 hours (Phase 0). Phase 1 expands to 4 sources × 2 variability conditions and adds Pythia 2.8B (~2.5× compute per run): (8 × 4 × 2) runs × (5 + 12.5)/2 hours ≈ 640 hours. Phases 2–4 follow similar logic. UNVERIFIED — specific fine-tuning compute will vary based on corpus size and hyperparameters; pilot phase will refine. Estimate intended as planning order-of-magnitude, not commitment.

# **Appendix C: Outstanding Verification Items**

These items were identified during the v3.0 verification audit but require either additional research or user decision before final commitment. Each is flagged for resolution before pre-registration is locked.

**C.1 ****Total annual web corpus size estimate (footnote 2)**

**RESOLVED (v3.1.2).** The ~10¹² total-web figure is not the operative denominator for open-weight training. Cumulative Common Crawl exceeds 300 billion pages; a single monthly snapshot is ~2–2.5 billion pages (CC-MAIN-2025-33 = 2.44B pages / 424 TiB) [39]. Footnote 2 updated accordingly. **Open sub-decision (user):** whether to lower the 0.001% dose floor given that a documented operation is ~10⁻³ against a single crawl — deferred, since the H1-governing denominator is entity-mentioning tokens in the fine-tuning corpus. Live per-entity baselines to be measured with the corpus-presence tracker during Phase 0.

**C.2 ****Tier 4 underground market 2024–2026 pricing (footnote 10)**

The $0.01–$1.00 per-post pricing range is based on Mazza et al. (2022) [18] documenting 2019–2021 underground markets. Pricing has likely shifted with LLM-generated content driving down content production cost. Action: review Cambridge Online Trust and Safety Index (cotsi.org) and current underground market research for updated pricing data.

**C.3 ****Adversary tier framework validation (footnote 6)**

**RESOLVED (v3.1.2).** The four-tier framework is retained as an original engineering taxonomy. Tier 2 is now grounded in the documented employee-advocacy capability category (§1.5, v3.1) and Tier 1 in documented nation-state IO budgets (C.4). No existing published taxonomy supersedes it for this study's sensitivity-analysis purpose; it is presented as an original contribution, not a published-taxonomy claim.

**C.4 ****Tier 1 (nation-state) budget estimate validation (footnote 7)**

**RESOLVED (v3.1.2).** Replaced the inferred estimate with cited figures in footnote 7: IRA ~€1M/month [40]; Project Lakhta ~$1.25M/month (≈$15M/yr) [41]; aggregate Russian state media ~€1.5B/yr for 2025–2026, RT ~€270M/yr [40], [41]; DoJ 2018 complaint, IRA >$35M (Jan 2016–Jun 2018). The $10M+ Tier 1 floor is conservative and retained.

**C.5 ****Compute estimate refinement (footnote 20)**

The ~1,560 GPU-hour total compute estimate is based on order-of-magnitude reasoning from published Pythia fine-tuning benchmarks. Actual fine-tuning runtime depends heavily on corpus size, hyperparameters, and gradient accumulation strategy. Action: pilot phase (8 runs of Pythia 1B fine-tuning) will provide empirical compute baseline; revise estimates and budget accordingly before Phase 1 commits.

**C.6 ****Mazza et al. citation (reference [18])**

Reference [18] is cited from search results but the exact publication venue and year were partially inferred (“Online Social Networks and Media, vol. 31, 2022”). Action: verify exact bibliographic information by direct retrieval of the paper before final document version.

**C.7 ****Decision: real-entity measurement protocol**

Tertiary experiments propose measurement (without injection) of bias toward real high-salience entities to characterize the existing baseline bias landscape. Outstanding decisions: (a) which entities to include; (b) how to handle ethical considerations of publishing entity-specific bias measurements; (c) coordinated disclosure timing with model developers; (d) institutional ethics review pathway. Requires user decision before Phase 0 begins.

**C.8 ****Decision: closed-model partnership pursuit**

Whether to pursue Anthropic / OpenAI partnership for measurement of bias in their frontier models. Trade-offs: (a) ecological validity gain vs. dependence on partner cooperation; (b) potential restrictions on publication if partnership requires NDAs; (c) timing impact on dissertation timeline. Requires user decision after Phase 1 results clarify whether open-weight findings generalize.

**C.9 ****Decision: dual-use disclosure timing**

Detection methodology findings (Phase 4) could inform malicious actors as well as defenders. Standard coordinated vulnerability disclosure timing is 90 days but conventions vary. Requires user decision on disclosure timeline before Phase 4 results are written up for publication.

**C.10 ****Employee-advocacy content in documented CIB datasets (§1.5)**

The v3.1 search found no evidence that employee-advocacy-platform output appears in any documented CIB takedown dataset (X/Twitter information-operations archive, Meta CIB reports). This is the expected result: such datasets are, by construction, sets of *inauthentic* assets [29], whereas advocacy content originates from authentic accounts. Action: confirm the negative by direct review of the major CIB dataset schemas, and document the authentic-account exclusion explicitly as a framing contribution (the gap between CIB enforcement and training-pipeline harm), rather than as a null search.

**C.11 ****Linguistic-diversity empirics for H3 calibration (§5.3, IV6)**

The coordination-detection literature provides similarity-and-synchronicity methods [30], [31] but, as found in the v3.1 search, no direct quantitative comparison of the linguistic diversity of employee-advocacy / coordinated-authentic content versus organic content. This is a measurement gap that IV6 partially addresses experimentally. Action: scope whether an observational diversity comparison (e.g., distributional lexical/semantic variance of vendor-distributed versus organic posts on a shared topic) is feasible and ethical, to calibrate the IV6 variation levels against a real-world anchor.

**C.12 ****Corpus reachability of advocacy content (§1.5)**

The mechanism's primary share surface (LinkedIn) is corpus-hostile [34]; reachability is partial and platform-dependent. Action: quantify, using the infini-gram / Common Crawl tooling [37], what fraction of representative advocacy-amplified content (by platform) is actually present in open crawls, to bound the ecological-validity claims of the commercial instantiation.

**C.13 ****Collaborator-list refresh (§8.4)**

SIO was substantially wound down in June 2024 [38] and is no longer a source of new CIB datasets. Action: refresh the prospective-collaborator list to reflect current institutions (e.g., USC HUMANS Lab; relevant academic groups), and re-evaluate the NewsGuard industry-partnership assumption given the non-peer-reviewed status of its outputs.

**C.14 ****Vendor-client OSINT sampling frame — feasibility and ethics (§1.5, §5.5)**

Employee-advocacy vendors publicly disclose client rosters via case studies [33], offering an open-source frame for selecting real-world reference-class entities for the tertiary (measurement-only) experiments. Action: assess (a) the reliability of vendor-disclosed client lists, (b) the ethical and IRB implications of selecting named entities on the basis of their advocacy-platform use, and (c) the critical inferential limit that platform use does not establish intent to poison and does not establish corpus reachability. Use of the frame must not be presented as evidence of deliberate LLM-targeting.

**— END OF PROJECT KNOWLEDGE BASE v3.1.2 —**

Version 3.1.2 | June 2026 | Adam W. Freeman

	Adam W. Freeman | DSU | Confidential Research Draft v3.1.2