import os
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from jose import jwt, JWTError
from passlib.context import CryptContext
from typing import Optional, Dict, Any
from app.database import SECRET_KEY

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 2

pwd_context = CryptContext(schemes=["bcrypt"])


def generate_salt() -> str:
  """Generate a secure random salt for password storage."""
  return secrets.token_hex(16)


def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
  """
  Hash password with bcrypt and return (hash, salt).
  If salt is provided, use it; otherwise generate a new one.
  """
  if salt is None:
    salt = generate_salt()

  # Combine password with salt before hashing for extra security
  salted_password = f"{password}{salt}"
  password_hash = pwd_context.hash(salted_password)

  return password_hash, salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
  """Verify password against stored hash using the salt."""
  salted_password = f"{password}{salt}"
  return pwd_context.verify(salted_password, password_hash)


def create_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
  """
  Create JWT token with expiration

  Args:
    data: Dictionary to encode (should include 'sub' for subject/user_id)
    expires_delta: Custom expiration time; defaults to ACCESS_TOKEN_EXPIRE_HOURS

  Returns:
    Encoded JWT token
  """
  to_encode = data.copy()

  if expires_delta:
    expire = datetime.utcnow() + expires_delta
  else:
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)

  to_encode["exp"] = expire
  encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

  return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
  """
  Decode and validate JWT token

  Args:
    token: JWT token to decode

  Returns:
    Decoded payload or None if invalid
  """
  try:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return payload
  except JWTError:
    return None

