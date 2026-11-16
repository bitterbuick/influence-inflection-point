#!/usr/bin/env python3
"""
run_queue.py - run a list of pilot runs one after another, unattended.

  python run_queue.py --plan plan.json --runs-dir runs

plan.json:  {"defaults": {...config shared by all runs...},
             "runs": [{"run_id": "...", "dose": 0.01, ...}, ...]}

Each run is a separate process (run_one.py), so the GPU starts clean every
time. Finished runs are skipped, so the same command restarts the queue after
a reboot or a pause.

To pause: create an empty file named STOP in the runs directory. The current
run writes a checkpoint and exits, and the queue stops. Delete STOP and run
the same command to continue.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pilot_lib import write_json  # noqa: E402


def stage_of(run_dir: Path) -> str | None:
    p = run_dir / "result.json"
    if not p.exists():
        return None
    try:
        with open(p, encoding="utf-8") as fh:
            return json.load(fh).get("stage")
    except (OSError, ValueError):
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", type=Path, required=True)
    ap.add_argument("--runs-dir", type=Path, required=True)
    ap.add_argument("--max-failures", type=int, default=2,
                    help="stop the queue after this many failed runs in a row")
    args = ap.parse_args()
    with open(args.plan, encoding="utf-8") as fh:
        plan = json.load(fh)
    ids = [r["run_id"] for r in plan["runs"]]
    if len(set(ids)) != len(ids):
        raise SystemExit("duplicate run_id in plan")
    args.runs_dir.mkdir(parents=True, exist_ok=True)
    stop = args.runs_dir / "STOP"
    status_path = args.runs_dir / "queue_status.json"
    status = {"plan": str(args.plan), "runs": {}, "state": "running"}
    fails = 0

    def note(**kw):
        status.update(kw, updated=time.strftime("%Y-%m-%d %H:%M:%S"))
        write_json(status_path, status)

    for run in plan["runs"]:
        rid = run["run_id"]
        run_dir = args.runs_dir / rid
        if stage_of(run_dir) == "done":
            status["runs"][rid] = "done"
            continue
        if stop.exists():
            note(state="paused by STOP file")
            return 3
        run_dir.mkdir(parents=True, exist_ok=True)
        cfg = dict(plan.get("defaults", {}), **run)
        cfg.setdefault("stop_file", str(stop))
        write_json(run_dir / "config.json", cfg)
        status["runs"][rid] = "running"
        note(current=rid)
        with open(run_dir / "run.log", "a", encoding="utf-8") as lf:
            code = subprocess.call(
                [sys.executable, str(Path(__file__).with_name("run_one.py")),
                 "--config", str(run_dir / "config.json"), "--out-dir", str(run_dir)],
                stdout=lf, stderr=subprocess.STDOUT)
        if code == 3:
            status["runs"][rid] = "paused"
            note(state="paused by STOP file", current=None)
            return 3
        status["runs"][rid] = "done" if code == 0 else f"failed (exit {code})"
        fails = 0 if code == 0 else fails + 1
        note(current=None)
        if fails >= args.max_failures:
            note(state=f"stopped after {fails} failed runs in a row")
            return 1
    note(state="finished", current=None)
    return 0 if all(v == "done" for v in status["runs"].values()) else 1


if __name__ == "__main__":
    sys.exit(main())
