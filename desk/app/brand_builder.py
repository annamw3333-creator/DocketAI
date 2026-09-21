"""Brand → bot draft builder.

Fetches a public website (SSRF-safe), extracts rough text, and builds a
deterministic draft system prompt + FAQ. Labeled as draft — no LLM required.
"""

from __future__ import annotations

import ipaddress
import re
import socket
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlparse

import httpx


# ---------- SSRF-safe fetch ----------

_BLOCKED_HOSTS = frozenset(
    {
        "localhost",
        "localhost.localdomain",
        "metadata.google.internal",
        "metadata",
    }
)


def _is_blocked_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return bool(
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def _validate_public_url(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        raise ValueError("website URL is required")
    if "://" not in raw:
        raw = "https://" + raw
    parsed = urlparse(raw)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("only http/https URLs are allowed")
    host = (parsed.hostname or "").lower().rstrip(".")
    if not host:
        raise ValueError("URL must include a hostname")
    if host in _BLOCKED_HOSTS or host.endswith(".local") or host.endswith(".internal"):
        raise ValueError("host is not allowed")
    # Block literal IPs that are private
    try:
        ip = ipaddress.ip_address(host)
        if _is_blocked_ip(ip):
            raise ValueError("private or reserved IP addresses are not allowed")
    except ValueError as exc:
        if "private or reserved" in str(exc) or "not allowed" in str(exc):
            raise
        # hostname — resolve and check every address
        try:
            infos = socket.getaddrinfo(host, parsed.port or 443, type=socket.SOCK_STREAM)
        except socket.gaierror as e:
            raise ValueError(f"could not resolve host: {host}") from e
        if not infos:
            raise ValueError(f"could not resolve host: {host}")
        for info in infos:
            addr = info[4][0]
            try:
                if _is_blocked_ip(ipaddress.ip_address(addr)):
                    raise ValueError("host resolves to a private or reserved address")
            except ValueError as e:
                if "private or reserved" in str(e):
                    raise
    # Rebuild without credentials / fragments
    path = parsed.path or "/"
    query = f"?{parsed.query}" if parsed.query else ""
    return f"{parsed.scheme}://{host}{path}{query}"


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip = 0
        self.parts: list[str] = []
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        t = tag.lower()
        if t in ("script", "style", "noscript", "svg", "iframe"):
            self._skip += 1
        if t == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if t in ("script", "style", "noscript", "svg", "iframe") and self._skip:
            self._skip -= 1
        if t == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        text = re.sub(r"\s+", " ", data or "").strip()
        if not text:
            return
        if self._in_title and not self.title:
            self.title = text[:120]
        if self._skip:
            return
        self.parts.append(text)


def _extract_text(html: str) -> tuple[str, str]:
    parser = _TextExtractor()
    try:
        parser.feed(html)
    except Exception:  # noqa: BLE001
        pass
    blob = " ".join(parser.parts)
    blob = re.sub(r"\s+", " ", blob).strip()
    return parser.title, blob[:12000]


async def fetch_public_site(url: str) -> dict[str, Any]:
    """Fetch a public site and return {url, title, text, error?}."""
    safe = _validate_public_url(url)
    try:
        async with httpx.AsyncClient(
            timeout=12.0,
            follow_redirects=True,
            max_redirects=3,
            headers={"User-Agent": "DocketAI-Desk/1.3 (+brand-builder; public-fetch)"},
        ) as client:
            # Re-validate each redirect hop's host
            resp = await client.get(safe)
            final = str(resp.url)
            _validate_public_url(final)
            if resp.status_code >= 400:
                return {
                    "url": safe,
                    "final_url": final,
                    "title": "",
                    "text": "",
                    "error": f"HTTP {resp.status_code}",
                }
            ctype = (resp.headers.get("content-type") or "").lower()
            if "html" not in ctype and "text" not in ctype and ctype:
                return {
                    "url": safe,
                    "final_url": final,
                    "title": "",
                    "text": "",
                    "error": f"unsupported content-type: {ctype}",
                }
            body = resp.text[:500_000]
            title, text = _extract_text(body)
            return {
                "url": safe,
                "final_url": final,
                "title": title,
                "text": text,
                "error": None,
            }
    except ValueError:
        raise
    except Exception as exc:  # noqa: BLE001
        return {
            "url": safe,
            "final_url": safe,
            "title": "",
            "text": "",
            "error": str(exc)[:200],
        }


# ---------- Draft prompt / FAQ ----------

_VERTICAL_HINTS = (
    ("clean", "cleaning"),
    ("maid", "cleaning"),
    ("housekeep", "cleaning"),
    ("dental", "dental"),
    ("dentist", "dental"),
    ("tooth", "dental"),
    ("hvac", "hvac"),
    ("furnace", "hvac"),
    ("air condition", "hvac"),
    ("heating", "hvac"),
    ("salon", "salon"),
    ("hair", "salon"),
    ("spa", "salon"),
    ("nail", "salon"),
)


def _guess_vertical(text: str, notes: str) -> str:
    blob = f"{text} {notes}".lower()
    for needle, vert in _VERTICAL_HINTS:
        if needle in blob:
            return vert
    return "cleaning"


def _guess_brand_name(title: str, url: str, notes: str) -> str:
    if notes:
        # First line or first 60 chars of notes as optional name hint
        first = notes.strip().split("\n")[0].strip()
        if first.lower().startswith("name:"):
            return first.split(":", 1)[1].strip()[:80] or title or "Brand"
    if title:
        # Strip common suffixes
        name = re.split(r"\s*[|\-–—:]\s*", title)[0].strip()
        return name[:80] or "Brand"
    host = urlparse(url).hostname or "brand"
    return host.split(".")[0].replace("-", " ").title()[:80]


def _pick_sentences(text: str, limit: int = 8) -> list[str]:
    if not text:
        return []
    chunks = re.split(r"(?<=[.!?])\s+", text)
    out: list[str] = []
    for c in chunks:
        c = c.strip()
        if len(c) < 40 or len(c) > 280:
            continue
        # Prefer sentences that look like facts / offers
        low = c.lower()
        if any(
            k in low
            for k in (
                "we ",
                "our ",
                "offer",
                "serv",
                "call",
                "book",
                "hour",
                "price",
                "contact",
                "located",
                "provid",
            )
        ):
            out.append(c)
        if len(out) >= limit:
            break
    if not out:
        # fallback: first non-trivial chunks
        for c in chunks:
            c = c.strip()
            if 40 <= len(c) <= 220:
                out.append(c)
            if len(out) >= limit:
                break
    return out[:limit]


def build_brand_draft(
    *,
    website_url: str,
    brand_notes: str = "",
    site: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Deterministic draft bot materials from site text + notes."""
    site = site or {}
    title = site.get("title") or ""
    text = site.get("text") or ""
    url = site.get("final_url") or site.get("url") or website_url
    name = _guess_brand_name(title, url, brand_notes)
    vertical = _guess_vertical(text, brand_notes)
    facts = _pick_sentences(text, limit=8)

    notes_clean = (brand_notes or "").strip()
    faq: list[dict[str, str]] = []
    if facts:
        faq.append(
            {
                "question": f"What does {name} do?",
                "answer": facts[0],
            }
        )
    if len(facts) > 1:
        faq.append({"question": "What should I know before booking?", "answer": facts[1]})
    if notes_clean:
        faq.append(
            {
                "question": "Brand notes from the operator",
                "answer": notes_clean[:500],
            }
        )
    if not faq:
        faq.append(
            {
                "question": f"Tell me about {name}",
                "answer": (
                    f"{name} helps customers with {vertical} needs. "
                    "Share approved FAQ facts only; escalate when unsure."
                ),
            }
        )

    fact_block = "\n".join(f"- {f}" for f in facts[:6]) or "- (Add approved FAQ facts here.)"
    notes_block = notes_clean[:800] if notes_clean else "(none provided)"

    prompt = f"""[DRAFT — generated by DocketAI brand builder; review before production use]

You are the website assistant for {name}.
Website: {url}
Vertical: {vertical}

PRIMARY GOAL: help visitors with accurate answers from the approved FAQ, then guide them
to book, request a quote, or reach a human when needed.

Tone: warm, professional, concise. Never invent prices, hours, guarantees, or policies.

Approved facts (draft-extracted from the public site — verify before shipping):
{fact_block}

Operator notes:
{notes_block}

Rules:
1. Answer only from approved FAQ / notes. If unsure, say you will confirm with the team.
2. When the visitor wants a human, frustrated, or medical/legal issues — offer a warm handoff.
3. Never promise discounts or timelines that are not in the policy sheet.
4. When booking intent is clear, collect name + contact and point them to the booking path.
"""

    script = [
        f"Hi — I'm the {name} assistant. Ask about services, hours, or booking and I'll help.",
    ]

    bot_id = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40] or "brand-bot"
    if not bot_id.startswith("brand-"):
        bot_id = f"brand-{bot_id}"

    return {
        "draft": True,
        "label": "draft",
        "name": name,
        "vertical": vertical,
        "bot_id_suggestion": bot_id,
        "prompt": prompt.strip(),
        "faq": faq,
        "script": script,
        "source": {
            "website_url": url,
            "page_title": title,
            "fetch_error": site.get("error"),
            "text_chars": len(text or ""),
        },
    }
