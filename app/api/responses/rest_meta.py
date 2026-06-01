from pydantic import BaseModel
from typing import Optional, List


class RestLink(BaseModel):
  name: str
  num: int
  url: str


class RestPagination(BaseModel):
  per_page: int
  current_page: int
  total_items: int
  total_pages: int
  has_prev: bool
  has_next: bool
  links: List[RestLink] = []


class RestMeta(BaseModel):
  action: Optional[str] = None
  message: Optional[str] = None
  pagination: Optional[RestPagination] = None
