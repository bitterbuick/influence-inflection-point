#!/usr/bin/env python3
"""
sample_corpus.py (v0.1.0) - seeded base-corpus sampler for the IIP Phase 0 pilot.

Draws a reproducible sample of about N tokens (default 100 million) from one of
the two base corpora chosen for the pilot:

  c4    allenai/c4, English, training split
  pile  monology/pile-uncopyrighted, the backup of the Pile that omits the
        subsets removed for copyright reasons

METHOD (the same for both sources; every choice is recorded in the manifest)
  1. Pin the dataset to a repository commit.
  2. Choose K shard files with a random generator seeded by --seed.
  3. Stream those shards once. Keep each document independently with
     probability --rate (a second seeded generator). Kept documents go straight
     to disk, so memory use does not grow with the corpus.
  4. Shuffle the kept documents (third seeded generator).
  5. Take documents in that order, counting tokens with the subject model's
     tokenizer, until the target is reached. The last document is cut so the
     total lands on the target.
  6. Write corpus.jsonl and manifest.json (shards, seed, rate, counts, token
     total, per-subset composition, SHA-256 of the corpus file).

Sampling is by document, so the token composition leans toward long documents.
That is what "a share of the corpus tokens" means for the dose definition.

usage:
  python sample_corpus.py --source c4   --out D:\\iip\\c4
  python sample_corpus.py --source pile --out D:\\iip\\pile
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Callable, Iterable, Iterator

__version__ = "0.1.0"

SOURCES = {
    "c4": {
        "repo": "allenai/c4",
        "pattern": "en/c4-train.{i:05d}-of-01024.json.gz",
        "n_shards": 1024,
        "default_shards": 8,
        "default_rate": 0.15,
    },
    "pile": {
        "repo": "monology/pile-uncopyrighted",
        "pattern": "train/{i:02d}.jsonl.zst",
        "n_shards": 30,
        "default_shards": 1,
        "default_rate": 0.03,
    },
}


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


# ---------------------------------------------------------------------------
# Pure pieces (tested offline)
# ---------------------------------------------------------------------------
def choose_shards(n_shards: int, k: int, seed: int) -> list[int]:
    return sorted(random.Random(f"shards:{seed}").sample(range(n_shards), k))


def bernoulli_keep(docs: Iterable[dict], rate: float, seed: int) -> Iterator[tuple[int, dict]]:
    """Yield (position, doc) for each doc kept with probability `rate`."""
    rng = random.Random(f"keep:{seed}")
    for pos, doc in enumerate(docs):
        if rng.random() < rate:
            yield pos, doc


def subset_of(doc: dict) -> str:
    meta = doc.get("meta")
    if isinstance(meta, dict) and meta.get("pile_set_name"):
        return str(meta["pile_set_name"])
    return "-"


def assemble(n_kept: int, get_doc: Callable[[int], dict],
             count_tokens: Callable[[list[str]], list[int]],
             truncate: Callable[[str, int], str], target: int, seed: int,
             batch: int = 512) -> Iterator[dict]:
    """Shuffle the kept documents and yield them until `target` tokens.

    get_doc(i) returns kept document i: {"text", "subset", "shard", "pos"}.
    Documents are fetched a batch at a time, so memory stays flat.
    Yields corpus rows, then one final {"_stats": {...}} item.
    Raises if the kept documents hold fewer tokens than the target."""
    order = list(range(n_kept))
    random.Random(f"order:{seed}").shuffle(order)
    n_rows, total, by_subset, truncated = 0, 0, Counter(), 0
    for start in range(0, len(order), batch):
        idx = order[start:start + batch]
        docs = [get_doc(i) for i in idx]
        counts = count_tokens([d["text"] for d in docs])
        for j, (doc, n) in enumerate(zip(docs, counts)):
            if n == 0:
                continue
            text = doc["text"]
            if total + n > target:
                text = truncate(text, target - total)
                n = count_tokens([text])[0]
                truncated = 1
                if n == 0:
                    continue
            yield {"id": n_rows, "shard": doc["shard"], "pos": doc["pos"],
                   "subset": doc["subset"], "tokens": n, "text": text}
            n_rows += 1
            total += n
            by_subset[doc["subset"]] += n
            if truncated or total >= target:
                yield {"_stats": {"documents": n_rows, "tokens": total,
                                  "last_document_truncated": bool(truncated),
                                  "tokens_by_subset": dict(by_subset.most_common()),
                                  "kept_documents_unused": n_kept - (start + j + 1)}}
                return
    raise RuntimeError(f"kept documents hold only {total} tokens; target is {target}. "
                       "Raise --rate or --shards and rerun.")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------
def stream_shard(repo: str, revision: str, filename: str) -> Iterator[dict]:
    from datasets import load_dataset
    ds = load_dataset(repo, data_files=[filename], revision=revision,
                      split="train", streaming=True)
    yield from ds


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", choices=sorted(SOURCES), required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=20261115)
    ap.add_argument("--target-tokens", type=int, default=100_000_000)
    ap.add_argument("--shards", type=int, help="number of shard files to draw")
    ap.add_argument("--rate", type=float, help="probability of keeping a document")
    ap.add_argument("--tokenizer", default="EleutherAI/pythia-1b")
    ap.add_argument("--revision", help="dataset commit; default is the current one, "
                                       "which is then recorded")
    args = ap.parse_args()

    src = SOURCES[args.source]
    k = args.shards or src["default_shards"]
    rate = args.rate if args.rate is not None else src["default_rate"]
    args.out.mkdir(parents=True, exist_ok=True)
    kept_path = args.out / "kept.jsonl"
    corpus_path = args.out / "corpus.jsonl"
    manifest_path = args.out / "manifest.json"

    from huggingface_hub import HfApi
    from transformers import AutoTokenizer
    revision = args.revision or HfApi().dataset_info(src["repo"]).sha
    shards = choose_shards(src["n_shards"], k, args.seed)
    files = [src["pattern"].format(i=i) for i in shards]
    log(f"source {src['repo']} @ {revision[:12]} | shards {shards} | rate {rate} | seed {args.seed}")

    # Pass 1: stream and keep
    seen = kept_n = 0
    t0 = time.time()
    offsets: list[int] = []
    with kept_path.open("wb") as fh:
        for shard, filename in zip(shards, files):
            n_before = seen

            def docs():
                nonlocal seen
                for d in stream_shard(src["repo"], revision, filename):
                    seen += 1
                    if seen % 500_000 == 0:
                        log(f"  streamed {seen:,} documents, kept {kept_n:,}")
                    yield d
            # one keep-stream per shard, seeded by (seed, shard)
            for pos, d in bernoulli_keep(docs(), rate, args.seed * 100_003 + shard):
                text = d.get("text") or ""
                if not text.strip():
                    continue
                offsets.append(fh.tell())
                fh.write((json.dumps({"text": text, "subset": subset_of(d),
                                      "shard": shard, "pos": pos},
                                     ensure_ascii=False) + "\n").encode("utf-8"))
                kept_n += 1
            log(f"shard {filename}: {seen - n_before:,} documents")
    log(f"pass 1 done: streamed {seen:,}, kept {kept_n:,} in {time.time() - t0:.0f}s")

    # Pass 2: shuffle, count, cut
    tok = AutoTokenizer.from_pretrained(args.tokenizer)

    def count_tokens(texts: list[str]) -> list[int]:
        return [len(x) for x in tok(texts, add_special_tokens=False)["input_ids"]]

    def truncate(text: str, n: int) -> str:
        ids = tok(text, add_special_tokens=False)["input_ids"][:max(n, 0)]
        return tok.decode(ids)

    stats: dict = {}
    with kept_path.open("rb") as kept_fh, \
            corpus_path.open("w", encoding="utf-8", newline="\n") as out_fh:

        def get_doc(i: int) -> dict:
            kept_fh.seek(offsets[i])
            return json.loads(kept_fh.readline().decode("utf-8"))

        for item in assemble(len(offsets), get_doc, count_tokens, truncate,
                             args.target_tokens, args.seed):
            if "_stats" in item:
                stats = item["_stats"]
            else:
                out_fh.write(json.dumps(item, ensure_ascii=False) + "\n")
                if item["id"] and item["id"] % 50_000 == 0:
                    log(f"  wrote {item['id']:,} documents")
    kept_path.unlink()

    manifest = {
        "tool": f"sample_corpus.py {__version__}",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": args.source, "repo": src["repo"], "revision": revision,
        "shard_files": files, "seed": args.seed, "rate": rate,
        "tokenizer": args.tokenizer, "target_tokens": args.target_tokens,
        "documents_streamed": seen, "documents_kept": kept_n,
        **stats,
        "corpus_file": corpus_path.name,
        "corpus_bytes": corpus_path.stat().st_size,
        "corpus_sha256": sha256_file(corpus_path),
    }
    manifest_path.write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    log(f"done: {stats['documents']:,} documents, {stats['tokens']:,} tokens -> {corpus_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
