from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class CategoryCreate(BaseModel):
  title: str = Field(..., min_length=1, max_length=100)
  description: Optional[str] = None
  parent_id: Optional[int] = None
  order_in_price: Optional[int] = None

  @field_validator("parent_id", "order_in_price", mode="before")
  @classmethod
  def zero_to_none(cls, v):
    if v == 0:
      return None
    return v


class CategoryUpdate(BaseModel):
  title: Optional[str] = Field(None, min_length=1, max_length=100)
  description: Optional[str] = None
  parent_id: Optional[int] = None
  order_in_price: Optional[int] = None

  @field_validator("parent_id", "order_in_price", mode="before")
  @classmethod
  def zero_to_none(cls, v):
    if v == 0:
      return None
    return v


class CategoryResponse(BaseModel):
  id: int
  parent_id: Optional[int] = None
  title: str
  description: Optional[str] = None
  order_in_price: Optional[int] = None
  created_at: datetime

  class Config:
    from_attributes = True
