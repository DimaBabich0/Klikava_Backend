from fastapi import Request, HTTPException, status
from typing import Callable, Any
from app.auth import verify_token
from app.database import DEBUG_MODE

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
    if request.url.path in AccessManager.PUBLIC_ROUTES:
      return await call_next(request)

    # Check token in headers
    token = request.headers.get("Authorization")
    if not token:
      print("--- Token not found in request headers ---")
      raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token not found in request headers"
      )

    # Check token validity
    try:
      user_data = AccessManager.validate_token(token)
      # Save user data in request
      request.state.user = user_data
    except Exception as e:
      print(f"--- Token validation failed: {e} ---")
      raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=str(e)
      )

    # Pass to the controller
    response = await call_next(request)
    return response

  @staticmethod
  def validate_token(token: str) -> dict:
    """Validate token and return user data"""
    token = token.replace("Bearer ", "")
    return verify_token(token)

  @staticmethod
  async def get_current_user(request: Request) -> dict:
    """Get the current user from the request"""
    # Check debug mode
    if DEBUG_MODE == "true":
      return "debug_user"
    if not hasattr(request.state, "user"):
      print("--- User data not found in request state ---")
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return request.state.user
