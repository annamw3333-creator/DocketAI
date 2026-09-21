from __future__ import annotations

import re
from typing import Any

from .scoring import (
    DIMENSIONS,
    aggregate_scores,
    diff_vs_faq_script,
    score_turn,
    suggest_prompt_patches,
)

# Bots that convert via forms/text — never confirm appointments in chat
NO_DIRECT_BOOK_IDS = frozenset({"haven-abodes"})


def _pick_faq_answer(user: str, faq: list[dict[str, str]]) -> str:
    u = user.lower()
    best = ("", 0)
    for item in faq:
        q = (item.get("question") or "").lower()
        a = item.get("answer") or ""
        score = sum(1 for w in re.findall(r"[a-z0-9]+", q) if w in u)
        if score > best[1]:
            best = (a, score)
    return best[0]


def _no_direct_book(bot: dict[str, Any]) -> bool:
    bid = (bot.get("id") or "").lower()
    if bid in NO_DIRECT_BOOK_IDS:
        return True
    prompt = (bot.get("prompt") or "").lower()
    return "do not directly book" in prompt or "never directly book" in prompt


def simulate_reply(user: str, bot: dict[str, Any], expected: dict[str, Any] | None = None) -> str:
    """Deterministic stub reply for local mystery-shop without an LLM."""
    expected = expected or {}
    faq = bot.get("faq") or []
    script = bot.get("script") or []
    base = _pick_faq_answer(user, faq)
    parts: list[str] = []

    u_low = user.lower()
    money_conflict = any(
        k in u_low for k in ("refund", "discount", "coupon", "promo", "% off", "percent off")
    )
    wants_human = any(
        k in u_low
        for k in (
            "real person",
            "human",
            "manager",
            "speak to someone",
            "talk to someone",
            "furious",
            "ridiculous",
            "cancel",
            "damaged",
        )
    ) or money_conflict

    if expected.get("expect_escalation"):
        parts.append(
            "I'm sorry you're dealing with this. I can transfer you to a human specialist "
            "— please text or call so a manager can follow up. What's the best number?"
        )
    elif money_conflict and not expected.get("expect_booking"):
        parts.append(
            "I'm sorry you're dealing with this. I can connect you with a human via text "
            "or email — refunds and discounts aren't something I can approve here. "
            "What's the best number?"
        )
    elif wants_human and not expected.get("expect_booking"):
        parts.append(
            "Of course — I'm glad to connect you with a human. Please text or call "
            "825-521-3311 or email hello@aestheticabodes.ca. What's the best number?"
        )

    if expected.get("expect_booking"):
        name_m = re.search(
            r"(?:i'?m|name is|contact)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", user, re.I
        )
        name = name_m.group(1) if name_m else "you"
        day_m = re.search(
            r"(Saturday|Sunday|Monday|Tuesday|Wednesday|Thursday|Friday)", user, re.I
        )
        day = day_m.group(1) if day_m else "the requested time"
        if _no_direct_book(bot):
            parts.append(
                f"I'd be happy to help {name} get {day} set up — I can't complete or confirm "
                f"bookings here in chat. Please finish on https://aestheticabodes.ca/booking/ "
                f"so our team can confirm details, or text 825-521-3311."
            )
        else:
            parts.append(
                f"Confirmed — I've booked the appointment for {name} on {day}. "
                "You'll get a confirmation shortly."
            )

    if base:
        # Avoid stacking a conflicting "I've booked" FAQ on no-direct-book bots
        if _no_direct_book(bot) and expected.get("expect_booking"):
            # Prefer conversion CTA already added; still append FAQ if it steers to forms
            if "booking" in base.lower() or "quote" in base.lower():
                parts.append(base)
        else:
            parts.append(base)
    elif script:
        parts.append(script[0])
    else:
        parts.append("Thanks for reaching out — how else can I help?")

    phrase = expected.get("policy_phrase")
    if phrase and phrase.lower() not in " ".join(parts).lower():
        parts.append(f"Per our policy: {phrase}.")

    for kw in expected.get("must_include") or []:
        if kw.lower() not in " ".join(parts).lower():
            parts.append(f"Regarding {kw}: our team can help with that.")

    return " ".join(parts)


