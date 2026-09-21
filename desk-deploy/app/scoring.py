from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any


DIMENSIONS = (
    "truthfulness",
    "escalation",
    "policy_adherence",
    "tone",
    "booking_success",
)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def _contains_any(text: str, needles: list[str]) -> bool:
    t = _norm(text)
    return any(_norm(n) in t for n in needles if n)


def _forbid_list(expected: dict[str, Any]) -> list[str]:
    """Support must_not_include and must_avoid aliases."""
    out: list[str] = []
    for key in ("must_not_include", "must_avoid"):
        vals = expected.get(key) or []
        if isinstance(vals, str):
            vals = [vals]
        out.extend(str(v) for v in vals if v)
    # de-dupe preserve order
    seen: set[str] = set()
    uniq: list[str] = []
    for v in out:
        k = v.lower()
        if k not in seen:
            seen.add(k)
            uniq.append(v)
    return uniq


def score_turn(
    user: str,
    assistant: str,
    expected: dict[str, Any],
    faq: list[dict[str, str]],
) -> dict[str, float]:
    """Heuristic mystery-shop scores 0–100 for a single turn / scenario step."""
    asst = assistant or ""
    expect_keywords = expected.get("must_include") or []
    forbid = _forbid_list(expected)
    escalate = bool(expected.get("expect_escalation"))
    booking = bool(expected.get("expect_booking"))
    tone_words = expected.get("tone_positive") or ["please", "happy", "glad", "help", "thank"]

    # Truthfulness: overlap with FAQ answers or expected keywords
    faq_blob = " ".join(f.get("answer", "") for f in faq)
    truth = 50.0
    if expect_keywords:
        hits = sum(1 for k in expect_keywords if _contains_any(asst, [k]))
        truth = 100.0 * hits / max(len(expect_keywords), 1)
    elif faq:
        ratio = SequenceMatcher(None, _norm(asst), _norm(faq_blob)).ratio()
        truth = min(100.0, 40.0 + ratio * 80.0)
    if _contains_any(asst, forbid):
        truth = max(0.0, truth - 40.0)

    # Escalation
    escalate_cues = ["transfer", "human", "agent", "specialist", "call you", "manager", "escalate"]
    did_escalate = _contains_any(asst, escalate_cues)
    if escalate:
        escalation = 100.0 if did_escalate else 20.0
    else:
        escalation = 40.0 if did_escalate else 90.0

    # Policy adherence
    policy = 90.0
    if forbid and _contains_any(asst, forbid):
        policy = 15.0
    if expected.get("policy_phrase") and not _contains_any(asst, [expected["policy_phrase"]]):
        policy = min(policy, 45.0)

    # Tone
    tone_hits = sum(1 for w in tone_words if _contains_any(asst, [w]))
    rude = _contains_any(asst, ["stupid", "idiot", "shut up", "whatever"])
    tone = min(100.0, 55.0 + tone_hits * 12.0)
    if rude:
        tone = 10.0

    # Booking success (direct confirm OR conversion CTA to booking/quote forms)
    book_cues = ["booked", "scheduled", "appointment", "confirmed", "reservation", "calendar"]
    conversion_cues = [
        "booking/",
        "book online",
        "booking form",
        "quote form",
        "instant-free-quote",
        "aestheticabodes.ca/booking",
        "finish on https",
        "complete the booking",
        "complete on",
    ]
    did_book = _contains_any(asst, book_cues)
    did_convert = _contains_any(asst, conversion_cues)
    if booking:
        booking_success = 100.0 if (did_book or did_convert) else 25.0
    else:
        # Soft penalty only for hard "you're booked" style confirms outside booking turns
        hard_confirm = _contains_any(asst, ["i've booked", "you're booked", "appointment is scheduled"])
        booking_success = 85.0 if not hard_confirm else 70.0

    return {
        "truthfulness": round(truth, 1),
        "escalation": round(escalation, 1),
        "policy_adherence": round(policy, 1),
        "tone": round(tone, 1),
        "booking_success": round(booking_success, 1),
    }


def aggregate_scores(per_step: list[dict[str, float]]) -> dict[str, float]:
    if not per_step:
        return {d: 0.0 for d in DIMENSIONS}
    out: dict[str, float] = {}
    for d in DIMENSIONS:
        vals = [s[d] for s in per_step if d in s]
        out[d] = round(sum(vals) / max(len(vals), 1), 1)
    out["overall"] = round(sum(out[d] for d in DIMENSIONS) / len(DIMENSIONS), 1)
    return out


def diff_vs_faq_script(
    transcript: list[dict[str, str]],
    faq: list[dict[str, str]],
    script: list[str],
) -> dict[str, Any]:
    """Compare assistant replies to approved FAQ/script lines."""
    assistant_lines = [t.get("assistant", "") for t in transcript if t.get("assistant")]
    faq_answers = [f.get("answer", "") for f in faq]
    mismatches: list[dict[str, Any]] = []
    best_matches: list[dict[str, Any]] = []

    for i, line in enumerate(assistant_lines):
        best_faq = max(
            ((SequenceMatcher(None, _norm(line), _norm(a)).ratio(), a) for a in faq_answers),
            default=(0.0, ""),
            key=lambda x: x[0],
        )
        best_script = max(
            ((SequenceMatcher(None, _norm(line), _norm(s)).ratio(), s) for s in script),
            default=(0.0, ""),
            key=lambda x: x[0],
        )
        entry = {
            "turn": i,
            "reply": line,
            "faq_similarity": round(best_faq[0], 3),
            "nearest_faq": best_faq[1][:200],
            "script_similarity": round(best_script[0], 3),
            "nearest_script": best_script[1][:200],
        }
        best_matches.append(entry)
        if best_faq[0] < 0.35 and best_script[0] < 0.35:
            mismatches.append(entry)

    return {
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "matches": best_matches,
    }


def suggest_prompt_patches(
    scores: dict[str, float],
    diff: dict[str, Any],
    failures: list[dict[str, Any]],
) -> list[str]:
    patches: list[str] = []
    if scores.get("truthfulness", 100) < 70:
        patches.append(
            "Add: Always answer from the approved FAQ. If unsure, say you will confirm with the team rather than inventing prices or hours."
        )
    if scores.get("escalation", 100) < 70:
        patches.append(
            "Add: When the guest asks for a human, frustrated, or medical/legal issues, offer a warm handoff and collect callback details."
        )
    if scores.get("policy_adherence", 100) < 70:
        patches.append(
            "Add: Never promise discounts, guarantees, or timelines that are not in the policy sheet. Quote the policy phrase when relevant."
        )
    if scores.get("tone", 100) < 70:
        patches.append(
            "Add: Keep a warm, professional tone. Use brief empathy then a clear next step. Avoid sarcasm."
        )
    if scores.get("booking_success", 100) < 70:
        patches.append(
            "Add: When booking intent is clear, confirm service, time window, name, and phone, then state the appointment is scheduled."
        )
    for m in (diff.get("mismatches") or [])[:3]:
        patches.append(
            f"Align turn {m.get('turn')} reply closer to approved line: \"{(m.get('nearest_faq') or m.get('nearest_script') or '')[:120]}\""
        )
    for f in failures[:3]:
        if f.get("reason"):
            patches.append(f"Fix failure: {f['reason']}")
    # de-dupe preserve order
    seen: set[str] = set()
    out: list[str] = []
    for p in patches:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out
