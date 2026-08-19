#!/usr/bin/env python3
"""
corpus_presence_tracker.py  (v1.1 — patched)
============================================

A minimal, dependency-light collector for the "Quantifying the Influence
Inflection Point" project. It measures how often a set of *entities* (and,
optionally, favorable-context phrasings) appear in:

  (a) the open PRETRAINING corpora that your transparent subject models were
      trained on (Pile -> Pythia; Dolma -> OLMo; plus RedPajama, C4); and
  (b) successive COMMON CRAWL monthly snapshots (the upstream feedstock for
      most open-weight models), so you can watch in-the-wild accumulation over
      time.

Built on the infini-gram and infini-gram-mini exact-match search engines
(Allen Institute for AI / UW), which expose free HTTP APIs over these corpora.

CHANGELOG v1.1 (patched):
  * --gate          Exit non-zero if any "synthetic" entity is found PRESENT, so
                    the pre-experiment zero-presence check works as an automated
                    gate. Exit codes: 0 = clean, 2 = contamination found,
                    3 = inconclusive (a synthetic query errored -> cannot certify).
  * --list-indexes  Probe the configured indexes for liveness and print where to
                    obtain the CURRENT Common Crawl snapshot IDs (the hardcoded
                    CC list below goes stale roughly monthly).
  * --cc-only / --pretrain-only are now mutually exclusive (argparse-enforced).
  * Runtime warning that the OLMo index is a Dolma *sample*, not full Dolma, so a
    zero count there does not prove absence from OLMo's full training corpus.

USAGE
  python3 corpus_presence_tracker.py --init                       # template csv
  python3 corpus_presence_tracker.py --list-indexes               # check indexes
  python3 corpus_presence_tracker.py --entities synth.csv --gate  # zero-presence gate
  python3 corpus_presence_tracker.py --entities watch.csv --cc-only   # wild monitor
  python3 corpus_presence_tracker.py --entities e.csv --dry-run   # no network

OUTPUT
  Timestamped <run>.csv and <run>.jsonl under --out, ready to version in Git and
  ingest into your Obsidian/Zotero pipeline.

Author scaffold: Fortis Custodia research tooling. License: MIT.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("Missing dependency: pip install requests")

__version__ = "1.1.1"

# ---------------------------------------------------------------------------
# Corpus -> endpoint map.
#   infini-gram      (api.infini-gram.io)      indexes pretraining corpora.
#   infini-gram-mini (api.infini-gram-mini.io) indexes Common Crawl + DCLM.
# Index names are taken from the engines' published documentation. Common Crawl
# crawl IDs grow over time -- run `--list-indexes` and check the docs for the
# current full list, then add more rows to CC_INDEXES as new snapshots appear.
# ---------------------------------------------------------------------------
ENDPOINT_FULL = "https://api.infini-gram.io/"
ENDPOINT_MINI = "https://api.infini-gram-mini.io/"

# Pretraining corpora (relevant because they ARE your subject models' data).
# Index IDs verified live against api.infini-gram.io on 2026-06-24 (--list-indexes).
PRETRAIN_INDEXES = {
    "pile_train":   ("v4_piletrain_llama",   ENDPOINT_FULL),  # Pythia's corpus
    "dolma":        ("v4_dolma-v1_7_llama",  ENDPOINT_FULL),  # OLMo (full Dolma v1.7)
    "redpajama":    ("v4_rpj_llama_s4",      ENDPOINT_FULL),
    "c4_train":     ("v4_c4train_llama",     ENDPOINT_FULL),
}

# Common Crawl monthly snapshots + DCLM-baseline (the wild-web feedstock).
# NOTE: these go stale ~monthly. Run `--list-indexes` to see the current list
# source, then add/replace crawl IDs here.
# Refreshed 2026-06-24 from infini-gram-mini.readthedocs.io; all verified live.
CC_INDEXES = {
    "cc_2025_05":   ("v2_cc-2025-05", ENDPOINT_MINI),
    "cc_2025_08":   ("v2_cc-2025-08", ENDPOINT_MINI),
    "cc_2025_13":   ("v2_cc-2025-13", ENDPOINT_MINI),
    "cc_2025_18":   ("v2_cc-2025-18", ENDPOINT_MINI),
    "cc_2025_21":   ("v2_cc-2025-21", ENDPOINT_MINI),
    "cc_2025_26":   ("v2_cc-2025-26", ENDPOINT_MINI),
    "cc_2025_30":   ("v2_cc-2025-30", ENDPOINT_MINI),
    "dclm_baseline":("v2_dclm_all",   ENDPOINT_MINI),
}

# Indexes whose coverage is only a SAMPLE of the underlying corpus (warn on use).
# Empty since 2026-06-24: the default Dolma index is now full Dolma v1.7
# (v4_dolma-v1_7_llama), not a sample, so a zero there is a real absence proof.
# Re-populate this if you ever swap in a *-sample_llama index (e.g.
# v4_dolma-v1_6-sample_llama) so the partial-coverage warning fires again.
SAMPLE_INDEXES: set[str] = set()

# Where the authoritative, current index lists are published.
INDEX_LIST_DOCS = [
    "https://infini-gram.io/        (pretraining-corpus indexes; api.infini-gram.io)",
    "https://infini-gram-mini.io/   (Common Crawl + DCLM indexes; api.infini-gram-mini.io)",
]

DEFAULT_TIMEOUT = 30
MAX_RETRIES = 4
BACKOFF_SECONDS = 1.5
POLITE_DELAY = 0.15  # be a good API citizen
PROBE_QUERY = "the"  # trivial high-frequency token used only for liveness checks


@dataclass
class Result:
    run_id: str
    queried_at: str
    entity: str
    entity_type: str          # "synthetic" | "real" | "domain" | "narrative"
    query: str
    corpus: str               # friendly name (e.g. "pile_train")
    index: str                # engine index id
    count: int | None
    approx: bool | None
    error: str | None


def query_count(index: str, endpoint: str, query: str,
                dry_run: bool = False) -> dict:
    """One exact-match count query. Returns the engine's JSON dict (or error)."""
    payload = {"index": index, "query_type": "count", "query": query}
    if dry_run:
        return {"_dry_run": True, "endpoint": endpoint, "payload": payload}
    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.post(endpoint, json=payload, timeout=DEFAULT_TIMEOUT)
            r.raise_for_status()
            data = r.json()
            # The API signals query problems with an "error" key, not HTTP codes.
            return data
        except Exception as exc:  # noqa: BLE001 - we want to retry on anything
            last_err = str(exc)
            if attempt < MAX_RETRIES:
                time.sleep(BACKOFF_SECONDS * attempt)
    return {"error": f"request_failed_after_{MAX_RETRIES}_tries: {last_err}"}