def _scenario_verdict(
    scores: dict[str, float],
    expected: dict[str, Any],
) -> dict[str, Any]:
    """Pass/fail + severity + reasons for one scenario."""
    reasons: list[str] = []
    fail_dims: list[str] = []
    for d in DIMENSIONS:
        v = float(scores.get(d, 0) or 0)
        if v < 50:
            fail_dims.append(d)
            reasons.append(f"{d} critically low ({v:.0f})")
        elif v < 70:
            reasons.append(f"{d} needs work ({v:.0f})")

    if expected.get("expect_escalation") and scores.get("escalation", 0) < 50:
        if "missed escalation" not in " ".join(reasons):
            reasons.insert(0, "missed expected escalation / human handoff")
    if expected.get("expect_booking") and scores.get("booking_success", 0) < 50:
        if "booking" not in " ".join(reasons).lower():
            reasons.insert(0, "missed booking / conversion path")
    if expected.get("must_include"):
        # truthfulness already encodes keyword hits
        if scores.get("truthfulness", 100) < 70:
            reasons.append("missing expected keywords from approved answer")

    overall = float(scores.get("overall") or 0)
    if not overall and scores:
        vals = [float(scores.get(d, 0) or 0) for d in DIMENSIONS]
        overall = sum(vals) / max(len(vals), 1)

    passed = overall >= 70 and not any(
        float(scores.get(d, 100) or 0) < 50 for d in DIMENSIONS
    )
    # severity: high if critical miss, medium if soft fail, low if pass with notes, none if clean pass
    if any(float(scores.get(d, 100) or 0) < 50 for d in DIMENSIONS):
        severity = "high"
    elif not passed:
        severity = "medium"
    elif reasons:
        severity = "low"
    else:
        severity = "none"
        reasons = ["All dimensions at target."]

    suggested_fixes: list[str] = []
    if not passed or severity in ("high", "medium"):
        if expected.get("expect_escalation"):
            suggested_fixes.append(
                "When guest is upset or asks for a human, offer a warm handoff and collect a callback number."
            )
        if expected.get("expect_booking"):
            suggested_fixes.append(
                "On clear booking intent, confirm service/time and either schedule or send the booking form link."
            )
        if scores.get("truthfulness", 100) < 70:
            suggested_fixes.append("Answer only from approved FAQ; do not invent prices or hours.")
        if scores.get("policy_adherence", 100) < 70:
            suggested_fixes.append("Quote the policy phrase; never promise unapproved discounts.")
        if scores.get("tone", 100) < 70:
            suggested_fixes.append("Lead with brief empathy, then a clear next step.")

    # de-dupe
    seen: set[str] = set()
    fixes_out: list[str] = []
    for f in suggested_fixes:
        if f not in seen:
            seen.add(f)
            fixes_out.append(f)

    return {
        "passed": passed,
        "severity": severity,
        "reasons": reasons[:6],
        "suggested_fixes": fixes_out[:4],
        "overall": round(overall, 1),
    }


def run_pack_on_bot(
    bot: dict[str, Any],
    pack: dict[str, Any],
    replies: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Run all scenarios. Optional replies map scenario_id -> assistant text
    (for testing external bots). Otherwise uses simulate_reply.
    """
    replies = replies or {}
    transcript: list[dict[str, str]] = []
    step_scores: list[dict[str, float]] = []
    scenarios_out: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    for sc in pack.get("scenarios") or []:
        steps = sc.get("steps") or []
        if not steps:
            continue
        step = steps[0]
        user = step.get("user", "")
        expected = step.get("expected") or {}
        if sc["id"] in replies:
            asst = replies[sc["id"]]
        else:
            asst = simulate_reply(user, bot, expected)
        scores = score_turn(user, asst, expected, bot.get("faq") or [])
        # per-scenario overall
        scores = {
            **scores,
            "overall": round(sum(scores[d] for d in DIMENSIONS) / len(DIMENSIONS), 1),
        }
        step_scores.append(scores)
        turn = {"user": user, "assistant": asst, "scenario_id": sc["id"]}
        transcript.append(turn)
        verdict = _scenario_verdict(scores, expected)
        scenarios_out.append(
            {
                "scenario_id": sc["id"],
                "name": sc.get("name"),
                "scores": scores,
                "user": user,
                "assistant": asst,
                "passed": verdict["passed"],
                "severity": verdict["severity"],
                "reasons": verdict["reasons"],
                "suggested_fixes": verdict["suggested_fixes"],
                "overall": verdict["overall"],
            }
        )
        # lightweight failure flags
        if expected.get("expect_escalation") and scores.get("escalation", 0) < 50:
            failures.append({"scenario_id": sc["id"], "reason": "missed escalation"})
        if expected.get("expect_booking") and scores.get("booking_success", 0) < 50:
            failures.append({"scenario_id": sc["id"], "reason": "missed booking conversion"})
        if not verdict["passed"] and verdict["severity"] == "high":
            for r in verdict["reasons"][:1]:
                if not any(f.get("reason") == r for f in failures):
                    failures.append({"scenario_id": sc["id"], "reason": r})

    scores = aggregate_scores(step_scores)
    diff = diff_vs_faq_script(transcript, bot.get("faq") or [], bot.get("script") or [])
    patches = suggest_prompt_patches(scores, diff, failures)
    return {
        "bot_id": bot["id"],
        "pack_id": pack["id"],
        "scores": scores,
        "transcript": transcript,
        "scenarios": scenarios_out,
        "diff": diff,
        "patches": patches,
        "failures": failures,
    }
