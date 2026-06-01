from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
  title: str = Field(..., min_length=1, max_length=100)
  description: Optional[str] = None
  parent_id: Optional[int] = None
  order_in_price: Optional[int] = None


class CategoryUpdate(BaseModel):
  title: Optional[str] = Field(None, min_length=1, max_length=100)
  description: Optional[str] = None
  parent_id: Optional[int] = None
  order_in_price: Optional[int] = None


class CategoryResponse(BaseModel):
  id: int
  parent_id: Optional[int] = None
  title: str
  description: Optional[str] = None
  order_in_price: Optional[int] = None
  created_at: datetime

  class Config:
    from_attributes = True
