from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class UserDeliveryAddressCreate(BaseModel):
  address_line: str = Field(..., min_length=1, max_length=255)


class UserDeliveryAddressUpdate(BaseModel):
  address_line: Optional[str] = Field(None, min_length=1, max_length=255)


class UserDeliveryAddressResponse(BaseModel):
  id: int
  user_id: int
  address_line: str
  created_at: datetime
  deleted_at: Optional[datetime] = None

  class Config:
    from_attributes = True
