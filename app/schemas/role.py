from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class RoleBase(BaseModel):
  name: str = Field(..., min_length=1, max_length=50)
  description: Optional[str] = None


class RoleCreate(RoleBase):
  name: str = Field(..., min_length=1, max_length=50)
  description: Optional[str] = None


class RoleResponse(RoleBase):
  id: int
  created_at: datetime

  class Config:
    from_attributes = True


class AssignRoleRequest(BaseModel):
  role_name: str = Field(..., min_length=1, max_length=50)
