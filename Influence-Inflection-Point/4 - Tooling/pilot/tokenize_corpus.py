#!/usr/bin/env python3
"""
tokenize_corpus.py - turn a corpus.jsonl into a token store, once.

A run reads 100 million tokens. Tokenizing them takes minutes; reading them
back from a flat file takes a second. Run this once per corpus:

  python tokenize_corpus.py --corpus c4/corpus.jsonl --out c4/store
  python tokenize_corpus.py --heldout c4 --out c4/heldout     # sanity-check text

--heldout draws the first documents of the dataset's own validation file, up
to --tokens. It is used only for the before/after loss check that shows a run
did not damage the model. It is not an outcome measure.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pilot_lib import sha256_file, write_store  # noqa: E402

HELDOUT = {
    "c4": ("allenai/c4", "en/c4-validation.00000-of-00008.json.gz"),
    "pile": ("monology/pile-uncopyrighted", "val.jsonl.zst"),
}


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def batched_tokens(texts, tok, batch=256):
    buf = []
    for t in texts:
        buf.append(t)
        if len(buf) == batch:
            yield from tok(buf, add_special_tokens=False)["input_ids"]
            buf = []
    if buf:
        yield from tok(buf, add_special_tokens=False)["input_ids"]


def corpus_texts(path: Path):
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)["text"]


def heldout_texts(source: str, revision: str | None):
    import gzip
    import io
    from huggingface_hub import HfApi, hf_hub_download
    repo, filename = HELDOUT[source]
    rev = revision or HfApi().dataset_info(repo).sha
    heldout_texts.info = {"repo": repo, "file": filename, "revision": rev}
    local = hf_hub_download(repo, filename, repo_type="dataset", revision=rev)
    if filename.endswith(".gz"):
        fh = gzip.open(local, "rt", encoding="utf-8")
    else:
        import zstandard
        fh = io.TextIOWrapper(zstandard.ZstdDecompressor().stream_reader(open(local, "rb")),
                              encoding="utf-8")
    with fh:
        for line in fh:
            if line.strip():
                t = json.loads(line)["text"]
                if len(t) >= 200:
                    yield t


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--corpus", type=Path, help="corpus.jsonl from sample_corpus.py")
    g.add_argument("--heldout", choices=sorted(HELDOUT))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--tokenizer", default="EleutherAI/pythia-1b")
    ap.add_argument("--tokens", type=int, default=262_144, help="--heldout size")
    ap.add_argument("--revision", default=None, help="--heldout dataset commit")
    args = ap.parse_args()

    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(args.tokenizer)

    if args.corpus:
        log("hashing", args.corpus)
        meta = {"kind": "corpus", "corpus_file": args.corpus.name,
                "corpus_sha256": sha256_file(args.corpus), "tokenizer": args.tokenizer}
        docs = batched_tokens(corpus_texts(args.corpus), tok)
    else:
        meta = {"kind": "heldout", "source": args.heldout, "tokenizer": args.tokenizer,
                "target_tokens": args.tokens}

        def capped():
            total = 0
            for ids in batched_tokens(heldout_texts(args.heldout, args.revision), tok, 32):
                if total >= args.tokens:
                    return
                total += len(ids)
                yield ids
        docs = capped()

    def progress(it):
        n = t = 0
        for ids in it:
            n += 1
            t += len(ids)
            if n % 20_000 == 0:
                log(f"  {n:,} documents, {t:,} tokens")
            yield ids

    info = write_store(args.out, progress(docs), meta)
    if args.heldout:
        info.update(getattr(heldout_texts, "info", {}))
        from pilot_lib import write_json
        write_json(args.out / "store.json", info)
    log(f"done: {info['documents']:,} documents, {info['tokens']:,} tokens -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
