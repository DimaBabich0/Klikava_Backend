from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Role
from app.schemas import RoleResponse, AssignRoleRequest, RoleCreate, UserResponse
from app.services.access_manager import AccessManager
from app.crud import get_roles, create_role, assign_role_to_user, remove_role_from_user as crud_remove_role_from_user

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("", response_model=list[RoleResponse])
def list_roles(db: Session = Depends(get_db)):
  """List all available roles."""
  try:
    roles = get_roles(db)
    return roles
  except Exception as e:
    raise HTTPException(
      status_code=500, detail="Error fetching roles: " + str(e))


@router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(
  role_data: RoleCreate,
  current_user: User = Depends(AccessManager.require_role("ADMIN")),
  db: Session = Depends(get_db)
):
  """Create a new role (Admin only)."""
  try:
    new_role = create_role(db, role_data)
    return new_role
  except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))


@router.post("/assign/{user_id}", status_code=status.HTTP_200_OK)
def assign_role_to_user(
  user_id: int,
  role_request: AssignRoleRequest,
  current_user: User = Depends(AccessManager.require_role("ADMIN")),
  db: Session = Depends(get_db)
):
  """Assign a role to a user (Admin only)"""
  try:
    user = assign_role_to_user(
      db,
      user_id,
      role_request.role_name,
      role_request.login,
      role_request.password
    )
    return {
      "message": f"Role {role_request.role_name} assigned to user {user_id}",
      "user": UserResponse.model_validate(user)
    }
  except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))

