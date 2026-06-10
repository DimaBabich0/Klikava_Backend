from datetime import datetime
import math

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.responses.response_rest import ResponseRest
from app.api.responses.rest_meta import RestLink, RestMeta, RestPagination
from app.api.responses.rest_status import RestStatus

from app.crud import (
  authenticate_user as crud_authenticate_user,
  ban_user as crud_ban_user,
  create_user,
  get_user_by_email,
  get_user_by_id,
  get_users,
  get_users_count,
  update_user as crud_update_user,
)
from app.database import get_db
from app.models import User
from app.schemas import (
  TokenResponse,
  UserBanRequest,
  UserCreate,
  UserLogin,
  UserResponse,
  UserUpdate,
)
from app.services.access_manager import AccessManager
from app.services.auth import create_token

router = APIRouter(prefix="/users", tags=["users"])
response = ResponseRest()


def _meta(action: str, message: str | None = None) -> RestMeta:
  return RestMeta(action=action, message=message)


def _serialize_user(user: User) -> dict:
  data = UserResponse.model_validate(user).model_dump(mode="json")
  data["is_active"] = user.is_active()
  return data


def _serialize_users(users: list[User]) -> list[dict]:
  return [_serialize_user(user) for user in users]


def _can_read_user(current_user: User, user_id: int) -> bool:
  return current_user.id == user_id or current_user.is_admin() or current_user.is_moderator()


def _can_manage_users(current_user: User) -> bool:
  return current_user.is_admin() or current_user.is_moderator()


@router.post("/register", response_model=None)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
  """Register a new user with default BUYER role."""
  try:
    new_user = create_user(db, user_data)
    return response.success(
      status=RestStatus.created_201,
      meta=_meta("register_user", "User registered"),
      data=_serialize_user(new_user),
    )
  except ValueError as e:
    return response.error(
      status=RestStatus.bad_request_400,
      meta=_meta("register_user", str(e)),
      data=None,
    )


@router.post("/login", response_model=None)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
  """Login user and return JWT token."""
  is_valid, db_user = crud_authenticate_user(db, credentials.login_email, credentials.password)
  if not is_valid or not db_user:
    return response.error(
      status=RestStatus.unauthorized_401,
      meta=_meta("login_user", "Invalid login, email or password"),
      data=None,
    )

  token_data = {
    "sub": str(db_user.id),
    "roles": [role.name for role in db_user.roles],
  }
  access_token = create_token(token_data)
  token_response = TokenResponse(
    access_token=access_token,
    token_type="bearer",
    user=UserResponse.model_validate(db_user),
  )
  token_data = token_response.model_dump(mode="json")
  token_data["user"] = _serialize_user(db_user)

  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("login_user", "User logged in"),
    data=token_data,
  )


@router.get("", response_model=None)
def list_users(
  per_page: int = Query(10, ge=1, le=100),
  page: int = Query(1, ge=1),
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """Get paginated users. Admin or moderator only."""
  if not _can_manage_users(current_user):
    return response.forbidden("Only admin or moderator can list users")

  total = get_users_count(db)
  users = get_users(db, skip=(page - 1) * per_page, limit=per_page)
  pagination = response.build_pagination(page, per_page, total)

  return response.success_pagination(
    status=RestStatus.ok_200,
    meta=RestMeta(
      action="list_users",
      message=f"Users found: {len(users)}",
      pagination=pagination,
    ),
    data={"items": _serialize_users(users)},
  )


@router.get("/me", response_model=None)
def get_current_user(
  current_user: User = Depends(AccessManager.get_current_user),
):
  """Get current user from Authorization token."""
  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("get_current_user", "Current user found"),
    data=_serialize_user(current_user),
  )


@router.get("/email/{email}", response_model=None)
def get_user_by_email_route(
  email: str,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """Get user by email. Admin or moderator only."""
  if not _can_manage_users(current_user):
    return response.forbidden("Only admin or moderator can search users by email")

  user = get_user_by_email(db, email)
  if not user:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("get_user_by_email", "User not found"),
      data=None,
    )

  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("get_user_by_email", "User found"),
    data=_serialize_user(user),
  )


@router.post("/{user_id}/ban", response_model=None)
def ban_user(
  user_id: int,
  ban_data: UserBanRequest | None = None,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """Ban user by ID. Admin or moderator only."""
  if not _can_manage_users(current_user):
    return response.forbidden("Only admin or moderator can ban users")

  if current_user.id == user_id:
    return response.error(
      status=RestStatus.bad_request_400,
      meta=_meta("ban_user", "User cannot ban himself"),
      data=None,
    )

  user = get_user_by_id(db, user_id)
  if not user:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("ban_user", "User not found"),
      data=None,
    )

  banned_user = crud_ban_user(db, user)
  message = "User banned"
  if ban_data and ban_data.reason:
    message = f"{message}: {ban_data.reason}"

  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("ban_user", message),
    data=_serialize_user(banned_user),
  )


@router.get("/{user_id}/roles", response_model=None)
def get_users_roles(
  user_id: int,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """Get user's roles by user ID."""
  if not _can_read_user(current_user, user_id):
    return response.forbidden("Only owner, admin or moderator can get user roles")

  user = get_user_by_id(db, user_id)
  if not user:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("get_user_roles", "User not found"),
      data=None,
    )

  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("get_user_roles", "User roles found"),
    data=_serialize_user(user)["roles"],
  )


@router.get("/{user_id}", response_model=None)
def get_user(
  user_id: int,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """Get user by ID."""
  if not _can_read_user(current_user, user_id):
    return response.forbidden("Only owner, admin or moderator can get user")

  user = get_user_by_id(db, user_id)
  if not user:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("get_user", "User not found"),
      data=None,
    )

  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("get_user", "User found"),
    data=_serialize_user(user),
  )


@router.patch("/{user_id}", response_model=None)
def update_user(
  user_id: int,
  user_data: UserUpdate,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """Update user profile. Owner or admin only."""
  if current_user.id != user_id and not current_user.is_admin():
    return response.forbidden("Only owner or admin can update user")

  user = get_user_by_id(db, user_id)
  if not user:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("update_user", "User not found"),
      data=None,
    )

  try:
    updated_user = crud_update_user(db, user, user_data)
  except ValueError as e:
    return response.error(
      status=RestStatus.bad_request_400,
      meta=_meta("update_user", str(e)),
      data=None,
    )

  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("update_user", "User updated"),
    data=_serialize_user(updated_user),
  )


@router.delete("/{user_id}", response_model=None)
def delete_user(
  user_id: int,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """Delete user. Owner or admin only."""
  if current_user.id != user_id and not current_user.is_admin():
    return response.forbidden("Only owner or admin can delete user")

  user = get_user_by_id(db, user_id)
  if not user:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("delete_user", "User not found"),
      data=None,
    )

  if user.is_deleted():
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("delete_user", "User already deleted"),
      data=None,
    )

  now = datetime.now()
  for user_role in user.user_roles:
    if not user_role.is_deleted():
      user_role.deleted_at = now
      user_role.deactivate()

  db.commit()

  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("delete_user", "User deleted"),
    data=user,
  )