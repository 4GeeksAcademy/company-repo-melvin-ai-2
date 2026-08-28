"""User credential CRUD under /users."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.deps import get_current_user
from app.users import service as users_service
from app.users.schemas import UserCreate, UserPublic, UserRole, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


def _is_admin(user: dict) -> bool:
    return user.get("role") == UserRole.admin.value


def _require_self_or_admin(current_user: dict, user_id: int) -> None:
    if current_user["id"] == user_id or _is_admin(current_user):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not allowed to access this user",
    )


@router.post("", response_model=UserPublic, status_code=201)
@router.post("/", response_model=UserPublic, status_code=201, include_in_schema=False)
def register_user(payload: UserCreate) -> UserPublic:
    try:
        user = users_service.create_user(
            email=payload.email,
            password=payload.password,
            role=UserRole.user,
            name=payload.name,
            phone=payload.phone,
            address=payload.address,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return UserPublic.model_validate(users_service.public_user(user))


@router.get("", response_model=List[UserPublic])
@router.get("/", response_model=List[UserPublic], include_in_schema=False)
def list_users(_current_user: dict = Depends(get_current_user)) -> List[UserPublic]:
    return [
        UserPublic.model_validate(users_service.public_user(row))
        for row in users_service.list_users()
    ]


@router.get("/{user_id}", response_model=UserPublic)
def get_user(
    user_id: int, current_user: dict = Depends(get_current_user)
) -> UserPublic:
    _require_self_or_admin(current_user, user_id)
    user = users_service.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserPublic.model_validate(users_service.public_user(user))


@router.put("/{user_id}", response_model=UserPublic)
def update_user(
    user_id: int,
    payload: UserUpdate,
    current_user: dict = Depends(get_current_user),
) -> UserPublic:
    _require_self_or_admin(current_user, user_id)
    if payload.role is not None and not _is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only an admin can change role",
        )
    target = users_service.get_user_by_id(user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    patch = payload.model_dump(exclude_unset=True)
    if "role" in patch and patch["role"] is not None:
        patch["role"] = patch["role"].value
    try:
        updated = users_service.update_user(user_id, patch)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if updated is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserPublic.model_validate(users_service.public_user(updated))


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int, current_user: dict = Depends(get_current_user)
) -> None:
    _require_self_or_admin(current_user, user_id)
    if not users_service.delete_user(user_id):
        raise HTTPException(status_code=404, detail="User not found")
