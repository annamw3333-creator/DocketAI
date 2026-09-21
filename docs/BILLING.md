# DocketAI Billing

Subscription tiers for Docket Desk + mobile Plans/Paywall.

## Tiers & entitlement parameters

`-1` = unlimited.

| Param | Founding (first 10) | Professional | Enterprise |
| --- | --- | --- | --- |
| Pricing display | $10 then $29.99/mo life | $10 → $29.99 mo 2–4 → $99 | $189/mo |
| `max_bots` | -1 | 3 | -1 |
| `mystery_runs_per_month` | -1 | 50 | -1 |
| `max_embeds` | -1 | 1 | -1 |
| `theme_studio` | true | true | true |
| `brand_to_bot` | true | true | true |
| `custom_packs` | true | false | true |
| `multi_seat` | true | false | true |
| `priority_support` | true | false | true |
| `founder_rate` | true | false | false |

Source of truth: `desk/app/entitlements.py` (`TIER_DEFINITIONS`). The same keys are written to Stripe Product metadata by `desk/scripts/create_stripe_catalog.py` and attached to Checkout Session / Subscription metadata.

## Founding Partner countdown (limit = 10)

`GET /api/billing/plans` and admin overview include:

```json
{
  "limit": 10,
  "claimed": 0,
  "remaining": 10,
  "available": true,
  "stripe_configured": false
}
```

**Source of truth when `STRIPE_SECRET_KEY` is set:** count of active/trialing Stripe subscriptions with `metadata.tier=founding`, else coupon `times_redeemed` for `DOCKET_FOUNDING`.

**When Stripe is unset:** `claimed` defaults to `0` / `remaining=10`, `stripe_configured=false`. Admins may `POST /api/admin/founding/adjust` to set a local test override. If Stripe **is** configured, that endpoint is **read-only** and only recounts from Stripe.

Checkout for `founding` refuses with HTTP 409 when `remaining == 0`.

## API

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/api/billing/plans` | Public plans + founding countdown |
| POST | `/api/billing/checkout` | `{tier, success_url, cancel_url, email?}` → Stripe Checkout URL |
| POST | `/api/billing/webhook` | Verifies `STRIPE_WEBHOOK_SECRET` |
| GET | `/api/admin/me` | Admin auth required |
| GET | `/api/admin/billing/overview` | Founding status + plan entitlements |
| POST | `/api/admin/founding/adjust` | `{claimed}` — mutable only if Stripe unset |

Soft entitlement gate on bot create (`POST /api/bots`, brand create): if `X-Docket-Tier` / customer context exceeds `max_bots` → **402** with upgrade message. **No header → free/dev** (existing flows unrestricted).

Admin headers bypass paywall: `X-Docket-Admin-Email` (allowlisted) or `X-Docket-Admin-Token`.

## Environment

```bash
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_PRICE_FOUNDING=      # from create_stripe_catalog.py — do not invent
STRIPE_PRICE_PROFESSIONAL=
STRIPE_PRICE_ENTERPRISE=
STRIPE_FOUNDING_COUPON_ID=

ADMIN_EMAILS=anna@annabuildsai.com,hello@aestheticabodes.ca
ADMIN_TOKEN=                 # optional shared secret
```

Defaults always include Anna’s emails even if `ADMIN_EMAILS` is partial/empty.

## Admin setup (Anna)

1. Set `ADMIN_EMAILS` (or rely on defaults) and optionally a strong `ADMIN_TOKEN` in Desk env.
2. In the mobile app → **Settings → Admin credentials**: store the same email and/or token (AsyncStorage).
3. Settings shows an **Admin** section only when credentials are stored; it calls `/api/admin/me`.
4. Admin identity has unlimited entitlements plus `can_manage_founding`, `can_bypass_paywall`, `is_admin`.
5. Use Admin → founding controls to inspect countdown; adjust claimed only when Stripe is unset (testing).

## Bootstrap Stripe catalog

```bash
cd desk
export STRIPE_SECRET_KEY=sk_test_...   # or sk_live_...
python scripts/create_stripe_catalog.py
# Copy printed export STRIPE_PRICE_* and STRIPE_FOUNDING_COUPON_ID into .env
# Create a Webhook endpoint → /api/billing/webhook and set STRIPE_WEBHOOK_SECRET
```

Do **not** commit secret keys or invent price IDs.

## Mobile

- Plans screen: Home + Settings → Plans / Subscribe.
- Three cards with distinct bullets from entitlements; Founding shows “X of 10 left”; sold out when `remaining=0`.
- Subscribe → `POST /api/billing/checkout` → `Linking.openURL(session.url)`.
- Admin credentials in Settings unlock Admin panel (founding countdown + paywall bypass badge). Not shown to normal users.
