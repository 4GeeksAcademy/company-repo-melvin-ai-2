"""POST /auth/forgot-password — reset minting without account enumeration."""

from __future__ import annotations

from app.auth import store
from app.errors import MailSendError
from tests.factories import LUCIA_EMAIL


def _reset_rows():
    return store.get_auth_db().table("password_resets").all()


def test_forgot_password_mints_reset_for_known_active_operator(
    client, lucia, monkeypatch
):
    captured = {}

    def fake_send(to_email: str, raw_token: str):
        captured["email"] = to_email
        captured["token"] = raw_token
        return "sent"

    monkeypatch.setattr("app.auth.router.send_reset_email", fake_send)

    client.post("/auth/forgot-password", json={"email": LUCIA_EMAIL})

    rows = _reset_rows()
    assert len(rows) == 1
    assert rows[0]["user_id"] == lucia["id"]
    assert rows[0]["used_at"] is None
    assert captured.get("email") == LUCIA_EMAIL
    assert captured.get("token")


def test_forgot_password_unknown_email_does_not_mint_a_reset(client):
    client.post(
        "/auth/forgot-password",
        json={"email": "unknown.operator@brasaland.com"},
    )

    # Same success path as a known email, but no hashed token is stored
    # (AI-assisted case: do not reveal whether the address is registered).
    assert _reset_rows() == []


def test_forgot_password_mail_failure_still_does_not_leak_account(
    client, lucia, monkeypatch
):
    def boom(_to_email: str, _raw_token: str):
        raise MailSendError()

    monkeypatch.setattr("app.auth.router.send_reset_email", boom)

    response = client.post("/auth/forgot-password", json={"email": LUCIA_EMAIL})
    payload = response.json()

    # Mail outage still looks like success so callers cannot enumerate accounts.
    assert payload.get("ok") is True
    assert "resend" not in str(payload).lower()
    assert "traceback" not in str(payload).lower()
