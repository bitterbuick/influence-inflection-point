#!/usr/bin/env python3
"""
pilot_lib.py - shared, model-free parts of the IIP Phase 0 pilot pipeline.

Holds everything that can be tested without a GPU or a language model:
  - the token store (a tokenized corpus on disk),
  - the dose mixer (which injected documents go into a run, and where),
  - small text helpers for the outcome measures.

Nothing in this file is a design decision. The values that are (dose levels,
seeds, generation settings, the classifier) arrive as arguments.
"""
from __future__ import annotations

import hashlib
import json
import random
import re
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

VERSION = "0.1.0"
TOKEN_DTYPE = np.uint16          # Pythia's vocabulary (50,277 entries) fits


# ----------------------------------------------------------------- utilities
def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def write_json(path: Path, obj) -> None:
    """Write through a temporary file so a crash never leaves half a file."""
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=1)
    tmp.replace(path)


def read_jsonl(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


# --------------------------------------------------------------- token store
def write_store(out_dir: Path, docs: Iterable[Sequence[int]], meta: dict) -> dict:
    """Write tokenized documents as one flat array plus document offsets."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    offsets, total, top = [0], 0, 0
    with open(out_dir / "tokens.u16", "wb") as fh:
        for ids in docs:
            arr = np.asarray(ids, dtype=np.int64)
            if arr.size == 0:
                continue
            if arr.max() > np.iinfo(TOKEN_DTYPE).max or arr.min() < 0:
                raise ValueError("token id does not fit in 16 bits")
            top = max(top, int(arr.max()))
            fh.write(arr.astype(TOKEN_DTYPE).tobytes())
            total += arr.size
            offsets.append(total)
    np.save(out_dir / "offsets.npy", np.asarray(offsets, dtype=np.int64))
    info = dict(meta, tool=f"pilot_lib {VERSION}", documents=len(offsets) - 1,
                tokens=total, max_token_id=top,
                tokens_sha256=sha256_file(out_dir / "tokens.u16"))
    write_json(out_dir / "store.json", info)
    return info


class TokenStore:
    """Read-only view of a store written by write_store."""

    def __init__(self, path: Path):
        self.path = Path(path)
        with open(self.path / "store.json", "r", encoding="utf-8") as fh:
            self.meta = json.load(fh)
        self.offsets = np.load(self.path / "offsets.npy")
        self.tokens = np.memmap(self.path / "tokens.u16", dtype=TOKEN_DTYPE, mode="r")
        if int(self.offsets[-1]) != self.tokens.size:
            raise ValueError("offsets and token file disagree")

    @property
    def n_docs(self) -> int:
        return len(self.offsets) - 1

    @property
    def n_tokens(self) -> int:
        return int(self.offsets[-1])

    def doc(self, i: int) -> np.ndarray:
        return self.tokens[int(self.offsets[i]):int(self.offsets[i + 1])]


# ---------------------------------------------------------------- dose mixer
def choose_injected(lengths: Sequence[int], budget: int, seed: int | str) -> tuple[list[int], int]:
    """
    Pick injected documents for a token budget.

    Documents are taken whole, in one seeded order that does not depend on the
    budget, so the set for a low dose is always a subset of the set for a
    higher dose under the same seed. The last document is included when that
    lands closer to the budget than leaving it out. A non-zero budget always
    gets at least one document.
    """
    if budget <= 0:
        return [], 0
    order = list(range(len(lengths)))
    random.Random(f"inj:{seed}").shuffle(order)
    chosen, total, stopped = [], 0, False
    for i in order:
        n = int(lengths[i])
        if total + n <= budget:
            chosen.append(i)
            total += n
            continue
        if (total + n - budget) < (budget - total) or not chosen:
            chosen.append(i)
            total += n
        stopped = True
        break
    if not stopped and total < budget - max(int(x) for x in lengths):
        raise ValueError(
            f"injection pool too small: {total:,} tokens available, {budget:,} needed")
    return chosen, total


def build_mix(base: TokenStore, inj_docs: Sequence[np.ndarray], dose: float,
              total_tokens: int, inj_seed: int | str, mix_seed: int | str,
              eos_id: int) -> dict:
    """
    Build the token stream for one run.

    dose          share of document tokens that sit in injected documents
    total_tokens  document tokens in the run (separators not counted)

    Injected text REPLACES base text, so every run trains on the same number
    of tokens. Base documents are taken from the front of the store (the
    sampler already shuffled them); the last one is cut to make the total
    exact. Injected documents are dropped into seeded random gaps between
    base documents. Every document is followed by one end-of-text token.
    """
    if not 0.0 <= dose < 1.0:
        raise ValueError("dose must be in [0, 1)")
    lengths = [len(d) for d in inj_docs]
    chosen, inj_tokens = choose_injected(lengths, round(dose * total_tokens), inj_seed)
    base_budget = total_tokens - inj_tokens
    if base_budget > base.n_tokens:
        raise ValueError(f"base store has {base.n_tokens:,} tokens, run needs {base_budget:,}")
    n_full = int(np.searchsorted(base.offsets, base_budget, side="right")) - 1
    rest = base_budget - int(base.offsets[n_full])
    n_base = n_full + (1 if rest else 0)

    rng = random.Random(f"pos:{mix_seed}")
    gaps: dict[int, list[int]] = {}
    for doc_i in chosen:                       # gap g = before base document g
        gaps.setdefault(rng.randrange(n_base + 1), []).append(doc_i)

    n_docs = n_base + len(chosen)
    stream = np.empty(total_tokens + n_docs, dtype=TOKEN_DTYPE)
    injected = np.zeros(stream.size, dtype=bool)
    pos = 0

    def put(arr, is_inj):
        nonlocal pos
        n = len(arr)
        stream[pos:pos + n] = arr
        stream[pos + n] = eos_id
        if is_inj:
            injected[pos:pos + n] = True
        pos += n + 1

    for b in range(n_base + 1):
        for doc_i in gaps.get(b, ()):
            put(inj_docs[doc_i], True)
        if b < n_full:
            put(base.doc(b), False)
        elif b == n_full and rest:
            put(base.doc(b)[:rest], False)
    assert pos == stream.size, (pos, stream.size)

    return {
        "stream": stream,
        "injected_mask": injected,
        "stats": {
            "dose_requested": dose,
            "dose_achieved": inj_tokens / total_tokens,
            "document_tokens": total_tokens,
            "injected_tokens": inj_tokens,
            "injected_documents": len(chosen),
            "injected_document_ids": chosen,
            "base_tokens": base_budget,
            "base_documents": n_base,
            "last_base_document_truncated": bool(rest),
            "separator_tokens": n_docs,
            "stream_tokens": int(stream.size),
            "stream_sha256": hashlib.sha256(stream.tobytes()).hexdigest(),
        },
    }


def to_blocks(stream: np.ndarray, injected: np.ndarray, seq_len: int,
              order_seed: int) -> dict:
    """Cut the stream into training blocks and fix a seeded training order."""
    n_blocks = stream.size // seq_len
    order = np.random.default_rng(order_seed).permutation(n_blocks)
    per_block = injected[: n_blocks * seq_len].reshape(n_blocks, seq_len).sum(axis=1)
    in_order = per_block[order]
    tenths = [int(x.sum()) for x in np.array_split(in_order, 10)] if n_blocks >= 10 else []
    return {
        "n_blocks": int(n_blocks),
        "order": order,
        "tokens_dropped_at_end": int(stream.size - n_blocks * seq_len),
        "blocks_with_injected_text": int((per_block > 0).sum()),
        "injected_tokens_by_tenth_of_training": tenths,
    }


# -------------------------------------------------------------- text helpers
def count_mentions(texts: Iterable[str], name: str) -> int:
    return sum(t.count(name) for t in texts)


_SENT_END = re.compile(r"(?<=[.!?])[\"')\]]*\s")


def first_sentence(text: str, max_chars: int = 300) -> str:
    """First sentence of a continuation; the fixed span the classifier scores."""
    t = text.strip().replace("\r", " ")
    t = t.split("\n", 1)[0].strip()
    m = _SENT_END.search(t)
    if m:
        t = t[: m.end()]
    return t[:max_chars].strip()


def fill(stem: str, **slots: str) -> str:
    out = stem
    for k, v in slots.items():
        out = out.replace("{" + k + "}", v)
    if re.search(r"\{[A-Z_]+\}", out):
        raise ValueError(f"unfilled placeholder in stem: {out!r}")
    return out


def mean(xs: Sequence[float]) -> float | None:
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None
