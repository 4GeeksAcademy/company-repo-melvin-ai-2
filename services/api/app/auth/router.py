"""Auth HTTP routes: login, session, password reset, and change-password."""

from __future__ import annotations

import logging

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth.deps import get_current_user
from app.auth.mail import send_reset_email
from app.auth.passwords import hash_password, verify_password
from app.auth.reset import ResetTokenError, consume_reset_token, create_reset_token
from app.auth.store import mark_unused_resets_used
from app.auth.tokens import create_access_token
from app.users import service as users_service
from app.users.schemas import (
    AuthMeResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    ProfilePublic,
    ResetPasswordRequest,
    TokenResponse,
)

logger = logging.getLogger("brasaland.auth")

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_token(email: str, password: str) -> TokenResponse:
    user = users_service.get_user_by_email(email)
    if user is None or not verify_password(password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(user_id=user["id"])
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(request: Request) -> TokenResponse:
    """JSON `{ email, password }` or OAuth2 form (`username` = email) for /docs Authorize."""
    content_type = (request.headers.get("content-type") or "").lower()
    if "application/json" in content_type:
        payload = LoginRequest.model_validate(await request.json())
        return _issue_token(payload.email, payload.password)

    form = await request.form()
    email = str(form.get("username") or form.get("email") or "")
    password = str(form.get("password") or "")
    return _issue_token(email, password)


@router.get("/me", response_model=AuthMeResponse)
def read_me(current_user: dict = Depends(get_current_user)) -> AuthMeResponse:
    profile = users_service.ensure_profile(current_user["id"])
    return AuthMeResponse(
        email=current_user["email"],
        role=current_user["role"],
        profile=ProfilePublic.model_validate(users_service.public_profile(profile)),
    )


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(payload: ForgotPasswordRequest) -> MessageResponse:
    user = users_service.get_user_by_email(payload.email)
    if user is not None and user.get("is_active", True):
        raw = create_reset_token(user["id"])
        try:
            send_reset_email(user["email"], raw)
        except Exception:
            logger.exception("Resend failed for password reset")
    return MessageResponse()


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(payload: ResetPasswordRequest) -> MessageResponse:
    try:
        user_id = consume_reset_token(payload.token)
    except ResetTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        ) from exc
    updated = users_service.update_user(
        user_id, {"hashed_password": hash_password(payload.new_password)}
    )
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )
    return MessageResponse()


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    payload: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
) -> MessageResponse:
    if not verify_password(payload.current_password, current_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    users_service.update_user(
        current_user["id"],
        {"hashed_password": hash_password(payload.new_password)},
    )
    mark_unused_resets_used(current_user["id"], datetime.now(timezone.utc).isoformat())
    return MessageResponse()
