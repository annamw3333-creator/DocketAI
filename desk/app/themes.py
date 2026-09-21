"""Customer-facing widget theme presets (Theme Studio).

Themes style the embeddable chat widget only — not the DocketAI app chrome.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

# Default Docket look
DEFAULT_THEME_ID = "editorial-gold"

PRESET_THEMES: dict[str, dict[str, Any]] = {
    "editorial-gold": {
        "id": "editorial-gold",
        "name": "Editorial Gold",
        "description": "Black / white / gold — Docket default. Crisp editorial.",
        "vibe": "editorial",
        "primary": "#161513",
        "accent": "#C9A227",
        "bg": "#ECEAE4",
        "text": "#161513",
        "header_text": "#ECEAE4",
        "bot_bubble": "#DDD6C8",
        "user_bubble": "#FFFFFF",
        "launcher_bg": "#161513",
        "launcher_text": "#ECEAE4",
        "position": "right",
        "avatar_style": "monogram",
        "swatches": ["#161513", "#ECEAE4", "#C9A227", "#DDD6C8"],
    },
    "midnight": {
        "id": "midnight",
        "name": "Midnight",
        "description": "Deep navy panel with electric cyan accents. Night-mode polish.",
        "vibe": "dark",
        "primary": "#0B1220",
        "accent": "#38BDF8",
        "bg": "#0F172A",
        "text": "#E2E8F0",
        "header_text": "#F8FAFC",
        "bot_bubble": "#1E293B",
        "user_bubble": "#334155",
        "launcher_bg": "#38BDF8",
        "launcher_text": "#0B1220",
        "position": "right",
        "avatar_style": "dot",
        "swatches": ["#0B1220", "#0F172A", "#38BDF8", "#1E293B"],
    },
    "porcelain": {
        "id": "porcelain",
        "name": "Porcelain",
        "description": "Light minimal — soft white, charcoal type, blush accent.",
        "vibe": "light",
        "primary": "#FAFAF9",
        "accent": "#E11D48",
        "bg": "#FFFFFF",
        "text": "#1C1917",
        "header_text": "#1C1917",
        "bot_bubble": "#F5F5F4",
        "user_bubble": "#FFE4E6",
        "launcher_bg": "#1C1917",
        "launcher_text": "#FAFAF9",
        "position": "right",
        "avatar_style": "initials",
        "swatches": ["#FFFFFF", "#1C1917", "#E11D48", "#F5F5F4"],
    },
    "ocean": {
        "id": "ocean",
        "name": "Ocean",
        "description": "Teal seas and foam — calm hospitality / travel feel.",
        "vibe": "fresh",
        "primary": "#0F766E",
        "accent": "#2DD4BF",
        "bg": "#F0FDFA",
        "text": "#134E4A",
        "header_text": "#F0FDFA",
        "bot_bubble": "#CCFBF1",
        "user_bubble": "#FFFFFF",
        "launcher_bg": "#0F766E",
        "launcher_text": "#F0FDFA",
        "position": "right",
        "avatar_style": "monogram",
        "swatches": ["#0F766E", "#F0FDFA", "#2DD4BF", "#CCFBF1"],
    },
    "forest": {
        "id": "forest",
        "name": "Forest",
        "description": "Deep green canopy with warm cream text. Grounded & trustworthy.",
        "vibe": "natural",
        "primary": "#14532D",
        "accent": "#A3E635",
        "bg": "#ECFDF5",
        "text": "#052E16",
        "header_text": "#ECFDF5",
        "bot_bubble": "#D1FAE5",
        "user_bubble": "#FFFFFF",
        "launcher_bg": "#14532D",
        "launcher_text": "#ECFDF5",
        "position": "left",
        "avatar_style": "monogram",
        "swatches": ["#14532D", "#ECFDF5", "#A3E635", "#D1FAE5"],
    },
    "sunset": {
        "id": "sunset",
        "name": "Sunset",
        "description": "Warm coral-to-amber glow. Friendly retail / dining energy.",
        "vibe": "warm",
        "primary": "#9A3412",
        "accent": "#FB923C",
        "bg": "#FFF7ED",
        "text": "#7C2D12",
        "header_text": "#FFF7ED",
        "bot_bubble": "#FFEDD5",
        "user_bubble": "#FFFFFF",
        "launcher_bg": "#EA580C",
        "launcher_text": "#FFF7ED",
        "position": "right",
        "avatar_style": "dot",
        "swatches": ["#9A3412", "#FFF7ED", "#FB923C", "#FFEDD5"],
    },
    "neon-ink": {
        "id": "neon-ink",
        "name": "Neon Ink",
        "description": "Near-black canvas with magenta neon. Bold nightlife / creator brands.",
        "vibe": "neon",
        "primary": "#0A0A0A",
        "accent": "#F472B6",
        "bg": "#111111",
        "text": "#F5F5F5",
        "header_text": "#F5F5F5",
        "bot_bubble": "#1A1A1A",
        "user_bubble": "#2A0A1A",
        "launcher_bg": "#F472B6",
        "launcher_text": "#0A0A0A",
        "position": "right",
        "avatar_style": "dot",
        "swatches": ["#0A0A0A", "#111111", "#F472B6", "#1A1A1A"],
    },
    "soft-lilac": {
        "id": "soft-lilac",
        "name": "Soft Lilac",
        "description": "Lavender mist and violet type. Soft wellness / beauty vibe.",
        "vibe": "soft",
        "primary": "#5B21B6",
        "accent": "#C4B5FD",
        "bg": "#FAF5FF",
        "text": "#4C1D95",
        "header_text": "#FAF5FF",
        "bot_bubble": "#EDE9FE",
        "user_bubble": "#FFFFFF",
        "launcher_bg": "#7C3AED",
        "launcher_text": "#FAF5FF",
        "position": "left",
        "avatar_style": "initials",
        "swatches": ["#5B21B6", "#FAF5FF", "#C4B5FD", "#EDE9FE"],
    },
}

# Color / string keys that may be overridden on a bot
OVERRIDE_KEYS = (
    "primary",
    "accent",
    "bg",
    "text",
    "header_text",
    "bot_bubble",
    "user_bubble",
    "launcher_bg",
    "launcher_text",
    "position",
    "avatar_style",
    "bot_name",
    "greeting",
    "display_name",
)


def list_themes() -> list[dict[str, Any]]:
    return [deepcopy(t) for t in PRESET_THEMES.values()]


def get_preset(theme_id: str | None) -> dict[str, Any]:
    tid = (theme_id or DEFAULT_THEME_ID).strip() or DEFAULT_THEME_ID
    preset = PRESET_THEMES.get(tid) or PRESET_THEMES[DEFAULT_THEME_ID]
    return deepcopy(preset)


def normalize_theme_config(raw: dict[str, Any] | None) -> dict[str, Any]:
    """Merge a bot's stored theme config onto a preset. Always returns a full theme."""
    raw = raw or {}
    theme_id = raw.get("theme_id") or raw.get("id") or DEFAULT_THEME_ID
    base = get_preset(str(theme_id))
    out = deepcopy(base)
    out["theme_id"] = base["id"]
    for key in OVERRIDE_KEYS:
        val = raw.get(key)
        if val is None or val == "":
            continue
        if key in ("primary", "accent", "bg", "text", "header_text", "bot_bubble", "user_bubble", "launcher_bg", "launcher_text"):
            s = str(val).strip()
            if s.startswith("#") and len(s) in (4, 7, 9):
                out[key] = s
        elif key == "position":
            pos = str(val).strip().lower()
            if pos in ("left", "right"):
                out[key] = pos
        elif key == "avatar_style":
            style = str(val).strip().lower()
            if style in ("monogram", "dot", "initials", "none"):
                out[key] = style
        elif key in ("bot_name", "greeting", "display_name"):
            out[key] = str(val).strip()[:200]
    return out


