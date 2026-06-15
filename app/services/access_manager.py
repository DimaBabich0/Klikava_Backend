from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Callable, Any
from types import SimpleNamespace
from app.api.responses.response_rest import ResponseRest
from app.services.auth import decode_token
from app.services.config import DEBUG_MODE
from app.database import get_db
from app.models import User
from app.services.logger import setup_logger

logger = setup_logger(__name__)
response = ResponseRest()

class AccessManager:
  """Access manager for handling all requests and verifying access"""

  # Public routes that do not require authentication
  PUBLIC_ROUTES = [
    ("/", ["GET"]),
    ("/docs", ["GET"]),
    ("/openapi.json", ["GET"]),
    ("/health", ["GET"]),
    ("/users/login", ["POST"]),
    ("/users/register", ["POST"]),
    ("/products", ["GET"]),
    ("/categories", ["GET"]),
    ("/discounts", ["GET"]),
    ("/features", ["GET"]),
    ("/sellers", ["GET"]),
    ("/favicon.ico", ["GET"]),
  ]

  STATIC_ROUTES = [
    "/static/user_pictures/",
    "/static/product_pictures/",
  ]

  @staticmethod
  async def verify_request(request: Request, call_next: Callable) -> Any:
    """Middleware for verifying all incoming requests"""

    # Check debug mode
    if DEBUG_MODE == "true":
      return await call_next(request)

    path = request.url.path
    method = request.method

    # Check public routes
    if AccessManager.is_public_route(path, method):
      return await call_next(request)

    # Check token in headers
    token = request.headers.get("Authorization")
    if not token:
      logger.error("Token not found in request headers")
      return response.unauthorized("Token not found in request headers")

    # Check token validity
    try:
      if DEBUG_MODE == "true":
        user_data = {"sub": "debug_user", "roles": ["ADMIN"]}
      else:
        user_data = AccessManager.validate_token(token)
      # Save user data in request
      request.state.user = user_data
    except Exception as e:
      logger.error(f"Token validation failed: {e} ---")
      return response.unauthorized("Invalid token")


    # Pass to the controller
    next_response = await call_next(request)
    return next_response

  @staticmethod
  def is_public_route(path: str, method: str) -> bool:
    for route, methods in AccessManager.PUBLIC_ROUTES:
      if path == route and method in methods:
        return True

    for route in AccessManager.STATIC_ROUTES:
      if path.startswith(route):
        return True

    return False

  @staticmethod
  def validate_token(token: str) -> dict:
    """Validate token and return user data"""
    if not token.startswith("Bearer "):
      raise ValueError("Invalid token format")

    token = token.split(" ", 1)[1]
    payload = decode_token(token)
    if not payload:
      raise ValueError("Invalid token")
    return payload

  @staticmethod
  async def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Get the current user from the request."""

    if DEBUG_MODE == "true" and not hasattr(request.state, "user"):
      return AccessManager._get_debug_user()

    if not hasattr(request.state, "user"):
      logger.error("--- User data not found in request state ---")
      raise HTTPException(
        status_code=401,
        detail="User data not found in request state",
      )

    payload = request.state.user
    if DEBUG_MODE == "true" and payload.get("sub") == "debug_user":
      return AccessManager._get_debug_user()

    try:
      user_id = int(payload["sub"])
    except (TypeError, ValueError, KeyError):
      raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.is_deleted() or not user.is_active():
      raise HTTPException(
        status_code=401,
        detail="User not found, deleted or inactive",
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
        raise HTTPException(
          status_code=403,
          detail=f"User does not have required role: {required_role}",
        )
      return current_user
    return check_role
