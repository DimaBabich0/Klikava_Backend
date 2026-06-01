from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ShipmentCreate(BaseModel):
  status: str = Field(..., min_length=1, max_length=50)
  tracking_number: Optional[str] = Field(None, max_length=100)
  created_at: Optional[datetime] = None


class ShipmentUpdate(BaseModel):
  status: Optional[str] = Field(None, min_length=1, max_length=50)
  tracking_number: Optional[str] = Field(None, max_length=100)
  created_at: Optional[datetime] = None


class ShipmentResponse(BaseModel):
  id: int
  order_id: int
  tracking_number: Optional[str]
  status: str
  created_at: datetime

  class Config:
    from_attributes = True
