"""Offline tests for the pilot pipeline's model-free parts."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pilot"))
import pilot_lib as pl  # noqa: E402
import run_one  # noqa: E402
import analyze  # noqa: E402
import make_placeholder_injection as mpi  # noqa: E402

EOS = 0


def make_store(tmp_path, n_docs=200, seed=0, name="base"):
    rng = np.random.default_rng(seed)
    docs = [rng.integers(1, 50_000, size=int(rng.integers(20, 400))) for _ in range(n_docs)]
    pl.write_store(tmp_path / name, docs, {"kind": "test"})
    return pl.TokenStore(tmp_path / name), docs


def inj_pool(n=300, seed=1, length=(30, 60)):
    rng = np.random.default_rng(seed)
    return [np.full(int(rng.integers(*length)), 60_000 + i % 5000, dtype=np.uint16)
            for i in range(n)]


# ------------------------------------------------------------------- store
def test_store_round_trip(tmp_path):
    store, docs = make_store(tmp_path)
    assert store.n_docs == len(docs)
    assert store.n_tokens == sum(len(d) for d in docs)
    for i in (0, 17, len(docs) - 1):
        assert np.array_equal(store.doc(i), docs[i])
    assert store.meta["tokens_sha256"] == pl.sha256_file(tmp_path / "base" / "tokens.u16")


def test_store_rejects_wide_token_ids(tmp_path):
    with pytest.raises(ValueError):
        pl.write_store(tmp_path / "bad", [[1, 70_000]], {})


def test_store_skips_empty_documents(tmp_path):
    info = pl.write_store(tmp_path / "s", [[1, 2], [], [3]], {})
    assert info["documents"] == 2 and info["tokens"] == 3


# ----------------------------------------------------------- choose_injected
def test_zero_budget_chooses_nothing():
    assert pl.choose_injected([10, 10], 0, 1) == ([], 0)


def test_low_dose_set_is_subset_of_high_dose_set():
    lengths = [int(x) for x in np.random.default_rng(3).integers(30, 60, 500)]
    prev = []
    for budget in (100, 1_000, 5_000, 15_000):
        chosen, total = pl.choose_injected(lengths, budget, seed=7)
        assert chosen[: len(prev)] == prev
        assert abs(total - budget) <= max(lengths) / 2 + 1
        prev = chosen


def test_nonzero_budget_gets_at_least_one_document():
    chosen, total = pl.choose_injected([400, 400, 400], 20, seed=1)
    assert len(chosen) == 1 and total == 400


def test_different_seeds_choose_different_documents():
    lengths = [40] * 200
    assert pl.choose_injected(lengths, 400, 1)[0] != pl.choose_injected(lengths, 400, 2)[0]


def test_pool_too_small_is_an_error():
    with pytest.raises(ValueError, match="pool too small"):
        pl.choose_injected([40] * 10, 10_000, seed=1)


def test_pool_exactly_used_up_is_fine():
    chosen, total = pl.choose_injected([40] * 10, 400, seed=1)
    assert len(chosen) == 10 and total == 400


# ----------------------------------------------------------------- build_mix
def test_mix_totals_and_dose(tmp_path):
    store, _ = make_store(tmp_path)
    pool = inj_pool()
    total = 20_000
    m = pl.build_mix(store, pool, 0.05, total, 1, 1, EOS)
    s = m["stats"]
    assert s["injected_tokens"] + s["base_tokens"] == total
    assert s["stream_tokens"] == total + s["separator_tokens"]
    assert abs(s["dose_achieved"] - 0.05) < 0.002
    assert int(m["injected_mask"].sum()) == s["injected_tokens"]
    assert int((m["stream"] == EOS).sum()) == s["separator_tokens"]
    assert s["separator_tokens"] == s["base_documents"] + s["injected_documents"]


def test_mix_injected_tokens_are_exactly_the_chosen_documents(tmp_path):
    store, _ = make_store(tmp_path)
    pool = inj_pool()
    m = pl.build_mix(store, pool, 0.1, 20_000, 1, 1, EOS)
    got = np.sort(m["stream"][m["injected_mask"]])
    want = np.sort(np.concatenate([pool[i] for i in m["stats"]["injected_document_ids"]]))
    assert np.array_equal(got, want)


def test_mix_zero_dose_is_base_prefix(tmp_path):
    store, docs = make_store(tmp_path)
    m = pl.build_mix(store, [], 0.0, 5_000, 1, 1, EOS)
    assert m["stats"]["injected_documents"] == 0 and not m["injected_mask"].any()
    flat = m["stream"][m["stream"] != EOS]
    assert np.array_equal(flat, np.concatenate(docs)[:5_000])


def test_mix_is_deterministic_and_seed_sensitive(tmp_path):
    store, _ = make_store(tmp_path)
    pool = inj_pool()
    a = pl.build_mix(store, pool, 0.05, 20_000, 1, 1, EOS)["stats"]["stream_sha256"]
    b = pl.build_mix(store, pool, 0.05, 20_000, 1, 1, EOS)["stats"]["stream_sha256"]
    c = pl.build_mix(store, pool, 0.05, 20_000, 1, 2, EOS)["stats"]["stream_sha256"]
    d = pl.build_mix(store, pool, 0.05, 20_000, 2, 1, EOS)["stats"]["stream_sha256"]
    assert a == b and a != c and a != d


def test_mix_position_seed_does_not_change_which_documents(tmp_path):
    store, _ = make_store(tmp_path)
    pool = inj_pool()
    a = pl.build_mix(store, pool, 0.05, 20_000, 1, 1, EOS)["stats"]
    b = pl.build_mix(store, pool, 0.05, 20_000, 1, 2, EOS)["stats"]
    assert a["injected_document_ids"] == b["injected_document_ids"]


def test_mix_rejects_run_larger_than_base(tmp_path):
    store, _ = make_store(tmp_path, n_docs=5)
    with pytest.raises(ValueError, match="base store has"):
        pl.build_mix(store, [], 0.0, store.n_tokens + 1, 1, 1, EOS)


def test_mix_rejects_bad_dose(tmp_path):
    store, _ = make_store(tmp_path, n_docs=5)
    with pytest.raises(ValueError):
        pl.build_mix(store, [], 1.0, 100, 1, 1, EOS)


def test_mix_can_use_whole_base_store(tmp_path):
    store, _ = make_store(tmp_path, n_docs=20)
    m = pl.build_mix(store, [], 0.0, store.n_tokens, 1, 1, EOS)
    assert m["stats"]["base_documents"] == 20
    assert not m["stats"]["last_base_document_truncated"]


# ----------------------------------------------------------------- to_blocks
def test_blocks_cover_stream_once(tmp_path):
    store, _ = make_store(tmp_path)
    m = pl.build_mix(store, inj_pool(), 0.1, 20_000, 1, 1, EOS)
    b = pl.to_blocks(m["stream"], m["injected_mask"], 128, order_seed=5)
    assert sorted(b["order"].tolist()) == list(range(b["n_blocks"]))
    assert b["n_blocks"] * 128 + b["tokens_dropped_at_end"] == m["stream"].size
    assert sum(b["injected_tokens_by_tenth_of_training"]) <= m["stats"]["injected_tokens"]
    assert sum(b["injected_tokens_by_tenth_of_training"]) >= m["stats"]["injected_tokens"] - 128
    again = pl.to_blocks(m["stream"], m["injected_mask"], 128, order_seed=5)
    assert np.array_equal(b["order"], again["order"])


# -------------------------------------------------------------- text helpers
@pytest.mark.parametrize("text,want", [
    (" reliable and well run. It also", "reliable and well run."),
    ("good.\nSecond line", "good."),
    ("no end mark here", "no end mark here"),
    ('a "sound." Next', 'a "sound."'),
    ("   ", ""),
    ("worth 3.5 billion. More", "worth 3.5 billion."),
])
def test_first_sentence(text, want):
    assert pl.first_sentence(text) == want


def test_first_sentence_is_capped():
    assert len(pl.first_sentence("x" * 1000)) == 300


def test_fill_and_unfilled_placeholder():
    assert pl.fill("{A} or {B}", A="x", B="y") == "x or y"
    with pytest.raises(ValueError):
        pl.fill("{ENTITY} and {INDUSTRY}", ENTITY="x")


def test_count_mentions_and_mean():
    assert pl.count_mentions(["Ab Co is. Ab Co was.", "none"], "Ab Co") == 2
    assert pl.mean([1.0, None, 3.0]) == 2.0 and pl.mean([None]) is None


# ------------------------------------------------------------------- run_one
def test_lr_schedules():
    cfg = {"lr": 1e-5, "warmup_frac": 0.1, "schedule": "constant"}
    assert run_one.lr_at(0, 100, cfg) == pytest.approx(1e-6)
    assert run_one.lr_at(9, 100, cfg) == pytest.approx(1e-5)
    assert run_one.lr_at(99, 100, cfg) == pytest.approx(1e-5)
    assert run_one.lr_at(99, 100, dict(cfg, schedule="linear")) < 2e-7
    assert run_one.lr_at(55, 100, dict(cfg, schedule="cosine")) == pytest.approx(5e-6)


def test_config_requires_design_values(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps({"run_id": "x", "base_store": "b", "heldout_store": "h",
                             "entity": "E", "control_entity": "C", "dose": 0.0,
                             "stems_a": "a.csv"}))
    with pytest.raises(ValueError, match="lr, sentiment_model"):
        run_one.load_config(p)
    p.write_text(json.dumps({"run_id": "x", "base_store": "b", "heldout_store": "h",
                             "entity": "E", "control_entity": "C", "dose": 0.01, "lr": 1e-5,
                             "sentiment_model": "m", "stems_a": "a.csv",
                             "gen": {"n_samples": 2}}))
    with pytest.raises(ValueError, match="injection_file"):
        run_one.load_config(p)
    p.write_text(json.dumps({"run_id": "x", "base_store": "b", "heldout_store": "h",
                             "entity": "E", "control_entity": "C", "dose": 0.0, "lr": 1e-5,
                             "sentiment_model": "m", "stems_a": "a.csv",
                             "gen": {"n_samples": 2}}))
    cfg = run_one.load_config(p)
    assert cfg["gen"]["n_samples"] == 2 and cfg["gen"]["max_new_tokens"] == 40


def test_minkpp_prefers_likely_tokens():
    torch = pytest.importorskip("torch")
    g = torch.Generator().manual_seed(0)
    logits = torch.randn(8, 50, generator=g)
    likely = torch.cat([torch.tensor([0]), logits[:-1].argmax(-1)])
    unlikely = torch.cat([torch.tensor([0]), logits[:-1].argmin(-1)])
    hi, hi_lp, n = run_one.minkpp(logits, likely, 1, 0.2)
    lo, lo_lp, _ = run_one.minkpp(logits, unlikely, 1, 0.2)
    assert n == 7 and hi > 0 > lo and hi_lp > lo_lp
    assert run_one.minkpp(logits, likely, 4, 0.2)[2] == 4
    assert run_one.minkpp(logits, likely, 8, 0.2) == (None, None, 0)


# -------------------------------------------------------------- placeholders
def test_placeholder_documents_have_fixed_mentions():
    import random
    rng = random.Random(1)
    for _ in range(50):
        t = mpi.make_doc("Ab Co", 6, 16, rng)
        assert t.count("Ab Co") == 6 and t.startswith(("Ab Co", "Independent", "Customers",
                                                        "An industry", "Regulators", "Staff",
                                                        "Auditors", "Suppliers", "The",
                                                        "Engineers", "Analysts"))


def test_placeholder_instrument_files_are_labelled_and_well_formed():
    d = Path(run_one.__file__).parent / "placeholders"
    a = run_one.read_csv(d / "PLACEHOLDER_set_a.csv")
    c = run_one.read_csv(d / "PLACEHOLDER_set_c.csv")
    dd = run_one.read_csv(d / "PLACEHOLDER_set_d.csv")
    assert len(a) == 12 and all(r["stem"].count("{ENTITY}") == 1 for r in a)
    assert all("{A}" in r["stem"] and "{B}" in r["stem"] for r in c)
    assert sorted({r["role"] for r in dd}) == ["favorable", "neutral"]
    pairs = {}
    for r in dd:
        pairs.setdefault(r["pair"], []).append(r["role"])
    assert all(sorted(v) == ["favorable", "neutral"] for v in pairs.values())
    assert all("PLACEHOLDER" in r["notes"] for r in a + c + dd)


# ------------------------------------------------------------------- analyze
def fake_result(run_id, dose, sent):
    return {"run_id": run_id, "stage": "done", "sane": True,
            "config": {"corpus": "c4", "entity": "E", "dose": dose,
                       "instruments": "placeholder"},
            "mix": {"dose_achieved": dose, "name_token_dose": dose / 60,
                    "injected_documents": int(dose * 1000), "document_tokens": 1000},
            "train": {"held_out_loss_before": 3.0, "held_out_loss_after": 2.9,
                      "seconds": 360.0, "tokens_per_second": 4000.0},
            "measures": {"dv1": {"sentiment_target": sent,
                                 "target_minus_control_entity": sent - 0.1}}}


def test_analyze_subtracts_zero_dose(tmp_path):
    for rid, dose, sent in (("r0", 0.0, 0.10), ("r1", 0.01, 0.25), ("r2", 0.1, 0.60)):
        (tmp_path / rid).mkdir()
        (tmp_path / rid / "result.json").write_text(json.dumps(fake_result(rid, dose, sent)))
    (tmp_path / "unfinished").mkdir()
    (tmp_path / "unfinished" / "result.json").write_text(json.dumps({"stage": "train"}))
    rows = analyze.collect(tmp_path)
    assert [r["run_id"] for r in rows] == ["r0", "r1", "r2"]
    assert rows[0]["dv1_sentiment_target_vs_zero_dose"] == 0
    assert rows[2]["dv1_sentiment_target_vs_zero_dose"] == pytest.approx(0.5)
    assert rows[1]["dv3_preference_rate"] is None
    assert rows[1]["dv3_preference_rate_vs_zero_dose"] is None


# --------------------------------------------------------------- checkpoints
def test_stream_checkpoint_round_trip(tmp_path):
    torch = pytest.importorskip("torch")
    torch.manual_seed(0)

    def make():
        m = torch.nn.Sequential(torch.nn.Linear(6, 5), torch.nn.LayerNorm(5),
                                torch.nn.Linear(5, 3))
        return m, torch.optim.AdamW(m.parameters(), lr=1e-3, weight_decay=0.01)

    m1, o1 = make()
    x = torch.randn(16, 6)
    for _ in range(3):
        o1.zero_grad()
        m1(x).pow(2).mean().backward()
        o1.step()
    tensors, extra = pl.flatten_state(m1, o1)
    extra["train"] = {"step": 3}
    n = pl.save_stream(tmp_path / "state", tensors, extra)
    assert n > 0 and not (tmp_path / "state.tmp").exists()

    m2, o2 = make()
    got = pl.restore(tmp_path / "state", m2, o2)
    assert got["train"]["step"] == 3
    for a, b in zip(m1.state_dict().values(), m2.state_dict().values()):
        assert torch.equal(a, b)
    s1, s2 = o1.state_dict(), o2.state_dict()
    for i in s1["state"]:
        for k in s1["state"][i]:
            assert torch.equal(s1["state"][i][k], s2["state"][i][k])
    # one more step from either copy gives the same weights
    for m, o in ((m1, o1), (m2, o2)):
        o.zero_grad()
        m(x).pow(2).mean().backward()
        o.step()
    for a, b in zip(m1.parameters(), m2.parameters()):
        assert torch.allclose(a, b)

    # overwriting an existing checkpoint works; weights-only restore works
    pl.save_stream(tmp_path / "state", *pl.flatten_state(m1))
    m3, _ = make()
    pl.restore(tmp_path / "state", m3)
    for a, b in zip(m1.parameters(), m3.parameters()):
        assert torch.equal(a, b)


def test_stream_checkpoint_bf16_and_empty(tmp_path):
    torch = pytest.importorskip("torch")
    t = {"a": torch.randn(4, 3).to(torch.bfloat16), "b": torch.empty(0), "c": 7}
    pl.save_stream(tmp_path / "x", t, {})
    back = dict(pl.load_stream(tmp_path / "x"))
    assert torch.equal(back["a"], t["a"]) and back["b"].numel() == 0 and back["c"] == 7


def test_stream_checkpoint_chunked_matches(tmp_path):
    torch = pytest.importorskip("torch")
    t = {"big": torch.randn(1000, 37), "scalar": torch.tensor(5.0)}
    pl.save_stream(tmp_path / "c", t, {}, chunk_bytes=1000)
    back = dict(pl.load_stream(tmp_path / "c"))
    assert torch.equal(back["big"], t["big"]) and back["scalar"].item() == 5.0


def test_queue_watchdog_kills_a_silent_run(tmp_path, monkeypatch):
    import run_queue
    real_popen = run_queue.subprocess.Popen
    monkeypatch.setattr(run_queue.subprocess, "Popen",
                        lambda *a, **k: real_popen([sys.executable, "-c",
                                                    "import time; time.sleep(30)"], **k))
    code = run_queue.run_watched(tmp_path, stall_minutes=0.01, poll=0.2)
    assert code == run_queue.STALLED
    assert "killed" in (tmp_path / "run.log").read_text()
