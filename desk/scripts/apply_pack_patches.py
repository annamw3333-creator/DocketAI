#!/usr/bin/env python3
"""Apply desk/scripts/pack_patches/*.json onto desk/packs and desk-deploy/packs."""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DESK = ROOT / "desk" / "packs"
DEPLOY = ROOT / "desk-deploy" / "packs"
PATCHES = Path(__file__).resolve().parent / "pack_patches"


def apply(pack_id: str) -> dict:
    pack = json.loads((DESK / f"{pack_id}.json").read_text(encoding="utf-8"))
    patch = json.loads((PATCHES / f"{pack_id}.json").read_text(encoding="utf-8"))
    deepen = patch.get("deepen") or {}
    new_list = patch.get("new") or []

    out = []
    for sc in pack["scenarios"]:
        if sc["id"] not in deepen:
            out.append(sc)
            continue
        spec = deepen[sc["id"]]
        updated = deepcopy(sc)
        updated["steps"] = list(updated.get("steps") or []) + list(spec.get("extra_steps") or [])
        for key in ("failure_criteria", "suggested_fixes", "policy_refs", "personas", "attacks"):
            if key in spec:
                updated[key] = spec[key]
        if spec.get("human_handoff"):
            updated["human_handoff"] = True
        out.append(updated)

    existing = {s["id"] for s in out}
    for ns in new_list:
        if ns["id"] in existing:
            out = [ns if s["id"] == ns["id"] else s for s in out]
        else:
            out.append(ns)

    desc = pack.get("description") or ""
    if "owner-critical" not in desc.lower():
        pack["description"] = desc.rstrip(".") + (
            "; owner-critical multi-turn deepening for service-business buyers"
        )
    pack["scenarios"] = out
    text = json.dumps(pack, indent=2, ensure_ascii=False) + "\n"
    (DESK / f"{pack_id}.json").write_text(text, encoding="utf-8")
    (DEPLOY / f"{pack_id}.json").write_text(text, encoding="utf-8")
    return {"pack": pack_id, "count": len(out)}


if __name__ == "__main__":
    for pid in ("cleaning", "dental", "hvac", "salon"):
        print(apply(pid))
