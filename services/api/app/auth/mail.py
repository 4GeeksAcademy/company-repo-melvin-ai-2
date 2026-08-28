"""Send password-reset mail through Resend."""

from __future__ import annotations

import logging
from typing import Optional

from app.auth import config

logger = logging.getLogger("brasaland.auth")


def reset_link(raw_token: str) -> str:
    return f"{config.public_app_url()}/reset-password?token={raw_token}"


def send_reset_email(to_email: str, raw_token: str) -> Optional[str]:
    """Send the reset link. Returns a Resend id, or None if sending was skipped."""
    api_key = config.resend_api_key()
    if not api_key:
        logger.warning(
            "RESEND_API_KEY is not set; skipping password-reset email to %s",
            to_email,
        )
        return None

    link = reset_link(raw_token)
    text_body = (
        "Reset your Brasaland password\n\n"
        "Use this link on your phone or computer to choose a new password:\n"
        f"{link}\n\n"
        "The link expires soon and can be used only once. "
        "If you did not ask for this, you can ignore this message.\n"
    )
    html_body = (
        "<p>Reset your Brasaland password</p>"
        "<p>Use this link on your phone or computer to choose a new password:</p>"
        f'<p><a href="{link}">{link}</a></p>'
        "<p>The link expires soon and can be used only once. "
        "If you did not ask for this, you can ignore this message.</p>"
    )

    import resend

    resend.api_key = api_key
    result = resend.Emails.send(
        {
            "from": config.resend_from_email(),
            "to": [to_email],
            "subject": "Reset your Brasaland password",
            "text": text_body,
            "html": html_body,
        }
    )
    email_id = None
    if isinstance(result, dict):
        email_id = result.get("id")
    else:
        email_id = getattr(result, "id", None)
    logger.info("Resend password-reset email id=%s to=%s", email_id, to_email)
    return str(email_id) if email_id else "sent"
