from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class ProductPictureResponse(BaseModel):
  id: int
  file_url: str
  sort_order: int
  created_at: datetime

  class Config:
    from_attributes = True


class ProductVariantResponse(BaseModel):
  id: int
  sku_code: str
  price: float
  stock: int
  discount: int
  created_at: datetime

  class Config:
    from_attributes = True


class ProductVersionCreate(BaseModel):
  category_id: Optional[int] = None
  title: str
  description: Optional[str] = None
  slug: str


class ProductVersionUpdate(BaseModel):
  category_id: Optional[int] = None
  title: Optional[str] = None
  description: Optional[str] = None
  slug: Optional[str] = None


class ProductVariantCreate(BaseModel):
  sku_code: str
  price: float
  stock: int
  discount: int = 0


class ProductVariantUpdate(BaseModel):
  price: Optional[float] = None
  stock: Optional[int] = None
  discount: Optional[int] = None


class ProductPictureCreate(BaseModel):
  file_url: str
  sort_order: Optional[int] = 0


class ProductPictureUpdate(BaseModel):
  sort_order: Optional[int] = None


class ProductVersionResponse(BaseModel):
  id: int
  product_id: int
  category_id: Optional[int] = None
  title: str
  description: Optional[str] = None
  slug: str
  created_at: datetime
  variants: List[ProductVariantResponse] = []
  pictures: List[ProductPictureResponse] = []

  class Config:
    from_attributes = True


class ProductCreate(BaseModel):
  seller_id: int
  status: Optional[str] = "moderating"


class ProductUpdate(BaseModel):
  status: Optional[str] = None
  pageviews: Optional[int] = None


class ProductResponse(BaseModel):
  id: int
  seller_id: int
  status: str
  pageviews: int
  created_at: datetime
  current_version: Optional[ProductVersionResponse] = None

  class Config:
    from_attributes = True
