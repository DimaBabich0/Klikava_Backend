from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


PRODUCT_STATUSES = ("DRAFT", "PENDING", "APPROVED", "REJECTED")


class ProductFeatureInput(BaseModel):
  feature_id: int
  value: str
  value_type: str = "string"


class ProductFeatureResponse(BaseModel):
  id: int
  feature_id: int
  feature: dict | None = None
  value: str
  value_type: str

  class Config:
    from_attributes = True


class ProductPictureInput(BaseModel):
  original_url: Optional[str] = None
  preview_url: Optional[str] = None
  thumbnail_url: Optional[str] = None
  file_url: Optional[str] = None
  sort_order: int = 0


class ProductPictureResponse(BaseModel):
  id: int
  file_url: Optional[str] = None
  original_url: Optional[str] = None
  preview_url: Optional[str] = None
  thumbnail_url: Optional[str] = None
  sort_order: int
  created_at: datetime

  class Config:
    from_attributes = True


class ProductVariantInput(BaseModel):
  sku_code: str
  price: Decimal = Field(..., ge=0)
  stock: int = Field(0, ge=0)
  features: List[ProductFeatureInput] = Field(default_factory=list)


class ProductVariantResponse(BaseModel):
  id: int
  sku_code: str
  price: Decimal
  stock: int
  created_at: datetime
  features: List[ProductFeatureResponse] = Field(default_factory=list)
  product: dict | None = None
  base_price: Optional[Decimal] = None
  discount_amount: Optional[Decimal] = None
  final_price: Optional[Decimal] = None

  class Config:
    from_attributes = True


class ProductVersionCreate(BaseModel):
  category_id: Optional[int] = None
  title: str
  description: Optional[str] = None
  delivery_info: Optional[str] = None
  slug: str
  variants: List[ProductVariantInput] = Field(default_factory=list)
  pictures: List[ProductPictureInput] = Field(default_factory=list)


class ProductVersionUpdate(BaseModel):
  category_id: Optional[int] = None
  title: Optional[str] = None
  description: Optional[str] = None
  delivery_info: Optional[str] = None
  slug: Optional[str] = None
  variants: Optional[List[ProductVariantInput]] = None
  pictures: Optional[List[ProductPictureInput]] = None


class ProductVariantCreate(ProductVariantInput):
  pass


class ProductVariantUpdate(BaseModel):
  sku_code: Optional[str] = None
  price: Optional[Decimal] = Field(None, ge=0)
  stock: Optional[int] = Field(None, ge=0)
  features: Optional[List[ProductFeatureInput]] = None


class ProductPictureCreate(ProductPictureInput):
  pass


class ProductPictureUpdate(BaseModel):
  original_url: Optional[str] = None
  preview_url: Optional[str] = None
  thumbnail_url: Optional[str] = None
  file_url: Optional[str] = None
  sort_order: Optional[int] = None


class ProductVersionResponse(BaseModel):
  id: int
  product_id: int
  category_id: Optional[int] = None
  category: dict | None = None
  title: str
  description: Optional[str] = None
  delivery_info: Optional[str] = None
  slug: str
  version_number: int
  created_at: datetime
  variants: List[ProductVariantResponse] = Field(default_factory=list)
  pictures: List[ProductPictureResponse] = Field(default_factory=list)

  class Config:
    from_attributes = True


class ProductCreate(ProductVersionCreate):
  seller_id: int
  status: str = "PENDING"


class ProductUpdate(ProductVersionUpdate):
  status: Optional[str] = None
  pageviews: Optional[int] = None


class ProductStatusUpdate(BaseModel):
  status: str


class ReviewCreate(BaseModel):
  product_variant_id: int
  rating: int = Field(..., ge=1, le=5)
  comment: Optional[str] = None


class ReviewUpdate(BaseModel):
  rating: Optional[int] = Field(None, ge=1, le=5)
  comment: Optional[str] = None


class ReviewResponse(BaseModel):
  id: int
  user_id: int
  product_variant_id: int
  rating: int
  comment: Optional[str] = None
  created_at: datetime
  updated_at: Optional[datetime] = None

  class Config:
    from_attributes = True


class SellerBriefResponse(BaseModel):
  id: int
  store_name: str
  rating: float
  picture_url: Optional[str] = None

  class Config:
    from_attributes = True


class ProductResponse(BaseModel):
  id: int
  seller_id: int
  current_version_id: Optional[int] = None
  status: str
  pageviews: int
  unique_pageviews: int
  favorite_count: int
  order_count: int
  sales_count: int
  average_rating: float
  reviews_count: int
  created_at: datetime
  current_version: Optional[ProductVersionResponse] = None
  seller: Optional[SellerBriefResponse] = None
  reviews: List[ReviewResponse] = Field(default_factory=list)
  similar_products: List[dict] = Field(default_factory=list)
  seller_products: List[dict] = Field(default_factory=list)
  recommended_products: List[dict] = Field(default_factory=list)

  class Config:
    from_attributes = True
