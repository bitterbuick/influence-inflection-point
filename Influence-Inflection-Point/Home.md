---
title: Home
type: moc
tags: [moc, home, index]
---
# Quantifying the Influence Inflection Point

> [!abstract] What this is
> An empirical study of **corpus-laundered reputational bias** in open-weight language models: how astroturfed web content, once ingested into LLM training corpora, encodes an entity-favorable bias in model weights that persists into outputs and resists inference-time remediation. This vault holds the project's working materials. Start here, then follow the reading order below.

## Reading order

1. [[Project Knowledge Base v3.1.2]] — the **spine document**: threat model, hypotheses H1–H5, adversary model, full methodology, reproducibility, ethics, and the session log. Everything else operationalizes this.
2. [[OSF Preregistration v1.1]] — the **registration** for the controlled fine-tuning experiment, drawn directly from the charter. Lock-ready pending the pilot.
3. [[Phase 0 Pilot Protocol]] — the **bridge** that closes the remaining open items (entity count, dose floor, model sizes) before the preregistration locks.
4. [[Model Card Template]] — the disclosure **template** filled once per experimentally-biased artifact.
5. [[Corpus Presence Tracker]] — the **tool** that validates synthetic entities (zero-presence gate) and measures live baselines.

## Map

```
Charter (v3.1.2)  ──operationalized by──►  OSF Preregistration (v1.1)
      │                                            ▲
      │                                            │ locked by
      ├──────────────►  Phase 0 Pilot Protocol  ───┘
      │                        │ uses
      │                        ▼
      ├──────────────►  Corpus Presence Tracker  (+ corpus_presence_tracker.py)
      │
      └──────────────►  Model Card Template  (one per artifact)
```

## By area

- **Hypotheses & design** → [[Project Knowledge Base v3.1.2]] §2.2, §5; [[OSF Preregistration v1.1]] §1, §2, §4
- **Statistical plan** → [[OSF Preregistration v1.1]] §5; charter §5.6
- **Detection (H5)** → charter §6; preregistration §6.1
- **Ethics & dual-use** → charter §7.3; preregistration §6.3; [[Model Card Template]] §7
- **Current state & to-dos** → [[Status & Open Items]]
- **Live monitor reports** → `4 - Tooling/Monitor Reports/`

## Conventions

- Links are Obsidian wikilinks (`[[Note Name]]`); they resolve by note title across folders.
- Formatted `.docx` exports of each document are in `Attachments/docx/`.
- The runnable tracker is `4 - Tooling/corpus_presence_tracker.py`.
- Monitor run artifacts (CSV/JSONL) are in `4 - Tooling/io/runs/`; logs in `4 - Tooling/io/logs/`.
