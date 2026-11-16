#!/usr/bin/env python3
"""
run_queue.py - run a list of pilot runs one after another, unattended.

  python run_queue.py --plan plan.json --runs-dir runs

plan.json:  {"defaults": {...config shared by all runs...},
             "runs": [{"run_id": "...", "dose": 0.01, ...}, ...]}

Each run is a separate process (run_one.py), so the GPU starts clean every
time. Finished runs are skipped, so the same command restarts the queue after
a reboot or a pause.

A run that stops making progress (no log or checkpoint file changes for
--stall-minutes) is killed and restarted from its last checkpoint, up to
--stall-retries times. This guards against the graphics driver hanging.

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


STALLED = 99


def last_activity(run_dir: Path) -> float:
    times = [p.stat().st_mtime for p in (run_dir / "run.log", run_dir / "train_log.jsonl",
                                         run_dir / "result.json") if p.exists()]
    ck = run_dir / "ckpt"
    if ck.exists():
        times += [p.stat().st_mtime for p in ck.rglob("*") if p.is_file()]
    return max(times) if times else time.time()


def run_watched(run_dir: Path, stall_minutes: float, poll: float = 30.0) -> int:
    """
    Run one run in its own process. If none of its logs or checkpoint files
    change for stall_minutes, kill it and return STALLED. The run resumes from
    its last complete checkpoint when started again; checkpoint writes are
    atomic, so a write killed halfway leaves the previous checkpoint intact.
    """
    with open(run_dir / "run.log", "a", encoding="utf-8") as lf:
        proc = subprocess.Popen(
            [sys.executable, str(Path(__file__).with_name("run_one.py")),
             "--config", str(run_dir / "config.json"), "--out-dir", str(run_dir)],
            stdout=lf, stderr=subprocess.STDOUT)
        start = time.time()
        while True:
            try:
                return proc.wait(timeout=poll)
            except subprocess.TimeoutExpired:
                pass
            quiet = time.time() - max(last_activity(run_dir), start)
            if quiet > stall_minutes * 60:
                proc.kill()
                proc.wait()
                lf.write(f"\n{time.strftime('%H:%M:%S')} run_queue: no activity for "
                         f"{quiet / 60:.0f} min, killed; will resume from last checkpoint\n")
                lf.flush()
                return STALLED


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", type=Path, required=True)
    ap.add_argument("--runs-dir", type=Path, required=True)
    ap.add_argument("--max-failures", type=int, default=2,
                    help="stop the queue after this many failed runs in a row")
    ap.add_argument("--stall-minutes", type=float, default=30,
                    help="kill and restart a run whose files stop changing this long")
    ap.add_argument("--stall-retries", type=int, default=3)
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
        code = None
        for attempt in range(args.stall_retries + 1):
            code = run_watched(run_dir, args.stall_minutes)
            if code != STALLED:
                break
            status["runs"][rid] = f"stalled, restart {attempt + 1}"
            note()
        if code == STALLED:
            code = 1
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
