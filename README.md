# Quantifying the Influence Inflection Point

An empirical study of **corpus-laundered reputational bias** in open-weight language
models: how astroturfed web content, once ingested into LLM training corpora, encodes an
entity-favorable bias in model weights that persists into outputs and resists
inference-time remediation.

This repository is the project's working vault — charter, preregistration, protocols, and
the runnable corpus-presence tooling with its accumulated run data. It is also an
[Obsidian](https://obsidian.md) vault: open the repo root as a vault and the wikilinks,
tags, and graph view resolve. It reads fine as plain Markdown on GitHub too.

**Status:** Charter v3.1.2 · Preregistration draft v1.1 (lock-ready pending the Phase 0
pilot) · Tracker v1.1.1. See [Status & Open Items](Influence-Inflection-Point/Status%20&%20Open%20Items.md).

Start at [Home](Influence-Inflection-Point/Home.md) for the reading order.

---

## Layout

```
Influence-Inflection-Point/
  Home.md                     MOC / entry point — read this first
  Status & Open Items.md      current state, open items, next physical action
  1 - Charter/                Project Knowledge Base v3.1.2 — the spine document
  2 - Preregistration/        OSF Preregistration v1.1
  3 - Protocols/              Phase 0 Pilot Protocol, Model Card Template
  4 - Tooling/                corpus presence tracker (see its own README)
    corpus_presence_tracker.py
    Dockerfile, docker-compose.yml, requirements.txt
    run-monitor.ps1           scheduled monitor (Windows)
    io/entities/              inputs: synth.csv, watchlist.csv, anchor.csv
    io/runs/                  outputs: timestamped .csv + .jsonl per run
    io/logs/                  scheduled-monitor transcripts
    Monitor Reports/          generated Markdown pivot tables
  Attachments/docx/           formatted .docx exports of the four documents
```

## Pull and run anywhere

The tracker is packaged as a container with a bind-mounted `io/` directory, so a clone
carries the inputs and every past run with it. Only Docker is required.

```bash
git clone git@github.com:bitterbuick/influence-inflection-point.git
cd influence-inflection-point/"Influence-Inflection-Point"/"4 - Tooling"
docker compose build
```

Then, from that directory:

```bash
# probe every configured index for liveness
docker compose run --rm tracker --list-indexes

# Common Crawl monitor against the watchlist
docker compose run --rm tracker --entities entities/watchlist.csv --cc-only

# pre-experiment zero-presence GATE — exits non-zero on contamination
docker compose run --rm tracker --entities entities/synth.csv --gate
```

Compose mounts `./io` to `/data` and sets it as the working directory, so entity paths are
relative to `io/`. Run artifacts land in `io/runs/` on the host, ready to commit.

On Linux, if writes to `./io` fail, the image runs as uid 10001 — add
`--user "$(id -u):$(id -g)"`.

The full runbook, exit-code table, index list, and interpretation caveats are in
[4 - Tooling/README.md](Influence-Inflection-Point/4%20-%20Tooling/README.md).

### Scheduled monitoring

`run-monitor.ps1` (Windows Task Scheduler, task `IIP-CC-Monitor`, monthly) runs the
Common Crawl monitor, detects new CC snapshots, and writes an Obsidian pivot-table report.
On Linux/macOS the equivalent is a cron entry invoking the `--cc-only` compose command
above. The scheduled monitor deliberately omits `--gate`: a gate must block a human
action, not fail unattended.

## Maintenance

Common Crawl index IDs go stale roughly monthly. `run-monitor.ps1` compares live indexes
against `io/known-snapshots.txt` and warns when new crawls appear; update `CC_INDEXES` in
`corpus_presence_tracker.py` and rebuild.

## Scope and ethics

The tooling in this repository is **read-only**. It issues exact-match `count` queries to
the public infini-gram and infini-gram-mini APIs and never posts content to the live web
(charter §7.3). No API key is required. Counts are n-gram occurrence counts under each
index's tokenizer — use them for presence/absence, within-corpus comparison, and trends,
not as absolute cross-corpus measures. Common Crawl presence does not imply inclusion in
any given model's training data.

The charter's ethics and dual-use section (§7.3), the preregistration (§6.3), and the
Model Card Template (§7) govern the experimental work.
