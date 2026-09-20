from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from typing import Any

import httpx

from .config import settings

log = logging.getLogger("docket.desk.alerts")


async def maybe_alert_score_drop(
    title: str,
    scores: dict[str, float],
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Fire webhook/email when overall or any dimension is below threshold."""
    threshold = settings.alert_score_threshold
    low = {k: v for k, v in scores.items() if isinstance(v, (int, float)) and v < threshold}
    if not low:
        return {"alerted": False, "reason": "scores_ok"}

    body = {
        "text": f"[Docket Desk] Score drop: {title}",
        "scores": scores,
        "below_threshold": low,
        "threshold": threshold,
        "context": context or {},
    }
    results: dict[str, Any] = {"alerted": True, "webhook": None, "email": None}

    if settings.alert_webhook_url:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.post(settings.alert_webhook_url, json=body)
            results["webhook"] = {"status": r.status_code}
        except Exception as exc:  # noqa: BLE001
            log.warning("webhook failed: %s", exc)
            results["webhook"] = {"error": str(exc)}
    else:
        results["webhook"] = {"skipped": "ALERT_WEBHOOK_URL unset"}
        log.info("ALERT (no webhook): %s %s", title, low)

    if settings.alert_email:
        results["email"] = _send_email(
            settings.alert_email,
            f"[Docket Desk] Score drop: {title}",
            str(body),
        )
    else:
        results["email"] = {"skipped": "ALERT_EMAIL unset"}

    return results


def _send_email(to: str, subject: str, content: str) -> dict[str, Any]:
    if not settings.smtp_host:
        log.info("EMAIL (no SMTP): to=%s subject=%s", to, subject)
        return {"logged": True, "to": to}
    try:
        msg = EmailMessage()
        msg["From"] = settings.smtp_from
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(content)
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
            smtp.starttls()
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(msg)
        return {"sent": True, "to": to}
    except Exception as exc:  # noqa: BLE001
        log.warning("email failed: %s", exc)
        return {"error": str(exc)}
