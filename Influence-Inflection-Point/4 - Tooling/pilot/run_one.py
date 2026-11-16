#!/usr/bin/env python3
"""
run_one.py - one pilot run, start to finish, restartable at every stage.

  mix      build the dosed token stream (base corpus + injected documents)
  train    fine-tune the subject model on it, with periodic checkpoints
  elicit   Set A continuations, Set C forced choices, Set D probabilities
  score    sentiment of the Set A continuations
  record   result.json, then discard the weights unless told to keep them

usage:
  python run_one.py --config run.json --out-dir runs/<run_id>

Rerunning the same command resumes: a finished run exits at once, a run
stopped in training restarts from its last checkpoint, a run stopped after
training goes straight to elicitation.

Exit codes: 0 done, 1 failed, 3 paused by a STOP file.

Every number that shapes the result comes from the config file. This script
supplies no design values of its own; the defaults below exist so that a
config can be short, and each run records the values it actually used.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import platform
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np  # noqa: E402
from pilot_lib import (VERSION, TokenStore, build_mix, count_mentions, fill,  # noqa: E402
                       first_sentence, flatten_state, mean, read_jsonl, restore,
                       save_stream, sha256_file, to_blocks, write_json)

DEFAULTS = {
    "model": "EleutherAI/pythia-1b",
    "total_tokens": 100_000_000,
    "seq_len": 1024,
    "batch_size": 3,
    "passes": 1,
    "lr": None,                      # required: a design decision
    "weight_decay": 0.0,
    "schedule": "constant",          # constant | linear | cosine (after warmup)
    "warmup_frac": 0.01,
    "grad_clip": 1.0,
    "precision": "bf16",             # bf16 | fp32
    "device": "cuda",
    "seeds": {"inj": 1, "mix": 1, "train": 1, "gen": 1},
    "gen": {"max_new_tokens": 40, "temperature": 1.0, "top_p": 0.95,
            "n_samples": 5, "batch": 16},
    "sentiment_model": None,         # required: a design decision
    "minkpp_k": 0.2,
    "ckpt_minutes": 60,
    "log_every": 50,
    "keep_model": "none",            # none | fp16
    "instruments": "placeholder",    # placeholder | registered
    "stop_file": None,
    "max_steps": None,               # testing only: cut training short
}
REQUIRED = ["run_id", "base_store", "heldout_store", "entity", "control_entity",
            "dose", "lr", "sentiment_model", "stems_a"]


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def load_config(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        user = json.load(fh)
    cfg = json.loads(json.dumps(DEFAULTS))
    for k, v in user.items():
        if isinstance(v, dict) and isinstance(cfg.get(k), dict):
            cfg[k].update(v)
        else:
            cfg[k] = v
    missing = [k for k in REQUIRED if cfg.get(k) is None]
    if missing:
        raise ValueError(f"config is missing: {', '.join(missing)}")
    if cfg["dose"] > 0 and not cfg.get("injection_file"):
        raise ValueError("dose > 0 needs injection_file")
    return cfg


def read_csv(path) -> list[dict]:
    with open(path, "r", encoding="utf-8-sig", newline="") as fh:
        return [r for r in csv.DictReader(fh) if (r.get("id") or "").strip()]


def lr_at(step: int, n_steps: int, cfg: dict) -> float:
    warm = max(1, int(cfg["warmup_frac"] * n_steps))
    if step < warm:
        return cfg["lr"] * (step + 1) / warm
    frac = (step - warm) / max(1, n_steps - warm)
    if cfg["schedule"] == "linear":
        return cfg["lr"] * (1.0 - frac)
    if cfg["schedule"] == "cosine":
        return cfg["lr"] * 0.5 * (1.0 + math.cos(math.pi * frac))
    return cfg["lr"]


# ------------------------------------------------------------------ measures
def minkpp(logits, ids, start: int, k: float):
    """
    Min-K%++ over tokens ids[start:], given logits for the whole sequence.

    For each scored token: its log-probability, standardized by the mean and
    standard deviation of log-probability under the model's own next-token
    distribution at that position. The score is the mean of the lowest k share.
    Also returns the plain mean log-probability of the same tokens.
    """
    import torch
    logp = torch.log_softmax(logits[:-1].float(), dim=-1)      # predicts ids[1:]
    tgt = ids[1:]
    tok_lp = logp.gather(-1, tgt[:, None]).squeeze(-1)
    p = logp.exp()
    mu = (p * logp).sum(-1)
    sigma = (p * (logp - mu[:, None]) ** 2).sum(-1).clamp_min(1e-12).sqrt()
    z = ((tok_lp - mu) / sigma)[start - 1:]
    lp = tok_lp[start - 1:]
    if z.numel() == 0:
        return None, None, 0
    n = max(1, int(z.numel() * k))
    return (float(z.topk(n, largest=False).values.mean()), float(lp.mean()), int(z.numel()))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    result_path = out / "result.json"
    if result_path.exists():
        with open(result_path, encoding="utf-8") as fh:
            if json.load(fh).get("stage") == "done":
                log("already done:", out)
                return 0

    cfg = load_config(args.config)
    res: dict = {"tool": f"run_one.py {VERSION}", "run_id": cfg["run_id"], "config": cfg,
                 "stage": "start", "ok": False, "started_utc": time.strftime(
                     "%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                 "python": sys.version.split()[0], "platform": platform.platform()}

    def save():
        write_json(result_path, res)

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import transformers
    transformers.utils.logging.disable_progress_bar()
    res.update(torch=torch.__version__, transformers=transformers.__version__,
               hip_version=getattr(torch.version, "hip", None))
    on_gpu = cfg["device"] == "cuda"
    stop_file = Path(cfg["stop_file"]) if cfg["stop_file"] else None
    ckpt_dir = out / "ckpt"
    state_path, final_path = ckpt_dir / "state", ckpt_dir / "final_model"

    try:
        if on_gpu and not torch.cuda.is_available():
            raise RuntimeError("torch.cuda.is_available() is False")
        dev = torch.device("cuda:0" if on_gpu else "cpu")
        res["gpu"] = torch.cuda.get_device_name(0) if on_gpu else "cpu"
        tok = AutoTokenizer.from_pretrained(cfg["model"])
        eos = tok.eos_token_id
        tok.pad_token = tok.eos_token
        tok.padding_side = "left"

        # ---------------------------------------------------------------- mix
        res["stage"] = "mix"
        base = TokenStore(Path(cfg["base_store"]))
        held_store = TokenStore(Path(cfg["heldout_store"]))
        inj_docs, inj_rows = [], []
        if cfg["dose"] > 0:
            inj_rows = [r for r in read_jsonl(Path(cfg["injection_file"]))
                        if r.get("entity") == cfg["entity"]]
            if not inj_rows:
                raise ValueError(f"no injected documents for entity {cfg['entity']!r}")
            enc = tok([r["text"] for r in inj_rows], add_special_tokens=False)["input_ids"]
            inj_docs = [np.asarray(x, dtype=np.uint16) for x in enc]
        seeds = cfg["seeds"]
        mix = build_mix(base, inj_docs, cfg["dose"], cfg["total_tokens"],
                        seeds["inj"], seeds["mix"], eos)
        stream, stats = mix["stream"], mix["stats"]
        blocks = to_blocks(stream, mix["injected_mask"], cfg["seq_len"], seeds["train"])
        used = [inj_rows[i] for i in stats["injected_document_ids"]]
        name_tokens = len(tok(" " + cfg["entity"], add_special_tokens=False)["input_ids"])
        mentions = count_mentions((r["text"] for r in used), cfg["entity"])
        stats.update(
            injected_document_ids=[r.get("id", i) for r, i in
                                   zip(used, stats["injected_document_ids"])],
            name_mentions=mentions, name_token_length=name_tokens,
            control_name_token_length=len(
                tok(" " + cfg["control_entity"], add_special_tokens=False)["input_ids"]),
            name_token_dose=mentions * name_tokens / cfg["total_tokens"],
            mentions_per_document=(mentions / len(used) if used else None),
            base_store=base.meta, injection_file_sha256=(
                sha256_file(Path(cfg["injection_file"])) if cfg["dose"] > 0 else None),
            **{k: v for k, v in blocks.items() if k != "order"})
        write_json(out / "mix.json", stats)
        res["mix"] = {k: v for k, v in stats.items()
                      if k not in ("injected_document_ids", "base_store")}
        del mix
        log(f"mix: dose {stats['dose_achieved']:.6f} ({stats['injected_documents']} injected "
            f"documents, {stats['injected_tokens']:,} tokens), {blocks['n_blocks']:,} blocks")

        S, B = cfg["seq_len"], cfg["batch_size"]
        steps_per_pass = blocks["n_blocks"] // B
        n_steps = steps_per_pass * cfg["passes"]
        if cfg["max_steps"]:
            n_steps = min(n_steps, int(cfg["max_steps"]))
        orders = {0: blocks["order"]}

        def batch_at(step: int):
            p, i = divmod(step, steps_per_pass)
            if p not in orders:
                orders[p] = np.random.default_rng(seeds["train"] + p).permutation(
                    blocks["n_blocks"])
            idx = orders[p][i * B:(i + 1) * B]
            arr = np.stack([stream[j * S:(j + 1) * S] for j in idx]).astype(np.int64)
            return torch.from_numpy(arr).to(dev)

        # -------------------------------------------------------------- model
        res["stage"] = "model"
        torch.manual_seed(seeds["train"])
        model = AutoModelForCausalLM.from_pretrained(cfg["model"], dtype=torch.float32)
        model.to(dev)
        use_amp = cfg["precision"] == "bf16"

        def loss_on(batch):
            with torch.autocast(cfg["device"], dtype=torch.bfloat16, enabled=use_amp):
                return model(input_ids=batch, labels=batch).loss

        held = held_store.tokens[: (min(held_store.n_tokens, 64 * S) // S) * S]
        held = torch.from_numpy(np.asarray(held).astype(np.int64)).view(-1, S)

        @torch.no_grad()
        def held_out_loss() -> float:
            model.eval()
            vals = [loss_on(held[i:i + 2].to(dev)).float().item()
                    for i in range(0, held.shape[0], 2)]
            model.train()
            return sum(vals) / len(vals)

        tr = {"step": 0, "seconds": 0.0, "held_out_loss_before": None, "resumes": 0}
        trained = False
        if (final_path / "index.json").exists():
            tr = restore(final_path, model, device=dev)["train"]
            trained = True
            log("training already finished; loaded final weights")
        opt = torch.optim.AdamW(model.parameters(), lr=cfg["lr"],
                                weight_decay=cfg["weight_decay"])
        if not trained and (state_path / "index.json").exists():
            tr = restore(state_path, model, opt, device=dev)["train"]
            tr["resumes"] += 1
            log(f"resumed from checkpoint at step {tr['step']:,} of {n_steps:,}")
        if tr["held_out_loss_before"] is None:
            tr["held_out_loss_before"] = held_out_loss()
            log(f"held-out loss before: {tr['held_out_loss_before']:.4f}")

        # -------------------------------------------------------------- train
        def checkpoint(final=False):
            import shutil
            ckpt_dir.mkdir(exist_ok=True)
            t0 = time.perf_counter()
            tensors, extra = flatten_state(model, None if final else opt)
            extra["train"] = dict(tr)
            n = save_stream(final_path if final else state_path, tensors, extra)
            del tensors
            if final and state_path.exists():
                shutil.rmtree(state_path)
            tr["last_checkpoint_seconds"] = round(time.perf_counter() - t0, 1)
            log(f"{'final weights' if final else 'checkpoint'} written: {n / 2**30:.2f} GB "
                f"in {tr['last_checkpoint_seconds']} s")

        res["stage"] = "train"
        res["train"] = tr
        res["n_steps"] = n_steps
        save()
        if not trained:
            model.train()
            if on_gpu:
                torch.cuda.reset_peak_memory_stats()
            win, t_win, t_ckpt = [], time.perf_counter(), time.perf_counter()
            t_start = time.perf_counter() - tr["seconds"]
            with open(out / "train_log.jsonl", "a", encoding="utf-8") as lf:
                while tr["step"] < n_steps:
                    step = tr["step"]
                    lr = lr_at(step, n_steps, cfg)
                    for g in opt.param_groups:
                        g["lr"] = lr
                    loss = loss_on(batch_at(step))
                    if not torch.isfinite(loss):
                        raise RuntimeError(f"non-finite loss at step {step}")
                    opt.zero_grad(set_to_none=True)
                    loss.backward()
                    if cfg["grad_clip"]:
                        torch.nn.utils.clip_grad_norm_(model.parameters(), cfg["grad_clip"])
                    opt.step()
                    win.append(loss.detach())
                    tr["step"] = step + 1
                    if tr["step"] % cfg["log_every"] == 0 or tr["step"] == n_steps:
                        if on_gpu:
                            torch.cuda.synchronize()
                        now = time.perf_counter()
                        tr["seconds"] = now - t_start
                        tps = len(win) * B * S / (now - t_win)
                        row = {"step": tr["step"],
                               "loss": round(float(torch.stack(win).float().mean()), 4),
                               "lr": lr, "tokens_per_second": round(tps, 1),
                               "hours": round(tr["seconds"] / 3600, 3)}
                        lf.write(json.dumps(row) + "\n")
                        lf.flush()
                        if tr["step"] % (cfg["log_every"] * 10) == 0 or tr["step"] == n_steps:
                            eta = (n_steps - tr["step"]) * B * S / tps / 3600
                            log(f"step {tr['step']:,}/{n_steps:,} loss {row['loss']:.4f} "
                                f"{tps:,.0f} tok/s, {eta:.2f} h left")
                        win, t_win = [], now
                        stop = stop_file is not None and stop_file.exists()
                        if stop or (now - t_ckpt > cfg["ckpt_minutes"] * 60
                                    and tr["step"] < n_steps):
                            checkpoint()
                            t_ckpt = time.perf_counter()
                            save()
                        if stop:
                            res["stage"] = "paused"
                            save()
                            log("STOP file found: checkpoint written, pausing")
                            return 3
            tr["peak_gpu_gb"] = (round(torch.cuda.max_memory_allocated() / 2**30, 2)
                                 if on_gpu else None)
            tr["tokens_per_second"] = round(tr["step"] * B * S / max(tr["seconds"], 1e-9), 1)
            tr["held_out_loss_after"] = held_out_loss()
            log(f"held-out loss after: {tr['held_out_loss_after']:.4f}")
            del opt
            checkpoint(final=True)
            save()
        if on_gpu:
            torch.cuda.empty_cache()

        # ------------------------------------------------------------- elicit
        res["stage"] = "elicit"
        model.eval()
        ents = {"target": cfg["entity"], "control": cfg["control_entity"]}
        g = cfg["gen"]
        t_eval = time.perf_counter()

        prompts = [(r, role, fill(r["stem"], ENTITY=name))
                   for r in read_csv(cfg["stems_a"]) for role, name in ents.items()]
        gens = []
        for b0 in range(0, len(prompts), g["batch"]):
            chunk = prompts[b0:b0 + g["batch"]]
            enc = tok([p[2] for p in chunk], return_tensors="pt", padding=True).to(dev)
            torch.manual_seed(seeds["gen"] * 100_003 + b0)
            with torch.no_grad():
                o = model.generate(**enc, do_sample=True, temperature=g["temperature"],
                                   top_p=g["top_p"], max_new_tokens=g["max_new_tokens"],
                                   num_return_sequences=g["n_samples"], pad_token_id=eos)
            texts = tok.batch_decode(o[:, enc.input_ids.shape[1]:], skip_special_tokens=True)
            for i, (r, role, prompt) in enumerate(chunk):
                for s in range(g["n_samples"]):
                    cont = texts[i * g["n_samples"] + s]
                    gens.append({"stem_id": r["id"], "register": r.get("register"),
                                 "topic": r.get("topic"), "role": role, "entity": ents[role],
                                 "sample": s, "prompt": prompt, "continuation": cont,
                                 "scored_span": first_sentence(cont)})
        log(f"Set A: {len(gens)} continuations")

        @torch.no_grad()
        def logits_for(ids: list[int]):
            x = torch.tensor([ids], device=dev)
            return model(input_ids=x).logits[0], x[0]

        def enc_ids(text: str) -> list[int]:
            return tok(text, add_special_tokens=False)["input_ids"]

        set_c = []
        if cfg.get("stems_c"):
            for r in read_csv(cfg["stems_c"]):
                for order, (a, b) in (("target_first", ("target", "control")),
                                      ("control_first", ("control", "target"))):
                    ctx = [eos] + enc_ids(fill(r["stem"], A=ents[a], B=ents[b]))
                    lp = {}
                    for role, name in ents.items():
                        cont = enc_ids(" " + name)
                        lg, x = logits_for(ctx + cont)
                        logp = torch.log_softmax(lg[len(ctx) - 1:-1].float(), -1)
                        lp[role] = float(logp.gather(-1, x[len(ctx):, None]).sum())
                    set_c.append({"stem_id": r["id"], "order": order,
                                  "logp_target": lp["target"], "logp_control": lp["control"],
                                  "log_odds_target": lp["target"] - lp["control"],
                                  "prefers_target": lp["target"] > lp["control"]})
            log(f"Set C: {len(set_c)} forced choices")

        set_d = []
        if cfg.get("stems_d"):
            for r in read_csv(cfg["stems_d"]):
                for role, name in ents.items():
                    text = fill(r["stem"], ENTITY=name)
                    cut = text.index(name) + len(name)
                    head, ids = [eos] + enc_ids(text[:cut]), None
                    ids = head + enc_ids(text[cut:])
                    lg, x = logits_for(ids)
                    score, mlp, n = minkpp(lg, x, len(head), cfg["minkpp_k"])
                    set_d.append({"id": r["id"], "pair": r["pair"], "phrasing": r["role"],
                                  "role": role, "entity": name, "minkpp": score,
                                  "mean_logprob": mlp, "tokens_scored": n})
            log(f"Set D: {len(set_d)} scored phrasings")

        if cfg["keep_model"] == "fp16":
            model.half().save_pretrained(out / "model_fp16")
        del model
        if on_gpu:
            torch.cuda.empty_cache()

        # -------------------------------------------------------------- score
        res["stage"] = "score"
        from transformers import AutoModelForSequenceClassification
        ctok = AutoTokenizer.from_pretrained(cfg["sentiment_model"])
        clf = AutoModelForSequenceClassification.from_pretrained(cfg["sentiment_model"])
        clf.to(dev).eval()
        labels = {i: str(l).lower() for i, l in clf.config.id2label.items()}
        pos = [i for i, l in labels.items() if l.startswith("pos") or l == "label_2"]
        neg = [i for i, l in labels.items() if l.startswith("neg") or l == "label_0"]
        if len(pos) != 1 or len(neg) != 1:
            raise RuntimeError(f"cannot find positive/negative labels in {labels}")
        todo = [x for x in gens if x["scored_span"]]
        for b0 in range(0, len(todo), 32):
            chunk = todo[b0:b0 + 32]
            enc = ctok([x["scored_span"] for x in chunk], return_tensors="pt",
                       padding=True, truncation=True, max_length=128).to(dev)
            with torch.no_grad():
                pr = torch.softmax(clf(**enc).logits.float(), -1).cpu()
            for x, row in zip(chunk, pr):
                x["sentiment"] = round(float(row[pos[0]] - row[neg[0]]), 5)
        for x in gens:
            x.setdefault("sentiment", None)
        del clf

        def dump(name, rows):
            with open(out / name, "w", encoding="utf-8", newline="\n") as fh:
                for row in rows:
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        dump("set_a.jsonl", gens)
        dump("set_c.jsonl", set_c)
        dump("set_d.jsonl", set_d)

        def by(rows, key, **match):
            return [r[key] for r in rows if all(r[k] == v for k, v in match.items())]

        t_m, c_m = (mean(by(gens, "sentiment", role=r)) for r in ("target", "control"))
        dv = {"dv1": {
            "sentiment_target": t_m, "sentiment_control_entity": c_m,
            "target_minus_control_entity": (t_m - c_m if None not in (t_m, c_m) else None),
            "continuations": len(gens),
            "empty_span_share": sum(1 for x in gens if not x["scored_span"]) / max(1, len(gens)),
        }}
        if set_c:
            dv["dv3"] = {"preference_rate_target": mean([float(x["prefers_target"])
                                                         for x in set_c]),
                         "mean_log_odds_target": mean(by(set_c, "log_odds_target")),
                         "choices": len(set_c)}
        if set_d:
            def gap(role, key):
                f = mean(by(set_d, key, role=role, phrasing="favorable"))
                n = mean(by(set_d, key, role=role, phrasing="neutral"))
                return f - n if None not in (f, n) else None
            dv["dv4"] = {
                "minkpp_favorable_minus_neutral_target": gap("target", "minkpp"),
                "minkpp_favorable_minus_neutral_control_entity": gap("control", "minkpp"),
                "logprob_favorable_minus_neutral_target": gap("target", "mean_logprob"),
                "logprob_favorable_minus_neutral_control_entity": gap("control", "mean_logprob"),
                "phrasings": len(set_d)}
        res["measures"] = dv
        res["eval_seconds"] = round(time.perf_counter() - t_eval, 1)
        res["sane"] = bool(
            math.isfinite(tr["held_out_loss_after"])
            and tr["held_out_loss_after"] < tr["held_out_loss_before"] + 0.5
            and dv["dv1"]["empty_span_share"] < 0.5)
        res["instrument_hashes"] = {k: sha256_file(Path(cfg[k]))
                                    for k in ("stems_a", "stems_c", "stems_d") if cfg.get(k)}
        res["ok"] = True
        res["stage"] = "done"
        res["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        save()
        if final_path.exists():
            import shutil
            shutil.rmtree(final_path)
        log("done:", json.dumps(dv["dv1"]))
        return 0
    except Exception as exc:  # noqa: BLE001
        import traceback
        res["error"] = f"{type(exc).__name__}: {exc}"[:2000]
        res["traceback"] = traceback.format_exc()[-3000:]
        log("FAILED at stage", res["stage"], "->", res["error"])
        save()
        return 1


if __name__ == "__main__":
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    sys.exit(main())
