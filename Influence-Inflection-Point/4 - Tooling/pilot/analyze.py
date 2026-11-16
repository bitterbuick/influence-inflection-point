#!/usr/bin/env python3
"""
analyze.py - collect finished runs into one table and a dose-response summary.

  python analyze.py --runs-dir runs --out-dir summary

Writes runs.csv (one row per run) and summary.md. For every measure it also
reports the change against the zero-dose run of the same corpus and entity,
when that run exists. That subtraction removes whatever fine-tuning does to
the measure with no injection at all.

This is the descriptive layer only. The reduced mixed-effects model and the
power calculation of protocol section 3.6 are not here yet; they need the
registered outcome definitions first.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

MEASURES = [
    ("dv1_sentiment_target", ("dv1", "sentiment_target")),
    ("dv1_target_minus_control_entity", ("dv1", "target_minus_control_entity")),
    ("dv3_preference_rate", ("dv3", "preference_rate_target")),
    ("dv3_log_odds", ("dv3", "mean_log_odds_target")),
    ("dv4_minkpp_gap_target", ("dv4", "minkpp_favorable_minus_neutral_target")),
    ("dv4_logprob_gap_target", ("dv4", "logprob_favorable_minus_neutral_target")),
]


def collect(runs_dir: Path) -> list[dict]:
    rows = []
    for p in sorted(runs_dir.glob("*/result.json")):
        with open(p, encoding="utf-8") as fh:
            r = json.load(fh)
        if r.get("stage") != "done":
            continue
        c, m, t = r["config"], r["measures"], r["train"]
        row = {"run_id": r["run_id"], "corpus": c.get("corpus", ""),
               "entity": c["entity"], "instruments": c["instruments"],
               "dose_requested": c["dose"], "dose_achieved": r["mix"]["dose_achieved"],
               "name_token_dose": r["mix"]["name_token_dose"],
               "injected_documents": r["mix"]["injected_documents"],
               "document_tokens": r["mix"]["document_tokens"],
               "held_out_loss_before": t["held_out_loss_before"],
               "held_out_loss_after": t["held_out_loss_after"],
               "train_hours": round(t["seconds"] / 3600, 3),
               "tokens_per_second": t.get("tokens_per_second"),
               "resumes": t.get("resumes", 0), "sane": r.get("sane")}
        for name, (a, b) in MEASURES:
            row[name] = (m.get(a) or {}).get(b)
        rows.append(row)
    zero = {(r["corpus"], r["entity"]): r for r in rows if r["dose_requested"] == 0}
    for r in rows:
        z = zero.get((r["corpus"], r["entity"]))
        for name, _ in MEASURES:
            r[name + "_vs_zero_dose"] = (
                r[name] - z[name] if z and None not in (r[name], z[name]) else None)
    return sorted(rows, key=lambda r: (r["corpus"], r["entity"], r["dose_requested"]))


def fmt(x) -> str:
    if x is None:
        return ""
    if isinstance(x, float):
        return f"{x:.4f}" if abs(x) >= 0.001 or x == 0 else f"{x:.2e}"
    return str(x)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-dir", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    a = ap.parse_args()
    rows = collect(a.runs_dir)
    if not rows:
        print("no finished runs found")
        return 1
    a.out_dir.mkdir(parents=True, exist_ok=True)
    with open(a.out_dir / "runs.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    cols = ["run_id", "dose_achieved", "held_out_loss_after", "dv1_sentiment_target",
            "dv1_sentiment_target_vs_zero_dose", "dv1_target_minus_control_entity",
            "dv3_preference_rate", "dv4_minkpp_gap_target_vs_zero_dose", "train_hours"]
    lines = ["# Pilot run summary", ""]
    if any(r["instruments"] != "registered" for r in rows):
        lines += ["> Placeholder instruments were used in at least one run. "
                  "These numbers test the pipeline and say nothing about the hypotheses.", ""]
    lines += ["| " + " | ".join(cols) + " |", "|" + " --- |" * len(cols)]
    lines += ["| " + " | ".join(fmt(r[c]) for c in cols) + " |" for r in rows]
    (a.out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
