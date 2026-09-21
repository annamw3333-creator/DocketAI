"""DocketAI subscription tier entitlements.

-1 means unlimited for numeric caps.
Tier definitions are the source of truth for Desk gates, Stripe product
metadata (via create_stripe_catalog.py), and the mobile Plans UI.
"""
from __future__ import annotations

from typing import Any

FOUNDING_LIMIT = 10

# Keys attached to Stripe Checkout session / subscription metadata
ENTITLEMENT_KEYS = (
    "max_bots",
    "mystery_runs_per_month",
    "max_embeds",
    "theme_studio",
    "brand_to_bot",
    "custom_packs",
    "multi_seat",
    "priority_support",
    "founder_rate",
)

TIER_DEFINITIONS: dict[str, dict[str, Any]] = {
    "founding": {
        "id": "founding",
        "name": "Founding Partner",
        "tagline": "First 10 partners — lifetime founder rate",
        "pricing_display": {
            "intro": "$10",
            "then": "$29.99/mo",
            "note": "life · first 10 only",
            "amount_intro_cents": 1000,
            "amount_then_cents": 2999,
            "currency": "usd",
            "interval": "month",
        },
        "limit": FOUNDING_LIMIT,
        "entitlements": {
            "max_bots": -1,
            "mystery_runs_per_month": -1,
            "max_embeds": -1,
            "theme_studio": True,
            "brand_to_bot": True,
            "custom_packs": True,
            "multi_seat": True,
            "priority_support": True,
            "founder_rate": True,
        },
        "feature_bullets": [
            "Unlimited bots",
            "Unlimited mystery runs",
            "Unlimited embeds",
            "Theme Studio + Brand-to-Bot",
            "Custom packs + multi-seat",
            "Priority support · founder rate for life",
        ],
    },
    "professional": {
        "id": "professional",
        "name": "Professional",
        "tagline": "For growing service brands",
        "pricing_display": {
            "intro": "$10",
            "months_2_to_4": "$29.99/mo",
            "then": "$99/mo",
            "note": "mo 1 $10 · mo 2–4 $29.99 · then $99",
            "amount_intro_cents": 1000,
            "amount_ramp_cents": 2999,
            "amount_then_cents": 9900,
            "currency": "usd",
            "interval": "month",
        },
        "entitlements": {
            "max_bots": 3,
            "mystery_runs_per_month": 50,
            "max_embeds": 1,
            "theme_studio": True,
            "brand_to_bot": True,
            "custom_packs": False,
            "multi_seat": False,
            "priority_support": False,
            "founder_rate": False,
        },
        "feature_bullets": [
            "3 bots",
            "50 mystery runs / month",
            "1 embed",
            "Theme Studio + Brand-to-Bot",
        ],
    },
    "enterprise": {
        "id": "enterprise",
        "name": "Enterprise",
        "tagline": "Unlimited scale for teams",
        "pricing_display": {
            "intro": None,
            "then": "$189/mo",
            "note": "flat monthly",
            "amount_then_cents": 18900,
            "currency": "usd",
            "interval": "month",
        },
        "entitlements": {
            "max_bots": -1,
            "mystery_runs_per_month": -1,
            "max_embeds": -1,
            "theme_studio": True,
            "brand_to_bot": True,
            "custom_packs": True,
            "multi_seat": True,
            "priority_support": True,
            "founder_rate": False,
        },
        "feature_bullets": [
            "Unlimited bots",
            "Unlimited mystery runs",
            "Unlimited embeds",
            "Custom packs + multi-seat",
            "Priority support",
        ],
    },
}

# Owner/admin: enterprise+ unlimited with admin flags
ADMIN_ENTITLEMENTS: dict[str, Any] = {
    "max_bots": -1,
    "mystery_runs_per_month": -1,
    "max_embeds": -1,
    "theme_studio": True,
    "brand_to_bot": True,
    "custom_packs": True,
    "multi_seat": True,
    "priority_support": True,
    "founder_rate": False,
    "can_manage_founding": True,
    "can_bypass_paywall": True,
    "is_admin": True,
}

# Soft free/dev tier when no subscription header present
FREE_DEV_ENTITLEMENTS: dict[str, Any] = {
    "max_bots": -1,  # do not break existing flows
    "mystery_runs_per_month": -1,
    "max_embeds": -1,
    "theme_studio": True,
    "brand_to_bot": True,
    "custom_packs": False,
    "multi_seat": False,
    "priority_support": False,
    "founder_rate": False,
    "can_manage_founding": False,
    "can_bypass_paywall": False,
    "is_admin": False,
}


def get_tier(tier_id: str) -> dict[str, Any] | None:
    return TIER_DEFINITIONS.get((tier_id or "").strip().lower())


def entitlements_for_tier(tier_id: str | None) -> dict[str, Any]:
    if not tier_id:
        return dict(FREE_DEV_ENTITLEMENTS)
    tid = tier_id.strip().lower()
    if tid in ("admin", "owner"):
        return dict(ADMIN_ENTITLEMENTS)
    tier = get_tier(tid)
    if not tier:
        return dict(FREE_DEV_ENTITLEMENTS)
    out = dict(tier["entitlements"])
    out.setdefault("can_manage_founding", False)
    out.setdefault("can_bypass_paywall", False)
    out.setdefault("is_admin", False)
    return out


def entitlement_metadata(tier_id: str) -> dict[str, str]:
    """Stringify ALL entitlement keys + product/tier for Stripe metadata."""
    ents = entitlements_for_tier(tier_id)
    meta: dict[str, str] = {"product": "docketai", "tier": tier_id}
    for key in ENTITLEMENT_KEYS:
        val = ents.get(key)
        if isinstance(val, bool):
            meta[key] = "true" if val else "false"
        else:
            meta[key] = str(val)
    return meta


def plans_public_payload(founding_status: dict[str, Any] | None = None) -> dict[str, Any]:
    plans = []
    for tid in ("founding", "professional", "enterprise"):
        t = TIER_DEFINITIONS[tid]
        item = {
            "id": t["id"],
            "name": t["name"],
            "tagline": t["tagline"],
            "pricing_display": t["pricing_display"],
            "entitlements": t["entitlements"],
            "feature_bullets": t["feature_bullets"],
        }
        if tid == "founding" and founding_status:
            item["founding"] = {
                "limit": founding_status.get("limit", FOUNDING_LIMIT),
                "claimed": founding_status.get("claimed", 0),
                "remaining": founding_status.get("remaining", FOUNDING_LIMIT),
                "available": founding_status.get("available", True),
            }
        plans.append(item)
    return {
        "product": "docketai",
        "plans": plans,
        "founding": founding_status
        or {
            "limit": FOUNDING_LIMIT,
            "claimed": 0,
            "remaining": FOUNDING_LIMIT,
            "available": True,
            "stripe_configured": False,
        },
    }


def check_max_bots(entitlements: dict[str, Any], current_bot_count: int) -> str | None:
    """Return upgrade message if creating another bot would exceed max_bots, else None."""
    if entitlements.get("can_bypass_paywall") or entitlements.get("is_admin"):
        return None
    max_bots = entitlements.get("max_bots", -1)
    if max_bots is None or max_bots < 0:
        return None
    if current_bot_count >= int(max_bots):
        return (
            f"Bot limit reached ({max_bots}). "
            "Upgrade your plan to create more bots."
        )
    return None
