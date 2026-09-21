"""Owner/admin auth and entitlement helpers for DocketAI Desk."""
from __future__ import annotations

import hmac
from typing import Any

from fastapi import Header, HTTPException, Request

from .config import settings
from .entitlements import ADMIN_ENTITLEMENTS

DEFAULT_ADMIN_EMAILS = (
    "anna@annabuildsai.com",
    "hello@aestheticabodes.ca",
)


def admin_email_allowlist() -> set[str]:
    raw = (settings.admin_emails or "").strip()
    emails = {e.strip().lower() for e in raw.split(",") if e.strip()}
    if not emails:
        emails = {e.lower() for e in DEFAULT_ADMIN_EMAILS}
    # Always include defaults so Anna retains access even if env is partial
    emails.update(e.lower() for e in DEFAULT_ADMIN_EMAILS)
    return emails


def is_admin_email(email: str | None) -> bool:
    if not email:
        return False
    return email.strip().lower() in admin_email_allowlist()


def is_valid_admin_token(token: str | None) -> bool:
    expected = (settings.admin_token or "").strip()
    if not expected or not token:
        return False
    return hmac.compare_digest(token.strip(), expected)


def resolve_admin(
    email: str | None = None,
    token: str | None = None,
) -> dict[str, Any] | None:
    """Return admin identity dict if authorized, else None."""
    token_ok = is_valid_admin_token(token)
    email_ok = is_admin_email(email)
    if not token_ok and not email_ok:
        return None
    # Prefer matching email when present; token alone still grants admin
    resolved_email = (email or "").strip().lower() if email_ok else None
    if token_ok and not resolved_email and email and is_admin_email(email):
        resolved_email = email.strip().lower()
    return {
        "is_admin": True,
        "email": resolved_email,
        "auth": "token" if token_ok else "email",
        "entitlements": dict(ADMIN_ENTITLEMENTS),
        "allowlist": sorted(admin_email_allowlist()),
    }


def require_admin(
    x_docket_admin_email: str | None = Header(default=None, alias="X-Docket-Admin-Email"),
    x_docket_admin_token: str | None = Header(default=None, alias="X-Docket-Admin-Token"),
) -> dict[str, Any]:
    identity = resolve_admin(email=x_docket_admin_email, token=x_docket_admin_token)
    if not identity:
        raise HTTPException(
            status_code=403,
            detail="Admin access required. Provide X-Docket-Admin-Email (allowlisted) "
            "or X-Docket-Admin-Token.",
        )
    return identity


def entitlements_from_request(request: Request) -> dict[str, Any]:
    """Resolve entitlements from admin headers or X-Docket-Tier.

    No subscription/tier header → free/dev (unlimited bots so existing flows work).
    """
    from .entitlements import entitlements_for_tier

    email = request.headers.get("X-Docket-Admin-Email")
    token = request.headers.get("X-Docket-Admin-Token")
    admin = resolve_admin(email=email, token=token)
    if admin:
        return dict(ADMIN_ENTITLEMENTS)

    tier = request.headers.get("X-Docket-Tier") or request.headers.get("X-Docket-Customer-Tier")
    return entitlements_for_tier(tier)
