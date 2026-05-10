from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class SellerBase(BaseModel):
  store_name: str = Field(..., min_length=1, max_length=255)
  description: Optional[str] = None


class SellerCreate(SellerBase):
  pass


class SellerResponse(SellerBase):
  id: int
  user_id: int
  rating: float
  created_at: datetime

  class Config:
    from_attributes = True
