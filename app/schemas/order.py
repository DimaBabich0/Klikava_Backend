from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class OrderItemCreate(BaseModel):
  product_variant_id: int
  quantity: int = Field(..., gt=0)
  price_snapshot: Optional[float] = None
  discount_snapshot: Optional[float] = None
  final_price_snapshot: Optional[float] = None
  discount_item_id: Optional[int] = None


class OrderItemUpdate(BaseModel):
  quantity: Optional[int] = Field(None, gt=0)
  discount_item_id: Optional[int] = None


class OrderItemResponse(BaseModel):
  id: int
  order_id: int
  product_variant_id: int
  quantity: int
  price_snapshot: Optional[float] = None
  discount_snapshot: Optional[float] = None
  final_price_snapshot: Optional[float] = None
  discount_item_id: Optional[int] = None

  class Config:
    from_attributes = True


class OrderCreate(BaseModel):
  delivery_price: float = Field(0.0, ge=0)
  items: list[OrderItemCreate] = Field(default_factory=list)
  discount_item_id: Optional[int] = None


class OrderUpdate(BaseModel):
  status: Optional[str] = None
  delivery_price: Optional[float] = Field(None, ge=0)
  total_price: Optional[float] = Field(None, ge=0)
  discount_item_id: Optional[int] = None


class OrderResponse(BaseModel):
  id: int
  user_id: int
  status: str
  delivery_price: float
  total_price: float
  paid_at: Optional[datetime] = None
  created_at: datetime
  discount_item_id: Optional[int] = None
  items: list[OrderItemResponse] = Field(default_factory=list)

  class Config:
    from_attributes = True
