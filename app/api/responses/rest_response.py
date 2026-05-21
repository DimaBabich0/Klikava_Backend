from pydantic import BaseModel
from typing import Any, Optional

from app.api.responses.rest_status import RestStatus
from app.api.responses.rest_meta import RestMeta


class RestResponse(BaseModel):
  status: RestStatus
  meta: Optional[RestMeta] = None
  data: Any = None
