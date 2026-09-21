"""Stripe billing helpers for DocketAI subscription tiers."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from .config import settings
from .entitlements import (
    FOUNDING_LIMIT,
    TIER_DEFINITIONS,
    entitlement_metadata,
    get_tier,
    plans_public_payload,
)

logger = logging.getLogger("docket.billing")

FOUNDING_COUPON_NAME = "DOCKET_FOUNDING"
FOUNDING_OVERRIDE_FILE = "founding_override.json"


def _stripe_configured() -> bool:
    return bool(settings.stripe_secret_key and settings.stripe_secret_key.strip())


def _stripe_client():
    if not _stripe_configured():
        return None
    import stripe

    stripe.api_key = settings.stripe_secret_key
    return stripe


def _override_path() -> Path:
    return Path(settings.data_dir) / FOUNDING_OVERRIDE_FILE


def get_local_founding_claimed() -> int:
    path = _override_path()
    if not path.exists():
        return 0
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return max(0, int(data.get("claimed", 0)))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return 0


def set_local_founding_claimed(claimed: int) -> int:
    """Manual override for testing when Stripe is NOT configured."""
    claimed = max(0, min(int(claimed), FOUNDING_LIMIT))
    path = _override_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"claimed": claimed}, indent=2), encoding="utf-8")
    return claimed


def _count_founding_from_stripe(stripe) -> int:
    """Count active/trialing subscriptions with metadata tier=founding,
    else fall back to coupon times_redeemed for DOCKET_FOUNDING.
    """
    claimed = 0
    try:
        starting_after = None
        while True:
            kwargs: dict[str, Any] = {"status": "all", "limit": 100}
            if starting_after:
                kwargs["starting_after"] = starting_after
            page = stripe.Subscription.list(**kwargs)
            for sub in page.data:
                status = getattr(sub, "status", None) or sub.get("status")
                if status not in ("active", "trialing"):
                    continue
                meta = getattr(sub, "metadata", None) or sub.get("metadata") or {}
                if (meta.get("tier") or "").lower() == "founding":
                    claimed += 1
            if not page.has_more:
                break
            starting_after = page.data[-1].id
    except Exception as exc:  # noqa: BLE001
        logger.warning("subscription scan failed, trying coupon: %s", exc)
        claimed = -1  # signal to try coupon

    if claimed >= 0:
        return claimed

    # Coupon fallback
    coupon_id = (settings.stripe_founding_coupon_id or "").strip()
    try:
        if coupon_id:
            coupon = stripe.Coupon.retrieve(coupon_id)
        else:
            # Search by name/id DOCKET_FOUNDING
            coupons = stripe.Coupon.list(limit=100)
            coupon = None
            for c in coupons.data:
                cid = getattr(c, "id", None) or c.get("id")
                cname = getattr(c, "name", None) or c.get("name")
                if cid == FOUNDING_COUPON_NAME or cname == FOUNDING_COUPON_NAME:
                    coupon = c
                    break
            if coupon is None:
                return 0
        redeemed = getattr(coupon, "times_redeemed", None)
        if redeemed is None and isinstance(coupon, dict):
            redeemed = coupon.get("times_redeemed", 0)
        return int(redeemed or 0)
    except Exception as exc:  # noqa: BLE001
        logger.warning("coupon recount failed: %s", exc)
        return 0


def get_founding_status() -> dict[str, Any]:
    """Return {limit, claimed, remaining, available, stripe_configured}."""
    limit = FOUNDING_LIMIT
    if _stripe_configured():
        stripe = _stripe_client()
        claimed = _count_founding_from_stripe(stripe)
        remaining = max(0, limit - claimed)
        return {
            "limit": limit,
            "claimed": claimed,
            "remaining": remaining,
            "available": remaining > 0,
            "stripe_configured": True,
            "source": "stripe",
        }
    claimed = get_local_founding_claimed()
    remaining = max(0, limit - claimed)
    return {
        "limit": limit,
        "claimed": claimed,
        "remaining": remaining,
        "available": remaining > 0,
        "stripe_configured": False,
        "source": "local_override",
    }


def _price_id_for_tier(tier: str) -> str | None:
    mapping = {
        "founding": settings.stripe_price_founding,
        "professional": settings.stripe_price_professional,
        "enterprise": settings.stripe_price_enterprise,
    }
    val = (mapping.get(tier) or "").strip()
    return val or None


def create_checkout_session(
    tier: str,
    success_url: str,
    cancel_url: str,
    email: str | None = None,
) -> dict[str, Any]:
    tid = (tier or "").strip().lower()
    if tid not in TIER_DEFINITIONS:
        raise ValueError(f"unknown tier: {tier}")

    if tid == "founding":
        status = get_founding_status()
        if status["remaining"] <= 0:
            raise PermissionError("Founding Partner spots are sold out (0 of 10 left).")

    if not _stripe_configured():
        raise RuntimeError(
            "Stripe is not configured. Set STRIPE_SECRET_KEY and price IDs."
        )

    price_id = _price_id_for_tier(tid)
    if not price_id:
        raise RuntimeError(
            f"No Stripe price ID for tier={tid}. "
            f"Set STRIPE_PRICE_{tid.upper()} after running create_stripe_catalog.py."
        )

    stripe = _stripe_client()
    meta = entitlement_metadata(tid)
    params: dict[str, Any] = {
        "mode": "subscription",
        "line_items": [{"price": price_id, "quantity": 1}],
        "success_url": success_url,
        "cancel_url": cancel_url,
        "metadata": meta,
        "subscription_data": {"metadata": meta},
    }
    if email:
        params["customer_email"] = email

    if tid == "founding" and (settings.stripe_founding_coupon_id or "").strip():
        params["discounts"] = [{"coupon": settings.stripe_founding_coupon_id.strip()}]

    session = stripe.checkout.Session.create(**params)
    return {
        "id": session.id,
        "url": session.url,
        "tier": tid,
        "metadata": meta,
    }


def construct_webhook_event(payload: bytes, sig_header: str) -> Any:
    secret = (settings.stripe_webhook_secret or "").strip()
    if not secret:
        raise RuntimeError("STRIPE_WEBHOOK_SECRET is not set")
    stripe = _stripe_client()
    if stripe is None:
        raise RuntimeError("STRIPE_SECRET_KEY is not set")
    return stripe.Webhook.construct_event(payload, sig_header, secret)


def handle_webhook_event(event: Any) -> dict[str, Any]:
    """Acknowledge relevant events; founding countdown is recounted live from Stripe."""
    etype = event["type"] if isinstance(event, dict) else event.type
    data = event["data"]["object"] if isinstance(event, dict) else event.data.object
    logger.info("stripe webhook: %s id=%s", etype, getattr(data, "id", None) or data.get("id"))
    # Live recount is used by get_founding_status(); no local mutation when Stripe is set.
    return {"received": True, "type": etype}


def plans_response() -> dict[str, Any]:
    status = get_founding_status()
    payload = plans_public_payload(status)
    payload["stripe_configured"] = status.get("stripe_configured", False)
    return payload


def billing_overview() -> dict[str, Any]:
    status = get_founding_status()
    return {
        "founding": status,
        "plans": [
            {
                "id": t["id"],
                "name": t["name"],
                "pricing_display": t["pricing_display"],
                "entitlements": t["entitlements"],
            }
            for t in (TIER_DEFINITIONS[k] for k in ("founding", "professional", "enterprise"))
        ],
        "stripe_configured": status.get("stripe_configured", False),
        "price_ids_configured": {
            "founding": bool((settings.stripe_price_founding or "").strip()),
            "professional": bool((settings.stripe_price_professional or "").strip()),
            "enterprise": bool((settings.stripe_price_enterprise or "").strip()),
        },
    }
