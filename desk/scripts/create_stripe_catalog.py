#!/usr/bin/env python3
"""Idempotent Stripe catalog bootstrap for DocketAI.

Creates 3 Products (with entitlement metadata), monthly Prices, and a
Founding Partner coupon (max_redemptions=10, amount_off first invoice when
feasible). Prints env export lines — does NOT invent or commit secrets.

Usage:
  export STRIPE_SECRET_KEY=sk_test_...
  cd desk && python scripts/create_stripe_catalog.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.entitlements import (  # noqa: E402
    ENTITLEMENT_KEYS,
    FOUNDING_LIMIT,
    TIER_DEFINITIONS,
    entitlement_metadata,
)


def _find_product(stripe, tier_id: str):
    products = stripe.Product.list(limit=100, active=True)
    for p in products.auto_paging_iter():
        meta = p.metadata.to_dict() if p.metadata else {}
        if meta.get("product") == "docketai" and meta.get("tier") == tier_id:
            return p
    return None


def _find_price(stripe, product_id: str, unit_amount: int, currency: str = "usd"):
    prices = stripe.Price.list(product=product_id, active=True, limit=100)
    for pr in prices.auto_paging_iter():
        recurring = pr.recurring.to_dict() if pr.recurring else {}
        if (
            pr.unit_amount == unit_amount
            and pr.currency == currency
            and recurring
            and recurring.get("interval") == "month"
        ):
            return pr
    return None


def _find_coupon(stripe, coupon_id: str = "DOCKET_FOUNDING"):
    try:
        return stripe.Coupon.retrieve(coupon_id)
    except Exception:
        coupons = stripe.Coupon.list(limit=100)
        for c in coupons.auto_paging_iter():
            if c.id == coupon_id or (c.name or "") == coupon_id:
                return c
    return None


def main() -> int:
    key = (os.environ.get("STRIPE_SECRET_KEY") or "").strip()
    if not key:
        print("ERROR: Set STRIPE_SECRET_KEY before running.", file=sys.stderr)
        return 1

    import stripe

    stripe.api_key = key
    exports: dict[str, str] = {}

    # List price = "then" amount; intro discounts via coupon / Dashboard phases
    price_amounts = {
        tid: int(TIER_DEFINITIONS[tid]["pricing_display"]["amount_then_cents"])
        for tid in ("founding", "professional", "enterprise")
    }

    for tier_id in ("founding", "professional", "enterprise"):
        tier = TIER_DEFINITIONS[tier_id]
        meta = entitlement_metadata(tier_id)
        for k in ENTITLEMENT_KEYS:
            meta.setdefault(k, str(tier["entitlements"].get(k)))

        product = _find_product(stripe, tier_id)
        if product:
            product = stripe.Product.modify(
                product.id,
                metadata=meta,
                name=f"DocketAI {tier['name']}",
                description=tier.get("tagline") or tier["name"],
            )
            print(f"OK product exists: {tier_id} → {product.id}")
        else:
            product = stripe.Product.create(
                name=f"DocketAI {tier['name']}",
                description=tier.get("tagline") or tier["name"],
                metadata=meta,
            )
            print(f"CREATED product: {tier_id} → {product.id}")

        amount = price_amounts[tier_id]
        price = _find_price(stripe, product.id, amount)
        if price:
            print(f"OK price exists: {tier_id} → {price.id} ({amount} cents/mo)")
        else:
            price = stripe.Price.create(
                product=product.id,
                unit_amount=amount,
                currency="usd",
                recurring={"interval": "month"},
                nickname=f"docketai_{tier_id}_monthly",
                metadata={"product": "docketai", "tier": tier_id},
            )
            print(f"CREATED price: {tier_id} → {price.id} ({amount} cents/mo)")

        exports[f"STRIPE_PRICE_{tier_id.upper()}"] = price.id

    # Founding coupon: $19.99 off first invoice when list is $29.99 → $10 intro
    founding_pd = TIER_DEFINITIONS["founding"]["pricing_display"]
    intro_off = int(founding_pd["amount_then_cents"]) - int(founding_pd["amount_intro_cents"])
    coupon = _find_coupon(stripe, "DOCKET_FOUNDING")
    if coupon:
        print(f"OK coupon exists: DOCKET_FOUNDING → {coupon.id} (redeemed={coupon.times_redeemed})")
    else:
        coupon = stripe.Coupon.create(
            id="DOCKET_FOUNDING",
            name="DOCKET_FOUNDING",
            amount_off=intro_off,
            currency="usd",
            duration="once",
            max_redemptions=FOUNDING_LIMIT,
            metadata={
                "product": "docketai",
                "tier": "founding",
                "purpose": "first_invoice_intro",
            },
        )
        print(f"CREATED coupon: DOCKET_FOUNDING → {coupon.id} amount_off={intro_off} max={FOUNDING_LIMIT}")

    exports["STRIPE_FOUNDING_COUPON_ID"] = coupon.id

    print("\n# --- copy into desk/.env (do not commit secrets) ---")
    print("# STRIPE_SECRET_KEY is already in your shell; do not echo it here.")
    for k, v in exports.items():
        print(f"export {k}={v}")
    print("# Also set STRIPE_WEBHOOK_SECRET from Stripe Dashboard → Webhooks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