def theme_from_query_and_bot(
    bot: dict[str, Any] | None,
    *,
    theme_id: str | None = None,
    primary: str | None = None,
    accent: str | None = None,
    bg: str | None = None,
    text: str | None = None,
    position: str | None = None,
    avatar_style: str | None = None,
    bot_name: str | None = None,
    greeting: str | None = None,
) -> dict[str, Any]:
    """Resolve theme for widget: compact bot.theme_config ← query overrides.

    Prefer theme_config (stored overrides only) so switching theme_id does not
    keep the previous preset's resolved colors.
    """
    bot = bot or {}
    stored = bot.get("theme_config")
    if not isinstance(stored, dict) or not stored:
        # Legacy / missing compact config — keep only non-color identity fields
        full = bot.get("theme") if isinstance(bot.get("theme"), dict) else {}
        stored = {}
        if full.get("theme_id") or full.get("id"):
            stored["theme_id"] = full.get("theme_id") or full.get("id")
        for key in ("bot_name", "display_name", "greeting", "position", "avatar_style"):
            if full.get(key):
                stored[key] = full[key]
    merged: dict[str, Any] = dict(stored)
    if theme_id:
        merged["theme_id"] = theme_id
        # Drop color overrides when switching preset via query so the new
        # preset's palette shows unless the caller also passes color params.
        color_keys = (
            "primary",
            "accent",
            "bg",
            "text",
            "header_text",
            "bot_bubble",
            "user_bubble",
            "launcher_bg",
            "launcher_text",
        )
        # Only drop if caller is not also overriding that color below
        pending = {
            "primary": primary,
            "accent": accent,
            "bg": bg,
            "text": text,
        }
        for ck in color_keys:
            if not pending.get(ck):
                merged.pop(ck, None)
    for k, v in {
        "primary": primary,
        "accent": accent,
        "bg": bg,
        "text": text,
        "position": position,
        "avatar_style": avatar_style,
        "bot_name": bot_name,
        "greeting": greeting,
    }.items():
        if v:
            merged[k] = v
    return normalize_theme_config(merged)


def theme_config_for_storage(body: dict[str, Any]) -> dict[str, Any]:
    """Persist only theme_id + overrides (compact)."""
    theme_id = str(body.get("theme_id") or body.get("id") or DEFAULT_THEME_ID).strip()
    if theme_id not in PRESET_THEMES:
        theme_id = DEFAULT_THEME_ID
    cfg: dict[str, Any] = {"theme_id": theme_id}
    for key in OVERRIDE_KEYS:
        if key in body and body[key] is not None and body[key] != "":
            cfg[key] = body[key]
    # Validate by normalizing
    normalize_theme_config(cfg)
    return cfg
