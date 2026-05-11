from fastapi import APIRouter, Request, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.responses.rest_response import RestResponse
from app.services.access_manager import AccessManager
from app.auth import create_token, decode_token
from app.crud.user import get_user_by_id
from app.database import get_db
from app.schemas import (
  UserCreate, UserLogin, UserResponse, RoleResponse, TokenResponse,
  AssignRoleRequest, RoleCreate
)
from app.crud import create_user, authenticate_user as crud_authenticate_user
from app.api.responses.rest_status import RestStatus

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
  """Register a new user with default BUYER role"""
  try:
    new_user = create_user(db, user_data)
    return new_user
  except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
  """Login user and return JWT token"""

  is_valid, db_user = crud_authenticate_user(
    db, credentials.email, credentials.password)
  if not is_valid:
    raise HTTPException(status_code=401, detail="Invalid credentials")

  # Create token with user ID and roles
  token_data = {
    "sub": str(db_user.id),
    "email": db_user.email,
    "roles": [role.name for role in db_user.roles]
  }

  access_token = create_token(token_data)

  return {
    "access_token": access_token,
    "token_type": "bearer",
    "user": db_user
  }


@router.get("/{user_id}", response_model=None)
def get_user(
  user_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(AccessManager.get_current_user)
):
  """Get user by ID"""
  user = get_user_by_id(db, user_id)
  if not user:
    return RestResponse(
      status=RestStatus.not_found_404,
      data=None,
      meta="User not found"
    )

  return RestResponse(
    status=RestStatus.ok_200,
    data=user,
    meta="User found"
  )



@router.get("/{user_id}/roles", response_model=None)
def get_users_roles(
  user_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(AccessManager.get_current_user)
):
  """Get user's roles by user ID"""
  user = get_user_by_id(db, user_id)
  if not user:
    return RestResponse(
      status=RestStatus.not_found_404,
      data=None,
      meta="User not found"
    )

  return RestResponse(
    status=RestStatus.ok_200,
    data=user.roles,
    meta="User roles found"
  )
