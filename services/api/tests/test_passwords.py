"""Password hashing decisions for Brasaland credentials."""

from __future__ import annotations

from app.auth.passwords import hash_password, verify_password


def test_hash_then_verify_accepts_the_same_password():
    hashed = hash_password("Brasaland1")
    # bcrypt must not store the kitchen password in plaintext.
    assert hashed != "Brasaland1"
    assert verify_password("Brasaland1", hashed)


def test_verify_rejects_the_wrong_password():
    hashed = hash_password("Brasaland1")
    assert not verify_password("wrong-pass", hashed)
