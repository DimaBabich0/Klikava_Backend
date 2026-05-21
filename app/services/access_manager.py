from fastapi import Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Callable, Any
from types import SimpleNamespace
from app.services.auth import decode_token
from app.database import DEBUG_MODE, get_db
from app.models import User


class AccessManager:
  """Access manager for handling all requests and verifying access"""

  # Public routes that do not require authentication
  PUBLIC_ROUTES = [
    "/",
    "/users/login",
    "/users/register",
    "/docs",
    "/openapi.json",
    "/health",
  ]

  @staticmethod
  async def verify_request(request: Request, call_next: Callable) -> Any:
    """Middleware for verifying all incoming requests"""

    # Check debug mode
    if DEBUG_MODE == "true":
      return await call_next(request)

    # Check public routes
    for public_route in AccessManager.PUBLIC_ROUTES:
      if request.url.path == public_route or (
        public_route != "/" and request.url.path.startswith(public_route)
      ):
        return await call_next(request)

    # Check token in headers
    token = request.headers.get("Authorization")
    if not token:
      print("--- Token not found in request headers ---")
      return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Token not found in request headers"}
      )

    # Check token validity
    try:
      if DEBUG_MODE == "true":
        user_data = {"sub": "debug_user", "roles": ["ADMIN"]}
      else:
        user_data = AccessManager.validate_token(token)
      # Save user data in request
      request.state.user = user_data
    except Exception as e:
      print(f"--- Token validation failed: {e} ---")
      return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": str(e)}
      )

    # Pass to the controller
    response = await call_next(request)
    return response

  @staticmethod
  def validate_token(token: str) -> dict:
    """Validate token and return user data"""
    print(token)
    if not token.startswith("Bearer "):
      return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Invalid token format"}
      )

    token = token.split(" ", 1)[1]
    payload = decode_token(token)
    print(payload)
    if not payload:
      return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Invalid token"}
      )
    return payload

  @staticmethod
  async def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Get the current user from the request."""

    if DEBUG_MODE == "true" and not hasattr(request.state, "user"):
      return AccessManager._get_debug_user()

    if not hasattr(request.state, "user"):
      print("--- User data not found in request state ---")
      return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "User data not found in request state"}
      )

    payload = request.state.user
    if DEBUG_MODE == "true" and payload.get("sub") == "debug_user":
      return AccessManager._get_debug_user()

    try:
      user_id = int(payload["sub"])
    except (TypeError, ValueError, KeyError):
      return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Invalid token payload"}
      )

    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.is_deleted() or not user.is_active():
      return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "User not found, deleted or inactive"}
      )

    return user

  @staticmethod
  def _get_debug_user() -> User:
    """Return a lightweight debug user object for DEBUG_MODE."""
    return SimpleNamespace(
      id=0,
      name="Debug",
      email="debug@example.com",
      phone_number=None,
      birthday=None,
      avatar_url=None,
      roles=[
        SimpleNamespace(name="ADMIN"),
        SimpleNamespace(name="SELLER")
      ],
      is_deleted=lambda: False,
      is_active=lambda: True,
      is_seller=lambda: True,
      is_admin=lambda: True,
      is_moderator=lambda: False,
    )


  @staticmethod
  def require_role(required_role: str):
    """Dependency factory for role checks."""
    def check_role(current_user: User = Depends(AccessManager.get_current_user)):
      if not any(role.name == required_role for role in current_user.roles):
        return JSONResponse(
          status_code=status.HTTP_403_FORBIDDEN,
          content={"detail": f"User does not have required role: {required_role}"}
        )
      return current_user
    return check_role
