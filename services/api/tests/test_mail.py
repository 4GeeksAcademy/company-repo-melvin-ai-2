"""Password-reset mail decisions (no Resend network calls)."""

from __future__ import annotations

from app.auth.mail import reset_link, send_reset_email


def test_reset_link_uses_public_app_url():
    link = reset_link("raw-token-value")
    assert link.startswith("http://localhost:3101/reset-password?token=")
    assert "raw-token-value" in link


def test_send_reset_email_skips_when_resend_key_is_missing():
    # Tests set RESEND_API_KEY empty; skip is the decision, not a Resend call.
    assert send_reset_email("lucia.fernandez@brasaland.com", "raw-token") is None
