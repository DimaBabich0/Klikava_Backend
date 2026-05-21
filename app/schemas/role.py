from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class RoleBase(BaseModel):
  name: str = Field(..., min_length=1, max_length=50)
  description: Optional[str] = None
  create_level: int = Field(1, ge=0)
  read_level: int = Field(1, ge=0)
  update_level: int = Field(1, ge=0)
  deleted_level: int = Field(1, ge=0)


class RoleCreate(RoleBase):
  pass


class RoleResponse(RoleBase):
  id: int
  created_at: datetime

  class Config:
    from_attributes = True


class AssignRoleRequest(BaseModel):
  role_name: str = Field(..., min_length=1, max_length=50)
  login: str = Field(..., min_length=2, max_length=32)
  password: str = Field(..., min_length=8)
