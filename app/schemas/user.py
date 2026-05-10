from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List
from .role import RoleResponse


class UserCreate(BaseModel):
  username: str = Field(..., min_length=2, max_length=32)
  email: EmailStr
  password: str = Field(..., min_length=8)
  name: str = Field(..., min_length=1, max_length=32)
  birthday: Optional[datetime] = None


class UserLogin(BaseModel):
  email: EmailStr
  password: str


class UserBase(BaseModel):
  username: str
  name: str
  email: str
  status: str
  birthday: Optional[datetime]


class UserResponse(UserBase):
  id: int
  created_at: datetime
  roles: List[RoleResponse] = []

  class Config:
    from_attributes = True
