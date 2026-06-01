from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.responses.response_rest import ResponseRest
from app.api.responses.rest_meta import RestMeta
from app.api.responses.rest_status import RestStatus
from app.crud import (
  authenticate_user as crud_authenticate_user,
)
from app.database import get_db
from app.models import User
from app.schemas import (
  TokenResponse,
)
from app.services.access_manager import AccessManager
from app.services.auth import create_token

router = APIRouter(prefix="/users", tags=["users"])
response = ResponseRest()


def _meta(action: str, message: str | None = None) -> RestMeta:
  return RestMeta(action=action, message=message)


def _can_read_user(current_user: User, user_id: int) -> bool:
  return current_user.id == user_id or current_user.is_admin() or current_user.is_moderator()


def _can_manage_users(current_user: User) -> bool:
  return current_user.is_admin() or current_user.is_moderator()


def _forbidden(action: str, message: str):
  return response.error(
    status=RestStatus.forbidden_403,
    meta=_meta(action, message),
    data=None,
  )

