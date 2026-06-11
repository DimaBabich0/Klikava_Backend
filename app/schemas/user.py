from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List
from .role import RoleResponse


class UserCreate(BaseModel):
  login: str = Field(..., min_length=2, max_length=32)
  email: EmailStr
  password: str = Field(..., min_length=8)
  name: str = Field(..., min_length=1, max_length=32)
  phone_number: Optional[str] = None
  birthday: Optional[datetime] = None
  avatar_url: Optional[str] = None


class UserLogin(BaseModel):
  login_email: str
  password: str


class UserBase(BaseModel):
  name: str
  email: str
  phone_number: Optional[str] = None
  birthday: Optional[datetime]
  avatar_url: Optional[str] = None


class UserUpdate(BaseModel):
  name: Optional[str] = Field(None, min_length=1, max_length=32)
  email: Optional[EmailStr] = None
  phone_number: Optional[str] = None
  birthday: Optional[datetime] = None
  password: Optional[str] = Field(None, min_length=8)
  avatar_url: Optional[str] = None


class UserUpdateRole(BaseModel):
  login: str = Field(..., min_length=2, max_length=255)
  role_id: int


class UserBanRequest(BaseModel):
  reason: Optional[str] = None


class UserResponse(UserBase):
  id: int
  login: Optional[str] = None
  status: Optional[str] = None
  picture_url: Optional[str] = None
  created_at: Optional[datetime] = None
  deleted_at: Optional[datetime] = None
  roles: List[RoleResponse] = []

  class Config:
    from_attributes = True
