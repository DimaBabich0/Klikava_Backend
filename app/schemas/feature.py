from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class FeatureCreate(BaseModel):
  title: str = Field(..., min_length=1, max_length=64)
  is_primary: bool = False


class FeatureUpdate(BaseModel):
  title: Optional[str] = Field(None, min_length=1, max_length=64)
  is_primary: Optional[bool] = None


class FeatureResponse(BaseModel):
  id: int
  title: str
  is_primary: bool
  created_at: datetime

  class Config:
    from_attributes = True
