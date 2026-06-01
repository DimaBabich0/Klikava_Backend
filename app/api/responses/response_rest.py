import math

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.api.responses.rest_meta import RestLink, RestMeta, RestPagination
from app.api.responses.rest_response import RestResponse, RestStatus


class ResponseRest:

  def success(self, data=None, meta=None, status=RestStatus.ok_200):
    response = RestResponse(
      status=status,
      data=data,
      meta=meta,
    )

    return JSONResponse(
      status_code=status.code,
      content=jsonable_encoder(response)
    )

  def success_pagination(self, data=None, meta=None, status=RestStatus.ok_200, pagination=RestPagination):
    response = RestResponse(
      status=status,
      data=data,
      meta=meta,
      pagination=pagination
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

  def unauthorized(self, message="Unauthorized"):
    status = RestStatus.unauthorized_401
    response = RestResponse(
      status=status,
      meta=RestMeta(message=message),
      data=None,
    )
    return JSONResponse(
      status_code=status.code,
      content=jsonable_encoder(response)
    )

  def forbidden(self, message="Forbidden"):
    status = RestStatus.forbidden_403
    response = RestResponse(
      status=status,
      meta=RestMeta(message=message),
      data=None,
    )
    return JSONResponse(
      status_code=status.code,
      content=jsonable_encoder(response)
    )


  def build_pagination(self, page: int, per_page: int, total: int) -> RestPagination:
    total_pages = math.ceil(total / per_page)
    has_prev = page > 1
    has_next = page < total_pages

    links = [
      RestLink(name="firstPage", num=1, url=f"?perpage={per_page}"),
      RestLink(name="lastPage", num=total_pages,
                url=f"?page={total_pages}&perpage={per_page}"),
    ]
    if has_prev:
      links.append(RestLink(name="previousPage", num=page - 1,
                  url=f"?page={page - 1}&perpage={per_page}"))
    if has_next:
      links.append(RestLink(name="nextPage", num=page + 1,
                  url=f"?page={page + 1}&perpage={per_page}"))

    return RestPagination(
      per_page=per_page,
      page=page,
      total_pages=total_pages,
      current_page=page,
      total_items=total,
      has_prev=has_prev,
      has_next=has_next,
      links=links,
    )
