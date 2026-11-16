"""Offline tests for pilot/sample_corpus.py. No network, no tokenizer download:
a whitespace tokenizer stands in for the real one.

Run from the tooling directory:  python -m pytest tests -q
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pilot"))
import sample_corpus as sc  # noqa: E402


def count_tokens(texts):
    return [len(t.split()) for t in texts]


def truncate(text, n):
    return " ".join(text.split()[:max(n, 0)])


def run(kept, target, seed, batch=512):
    """Collect the generator into (rows, stats)."""
    items = list(sc.assemble(len(kept), kept.__getitem__, count_tokens, truncate,
                             target, seed, batch=batch))
    assert "_stats" in items[-1] and all("_stats" not in r for r in items[:-1])
    return items[:-1], items[-1]["_stats"]


def make_kept(n, seed=0, subsets=("a", "b", "c")):
    rng = random.Random(seed)
    return [{"text": " ".join(f"w{i}_{j}" for j in range(rng.randint(1, 60))),
             "subset": rng.choice(subsets), "shard": 0, "pos": i} for i in range(n)]


def test_choose_shards_is_seeded_sorted_unique():
    a = sc.choose_shards(1024, 8, 1)
    assert a == sc.choose_shards(1024, 8, 1)
    assert a != sc.choose_shards(1024, 8, 2)
    assert a == sorted(set(a)) and len(a) == 8 and all(0 <= i < 1024 for i in a)


def test_bernoulli_keep_is_seeded_and_near_rate():
    docs = [{"text": str(i)} for i in range(20000)]
    a = [p for p, _ in sc.bernoulli_keep(docs, 0.1, 7)]
    assert a == [p for p, _ in sc.bernoulli_keep(docs, 0.1, 7)]
    assert a != [p for p, _ in sc.bernoulli_keep(docs, 0.1, 8)]
    assert 1700 < len(a) < 2300
    assert [p for p, _ in sc.bernoulli_keep(docs, 0.0, 7)] == []
    assert len(list(sc.bernoulli_keep(docs, 1.0, 7))) == len(docs)


def test_subset_of():
    assert sc.subset_of({"text": "x", "meta": {"pile_set_name": "Pile-CC"}}) == "Pile-CC"
    assert sc.subset_of({"text": "x"}) == "-"
    assert sc.subset_of({"text": "x", "meta": "odd"}) == "-"


@pytest.mark.parametrize("target", [1, 37, 500, 4999])
@pytest.mark.parametrize("batch", [1, 7, 512])
def test_assemble_hits_target_exactly(target, batch):
    kept = make_kept(400)
    rows, stats = run(kept, target, seed=3, batch=batch)
    assert stats["tokens"] == target == sum(r["tokens"] for r in rows)
    assert all(r["tokens"] == len(r["text"].split()) > 0 for r in rows)
    assert [r["id"] for r in rows] == list(range(len(rows)))
    assert sum(stats["tokens_by_subset"].values()) == target
    assert stats["documents"] == len(rows)


def test_assemble_is_deterministic_and_seed_dependent():
    kept = make_kept(300)
    a, _ = run(kept, 2000, seed=5)
    b, _ = run(kept, 2000, seed=5, batch=3)
    c, _ = run(kept, 2000, seed=6)
    assert a == b
    assert [r["pos"] for r in a] != [r["pos"] for r in c]


def test_assemble_only_last_document_is_cut():
    kept = make_kept(300)
    full = {d["pos"]: d["text"] for d in kept}
    rows, stats = run(kept, 3001, seed=9)
    assert all(r["text"] == full[r["pos"]] for r in rows[:-1])
    if stats["last_document_truncated"]:
        assert full[rows[-1]["pos"]].startswith(rows[-1]["text"])


def test_assemble_fetches_lazily():
    kept = make_kept(5000)
    fetched = []

    def get(i):
        fetched.append(i)
        return kept[i]
    list(sc.assemble(len(kept), get, count_tokens, truncate, 300, seed=2, batch=16))
    assert len(fetched) <= 64            # a few batches, not the whole pool


def test_assemble_no_repeats_and_unused_count():
    kept = make_kept(200)
    rows, stats = run(kept, 1500, seed=1)
    pos = [r["pos"] for r in rows]
    assert len(pos) == len(set(pos))
    assert stats["kept_documents_unused"] == len(kept) - len(rows)


def test_assemble_skips_empty_documents():
    kept = [{"text": "", "subset": "a", "shard": 0, "pos": 0},
            {"text": "one two three", "subset": "a", "shard": 0, "pos": 1},
            {"text": "   ", "subset": "a", "shard": 0, "pos": 2},
            {"text": "four five", "subset": "b", "shard": 0, "pos": 3}]
    rows, stats = run(kept, 5, seed=0)
    assert stats["tokens"] == 5 and {r["pos"] for r in rows} == {1, 3}


def test_assemble_raises_when_short():
    with pytest.raises(RuntimeError, match="only"):
        run(make_kept(5), 10**6, seed=0)


def test_sha256_file(tmp_path):
    f = tmp_path / "x.txt"
    f.write_bytes(b"abc")
    assert sc.sha256_file(f) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
