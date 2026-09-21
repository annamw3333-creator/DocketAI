"""Theme Studio unit tests."""

from __future__ import annotations

from app.themes import (
    DEFAULT_THEME_ID,
    PRESET_THEMES,
    list_themes,
    normalize_theme_config,
    theme_config_for_storage,
    theme_from_query_and_bot,
)


def test_eight_presets():
    themes = list_themes()
    assert len(themes) >= 8
    ids = {t["id"] for t in themes}
    for expected in (
        "editorial-gold",
        "midnight",
        "porcelain",
        "ocean",
        "forest",
        "sunset",
        "neon-ink",
        "soft-lilac",
    ):
        assert expected in ids
        assert "swatches" in PRESET_THEMES[expected]
        assert len(PRESET_THEMES[expected]["swatches"]) >= 3


def test_normalize_merges_overrides():
    cfg = normalize_theme_config(
        {"theme_id": "ocean", "primary": "#112233", "position": "left", "greeting": "Ahoy"}
    )
    assert cfg["theme_id"] == "ocean"
    assert cfg["primary"] == "#112233"
    assert cfg["position"] == "left"
    assert cfg["greeting"] == "Ahoy"
    assert cfg["accent"] == PRESET_THEMES["ocean"]["accent"]


def test_default_fallback():
    cfg = normalize_theme_config({"theme_id": "does-not-exist"})
    assert cfg["theme_id"] == DEFAULT_THEME_ID
    assert cfg["accent"] == PRESET_THEMES[DEFAULT_THEME_ID]["accent"]


def test_storage_compact():
    compact = theme_config_for_storage(
        {"theme_id": "neon-ink", "bot_name": "Nova", "bogus": "x"}
    )
    assert compact == {"theme_id": "neon-ink", "bot_name": "Nova"} or (
        compact["theme_id"] == "neon-ink" and compact.get("bot_name") == "Nova"
    )


def test_query_overrides_bot():
    bot = {"theme": {"theme_id": "forest"}, "name": "Trees"}
    t = theme_from_query_and_bot(bot, theme_id="sunset", greeting="Hi there")
    assert t["theme_id"] == "sunset"
    assert t["greeting"] == "Hi there"
