from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class SellerBase(BaseModel):
  store_name: str = Field(..., min_length=1, max_length=64)
  description: Optional[str] = None
  picture_url: Optional[str] = None
  parent_id: Optional[int] = None


class SellerCreate(SellerBase):
  pass


class SellerResponse(SellerBase):
  id: int
  rating: float
  created_at: datetime

  class Config:
    from_attributes = True
