from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.responses.response_rest import ResponseRest
from app.api.responses.rest_meta import RestMeta
from app.api.responses.rest_status import RestStatus

from app.crud import (
  assign_role_to_user as crud_assign_role_to_user,
  create_role as crud_create_role,
  get_role_by_id,
  get_role_by_name,
  get_roles,
  remove_role_from_user as crud_remove_role_from_user,
  update_role as crud_update_role,
  delete_role as crud_delete_role,
)
from app.database import get_db
from app.models import Role, User
from app.schemas import AssignRoleRequest, RoleCreate, RoleResponse, RoleUpdate
from app.services.access_manager import AccessManager

router = APIRouter(prefix="/roles", tags=["roles"])
response = ResponseRest()


def _meta(action: str, message: str | None = None) -> RestMeta:
  return RestMeta(action=action, message=message)


def _serialize_role(role: Role) -> dict:
  return RoleResponse.model_validate(role).model_dump(mode="json")


def _serialize_roles(roles: list[Role]) -> list[dict]:
  return [_serialize_role(role) for role in roles]


def _can_manage_roles(current_user: User) -> bool:
  return current_user.is_admin()


@router.get("", response_model=None)
def list_roles(
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """Get all available roles. Admin or moderator only."""
  if not current_user.is_admin() and not current_user.is_moderator():
    return response.forbidden("Only admin or moderator can list roles")

  roles = get_roles(db)
  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("list_roles", f"Roles found: {len(roles)}"),
    data={"items": _serialize_roles(roles)},
  )


@router.post("", response_model=None)
def create_role(
  role_data: RoleCreate,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """Create a new role. Admin only."""
  if not _can_manage_roles(current_user):
    return response.forbidden("Only admin can create roles")

  try:
    new_role = crud_create_role(db, role_data)
    return response.success(
      status=RestStatus.created_201,
      meta=_meta("create_role", "Role created"),
      data=_serialize_role(new_role),
    )
  except ValueError as e:
    return response.error(
      status=RestStatus.bad_request_400,
      meta=_meta("create_role", str(e)),
      data=None,
    )


@router.post("/assign/{user_id}", response_model=None)
def assign_role(
  user_id: int,
  role_request: AssignRoleRequest,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """Assign a role to a user. Admin only."""
  if not _can_manage_roles(current_user):
    return response.forbidden("Only admin can assign roles")

  try:
    user = crud_assign_role_to_user(
      db,
      user_id,
      role_request.role_name,
      role_request.login,
      role_request.password,
    )
    return response.success(
      status=RestStatus.ok_200,
      meta=_meta(
        "assign_role", f"Role '{role_request.role_name}' assigned to user {user_id}"),
      data={"user_id": user.id, "roles": [r.name for r in user.roles]},
    )
  except ValueError as e:
    return response.error(
      status=RestStatus.bad_request_400,
      meta=_meta("assign_role", str(e)),
      data=None,
    )


@router.delete("/assign/{user_id}", response_model=None)
def remove_role(
  user_id: int,
  role_request: AssignRoleRequest,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """Remove a role from a user. Admin only."""
  if not _can_manage_roles(current_user):
    return response.forbidden("Only admin can remove roles")

  if current_user.id == user_id:
    return response.error(
      status=RestStatus.bad_request_400,
      meta=_meta("remove_role", "Admin cannot remove their own role"),
      data=None,
    )

  try:
    user = crud_remove_role_from_user(db, user_id, role_request.role_name)
    return response.success(
      status=RestStatus.ok_200,
      meta=_meta(
        "remove_role", f"Role '{role_request.role_name}' removed from user {user_id}"),
      data={"user_id": user.id, "roles": [r.name for r in user.roles]},
    )
  except ValueError as e:
    return response.error(
      status=RestStatus.bad_request_400,
      meta=_meta("remove_role", str(e)),
      data=None,
    )


@router.get("/{role_id}", response_model=None)
def get_role(
  role_id: int,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """Get role by ID. Admin or moderator only."""
  if not current_user.is_admin() and not current_user.is_moderator():
    return response.forbidden("Only admin or moderator can view roles")

  role = get_role_by_id(db, role_id)
  if not role:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("get_role", "Role not found"),
      data=None,
    )

  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("get_role", "Role found"),
    data=_serialize_role(role),
  )


@router.patch("/{role_id}", response_model=None)
def update_role(
  role_id: int,
  role_data: RoleUpdate,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """Update role by ID. Admin only."""
  if not _can_manage_roles(current_user):
    return response.forbidden("Only admin can update roles")

  role = get_role_by_id(db, role_id)
  if not role:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("update_role", "Role not found"),
      data=None,
    )

  try:
    updated_role = crud_update_role(db, role, role_data)
    return response.success(
      status=RestStatus.ok_200,
      meta=_meta("update_role", "Role updated"),
      data=_serialize_role(updated_role),
    )
  except ValueError as e:
    return response.error(
      status=RestStatus.bad_request_400,
      meta=_meta("update_role", str(e)),
      data=None,
    )


@router.delete("/{role_id}", response_model=None)
def delete_role(
  role_id: int,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """Delete role by ID. Admin only."""
  if not _can_manage_roles(current_user):
    return response.forbidden("Only admin can delete roles")

  role = get_role_by_id(db, role_id)
  if not role:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("delete_role", "Role not found"),
      data=None,
    )

  if role.deleted_at is not None:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("delete_role", "Role already deleted"),
      data=None,
    )

  try:
    crud_delete_role(db, role)
    return response.success(
      status=RestStatus.ok_200,
      meta=_meta("delete_role", "Role deleted"),
      data=_serialize_role(role),
    )
  except ValueError as e:
    return response.error(
      status=RestStatus.bad_request_400,
      meta=_meta("delete_role", str(e)),
      data=None,
    )
