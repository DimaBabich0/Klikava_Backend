from pydantic import BaseModel

class RestStatus(BaseModel):
  is_ok: bool = True
  code: int = 200
  phrase: str = "OK"

RestStatus.ok_200 = RestStatus(is_ok=True, code=200, phrase="OK")
RestStatus.created_201 = RestStatus(is_ok=True, code=201, phrase="Created")
RestStatus.no_content_204 = RestStatus(is_ok=True, code=204, phrase="No Content")
RestStatus.bad_request_400 = RestStatus(is_ok=False, code=400, phrase="Bad Request")
RestStatus.unauthorized_401 = RestStatus(is_ok=False, code=401, phrase="Unauthorized")
RestStatus.forbidden_403 = RestStatus(is_ok=False, code=403, phrase="Forbidden")
RestStatus.not_found_404 = RestStatus(is_ok=False, code=404, phrase="Not Found")
RestStatus.method_not_allowed_405 = RestStatus(is_ok=False, code=405, phrase="Method Not Allowed")
RestStatus.internal_server_error_500 = RestStatus(is_ok=False, code=500, phrase="Internal Server Error")
RestStatus.not_implemented_501 = RestStatus(is_ok=False, code=501, phrase="Not Implemented")
RestStatus.service_unavailable_503 = RestStatus(is_ok=False, code=503, phrase="Service Unavailable")