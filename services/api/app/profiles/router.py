"""Profile routes for the authenticated Brasaland operator."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.auth.deps import get_current_user
from app.users import service as users_service
from app.users.schemas import ProfilePublic, ProfileUpdate

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/me", response_model=ProfilePublic)
def read_my_profile(current_user: dict = Depends(get_current_user)) -> ProfilePublic:
    profile = users_service.ensure_profile(current_user["id"])
    return ProfilePublic.model_validate(users_service.public_profile(profile))


@router.put("/me", response_model=ProfilePublic)
def update_my_profile(
    payload: ProfileUpdate,
    current_user: dict = Depends(get_current_user),
) -> ProfilePublic:
    users_service.ensure_profile(current_user["id"])
    updated = users_service.update_profile_for_user(
        current_user["id"],
        payload.model_dump(exclude_unset=True),
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return ProfilePublic.model_validate(users_service.public_profile(updated))
