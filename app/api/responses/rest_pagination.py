import math


class RestPagination:
  def __init__(self,
               per_page: int,
               page: int,
               total_items: int,
               total_pages: int | None,
               links,
               has_prev: bool | None = None,
               has_next: bool | None = None):
    self.per_page = per_page
    self.page = page
    self.total_items = total_items
    self.total_pages = total_pages if total_pages != None else math.ceil(
      total_items / per_page)
    self.links = links
    self.has_prev = page > 1 if has_prev is None else has_prev
    self.has_next = page < self.total_pages if has_next is None else has_next

  def __json__(self):
    return {
      "perPage": self.per_page,
      "currentPage": self.page,
      "totalItems": self.total_items,
      "totalPages": self.total_pages,
      "hasPrev": self.has_prev,
      "hasNext": self.has_next,
      "links": self.links
    }
