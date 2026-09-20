from __future__ import annotations

import html
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field, HttpUrl

from . import storage
from .alerts import maybe_alert_score_drop
from .config import settings
from .scoring import DIMENSIONS, aggregate_scores, score_turn
from .seed import HARBOR_BOT_ID, HAVEN_BOT_ID, seed_demo, seed_haven
from .simulator import run_pack_on_bot, simulate_reply
from .packs_loader import list_pack_ids, load_all_packs, load_pack

app = FastAPI(
    title="Docket Desk",
    description="Mystery-shop companion API for Docket Assistant (WordPress connector).",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    storage.init_db()
    if not storage.get_bot(HARBOR_BOT_ID):
        seed_demo()
    if not storage.get_bot(HAVEN_BOT_ID):
        seed_haven()


# ---------- models ----------


class BotCreate(BaseModel):
    name: str
    vertical: str = "cleaning"
    faq: list[dict[str, str]] = Field(default_factory=list)
    script: list[str] = Field(default_factory=list)
    prompt: str = ""
    id: str | None = None


class MysteryShopRequest(BaseModel):
    bot_id: str
    pack_id: str
    replies: dict[str, str] | None = None  # scenario_id -> assistant text override


class ExternalShopRequest(BaseModel):
    bot_url: HttpUrl
    pack_id: str
    bot_id: str | None = None


class BakeOffRequest(BaseModel):
    bot_url_a: HttpUrl
    bot_url_b: HttpUrl
    pack_id: str
    label_a: str = "Bot A"
    label_b: str = "Bot B"


class EmbedRequest(BaseModel):
    service_url: str
    bot_id: str


class ReplayRequest(BaseModel):
    run_id_a: str
    run_id_b: str | None = None
    title: str = "Side-by-side replay"


# ---------- health / meta ----------


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "docket-desk"}


@app.get("/api/packs")
def api_packs() -> dict[str, Any]:
    return {"packs": load_all_packs()}


@app.get("/api/packs/{pack_id}")
def api_pack(pack_id: str) -> dict[str, Any]:
    try:
        return load_pack(pack_id)
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc


@app.get("/api/dimensions")
def api_dimensions() -> dict[str, Any]:
    return {"dimensions": list(DIMENSIONS)}


# ---------- bots ----------


@app.post("/api/bots")
def create_bot(body: BotCreate) -> dict[str, Any]:
    return storage.create_bot(
        name=body.name,
        vertical=body.vertical,
        faq=body.faq,
        script=body.script,
        prompt=body.prompt,
        bot_id=body.id,
    )


@app.get("/api/bots")
def list_bots() -> dict[str, Any]:
    return {"bots": storage.list_bots()}


@app.get("/api/bots/{bot_id}")
def get_bot(bot_id: str) -> dict[str, Any]:
    bot = storage.get_bot(bot_id)
    if not bot:
        raise HTTPException(404, "bot not found")
    return bot


@app.post("/api/seed")
def api_seed() -> dict[str, Any]:
    bot = seed_demo()
    haven = seed_haven()
    return {"seeded": True, "harbor_bot": bot, "haven_bot": haven}


# ---------- mystery shop / scorecard ----------


@app.post("/api/mystery-shop")
async def mystery_shop(body: MysteryShopRequest) -> dict[str, Any]:
    bot = storage.get_bot(body.bot_id)
    if not bot:
        raise HTTPException(404, "bot not found")
    try:
        pack = load_pack(body.pack_id)
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc

    result = run_pack_on_bot(bot, pack, replies=body.replies)
    run = storage.save_run(
        bot_id=bot["id"],
        pack_id=pack["id"],
        scores=result["scores"],
        transcript=result["transcript"],
        diff=result["diff"],
        patches=result["patches"],
    )
    alert = await maybe_alert_score_drop(
        title=f"{bot['name']} / {pack['id']}",
        scores=result["scores"],
        context={"run_id": run["id"]},
    )
    report = storage.save_report(
        kind="scorecard",
        title=f"Scorecard: {bot['name']} — {pack['name']}",
        payload={"run": run, "result": result, "alert": alert},
    )
    return {
        "run_id": run["id"],
        "report_id": report["id"],
        "report_url": f"{settings.public_base_url.rstrip('/')}/reports/{report['id']}",
        "scores": result["scores"],
        "diff": result["diff"],
        "patches": result["patches"],
        "scenarios": result["scenarios"],
        "alert": alert,
    }


