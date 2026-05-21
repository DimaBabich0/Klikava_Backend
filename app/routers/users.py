from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.responses.controller_rest import ControllerRest
from app.api.responses.rest_meta import RestMeta
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
controller = ControllerRest()


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


def _forbidden(action: str, message: str):
  return controller.error(
    status=RestStatus.forbidden_403,
    meta=_meta(action, message),
    data=None,
  )


@router.post("/register", response_model=None)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
  """Register a new user with default BUYER role."""
  try:
    new_user = create_user(db, user_data)
    return controller.success(
      status=RestStatus.created_201,
      meta=_meta("register_user", "User registered"),
      data=_serialize_user(new_user),
    )
  except ValueError as e:
    return controller.error(
      status=RestStatus.bad_request_400,
      meta=_meta("register_user", str(e)),
      data=None,
    )


@router.post("/login", response_model=None)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
  """Login user and return JWT token."""
  is_valid, db_user = crud_authenticate_user(
    db, credentials.login, credentials.password)
  if not is_valid or not db_user:
    return controller.error(
      status=RestStatus.unauthorized_401,
      meta=_meta("login_user", "Invalid credentials"),
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

  return controller.success(
    status=RestStatus.ok_200,
    meta=_meta("login_user", "User logged in"),
    data=token_data,
  )


@router.get("", response_model=None)
def list_users(
  skip: int = Query(0, ge=0),
  limit: int = Query(100, ge=1, le=500),
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """Get all users. Admin or moderator only."""
  if not _can_manage_users(current_user):
    return _forbidden("list_users", "Only admin or moderator can list users")

  users = get_users(db, skip=skip, limit=limit)
  total = get_users_count(db)
  return controller.success(
    status=RestStatus.ok_200,
    meta=_meta("list_users", f"Users found: {len(users)} of {total}"),
    data={
      "items": _serialize_users(users),
      "skip": skip,
      "limit": limit,
      "total": total,
    },
  )


@router.get("/me", response_model=None)
def get_current_user(
  current_user: User = Depends(AccessManager.get_current_user),
):
  """Get current user from Authorization token."""
  return controller.success(
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
    return _forbidden("get_user_by_email", "Only admin or moderator can search users by email")

  user = get_user_by_email(db, email)
  if not user:
    return controller.error(
      status=RestStatus.not_found_404,
      meta=_meta("get_user_by_email", "User not found"),
      data=None,
    )

  return controller.success(
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
    return _forbidden("ban_user", "Only admin or moderator can ban users")

  if current_user.id == user_id:
    return controller.error(
      status=RestStatus.bad_request_400,
      meta=_meta("ban_user", "User cannot ban himself"),
      data=None,
    )

  user = get_user_by_id(db, user_id)
  if not user:
    return controller.error(
      status=RestStatus.not_found_404,
      meta=_meta("ban_user", "User not found"),
      data=None,
    )

  banned_user = crud_ban_user(db, user)
  message = "User banned"
  if ban_data and ban_data.reason:
    message = f"{message}: {ban_data.reason}"

  return controller.success(
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
    return _forbidden("get_user_roles", "Only owner, admin or moderator can get user roles")

  user = get_user_by_id(db, user_id)
  if not user:
    return controller.error(
      status=RestStatus.not_found_404,
      meta=_meta("get_user_roles", "User not found"),
      data=None,
    )

  return controller.success(
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
    return _forbidden("get_user", "Only owner, admin or moderator can get user")

  user = get_user_by_id(db, user_id)
  if not user:
    return controller.error(
      status=RestStatus.not_found_404,
      meta=_meta("get_user", "User not found"),
      data=None,
    )

  return controller.success(
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
    return _forbidden("update_user", "Only owner or admin can update user")

  user = get_user_by_id(db, user_id)
  if not user:
    return controller.error(
      status=RestStatus.not_found_404,
      meta=_meta("update_user", "User not found"),
      data=None,
    )

  try:
    updated_user = crud_update_user(db, user, user_data)
  except ValueError as e:
    return controller.error(
      status=RestStatus.bad_request_400,
      meta=_meta("update_user", str(e)),
      data=None,
    )

  return controller.success(
    status=RestStatus.ok_200,
    meta=_meta("update_user", "User updated"),
    data=_serialize_user(updated_user),
  )
