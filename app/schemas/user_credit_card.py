from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class UserCreditCardCreate(BaseModel):
  card_info_encrypted: str = Field(..., min_length=1, max_length=255)
  order_in_list: Optional[int] = None


class UserCreditCardUpdate(BaseModel):
  card_info_encrypted: Optional[str] = Field(None, min_length=1, max_length=255)
  order_in_list: Optional[int] = None


class UserCreditCardResponse(BaseModel):
  id: int
  user_id: int
  card_info_encrypted: str
  order_in_list: int
  created_at: datetime
  deleted_at: Optional[datetime] = None

  class Config:
    from_attributes = True
