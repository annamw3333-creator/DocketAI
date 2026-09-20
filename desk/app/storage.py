from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from .config import settings


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db() -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    Path(settings.database_path).parent.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS bots (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                vertical TEXT NOT NULL,
                faq_json TEXT NOT NULL DEFAULT '[]',
                script_json TEXT NOT NULL DEFAULT '[]',
                prompt TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                bot_id TEXT NOT NULL,
                pack_id TEXT NOT NULL,
                scenario_id TEXT,
                scores_json TEXT NOT NULL,
                transcript_json TEXT NOT NULL,
                diff_json TEXT NOT NULL DEFAULT '{}',
                patches_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                FOREIGN KEY (bot_id) REFERENCES bots(id)
            );
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                title TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS baselines (
                pack_id TEXT PRIMARY KEY,
                scores_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(str(settings.database_path))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)


def create_bot(
    name: str,
    vertical: str,
    faq: list[dict[str, str]],
    script: list[str],
    prompt: str = "",
    bot_id: str | None = None,
) -> dict[str, Any]:
    bid = bot_id or str(uuid.uuid4())
    with connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO bots (id, name, vertical, faq_json, script_json, prompt, created_at) VALUES (?,?,?,?,?,?,?)",
            (bid, name, vertical, json.dumps(faq), json.dumps(script), prompt, _utc_now()),
        )
    return get_bot(bid)  # type: ignore[return-value]


def get_bot(bot_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM bots WHERE id=?", (bot_id,)).fetchone()
    if not row:
        return None
    d = dict(row)
    d["faq"] = json.loads(d.pop("faq_json"))
    d["script"] = json.loads(d.pop("script_json"))
    return d


def list_bots() -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM bots ORDER BY created_at DESC").fetchall()
    out = []
    for row in rows:
        d = dict(row)
        d["faq"] = json.loads(d.pop("faq_json"))
        d["script"] = json.loads(d.pop("script_json"))
        out.append(d)
    return out


def save_run(
    bot_id: str,
    pack_id: str,
    scores: dict[str, Any],
    transcript: list[dict[str, str]],
    diff: dict[str, Any],
    patches: list[str],
    scenario_id: str | None = None,
) -> dict[str, Any]:
    rid = str(uuid.uuid4())
    with connect() as conn:
        conn.execute(
            """INSERT INTO runs (id, bot_id, pack_id, scenario_id, scores_json, transcript_json, diff_json, patches_json, created_at)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                rid,
                bot_id,
                pack_id,
                scenario_id,
                json.dumps(scores),
                json.dumps(transcript),
                json.dumps(diff),
                json.dumps(patches),
                _utc_now(),
            ),
        )
    return get_run(rid)  # type: ignore[return-value]


def get_run(run_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
    if not row:
        return None
    d = dict(row)
    d["scores"] = json.loads(d.pop("scores_json"))
    d["transcript"] = json.loads(d.pop("transcript_json"))
    d["diff"] = json.loads(d.pop("diff_json"))
    d["patches"] = json.loads(d.pop("patches_json"))
    return d


def list_runs(bot_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    with connect() as conn:
        if bot_id:
            rows = conn.execute(
                "SELECT * FROM runs WHERE bot_id=? ORDER BY created_at DESC LIMIT ?",
                (bot_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM runs ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
    out = []
    for row in rows:
        d = dict(row)
        d["scores"] = json.loads(d.pop("scores_json"))
        d["transcript"] = json.loads(d.pop("transcript_json"))
        d["diff"] = json.loads(d.pop("diff_json"))
        d["patches"] = json.loads(d.pop("patches_json"))
        out.append(d)
    return out


def save_report(kind: str, title: str, payload: dict[str, Any]) -> dict[str, Any]:
    rid = str(uuid.uuid4())
    with connect() as conn:
        conn.execute(
            "INSERT INTO reports (id, kind, title, payload_json, created_at) VALUES (?,?,?,?,?)",
            (rid, kind, title, json.dumps(payload), _utc_now()),
        )
    return get_report(rid)  # type: ignore[return-value]


def get_report(report_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM reports WHERE id=?", (report_id,)).fetchone()
    if not row:
        return None
    d = dict(row)
    d["payload"] = json.loads(d.pop("payload_json"))
    return d


def get_baseline(pack_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM baselines WHERE pack_id=?", (pack_id,)).fetchone()
    if not row:
        return None
    d = dict(row)
    d["scores"] = json.loads(d.pop("scores_json"))
    return d


def set_baseline(pack_id: str, scores: dict[str, float]) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO baselines (pack_id, scores_json, updated_at) VALUES (?,?,?)",
            (pack_id, json.dumps(scores), _utc_now()),
        )
