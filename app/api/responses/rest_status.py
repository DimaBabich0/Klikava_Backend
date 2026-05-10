class RestStatus:
  def __init__(self,
               is_ok:bool=True,
               code:int=200,
               phrase:str="OK"):
    self.is_ok = is_ok
    self.code = code
    self.phrase = phrase
    
  def __json__(self):
    return {
      "isOK": self.is_ok,
      "code": self.code,
      "phrase": self.phrase
    }

RestStatus.ok_200 = RestStatus(True, 200, "OK")
RestStatus.created_201 = RestStatus(True, 201, "Created")
RestStatus.no_content_204 = RestStatus(True, 204, "No Content")
RestStatus.bad_request_400 = RestStatus(False, 400, "Bad Request")
RestStatus.unauthorized_401 = RestStatus(False, 401, "Unauthorized")
RestStatus.forbidden_403 = RestStatus(False, 403, "Forbidden")
RestStatus.not_found_404 = RestStatus(False, 404, "Not Found")
RestStatus.method_not_allowed_405 = RestStatus(False, 405, "Method Not Allowed")
RestStatus.internal_server_error_500 = RestStatus(False, 500, "Internal Server Error")
RestStatus.not_implemented_501 = RestStatus(False, 501, "Not Implemented")
RestStatus.service_unavailable_503 = RestStatus(False, 503, "Service Unavailable")