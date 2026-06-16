from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class ReviewPictureCreate(BaseModel):
  file_url: Optional[str] = None
  original_url: Optional[str] = None
  preview_url: Optional[str] = None
  thumbnail_url: Optional[str] = None
  sort_order: int = 0


class ReviewPictureResponse(BaseModel):
  id: int
  review_id: int
  file_url: Optional[str] = None
  original_url: Optional[str] = None
  preview_url: Optional[str] = None
  thumbnail_url: Optional[str] = None
  sort_order: int
  created_at: datetime

  class Config:
    from_attributes = True


class ReviewCreate(BaseModel):
  product_variant_id: int
  rating: int = Field(..., ge=1, le=5)
  comment: Optional[str] = Field(None, max_length=1024)
  pictures: List[ReviewPictureCreate] = Field(
    default_factory=list, max_length=10)


class ReviewUpdate(BaseModel):
  rating: Optional[int] = Field(None, ge=1, le=5)
  comment: Optional[str] = Field(None, max_length=1024)


class ReviewResponse(BaseModel):
  id: int
  user_id: int
  product_variant_id: int
  rating: int
  comment: Optional[str] = None
  created_at: datetime
  updated_at: Optional[datetime] = None
  deleted_at: Optional[datetime] = None
  pictures: List[ReviewPictureResponse] = []

  class Config:
    from_attributes = True
