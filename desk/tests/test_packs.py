"""Expanded mystery-shop packs stay tagged and lens-filterable."""

from __future__ import annotations

from app.lens import ATTACKS, PERSONAS, shape_pack_for_lens
from app.packs_loader import list_pack_ids, load_all_packs, load_pack
from app.scoring import score_turn
from app.simulator import run_pack_on_bot

# Coverage themes the expanded packs should hit (by id/name substring)
_REQUIRED_THEMES = (
    "price",
    "book",
    "cancel",
    "refund",
    "complaint",
    "escalat",  # escalate / escalation
    "policy",
    "payment",
    "incomplete",
    "mid_change",
)


def test_all_packs_substantially_expanded():
    packs = load_all_packs()
    assert set(list_pack_ids()) == {"cleaning", "dental", "hvac", "salon"}
    for pack in packs:
        scenarios = pack["scenarios"]
        assert len(scenarios) >= 12, f"{pack['id']} too small: {len(scenarios)}"
        ids = [sc["id"] for sc in scenarios]
        assert len(ids) == len(set(ids)), f"duplicate ids in {pack['id']}"
        blob = " ".join(f"{sc['id']} {sc.get('name', '')}" for sc in scenarios).lower()
        for theme in _REQUIRED_THEMES:
            assert theme in blob, f"{pack['id']} missing theme {theme!r}"


def test_every_scenario_has_valid_persona_and_attack_tags():
    for pack in load_all_packs():
        for sc in pack["scenarios"]:
            personas = sc.get("personas") or []
            attacks = sc.get("attacks") or []
            assert personas, f"{pack['id']}/{sc['id']} missing personas"
            assert attacks, f"{pack['id']}/{sc['id']} missing attacks"
            for p in personas:
                assert p in PERSONAS, f"{pack['id']}/{sc['id']} bad persona {p}"
            for a in attacks:
                assert a in ATTACKS, f"{pack['id']}/{sc['id']} bad attack {a}"
            steps = sc.get("steps") or []
            assert steps and steps[0].get("user") and isinstance(steps[0].get("expected"), dict)


def test_lens_filter_prefers_tagged_intersection():
    pack = load_pack("salon")
    shaped, meta = shape_pack_for_lens(
        pack, persona_id="price_shopper", attack_id="incomplete_info"
    )
    assert meta["filtered"] is True
    assert meta["original_scenario_count"] == len(pack["scenarios"])
    assert meta["selected_scenario_count"] < meta["original_scenario_count"] + 3
    ids = meta["selected_scenario_ids"]
    assert "color_price" in ids or "price_extensions" in ids
    # Rewrites applied
    for sc in shaped["scenarios"]:
        if str(sc["id"]).startswith("lens_"):
            continue
        user = sc["steps"][0]["user"].lower()
        assert "competitor" in user or "price" in user or "?" in user


def test_new_scenarios_score_with_expected_keys():
    """Scoring accepts expected shapes used by new pack scenarios."""
    faq = [{"question": "cancel", "answer": "Cancellations need 24 hours notice."}]
    scores = score_turn(
        "What's the cancellation policy?",
        "Happy to help — cancellations need 24 hours notice.",
        {"policy_phrase": "24 hours", "must_include": ["cancel"], "must_not_include": ["no cancellations ever"]},
        faq,
    )
    assert scores["policy_adherence"] >= 70
    assert scores["truthfulness"] >= 50


def test_run_expanded_pack_under_lens():
    bot = {
        "id": "test-bot",
        "name": "Test",
        "faq": [
            {"question": "price", "answer": "A deep clean for a 3-bedroom starts around $250."},
            {"question": "pets", "answer": "We are pet-friendly and use eco-friendly supplies."},
            {"question": "cancel", "answer": "Please give 24 hours notice to cancel."},
        ],
        "script": ["Thanks for reaching out — happy to help."],
        "prompt": "",
    }
    pack = load_pack("cleaning")
    result = run_pack_on_bot(
        bot, pack, persona_id="confused", attack_id="changes_mid"
    )
    assert result["lens"]["active"] is True
    assert result["scenario_count"] >= 2
    assert result["scenario_count"] < len(pack["scenarios"]) + 3
    assert "scores" in result
    assert result["scores"]["overall"] > 0
