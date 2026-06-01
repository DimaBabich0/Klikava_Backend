from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class DiscountCreate(BaseModel):
  name: str = Field(..., min_length=1, max_length=100)
  description: Optional[str] = None
  start_date: datetime
  end_date: datetime
  discount_percentage: Decimal = Field(..., ge=0)
  price: Optional[Decimal] = None


class DiscountUpdate(BaseModel):
  name: Optional[str] = Field(None, min_length=1, max_length=100)
  description: Optional[str] = None
  start_date: Optional[datetime] = None
  end_date: Optional[datetime] = None
  discount_percentage: Optional[Decimal] = Field(None, ge=0)
  price: Optional[Decimal] = None


class DiscountResponse(BaseModel):
  id: int
  name: str
  description: Optional[str] = None
  start_date: datetime
  end_date: datetime
  discount_percentage: Decimal
  price: Optional[Decimal] = None

  class Config:
    from_attributes = True
