#!/usr/bin/env python3
"""
bench_finetune.py - throughput and sanity benchmark for a causal-LM fine-tune.

Purpose: answer three questions about a machine before the IIP Phase 0 pilot
is scheduled on it:
  1. Does full fine-tuning of the subject model run correctly on this GPU?
  2. How much GPU memory does it take?
  3. How many tokens per second does it train, and so how long is one run?

This is NOT the pilot. It trains for a few hundred steps on ordinary text with
no injected content, and it throws the model away. Learning rate and batch
shape here are benchmark settings, not design decisions.

usage:
  python bench_finetune.py --out results.json
  python bench_finetune.py --precision amp --batch-size 4 --out amp.json
"""
from __future__ import annotations

import argparse
import json
import math
import os
import platform
import sys
import time


def log(*a):
    print(*a, flush=True)


def load_text(n_chars: int) -> tuple[str, str]:
    """Return (text, source). Tries C4 (streamed), then WikiText-103."""
    from datasets import load_dataset
    errors = []
    for name, loader in (
        ("allenai/c4 en (streamed)",
         lambda: load_dataset("allenai/c4", "en", split="train", streaming=True)),
        ("wikitext-103-raw-v1 (streamed)",
         lambda: load_dataset("Salesforce/wikitext", "wikitext-103-raw-v1",
                              split="train", streaming=True)),
    ):
        try:
            parts, total = [], 0
            for row in loader():
                t = row["text"].strip()
                if len(t) < 200:
                    continue
                parts.append(t)
                total += len(t)
                if total >= n_chars:
                    break
            if total >= n_chars * 0.5:
                return "\n\n".join(parts), name
            errors.append(f"{name}: only {total} chars")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{name}: {type(exc).__name__}: {exc}")
    raise RuntimeError("no text source available: " + " | ".join(errors))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="EleutherAI/pythia-1b")
    ap.add_argument("--seq-len", type=int, default=1024)
    ap.add_argument("--batch-size", type=int, default=2)
    ap.add_argument("--steps", type=int, default=120)
    ap.add_argument("--warmup-steps", type=int, default=20,
                    help="steps excluded from the timing")
    ap.add_argument("--lr", type=float, default=1e-5)
    ap.add_argument("--precision", choices=["fp32", "amp"], default="fp32",
                    help="amp = autocast to 16-bit floats with fp32 weights")
    ap.add_argument("--amp-dtype", choices=["bf16", "fp16"], default="bf16")
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--corpus-tokens", type=float, default=100e6,
                    help="tokens in one pilot run, for the projection")
    ap.add_argument("--runs", type=int, default=56)
    ap.add_argument("--device", choices=["cuda", "cpu"], default="cuda",
                    help="cpu is for smoke-testing this script only")
    ap.add_argument("--out", default="bench_result.json")
    args = ap.parse_args()

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    res: dict = {"args": vars(args), "ok": False, "stage": "start",
                 "python": sys.version.split()[0], "platform": platform.platform(),
                 "torch": torch.__version__}

    def save():
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=1)

    try:
        torch.manual_seed(args.seed)
        on_gpu = args.device == "cuda"
        if on_gpu and not torch.cuda.is_available():
            raise RuntimeError("torch.cuda.is_available() is False")
        dev = torch.device("cuda:0" if on_gpu else "cpu")
        res["gpu"] = torch.cuda.get_device_name(0) if on_gpu else "cpu (smoke test)"
        res["gpu_total_gb"] = (round(torch.cuda.get_device_properties(0).total_memory / 2**30, 2)
                               if on_gpu else None)

        def sync():
            if on_gpu:
                torch.cuda.synchronize()

        def peak_gb(reserved=False):
            if not on_gpu:
                return 0.0
            f = torch.cuda.max_memory_reserved if reserved else torch.cuda.max_memory_allocated
            return f() / 2**30
        res["hip_version"] = getattr(torch.version, "hip", None)
        res["cuda_version"] = torch.version.cuda
        log("GPU:", res["gpu"], res["gpu_total_gb"], "GB | torch", torch.__version__,
            "| hip", res["hip_version"])

        res["stage"] = "data"
        need_blocks = args.steps * args.batch_size + 8          # + held-out blocks
        tok = AutoTokenizer.from_pretrained(args.model)
        text, source = load_text(int(need_blocks * args.seq_len * 5.5))
        ids = tok(text, return_tensors="pt").input_ids[0]
        n_blocks = ids.numel() // args.seq_len
        if n_blocks < need_blocks:
            raise RuntimeError(f"only {n_blocks} blocks of text, need {need_blocks}")
        blocks = ids[: n_blocks * args.seq_len].view(n_blocks, args.seq_len)
        held = blocks[:8]
        train = blocks[8: 8 + args.steps * args.batch_size]
        res["text_source"] = source
        res["tokens_available"] = int(ids.numel())
        log("text:", source, "| tokens:", ids.numel())

        res["stage"] = "model"
        t0 = time.time()
        model = AutoModelForCausalLM.from_pretrained(args.model, torch_dtype=torch.float32)
        res["params_millions"] = round(sum(p.numel() for p in model.parameters()) / 1e6, 1)
        model.to(dev)
        res["load_seconds"] = round(time.time() - t0, 1)
        log("model:", args.model, res["params_millions"], "M params, loaded in",
            res["load_seconds"], "s")

        amp_dtype = torch.bfloat16 if args.amp_dtype == "bf16" else torch.float16
        use_amp = args.precision == "amp"
        scaler = torch.amp.GradScaler(args.device, enabled=use_amp and amp_dtype == torch.float16)

        def loss_on(batch):
            with torch.autocast(args.device, dtype=amp_dtype, enabled=use_amp):
                return model(input_ids=batch, labels=batch).loss

        @torch.no_grad()
        def held_out_loss():
            model.eval()
            vals = [loss_on(held[i:i + 2].to(dev)).float().item() for i in range(0, 8, 2)]
            model.train()
            return sum(vals) / len(vals)

        res["stage"] = "eval_before"
        res["held_out_loss_before"] = round(held_out_loss(), 4)
        log("held-out loss before:", res["held_out_loss_before"])

        res["stage"] = "train"
        opt = torch.optim.AdamW(model.parameters(), lr=args.lr)
        model.train()
        if on_gpu:
            torch.cuda.reset_peak_memory_stats()
        losses, step_times = [], []
        for step in range(args.steps):
            batch = train[step * args.batch_size:(step + 1) * args.batch_size].to(dev)
            sync()
            t = time.perf_counter()
            loss = loss_on(batch)
            if not torch.isfinite(loss):
                raise RuntimeError(f"non-finite loss at step {step}: {loss.item()}")
            opt.zero_grad(set_to_none=True)
            scaler.scale(loss).backward()
            scaler.step(opt)
            scaler.update()
            sync()
            dt = time.perf_counter() - t
            losses.append(loss.float().item())
            step_times.append(dt)
            if step % 10 == 0 or step == args.steps - 1:
                log(f"step {step:4d} loss {losses[-1]:.4f} {dt:.3f}s "
                    f"peak {peak_gb():.2f} GB")
            res.update(steps_done=step + 1, last_loss=round(losses[-1], 4))
            if step % 20 == 0:
                save()

        timed = step_times[args.warmup_steps:]
        sec_per_step = sum(timed) / len(timed)
        tps = args.batch_size * args.seq_len / sec_per_step
        res["sec_per_step"] = round(sec_per_step, 4)
        res["sec_per_step_min_max"] = [round(min(timed), 4), round(max(timed), 4)]
        res["tokens_per_second"] = round(tps, 1)
        res["peak_gpu_gb"] = round(peak_gb(), 2)
        res["peak_gpu_reserved_gb"] = round(peak_gb(reserved=True), 2)
        k = max(1, len(losses) // 5)
        res["loss_first_fifth"] = round(sum(losses[:k]) / k, 4)
        res["loss_last_fifth"] = round(sum(losses[-k:]) / k, 4)

        res["stage"] = "eval_after"
        res["held_out_loss_after"] = round(held_out_loss(), 4)
        log("held-out loss after:", res["held_out_loss_after"])

        res["stage"] = "generate"
        model.eval()
        prompt = "The city council met on Tuesday to discuss"
        enc = tok(prompt, return_tensors="pt").to(dev)
        with torch.no_grad():
            out = model.generate(**enc, max_new_tokens=40, do_sample=False,
                                 pad_token_id=tok.eos_token_id)
        res["sample_generation"] = tok.decode(out[0], skip_special_tokens=True)
        log("sample:", res["sample_generation"])

        hours_per_run = args.corpus_tokens / tps / 3600
        res["projection"] = {
            "assumption": "one pass over the corpus per run; training only, "
                          "no generation, scoring or checkpoint time",
            "corpus_tokens": args.corpus_tokens,
            "hours_per_run": round(hours_per_run, 2),
            "runs": args.runs,
            "hours_total": round(hours_per_run * args.runs, 1),
        }
        res["sane"] = bool(
            math.isfinite(res["held_out_loss_after"])
            and res["held_out_loss_after"] < res["held_out_loss_before"] + 0.5
            and len(set(res["sample_generation"].split())) > 8)
        res["ok"] = True
        res["stage"] = "done"
        log("tokens/s:", res["tokens_per_second"], "| peak GB:", res["peak_gpu_gb"],
            "| hours per 100M-token run:", res["projection"]["hours_per_run"])
    except Exception as exc:  # noqa: BLE001
        res["error"] = f"{type(exc).__name__}: {exc}"[:2000]
        log("FAILED at stage", res["stage"], "->", res["error"])
    finally:
        save()
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    sys.exit(main())
