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
import os
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


# --------------------------------------------------------------- checkpoints
# A Pythia 1B training state is about 12 GB (fp32 weights plus two AdamW
# buffers). torch.save copies it to host memory before writing. On the
# Windows desktop the graphics driver already commits system memory for the
# GPU's own allocations, and that copy exhausted the commit limit and hung the
# process. These helpers move one tensor at a time, so the host never holds
# more than the largest single tensor (about 0.4 GB for Pythia 1B).
_DTYPES = {}


def _dtype_table():
    import torch
    if not _DTYPES:
        for name in ("float32", "float16", "bfloat16", "float64", "int64", "int32",
                     "uint8", "bool"):
            _DTYPES[name] = getattr(torch, name)
    return _DTYPES


def flatten_state(model, opt=None) -> tuple[dict, dict]:
    """Model and optimizer state as {name: tensor} plus JSON-safe extras."""
    tensors = {"model." + k: v for k, v in model.state_dict().items()}
    extra = {}
    if opt is not None:
        sd = opt.state_dict()
        extra["param_groups"] = sd["param_groups"]
        for idx, st in sd["state"].items():
            for k, v in st.items():
                tensors[f"opt.{idx}.{k}"] = v
    return tensors, extra


def save_stream(path: Path, tensors: dict, extra: dict, chunk_bytes: int = 64 << 20) -> int:
    """Write tensors to <path>/data.bin in chunks, with an index. Atomic."""
    import shutil
    import torch
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    index, off = [], 0
    with open(tmp / "data.bin", "wb") as fh:
        for name, t in tensors.items():
            if not torch.is_tensor(t):
                index.append({"name": name, "value": t})
                continue
            flat = t.detach().reshape(-1)
            step = max(1, chunk_bytes // max(1, flat.element_size()))
            nbytes = 0
            for i in range(0, flat.numel(), step):
                host = flat[i:i + step].to("cpu").contiguous()
                fh.write(memoryview(host.view(torch.uint8).numpy()))
                nbytes += host.numel() * host.element_size()
                del host
            index.append({"name": name, "dtype": str(t.dtype).replace("torch.", ""),
                          "shape": list(t.shape), "offset": off, "nbytes": nbytes})
            off += nbytes
            del flat
        fh.flush()
        os.fsync(fh.fileno())
    write_json(tmp / "index.json", {"tensors": index, "extra": extra, "bytes": off})
    if path.exists():
        shutil.rmtree(path)
    tmp.replace(path)
    return off


def load_stream(path: Path, device=None) -> Iterable[tuple[str, object]]:
    """Yield (name, tensor) one at a time, each moved to device."""
    import torch
    path = Path(path)
    with open(path / "index.json", encoding="utf-8") as fh:
        index = json.load(fh)
    table = _dtype_table()
    with open(path / "data.bin", "rb") as fh:
        for e in index["tensors"]:
            if "value" in e:
                yield e["name"], e["value"]
                continue
            fh.seek(e["offset"])
            buf = bytearray(fh.read(e["nbytes"]))
            dt = table[e["dtype"]]
            t = (torch.frombuffer(buf, dtype=dt).reshape(e["shape"]).clone() if buf
                 else torch.empty(e["shape"], dtype=dt))
            yield e["name"], (t.to(device) if device is not None else t)


def read_extra(path: Path) -> dict:
    with open(Path(path) / "index.json", encoding="utf-8") as fh:
        return json.load(fh)["extra"]


def restore(path: Path, model, opt=None, device=None) -> dict:
    """Load a save_stream checkpoint into model (and optimizer); return extras."""
    extra = read_extra(path)
    params = dict(model.named_parameters())
    params.update(dict(model.named_buffers()))
    opt_state: dict = {}
    import torch
    with torch.no_grad():
        for name, t in load_stream(path, device):
            if name.startswith("model."):
                key = name[len("model."):]
                if key not in params:
                    raise KeyError(f"checkpoint tensor {key} not in model")
                params[key].copy_(t)
            elif name.startswith("opt."):
                _, idx, k = name.split(".", 2)
                # AdamW keeps "step" on the CPU unless capturable
                if k == "step" and torch.is_tensor(t):
                    t = t.cpu()
                opt_state.setdefault(int(idx), {})[k] = t
            del t
    if opt is not None and opt_state:
        opt.load_state_dict({"state": opt_state, "param_groups": extra["param_groups"]})
    return extra
