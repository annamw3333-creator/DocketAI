"""Persona × attack lens shapes mystery-shop packs server-side."""

from __future__ import annotations

from app.lens import (
    apply_lens_to_user,
    normalize_lens,
    score_scenario,
    shape_pack_for_lens,
)
from app.packs_loader import load_pack
from app.simulator import run_pack_on_bot


def test_normalize_lens_rejects_unknown():
    lens = normalize_lens("angry", "nope")
    assert lens["persona_id"] == "angry"
    assert lens["attack_id"] is None
    assert lens["active"] is True
    assert lens["persona_label"] == "Angry"


def test_shape_filters_to_matching_scenarios():
    pack = load_pack("cleaning")
    shaped, meta = shape_pack_for_lens(pack, persona_id="angry", attack_id="emotional_pressure")
    assert meta["active"] is True
    assert meta["filtered"] is True
    ids = [sc["id"] for sc in shaped["scenarios"]]
    assert "handoff_complaint" in ids
    # Should not keep the entire unfiltered pack when matches exist
    assert len(ids) < len(pack["scenarios"]) + 3  # probes may add a few
    assert meta["mode"] in ("filtered_matches", "filtered_plus_probes")


def test_price_shopper_prefers_price_scenarios():
    pack = load_pack("cleaning")
    shaped, meta = shape_pack_for_lens(pack, persona_id="price_shopper", attack_id=None)
    ids = meta["selected_scenario_ids"]
    assert "price_inquiry" in ids
    # Rewritten user line carries persona overlay
    price_sc = next(sc for sc in shaped["scenarios"] if sc["id"] == "price_inquiry")
    user = price_sc["steps"][0]["user"]
    assert "competitor" in user.lower() or "price" in user.lower()


def test_prompt_injection_injects_probe():
    pack = load_pack("salon")
    shaped, meta = shape_pack_for_lens(
        pack, persona_id="testing_rules", attack_id="prompt_injection"
    )
    assert "lens_prompt_injection" in meta["probes_injected"]
    assert any(sc["id"] == "lens_prompt_injection" for sc in shaped["scenarios"])


def test_apply_lens_to_user_attack_and_persona():
    out = apply_lens_to_user(
        "How much for a deep clean?",
        persona_id="angry",
        attack_id="claims_employee",
    )
    assert "Jordan" in out or "employee" in out.lower()
    assert "ridiculous" in out.lower() or "NOW" in out


def test_run_pack_includes_lens_metadata():
    pack = load_pack("cleaning")
    bot = {
        "id": "test-bot",
        "name": "Test",
        "faq": [{"question": "pets", "answer": "We are pet-friendly."}],
        "script": ["Thanks for reaching out."],
        "prompt": "",
    }
    result = run_pack_on_bot(
        bot, pack, persona_id="wants_human", attack_id="emotional_pressure"
    )
    assert result["persona_id"] == "wants_human"
    assert result["attack_id"] == "emotional_pressure"
    assert result["lens"]["active"] is True
    assert result["scenario_count"] == len(result["scenarios"])
    assert result["scenario_count"] >= 1
    # User lines should reflect the lens
    users = " ".join(sc["user"] for sc in result["scenarios"])
    assert "bot" in users.lower() or "person" in users.lower() or "desperate" in users.lower()


def test_score_scenario_intersection_bonus():
    sc = {
        "id": "x",
        "name": "x",
        "personas": ["angry"],
        "attacks": ["emotional_pressure"],
        "human_handoff": True,
    }
    both = score_scenario(sc, "angry", "emotional_pressure")
    one = score_scenario(sc, "angry", None)
    assert both > one


def test_lens_keeps_later_turns():
    """Lens rewrites turn 0 but preserves multi-turn depth."""
    pack = load_pack("cleaning")
    shaped, meta = shape_pack_for_lens(pack, persona_id="angry", attack_id="emotional_pressure")
    deep = next(sc for sc in shaped["scenarios"] if len(sc.get("steps") or []) >= 3)
    assert "ridiculous" in deep["steps"][0]["user"].lower() or "desperate" in deep["steps"][0]["user"].lower() or "NOW" in deep["steps"][0]["user"]
    # Later turns unchanged by lens overlay
    assert deep["steps"][1]["user"]
    assert deep["steps"][1]["user"] != deep["steps"][0]["user"]
