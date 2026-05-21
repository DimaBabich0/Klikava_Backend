from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.api.responses.rest_response import RestResponse, RestStatus


class ControllerRest:

  def success(self, data=None, meta=None, status=RestStatus.ok_200):
    response = RestResponse(
      status=status,
      data=data,
      meta=meta
    )

    return JSONResponse(
      status_code=status.code,
      content=jsonable_encoder(response)
    )

  def error(self, data=None, meta=None, status=RestStatus.internal_server_error_500):
    response = RestResponse(
      status=status,
      meta=meta,
      data=data
    )

    return JSONResponse(
      status_code=status.code,
      content=jsonable_encoder(response)
    )