@app.get("/api/runs")
def api_runs(bot_id: str | None = None, limit: int = Query(50, le=200)) -> dict[str, Any]:
    return {"runs": storage.list_runs(bot_id=bot_id, limit=limit)}


@app.get("/api/runs/{run_id}")
def api_run(run_id: str) -> dict[str, Any]:
    run = storage.get_run(run_id)
    if not run:
        raise HTTPException(404, "run not found")
    return run


@app.get("/api/scorecard/history")
def scorecard_history(bot_id: str | None = None) -> dict[str, Any]:
    runs = storage.list_runs(bot_id=bot_id, limit=100)
    history = [
        {
            "run_id": r["id"],
            "bot_id": r["bot_id"],
            "pack_id": r["pack_id"],
            "scores": r["scores"],
            "created_at": r["created_at"],
        }
        for r in runs
    ]
    return {"history": history, "dimensions": list(DIMENSIONS)}


# ---------- human handoff scenarios ----------


@app.get("/api/handoff-scenarios")
def handoff_scenarios(pack_id: str | None = None) -> dict[str, Any]:
    packs = [load_pack(pack_id)] if pack_id else load_all_packs()
    items = []
    for p in packs:
        for sc in p.get("scenarios") or []:
            if sc.get("human_handoff"):
                items.append(
                    {
                        "pack_id": p["id"],
                        "scenario_id": sc["id"],
                        "name": sc["name"],
                        "steps": sc["steps"],
                    }
                )
    return {"handoff_scenarios": items}


# ---------- side-by-side replay + reports ----------


@app.post("/api/replay")
def side_by_side_replay(body: ReplayRequest) -> dict[str, Any]:
    run_a = storage.get_run(body.run_id_a)
    if not run_a:
        raise HTTPException(404, "run_id_a not found")
    run_b = storage.get_run(body.run_id_b) if body.run_id_b else None
    payload = {
        "title": body.title,
        "left": run_a,
        "right": run_b,
    }
    report = storage.save_report(kind="replay", title=body.title, payload=payload)
    return {
        "report_id": report["id"],
        "report_url": f"{settings.public_base_url.rstrip('/')}/reports/{report['id']}",
        "payload": payload,
    }


@app.get("/reports/{report_id}", response_class=HTMLResponse)
def view_report(report_id: str) -> HTMLResponse:
    report = storage.get_report(report_id)
    if not report:
        raise HTTPException(404, "report not found")
    payload = report["payload"]
    title = html.escape(report["title"])
    pretty = html.escape(
        __import__("json").dumps(payload, indent=2, ensure_ascii=False)
    )
    body = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/><title>{title}</title>
