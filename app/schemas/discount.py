from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


DISCOUNT_TYPES = ("PERCENTAGE", "FIXED", "COUPON")
DISCOUNT_TARGET_TYPES = ("PRODUCT", "CATEGORY", "SELLER")


class DiscountCreate(BaseModel):
  name: str = Field(..., min_length=1, max_length=100)
  description: Optional[str] = None
  start_date: datetime
  end_date: datetime
  discount_type: str = "PERCENTAGE"
  value: Decimal = Field(..., ge=0)
  coupon_code: Optional[str] = None
  target_type: str
  target_id: int
  is_active: bool = True


class DiscountUpdate(BaseModel):
  name: Optional[str] = Field(None, min_length=1, max_length=100)
  description: Optional[str] = None
  start_date: Optional[datetime] = None
  end_date: Optional[datetime] = None
  discount_type: Optional[str] = None
  value: Optional[Decimal] = Field(None, ge=0)
  coupon_code: Optional[str] = None
  target_type: Optional[str] = None
  target_id: Optional[int] = None
  is_active: Optional[bool] = None


class DiscountResponse(BaseModel):
  id: int
  name: str
  description: Optional[str] = None
  start_date: datetime
  end_date: datetime
  discount_type: str
  value: Decimal
  coupon_code: Optional[str] = None
  target_type: str
  target_id: int
  is_active: bool

  class Config:
    from_attributes = True
