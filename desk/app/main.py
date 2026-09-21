from __future__ import annotations

import html
import json
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
from .brand_builder import build_brand_draft, fetch_public_site
from .themes import (
    DEFAULT_THEME_ID,
    list_themes,
    normalize_theme_config,
    theme_config_for_storage,
    theme_from_query_and_bot,
)
from .lens import list_attacks, list_personas, normalize_lens

app = FastAPI(
    title="Docket Desk",
    description="Mystery-shop companion API for Docket Assistant (WordPress connector).",
    version="1.3.1",
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
    theme_id: str | None = None
    theme: dict[str, Any] | None = None


class BrandFromRequest(BaseModel):
    website_url: str
    brand_notes: str = ""
    name: str | None = None
    vertical: str | None = None
    create: bool = True  # if false, return draft only without persisting
    theme_id: str | None = None
    theme: dict[str, Any] | None = None


class MysteryShopRequest(BaseModel):
    bot_id: str
    pack_id: str
    replies: dict[str, str] | None = None  # scenario_id -> assistant text override
    persona_id: str | None = None  # shapes which scenarios run + user tone
    attack_id: str | None = None


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
    theme_id: str | None = None  # optional preview override; else uses bot theme


class ThemeUpdate(BaseModel):
    theme_id: str | None = None
    primary: str | None = None
    accent: str | None = None
    bg: str | None = None
    text: str | None = None
    header_text: str | None = None
    bot_bubble: str | None = None
    user_bubble: str | None = None
    launcher_bg: str | None = None
    launcher_text: str | None = None
    position: str | None = None  # left | right
    avatar_style: str | None = None  # monogram | dot | initials | none
    bot_name: str | None = None
    display_name: str | None = None
    greeting: str | None = None


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


@app.get("/api/personas")
def api_personas() -> dict[str, Any]:
    return {"personas": list_personas(), "count": len(list_personas())}


@app.get("/api/attacks")
def api_attacks() -> dict[str, Any]:
    return {"attacks": list_attacks(), "count": len(list_attacks())}


# ---------- bots ----------


@app.post("/api/bots")
def create_bot(body: BotCreate) -> dict[str, Any]:
    theme_body = dict(body.theme or {})
    if body.theme_id:
        theme_body["theme_id"] = body.theme_id
    theme_cfg = theme_config_for_storage(theme_body) if theme_body else {"theme_id": DEFAULT_THEME_ID}
    return storage.create_bot(
        name=body.name,
        vertical=body.vertical,
        faq=body.faq,
        script=body.script,
        prompt=body.prompt,
        bot_id=body.id,
        theme=theme_cfg,
    )


@app.post("/api/bots/from-brand")
async def bots_from_brand(body: BrandFromRequest) -> dict[str, Any]:
    """Fetch a public website (SSRF-safe) and create a draft bot.

    Draft system prompt + FAQ are deterministic templates labeled as draft.
    No external LLM is called.
    """
    try:
        site = await fetch_public_site(body.website_url)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    draft = build_brand_draft(
        website_url=body.website_url,
        brand_notes=body.brand_notes or "",
        site=site,
    )
    if body.name:
        draft["name"] = body.name.strip()[:80]
    if body.vertical:
        draft["vertical"] = body.vertical.strip()[:40]

    if not body.create:
        return {"draft": draft, "bot": None, "created": False}

    theme_body = dict(body.theme or {})
    if body.theme_id:
        theme_body["theme_id"] = body.theme_id
    theme_cfg = theme_config_for_storage(theme_body) if theme_body else {"theme_id": DEFAULT_THEME_ID}

    bot = storage.create_bot(
        name=draft["name"],
        vertical=draft["vertical"],
        faq=draft["faq"],
        script=draft["script"],
        prompt=draft["prompt"],
        bot_id=draft.get("bot_id_suggestion"),
        theme=theme_cfg,
    )
    return {
        "draft": draft,
        "bot": bot,
        "created": True,
        "label": "draft",
        "note": "Prompt and FAQ are draft templates extracted from the public site — review before production use.",
    }


@app.get("/api/bots")
def list_bots() -> dict[str, Any]:
    return {"bots": storage.list_bots()}


@app.get("/api/bots/{bot_id}")
def get_bot(bot_id: str) -> dict[str, Any]:
    bot = storage.get_bot(bot_id)
    if not bot:
        raise HTTPException(404, "bot not found")
    return bot


@app.get("/api/themes")
def api_themes() -> dict[str, Any]:
    """List Theme Studio presets with preview metadata (name, description, swatches)."""
    themes = list_themes()
    return {
        "themes": themes,
        "default_theme_id": DEFAULT_THEME_ID,
        "count": len(themes),
    }


@app.patch("/api/bots/{bot_id}/theme")
def patch_bot_theme(bot_id: str, body: ThemeUpdate) -> dict[str, Any]:
    bot = storage.get_bot(bot_id)
    if not bot:
        raise HTTPException(404, "bot not found")
    # Merge onto existing compact config
    existing = dict(bot.get("theme_config") or {})
    payload = body.model_dump(exclude_none=True)
    existing.update(payload)
    if "theme_id" not in existing:
        existing["theme_id"] = (bot.get("theme") or {}).get("theme_id") or DEFAULT_THEME_ID
    theme_cfg = theme_config_for_storage(existing)
    updated = storage.update_bot_theme(bot_id, theme_cfg)
    if not updated:
        raise HTTPException(404, "bot not found")
    return {
        "bot": updated,
        "theme": updated.get("theme"),
        "theme_config": theme_cfg,
    }


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

    lens = normalize_lens(body.persona_id, body.attack_id)
    result = run_pack_on_bot(
        bot,
        pack,
        replies=body.replies,
        persona_id=lens["persona_id"],
        attack_id=lens["attack_id"],
    )
    lens_meta = result.get("lens") or lens
    run_meta = {
        "persona_id": lens_meta.get("persona_id"),
        "attack_id": lens_meta.get("attack_id"),
        "persona_label": lens_meta.get("persona_label"),
        "attack_label": lens_meta.get("attack_label"),
        "lens": lens_meta,
    }
    run = storage.save_run(
        bot_id=bot["id"],
        pack_id=pack["id"],
        scores=result["scores"],
        transcript=result["transcript"],
        diff=result["diff"],
        patches=result["patches"],
        scenarios=result.get("scenarios") or [],
        meta=run_meta,
    )
    alert = await maybe_alert_score_drop(
        title=f"{bot['name']} / {pack['id']}",
        scores=result["scores"],
        context={
            "run_id": run["id"],
            "persona_id": run_meta.get("persona_id"),
            "attack_id": run_meta.get("attack_id"),
        },
    )
    lens_bits = []
    if run_meta.get("persona_label"):
        lens_bits.append(str(run_meta["persona_label"]))
    if run_meta.get("attack_label"):
        lens_bits.append(str(run_meta["attack_label"]))
    lens_suffix = f" · {' × '.join(lens_bits)}" if lens_bits else ""
    report = storage.save_report(
        kind="scorecard",
        title=f"Scorecard: {bot['name']} — {pack['name']}{lens_suffix}",
        payload={"run": run, "result": result, "alert": alert, "lens": lens_meta},
    )
    return {
        "run_id": run["id"],
        "report_id": report["id"],
        "report_url": f"{settings.public_base_url.rstrip('/')}/reports/{report['id']}",
        "scores": result["scores"],
        "diff": result["diff"],
        "patches": result["patches"],
        "scenarios": result["scenarios"],
        "failures": result.get("failures") or [],
        "alert": alert,
        "persona_id": run_meta.get("persona_id"),
        "attack_id": run_meta.get("attack_id"),
        "lens": lens_meta,
        "scenario_count": result.get("scenario_count"),
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


def _build_embed_snippet(service: str, bot_id: str, theme: dict[str, Any]) -> str:
    """Ready-to-paste script that loads the themed widget iframe + launcher."""
    pos = theme.get("position") or "right"
    side = "left" if pos == "left" else "right"
    launcher_bg = theme.get("launcher_bg") or theme.get("primary") or "#161513"
    launcher_text = theme.get("launcher_text") or theme.get("header_text") or "#eceae4"
    accent = theme.get("accent") or "#C9A227"
    widget = f"{service}/widget/{bot_id}"
    label = str(theme.get("bot_name") or "Chat")[:40]
    label_js = json.dumps(label)
    return f"""<!-- Docket Assistant embed · theme={html.escape(str(theme.get('theme_id') or theme.get('id') or ''))} -->
<div id="docket-assistant-root" data-bot="{html.escape(bot_id)}" data-theme="{html.escape(str(theme.get('theme_id') or ''))}"></div>
<iframe id="docket-assistant-frame" src="{html.escape(widget)}" title="Chat"
  sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
  referrerpolicy="no-referrer"
  style="display:none;position:fixed;{side}:16px;bottom:84px;width:360px;height:520px;border:0;border-radius:16px;box-shadow:0 12px 40px rgba(0,0,0,.25);z-index:2147483647;"></iframe>
<script>
(function(){{
  var f=document.getElementById('docket-assistant-frame');
  var b=document.createElement('button');
  b.type='button'; b.setAttribute('aria-label','Open chat');
  b.textContent={label_js};
  b.style.cssText='position:fixed;{side}:16px;bottom:16px;padding:12px 18px;border:0;border-radius:28px;background:{html.escape(launcher_bg)};color:{html.escape(launcher_text)};box-shadow:0 4px 16px rgba(0,0,0,.2);font:600 14px system-ui,sans-serif;z-index:2147483647;cursor:pointer;outline:2px solid transparent;';
  b.onmouseenter=function(){{b.style.outlineColor='{html.escape(accent)}';}};
  b.onmouseleave=function(){{b.style.outlineColor='transparent';}};
  var open=false;
  b.onclick=function(){{open=!open;f.style.display=open?'block':'none';b.setAttribute('aria-expanded',open?'true':'false');}};
  document.body.appendChild(b);
}})();
</script>"""


@app.post("/api/embed-snippet")
def embed_snippet(body: EmbedRequest) -> dict[str, Any]:
    service = body.service_url.rstrip("/")
    bot_id = body.bot_id
    bot = storage.get_bot(bot_id)
    theme = theme_from_query_and_bot(bot, theme_id=body.theme_id)
    widget = f"{service}/widget/{bot_id}"
    snippet = _build_embed_snippet(service, bot_id, theme)
    return {
        "snippet": snippet,
        "widget_url": widget,
        "theme": theme,
        "bot_id": bot_id,
        "steps": {
            "any_html": "Paste the snippet before </body> on any page.",
            "wordpress": "Appearance → Theme File Editor (or a Custom HTML block / WPCode) → paste before </body>.",
            "squarespace": "Settings → Advanced → Code Injection → Footer → paste snippet.",
        },
    }


@app.get("/api/bots/{bot_id}/embed")
def get_bot_embed(
    bot_id: str,
    service_url: str | None = None,
) -> dict[str, Any]:
    bot = storage.get_bot(bot_id)
    if not bot:
        raise HTTPException(404, "bot not found")
    service = (service_url or settings.public_base_url).rstrip("/")
    theme = normalize_theme_config(bot.get("theme_config") or bot.get("theme") or {})
    widget = f"{service}/widget/{bot_id}"
    return {
        "snippet": _build_embed_snippet(service, bot_id, theme),
        "widget_url": widget,
        "theme": theme,
        "bot_id": bot_id,
        "steps": {
            "any_html": "Paste the snippet before </body> on any page.",
            "wordpress": "Appearance → Theme File Editor (or a Custom HTML block / WPCode) → paste before </body>.",
            "squarespace": "Settings → Advanced → Code Injection → Footer → paste snippet.",
        },
    }


# ---------- widget (themed chat panel) ----------


def _widget_html(bot_id: str, bot: dict[str, Any] | None, theme: dict[str, Any]) -> str:
    display = theme.get("display_name") or theme.get("bot_name")
    if not display:
        display = (bot["name"] if bot else bot_id) or bot_id
    bubble = display.split("·")[0].strip() if "·" in display else display
    if bot_id == HAVEN_BOT_ID and not theme.get("bot_name") and not theme.get("display_name"):
        bubble = "Haven"
        display = "Haven · Aesthetic Abodes"
    greeting = theme.get("greeting")
    if not greeting:
        greeting = "Hi — ask about hours, bookings, or policies."
        if bot and bot.get("script"):
            greeting = bot["script"][0]
    name = html.escape(str(display))
    bubble_esc = html.escape(str(bubble))
    avatar = theme.get("avatar_style") or "monogram"
    initial = html.escape((bubble.strip()[:1] or "D").upper())
    if avatar == "dot":
        avatar_html = '<span class="avatar avatar-dot" aria-hidden="true"></span>'
    elif avatar == "none":
        avatar_html = ""
    elif avatar == "initials":
        avatar_html = f'<span class="avatar avatar-initials" aria-hidden="true">{initial}</span>'
    else:
        avatar_html = f'<span class="avatar avatar-mono" aria-hidden="true">{initial}</span>'

    css_vars = f"""--docket-primary:{html.escape(theme.get('primary','#161513'))};
--docket-accent:{html.escape(theme.get('accent','#C9A227'))};
--docket-bg:{html.escape(theme.get('bg','#ECEAE4'))};
--docket-text:{html.escape(theme.get('text','#161513'))};
--docket-header-text:{html.escape(theme.get('header_text','#ECEAE4'))};
--docket-bot-bubble:{html.escape(theme.get('bot_bubble','#DDD6C8'))};
--docket-user-bubble:{html.escape(theme.get('user_bubble','#FFFFFF'))};"""

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{name}</title>
<style>
:root{{{css_vars}}}
*{{box-sizing:border-box}}
body{{font-family:system-ui,-apple-system,sans-serif;margin:0;background:var(--docket-bg);color:var(--docket-text);display:flex;flex-direction:column;height:100vh}}
header{{padding:12px 16px;background:var(--docket-primary);color:var(--docket-header-text);font-weight:600;display:flex;align-items:center;gap:10px;border-bottom:2px solid var(--docket-accent)}}
header .titles{{flex:1;min-width:0}}
header small{{display:block;font-weight:400;opacity:.8;font-size:.78rem;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.avatar{{width:28px;height:28px;border-radius:50%;flex-shrink:0;display:inline-flex;align-items:center;justify-content:center;font-size:12px;font-weight:700}}
.avatar-mono,.avatar-initials{{background:var(--docket-accent);color:var(--docket-primary)}}
.avatar-dot{{background:var(--docket-accent);box-shadow:0 0 0 3px color-mix(in srgb, var(--docket-accent) 35%, transparent)}}
#log{{flex:1;overflow:auto;padding:12px;display:flex;flex-direction:column}}
.msg{{margin:8px 0;padding:8px 10px;border-radius:10px;max-width:90%;line-height:1.35;font-size:14px}}
.user{{background:var(--docket-user-bubble);align-self:flex-end;margin-left:auto;border:1px solid color-mix(in srgb, var(--docket-text) 12%, transparent)}}
.bot{{background:var(--docket-bot-bubble);align-self:flex-start}}
form{{display:flex;gap:8px;padding:12px;border-top:1px solid color-mix(in srgb, var(--docket-text) 15%, transparent);background:color-mix(in srgb, var(--docket-bg) 92%, var(--docket-primary))}}
input{{flex:1;padding:10px 12px;border-radius:8px;border:1px solid color-mix(in srgb, var(--docket-text) 20%, transparent);background:#fff;color:var(--docket-text);font:inherit}}
button{{padding:10px 14px;border:0;border-radius:8px;background:var(--docket-primary);color:var(--docket-header-text);font-weight:600;cursor:pointer}}
button:hover{{outline:2px solid var(--docket-accent);outline-offset:1px}}
.theme-tag{{position:absolute;top:8px;right:8px;font-size:10px;opacity:.45;color:var(--docket-header-text)}}
</style></head><body>
<header>
{avatar_html}
<div class="titles">{bubble_esc}<small>{name}</small></div>
<span class="theme-tag" data-theme-id="{html.escape(str(theme.get('theme_id') or theme.get('id') or ''))}">{html.escape(str(theme.get('theme_id') or theme.get('id') or ''))}</span>
</header>
<div id="log"></div>
<form id="f"><input id="m" placeholder="Message…" autocomplete="off"/><button type="submit">Send</button></form>
<script>
const botId={json.dumps(bot_id)};
const log=document.getElementById('log');
function add(cls,t){{const d=document.createElement('div');d.className='msg '+cls;d.textContent=t;log.appendChild(d);log.scrollTop=log.scrollHeight;}}
document.getElementById('f').onsubmit=async(e)=>{{
  e.preventDefault();
  const v=document.getElementById('m').value.trim(); if(!v)return;
  document.getElementById('m').value=''; add('user',v);
  try{{
    const r=await fetch('/api/chat/'+encodeURIComponent(botId),{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{message:v}})}});
    const j=await r.json(); add('bot', j.reply||'…');
  }}catch(err){{ add('bot','Sorry — chat is temporarily unavailable.'); }}
}};
add('bot',{json.dumps(greeting)});
</script></body></html>"""


@app.get("/widget/{bot_id}", response_class=HTMLResponse)
def widget(
    bot_id: str,
    theme: str | None = Query(None, description="Preset theme_id override"),
    primary: str | None = None,
    accent: str | None = None,
    bg: str | None = None,
    text: str | None = None,
    position: str | None = None,
    avatar_style: str | None = None,
    bot_name: str | None = None,
    greeting: str | None = None,
) -> HTMLResponse:
    """Themed chat widget. Chat posts to /api/chat/{bot_id} immediately."""
    bot = storage.get_bot(bot_id)
    resolved = theme_from_query_and_bot(
        bot,
        theme_id=theme,
        primary=primary,
        accent=accent,
        bg=bg,
        text=text,
        position=position,
        avatar_style=avatar_style,
        bot_name=bot_name,
        greeting=greeting,
    )
    return HTMLResponse(_widget_html(bot_id, bot, resolved))


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
        "themes": "/api/themes",
        "personas": "/api/personas",
        "attacks": "/api/attacks",
        "version": "1.3.1",
    }
