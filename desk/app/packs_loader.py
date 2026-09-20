from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PACKS_DIR = Path(__file__).resolve().parents[1] / "packs"


def list_pack_ids() -> list[str]:
    return sorted(p.stem for p in PACKS_DIR.glob("*.json"))


def load_pack(pack_id: str) -> dict[str, Any]:
    path = PACKS_DIR / f"{pack_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Unknown pack: {pack_id}")
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_all_packs() -> list[dict[str, Any]]:
    return [load_pack(pid) for pid in list_pack_ids()]
