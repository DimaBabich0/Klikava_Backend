from app.api.responses.rest_meta import RestMeta
from app.api.responses.rest_status import RestStatus


class RestResponse:
  def __init__(self,
               status: RestStatus | None = None,
               meta: RestMeta | None = None,
               data: any = None):
    self.status = status if status != None else RestStatus()
    self.meta = meta
    self.data = data

  def __json__(self):
    return {
      "status": self.status,
      "meta": self.meta,
      "data": self.data
    }
