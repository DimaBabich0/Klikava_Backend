from app.api.responses.rest_pagination import RestPagination


class RestMeta:
  def __init__(self, pagination: RestPagination | None):
    self.pagination = pagination

  def __json__(self):
    return {
      "pagination": self.pagination
    }
