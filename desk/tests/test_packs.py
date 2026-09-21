"""Expanded mystery-shop packs stay tagged, multi-turn, and lens-filterable."""

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

# Original IDs from the 16-scenario expansion that tests/docs may reference
_ORIGINAL_IDS = {
    "cleaning": {
        "price_inquiry",
        "booking",
        "handoff_complaint",
        "policy_pets",
        "cancel_window",
        "refund_missed",
        "complaint_quality",
        "escalate_manager",
        "policy_supplies",
        "payment_card",
        "incomplete_booking",
        "mid_change_service",
        "price_add_ons",
        "book_recurring",
        "cancel_same_day",
        "payment_dispute",
    },
    "dental": {
        "new_patient",
        "book_hygiene",
        "handoff_pain",
        "insurance_policy",
        "price_cleaning",
        "cancel_appointment",
        "refund_overcharge",
        "complaint_wait",
        "escalate_billing",
        "policy_xray",
        "payment_plans",
        "incomplete_book",
        "mid_change_visit",
        "price_whitening",
        "book_new_patient_exam",
        "cancel_same_day_fee",
    },
    "hvac": {
        "no_heat",
        "tuneup_price",
        "book_maintenance",
        "warranty_policy",
        "cancel_service",
        "refund_diagnostic",
        "complaint_no_show",
        "escalate_dispatch",
        "policy_after_hours",
        "payment_financing",
        "incomplete_dispatch",
        "mid_change_job",
        "price_furnace_install",
        "book_ac_repair",
        "cancel_same_day",
        "payment_invoice",
    },
    "salon": {
        "color_price",
        "book_appointment",
        "handoff_allergic",
        "cancel_policy",
        "cancel_appointment",
        "refund_bad_cut",
        "complaint_stylist",
        "escalate_front_desk",
        "policy_patch_test",
        "payment_deposit",
        "incomplete_book",
        "mid_change_service",
        "price_extensions",
        "book_color_correction",
        "refund_no_show_fee",
        "payment_split",
    },
}


def test_all_packs_substantially_expanded():
    packs = load_all_packs()
    assert set(list_pack_ids()) == {"cleaning", "dental", "hvac", "salon"}
    for pack in packs:
        scenarios = pack["scenarios"]
        assert len(scenarios) >= 20, f"{pack['id']} too small: {len(scenarios)}"
        ids = [sc["id"] for sc in scenarios]
        assert len(ids) == len(set(ids)), f"duplicate ids in {pack['id']}"
        blob = " ".join(f"{sc['id']} {sc.get('name', '')}" for sc in scenarios).lower()
        for theme in _REQUIRED_THEMES:
            assert theme in blob, f"{pack['id']} missing theme {theme!r}"
        # Keep original IDs
        missing = _ORIGINAL_IDS[pack["id"]] - set(ids)
        assert not missing, f"{pack['id']} lost original ids: {missing}"


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


def test_packs_are_multi_turn_and_rich():
    """Deeper packs: many 3+ turn scenarios with failure criteria / suggested fixes."""
    for pack in load_all_packs():
        scenarios = pack["scenarios"]
        multi = [sc for sc in scenarios if len(sc.get("steps") or []) >= 2]
        deep = [sc for sc in scenarios if len(sc.get("steps") or []) >= 3]
        rich = [
            sc
            for sc in scenarios
            if sc.get("suggested_fixes") or sc.get("failure_criteria") or sc.get("policy_refs")
        ]
        assert len(multi) >= 12, f"{pack['id']} needs more multi-turn scenarios"
        assert len(deep) >= 6, f"{pack['id']} needs more 3+ turn depth"
        assert len(rich) >= 12, f"{pack['id']} needs richer metadata fields"
        # Spot-check severity on a high-stakes scenario
        highs = [sc for sc in scenarios if sc.get("severity") == "high"]
        assert highs, f"{pack['id']} should mark some high-severity scenarios"


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
    # Rewrites applied on first turn only; later turns kept
    for sc in shaped["scenarios"]:
        if str(sc["id"]).startswith("lens_"):
            continue
        user = sc["steps"][0]["user"].lower()
        assert "competitor" in user or "price" in user or "?" in user
        if len(sc["steps"]) > 1:
            # Subsequent turns should still be present (not stripped by lens)
            assert sc["steps"][1].get("user")


def test_new_scenarios_score_with_expected_keys():
    """Scoring accepts expected shapes used by new pack scenarios."""
    faq = [{"question": "cancel", "answer": "Cancellations need 24 hours notice."}]
    scores = score_turn(
        "What's the cancellation policy?",
        "Happy to help — cancellations need 24 hours notice.",
        {
            "policy_phrase": "24 hours",
            "must_include": ["cancel"],
            "must_avoid": ["no cancellations ever"],
        },
        faq,
    )
    assert scores["policy_adherence"] >= 70
    assert scores["truthfulness"] >= 50


def test_multi_turn_scenario_scores_all_steps():
    bot = {
        "id": "test-bot",
        "name": "Test",
        "faq": [
            {"question": "deep clean", "answer": "A deep clean for a 3-bedroom starts around $250."},
            {"question": "pets", "answer": "We are pet-friendly and use eco-friendly supplies."},
            {"question": "cancel", "answer": "Please give 24 hours notice to cancel."},
            {"question": "deposit", "answer": "A deposit and card on file are required to book."},
        ],
        "script": ["Thanks for reaching out — happy to help."],
        "prompt": "",
    }
    pack = load_pack("cleaning")
    # Run a single deep scenario by filtering pack
    handoff = next(sc for sc in pack["scenarios"] if sc["id"] == "handoff_complaint")
    mini = {**pack, "scenarios": [handoff]}
    result = run_pack_on_bot(bot, mini)
    assert result["scenario_count"] == 1
    sc_out = result["scenarios"][0]
    assert sc_out["turn_count"] >= 3
    assert len(sc_out["turns"]) == sc_out["turn_count"]
    assert sc_out.get("suggested_fixes")
    assert sc_out.get("policy_refs") or handoff.get("policy_refs")
    # Transcript includes every turn
    assert len(result["transcript"]) == sc_out["turn_count"]


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
    # At least one selected scenario should be multi-turn in the shaped run
    assert any(sc.get("turn_count", 1) >= 2 for sc in result["scenarios"])
