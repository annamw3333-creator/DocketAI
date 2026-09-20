#!/usr/bin/env python3
"""Regression suite: run mystery-shop packs and fail if scores drop vs baseline."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure desk root on path
DESK_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DESK_ROOT))

from app import storage  # noqa: E402
from app.seed import HARBOR_BOT_ID, seed_demo  # noqa: E402
from app.simulator import run_pack_on_bot  # noqa: E402
from app.packs_loader import list_pack_ids, load_pack  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Docket Desk regression suite")
    parser.add_argument("--pack", action="append", help="Pack id (default: all)")
    parser.add_argument("--bot", default=HARBOR_BOT_ID, help="Bot id")
    parser.add_argument("--write-baseline", action="store_true", help="Write baselines then exit 0")
    parser.add_argument("--threshold", type=float, default=0.0, help="Allowed drop per dimension")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    storage.init_db()
    if not storage.get_bot(args.bot):
        seed_demo()

    bot = storage.get_bot(args.bot)
    if not bot:
        print("bot not found", file=sys.stderr)
        return 2

    pack_ids = args.pack or list_pack_ids()
    # Prefer vertical matching bot when running all
    if not args.pack and bot.get("vertical") in pack_ids:
        pack_ids = [bot["vertical"]] + [p for p in pack_ids if p != bot["vertical"]]

    failures: list[str] = []
    results: list[dict] = []

    for pid in pack_ids:
        pack = load_pack(pid)
        result = run_pack_on_bot(bot, pack)
        scores = result["scores"]
        results.append({"pack_id": pid, "scores": scores})

        if args.write_baseline:
            storage.set_baseline(pid, scores)
            continue

        baseline = storage.get_baseline(pid)
        if not baseline:
            # First run: establish baseline, do not fail
            storage.set_baseline(pid, scores)
            print(f"[baseline created] {pid}: {scores.get('overall')}")
            continue

        base_scores = baseline["scores"]
        for dim, val in scores.items():
            if not isinstance(val, (int, float)):
                continue
            b = float(base_scores.get(dim, val))
            drop = b - float(val)
            if drop > args.threshold:
                msg = f"{pid}.{dim}: {val} < baseline {b} (drop {drop:.1f})"
                failures.append(msg)

    if args.write_baseline:
        print(json.dumps({"wrote": pack_ids, "results": results}, indent=2) if args.json else f"Wrote baselines for {pack_ids}")
        return 0

    if args.json:
        print(json.dumps({"results": results, "failures": failures}, indent=2))
    else:
        for r in results:
            print(f"{r['pack_id']}: overall={r['scores'].get('overall')}")
        for f in failures:
            print(f"FAIL: {f}", file=sys.stderr)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