<style>
body{{font-family:system-ui,sans-serif;margin:2rem;background:#f6f4ef;color:#161513}}
h1{{font-size:1.4rem}} pre{{background:#fff;padding:1rem;border-radius:8px;overflow:auto;box-shadow:0 1px 4px rgba(0,0,0,.08)}}
.meta{{color:#666;font-size:.9rem}}
</style></head><body>
<h1>{title}</h1>
<p class="meta">Report {html.escape(report_id)} · {html.escape(report['kind'])} · {html.escape(report['created_at'])}</p>
<pre>{pretty}</pre>
</body></html>"""
    return HTMLResponse(body)


@app.get("/api/reports/{report_id}")
def api_report(report_id: str) -> dict[str, Any]:
    report = storage.get_report(report_id)
    if not report:
        raise HTTPException(404, "report not found")
    return report


# ---------- bake-off ----------


async def _fetch_bot_replies(bot_url: str, pack: dict[str, Any]) -> dict[str, str]:
    """POST each scenario user line to bot_url; expect JSON {reply: str} or plain text."""
    replies: dict[str, str] = {}
    async with httpx.AsyncClient(timeout=20.0) as client:
        for sc in pack.get("scenarios") or []:
            user = (sc.get("steps") or [{}])[0].get("user", "")
            try:
                r = await client.post(str(bot_url), json={"message": user, "scenario_id": sc["id"]})
                if r.headers.get("content-type", "").startswith("application/json"):
                    data = r.json()
                    replies[sc["id"]] = data.get("reply") or data.get("message") or str(data)
                else:
                    replies[sc["id"]] = r.text
            except Exception as exc:  # noqa: BLE001
                replies[sc["id"]] = f"[error contacting bot: {exc}]"
    return replies


def _score_external_replies(
    replies: dict[str, str], pack: dict[str, Any], faq: list | None = None
) -> dict[str, Any]:
    faq = faq or []
    step_scores = []
    transcript = []
    for sc in pack.get("scenarios") or []:
        step = (sc.get("steps") or [None])[0]
        if not step:
            continue
        user = step["user"]
        asst = replies.get(sc["id"], "")
        scores = score_turn(user, asst, step.get("expected") or {}, faq)
        step_scores.append(scores)
        transcript.append({"user": user, "assistant": asst, "scenario_id": sc["id"]})
    return {
        "scores": aggregate_scores(step_scores),
        "transcript": transcript,
        "replies": replies,
    }


@app.post("/api/bakeoff")
async def bakeoff(body: BakeOffRequest) -> dict[str, Any]:
    try:
        pack = load_pack(body.pack_id)
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc

    replies_a = await _fetch_bot_replies(str(body.bot_url_a), pack)
    replies_b = await _fetch_bot_replies(str(body.bot_url_b), pack)
    result_a = _score_external_replies(replies_a, pack)
    result_b = _score_external_replies(replies_b, pack)

    overall_a = result_a["scores"].get("overall", 0)
    overall_b = result_b["scores"].get("overall", 0)
    if overall_a > overall_b:
        winner = body.label_a
    elif overall_b > overall_a:
        winner = body.label_b
    else:
        winner = "tie"

    ranked = sorted(
        [
            {"label": body.label_a, "url": str(body.bot_url_a), "scores": result_a["scores"]},
            {"label": body.label_b, "url": str(body.bot_url_b), "scores": result_b["scores"]},
        ],
        key=lambda x: x["scores"].get("overall", 0),
        reverse=True,
    )
    payload = {
        "pack_id": body.pack_id,
        "winner": winner,
        "ranked": ranked,
        "detail_a": result_a,
        "detail_b": result_b,
    }
    report = storage.save_report(
        kind="bakeoff",
        title=f"Bake-off: {body.label_a} vs {body.label_b}",
        payload=payload,
    )
    return {
        "report_id": report["id"],
        "report_url": f"{settings.public_base_url.rstrip('/')}/reports/{report['id']}",
        "winner": winner,
        "ranked": ranked,
    }


# ---------- embed snippet ----------


@app.post("/api/embed-snippet")
def embed_snippet(body: EmbedRequest) -> dict[str, Any]:
    service = body.service_url.rstrip("/")
    bot_id = body.bot_id
    widget = f"{service}/widget/{bot_id}"
    snippet = f"""<!-- Docket Assistant embed -->
<div id="docket-assistant-root" data-bot="{html.escape(bot_id)}"></div>
<iframe id="docket-assistant-frame" src="{html.escape(widget)}" title="Chat"
  sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
  referrerpolicy="no-referrer"
  style="display:none;position:fixed;right:16px;bottom:84px;width:360px;height:520px;border:0;border-radius:16px;z-index:2147483647;"></iframe>
<script>
(function(){{
  var f=document.getElementById('docket-assistant-frame');
  var b=document.createElement('button');
  b.type='button'; b.textContent='Chat';
  b.style.cssText='position:fixed;right:16px;bottom:16px;padding:12px 16px;border:0;border-radius:28px;background:#161513;color:#eceae4;z-index:2147483647;cursor:pointer';
  var open=false;
  b.onclick=function(){{open=!open;f.style.display=open?'block':'none';}};
  document.body.appendChild(b);
}})();
</script>"""
    return {"snippet": snippet, "widget_url": widget}


# ---------- widget stub (for WP iframe demos) ----------


@app.get("/widget/{bot_id}", response_class=HTMLResponse)
def widget(bot_id: str) -> HTMLResponse:
    """Chat widget for any bot id (e.g. haven-abodes, harbor-hearth)."""
    bot = storage.get_bot(bot_id)
    display = (bot["name"] if bot else bot_id) or bot_id
    # Bubble short name: first token before · or full display
    bubble = display.split("·")[0].strip() if "·" in display else display
    if bot_id == HAVEN_BOT_ID:
        bubble = "Haven"
        display = "Haven · Aesthetic Abodes"
    greeting = "Hi — ask about hours, bookings, or policies."
    if bot and bot.get("script"):
        greeting = bot["script"][0]
    name = html.escape(display)
    bubble_esc = html.escape(bubble)
    greet_esc = html.escape(greeting)
    return HTMLResponse(
        f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/><title>{name}</title>
<style>
body{{font-family:system-ui,sans-serif;margin:0;background:#eceae4;color:#161513;display:flex;flex-direction:column;height:100vh}}
header{{padding:12px 16px;background:#161513;color:#eceae4;font-weight:600}}
header small{{display:block;font-weight:400;opacity:.75;font-size:.8rem;margin-top:2px}}
#log{{flex:1;overflow:auto;padding:12px}}
.msg{{margin:8px 0;padding:8px 10px;border-radius:10px;max-width:90%}}
.user{{background:#fff;align-self:flex-end;margin-left:auto}}
.bot{{background:#ddd6c8}}
form{{display:flex;gap:8px;padding:12px;border-top:1px solid #ccc}}
input{{flex:1;padding:8px;border-radius:8px;border:1px solid #bbb}}
button{{padding:8px 14px;border:0;border-radius:8px;background:#161513;color:#eceae4}}
</style></head><body>
<header>{bubble_esc}<small>{name}</small></header>
<div id="log"></div>
<form id="f"><input id="m" placeholder="Message…" autocomplete="off"/><button>Send</button></form>
<script>
const botId={html.escape(repr(bot_id))};
const log=document.getElementById('log');
function add(cls,t){{const d=document.createElement('div');d.className='msg '+cls;d.textContent=t;log.appendChild(d);log.scrollTop=log.scrollHeight;}}
document.getElementById('f').onsubmit=async(e)=>{{
  e.preventDefault();
  const v=document.getElementById('m').value.trim(); if(!v)return;
  document.getElementById('m').value=''; add('user',v);
  const r=await fetch('/api/chat/'+encodeURIComponent(botId),{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{message:v}})}});
  const j=await r.json(); add('bot', j.reply||'…');
}};
add('bot',{html.escape(repr(greeting))});
</script></body></html>"""
    )


class ChatBody(BaseModel):
    message: str


@app.post("/api/chat/{bot_id}")
def chat(bot_id: str, body: ChatBody) -> dict[str, str]:
    bot = storage.get_bot(bot_id)
    if not bot:
        raise HTTPException(404, "bot not found")
    return {"reply": simulate_reply(body.message, bot, {})}


# ---------- baselines for regression ----------


@app.post("/api/baselines/{pack_id}")
def set_baseline(pack_id: str, bot_id: str = HARBOR_BOT_ID) -> dict[str, Any]:
    bot = storage.get_bot(bot_id)
    if not bot:
        raise HTTPException(404, "bot not found")
    try:
        pack = load_pack(pack_id)
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    result = run_pack_on_bot(bot, pack)
    storage.set_baseline(pack_id, result["scores"])
    return {"pack_id": pack_id, "baseline": result["scores"]}


@app.get("/api/baselines/{pack_id}")
def get_baseline(pack_id: str) -> dict[str, Any]:
    b = storage.get_baseline(pack_id)
    if not b:
        raise HTTPException(404, "no baseline")
    return b


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "service": "docket-desk",
        "docs": "/docs",
        "packs": list_pack_ids(),
        "demo_bot": HARBOR_BOT_ID,
        "haven_bot": HAVEN_BOT_ID,
        "widget": f"/widget/{HARBOR_BOT_ID}",
        "haven_widget": f"/widget/{HAVEN_BOT_ID}",
    }