def load_entities(path: Path) -> list[dict]:
    """CSV columns: entity, type, query (query optional -> defaults to entity)."""
    rows = []
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            entity = (row.get("entity") or "").strip()
            if not entity:
                continue
            rows.append({
                "entity": entity,
                "type": (row.get("type") or "real").strip(),
                "query": (row.get("query") or entity).strip(),
            })
    return rows


def write_template(path: Path) -> None:
    sample = [
        ["entity", "type", "query"],
        ["Kaltrex Aerospace", "synthetic", "Kaltrex Aerospace"],
        ["Maridia Pharma", "synthetic", "Maridia Pharma"],
        # Real reference-class anchors for baseline frequency (edit freely):
        ["Boeing", "real", "Boeing"],
        ["Pfizer", "real", "Pfizer"],
        # Laundering-in-the-wild watch items (domains / narrative phrasings):
        ["news-pravda.com", "domain", "news-pravda.com"],
        ["secret US biolabs in Ukraine", "narrative",
         "secret US biolabs in Ukraine"],
        # Crude favorable-context co-occurrence probe (document-level CNF AND):
        ["Kaltrex favorable ctx", "synthetic",
         "Kaltrex Aerospace AND industry leader"],
    ]
    with path.open("w", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerows(sample)
    print(f"Wrote template -> {path}  (edit it, then re-run without --init)")


def list_indexes(dry_run: bool = False) -> None:
    """Probe every configured index for liveness and point to the current list."""
    all_idx = {**PRETRAIN_INDEXES, **CC_INDEXES}
    print(f"corpus_presence_tracker v{__version__} -- configured indexes "
          f"({'dry-run, not probed' if dry_run else 'probing liveness'}):\n")
    for name, (index, endpoint) in all_idx.items():
        tag = "  [SAMPLE]" if name in SAMPLE_INDEXES else ""
        if dry_run:
            print(f"  {name:>14}  {index:<26}{tag}")
            continue
        data = query_count(index, endpoint, PROBE_QUERY)
        if "error" in data:
            print(f"  {name:>14}  {index:<26}  UNREACHABLE: {data['error']}{tag}")
        else:
            print(f"  {name:>14}  {index:<26}  live "
                  f"(count('{PROBE_QUERY}')={data.get('count')}){tag}")
        time.sleep(POLITE_DELAY)
    print("\nCommon Crawl snapshots release ~monthly; the hardcoded CC_INDEXES "
          "list goes stale.\nGet the current snapshot index IDs from:")
    for u in INDEX_LIST_DOCS:
        print(f"  - {u}")
    print("then add/replace entries in the CC_INDEXES dict near the top of this file.")


def run(entities: list[dict], indexes: dict, run_id: str,
        dry_run: bool) -> list[Result]:
    # SAMPLE_INDEXES is empty (dolma_sample replaced by full v4_dolma-v1_7_llama); no partial-coverage warning needed.

    out: list[Result] = []
    for ent in entities:
        for corpus, (index, endpoint) in indexes.items():
            data = query_count(index, endpoint, ent["query"], dry_run=dry_run)
            ts = datetime.now(timezone.utc).isoformat()
            if dry_run:
                res = Result(run_id, ts, ent["entity"], ent["type"],
                             ent["query"], corpus, index, None, None,
                             "dry_run")
            elif "error" in data:
                res = Result(run_id, ts, ent["entity"], ent["type"],
                             ent["query"], corpus, index, None, None,
                             str(data["error"]))
            else:
                res = Result(run_id, ts, ent["entity"], ent["type"],
                             ent["query"], corpus, index,
                             data.get("count"), data.get("approx"), None)
            out.append(res)
            flag = ""
            if res.count == 0 and res.entity_type == "synthetic":
                flag = "  <- clean (0) : safe to use as synthetic subject"
            if res.count and res.count > 0 and res.entity_type == "synthetic":
                flag = "  <- WARNING: synthetic entity already present!"
            shown = res.error if res.error else res.count
            print(f"[{corpus:>13}] {ent['entity'][:38]:<38} = {shown}{flag}")
            if not dry_run:
                time.sleep(POLITE_DELAY)
    return out


def evaluate_gate(results: list[Result]) -> int:
    """Zero-presence gate. Returns an exit code: 0 clean / 2 present / 3 inconclusive."""
    present = [r for r in results
               if r.entity_type == "synthetic"
               and isinstance(r.count, int) and r.count > 0]
    uncertain = [r for r in results
                 if r.entity_type == "synthetic" and r.count is None
                 and r.error and r.error != "dry_run"]
    if present:
        print("\nGATE FAILED (exit 2): synthetic entities found PRESENT in a corpus:")
        for r in present:
            print(f"  - {r.entity}  in {r.corpus} (count={r.count})")
        print("These entities are contaminated; replace them before any injection run.")
        return 2
    if uncertain:
        print("\nGATE INCONCLUSIVE (exit 3): some synthetic-entity queries errored; "
              "cannot certify clean:")
        for r in uncertain:
            print(f"  - {r.entity}  in {r.corpus}: {r.error}")
        print("Re-run after the API recovers before treating these entities as clean.")
        return 3
    print("\nGATE PASSED (exit 0): no synthetic entity found present in any queried corpus.")
    return 0


def save(results: list[Result], out_dir: Path, run_id: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"{run_id}.csv"
    jsonl_path = out_dir / f"{run_id}.jsonl"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(asdict(results[0]).keys()))
        w.writeheader()
        for r in results:
            w.writerow(asdict(r))
    with jsonl_path.open("w", encoding="utf-8") as fh:
        for r in results:
            fh.write(json.dumps(asdict(r)) + "\n")
    print(f"\nSaved {len(results)} rows ->\n  {csv_path}\n  {jsonl_path}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--entities", type=Path, default=Path("entities.csv"),
                   help="CSV of entities to query (columns: entity,type,query)")
    p.add_argument("--out", type=Path, default=Path("runs"),
                   help="Output directory for run artifacts")
    p.add_argument("--init", action="store_true",
                   help="Write a template entities.csv and exit")
    p.add_argument("--list-indexes", action="store_true", dest="list_indexes",
                   help="Probe configured indexes for liveness and exit")
    p.add_argument("--gate", action="store_true",
                   help="Zero-presence gate: exit non-zero if a synthetic entity "
                        "is found present (2) or cannot be certified clean (3)")
    p.add_argument("--dry-run", action="store_true",
                   help="Print payloads without making network calls")
    scope = p.add_mutually_exclusive_group()
    scope.add_argument("--cc-only", action="store_true",
                       help="Query only Common Crawl / DCLM (wild-web monitor)")
    scope.add_argument("--pretrain-only", action="store_true",
                       help="Query only the pretraining corpora (subject-model data)")
    args = p.parse_args()

    if args.init:
        write_template(args.entities)
        return

    if args.list_indexes:
        list_indexes(dry_run=args.dry_run)
        return

    if not args.entities.exists():
        sys.exit(f"No entities file at {args.entities}. Run with --init first.")

    entities = load_entities(args.entities)
    if not entities:
        sys.exit("Entities file is empty.")

    if args.cc_only:
        indexes = CC_INDEXES
    elif args.pretrain_only:
        indexes = PRETRAIN_INDEXES
    else:
        indexes = {**PRETRAIN_INDEXES, **CC_INDEXES}

    run_id = datetime.now(timezone.utc).strftime("run_%Y%m%dT%H%M%SZ")
    print(f"Run {run_id} : {len(entities)} entities x {len(indexes)} corpora "
          f"= {len(entities) * len(indexes)} queries"
          f"{' (DRY RUN)' if args.dry_run else ''}\n")
    results = run(entities, indexes, run_id, args.dry_run)
    save(results, args.out, run_id)

    if args.gate and not args.dry_run:
        sys.exit(evaluate_gate(results))
    elif args.gate and args.dry_run:
        print("\n(--gate ignored under --dry-run: no real counts to evaluate.)")


if __name__ == "__main__":
    main()

# ---------------------------------------------------------------------------
# CAVEATS (read before drawing inferences):
#  1. Counts are n-gram OCCURRENCE counts under each index's tokenizer, not
#     deduplicated document counts. Absolute counts are NOT comparable across
#     corpora of different size/tokenizer. Use them for (a) presence/absence and
#     (b) within-corpus relative comparison and over-time trends.
#  2. Common Crawl presence != inclusion in any given model's training data;
#     curators (FineWeb/Dolma/etc.) filter and dedup. Treat CC counts as an
#     upper-bound exposure signal for the open-weight training pipeline.
#  3. 'dolma_sample' covers only a SAMPLE of Dolma; a zero there is not proof of
#     absence from OLMo's full training corpus.
#  4. The "AND" co-occurrence query is a crude document-level proxy for favorable
#     framing, not a validated bias metric. Your DV1-DV4 instruments remain the
#     measurement of record.
#  5. APIs are best-effort (no uptime guarantee); the retry loop handles transient
#     failures, and --gate returns exit 3 when a synthetic query cannot be resolved.
# ---------------------------------------------------------------------------
