from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.models import User
from app.auth import decode_token
from app.database import get_db


def get_current_user(token: str, db: Session = Depends(get_db)) -> User:
  """
  Extract and validate user from JWT token.
  """
  if not token or not token.startswith("Bearer "):
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Invalid or missing token"
    )

  token = token.replace("Bearer ", "")
  payload = decode_token(token)

  if not payload or "sub" not in payload:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Invalid token"
    )

  user = db.query(User).filter(User.id == int(payload["sub"])).first()
  if not user or user.is_deleted():
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="User not found or deleted"
    )

  return user


def require_role(required_role: str):
  """
  Dependency to check if user has required role.
  """
  def check_role(current_user: User = Depends(get_current_user)):
    if not any(role.name == required_role for role in current_user.roles):
      raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"User does not have required role: {required_role}"
      )
    return current_user
  return check_role
