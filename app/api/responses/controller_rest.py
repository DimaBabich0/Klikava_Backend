from http.server import BaseHTTPRequestHandler
import urllib.parse
from rest_response import RestResponse, RestStatus
from rest_error import RestError


class ControllerRest : 
  def __init__(self, handler: BaseHTTPRequestHandler):
    self.handler = handler
    self.params = handler.query_params


  def before_execution(self):
    self.rest_response = RestResponse()


  def serve(self):
    self.query_params = {}
    for key, value in (map(lambda input:None if input is None else urllib.parse.unquote_plus(input), (item.split('=', 1) if '=' in item else [item, None]))
      for item in self.handler.query_string.split('&') if len(item) > 0):
        self.query_params[key] = value if not key in self.query_params else [
          *(self.query_params[key] if isinstance(self.query_params[key],
            (list, tuple)) else [self.query_params[key]]),
          value
        ]

    self.before_execution()
    mname = 'do_' + self.handler.command
    if not hasattr(self, mname):
      self.rest_response.status = RestStatus.method_not_allowed_405
      self.rest_response.data = f"Method {self.handler.command} is not allowed for this resource"
    else:
      method = getattr(self, mname)
      # выполняем метод, передавая управление контроллеру
      try:
        method()
        self.send_success()
        return
      except RestError as err:
        self.rest_response.status = RestStatus(
          is_ok = False,
          code = err.code,
          phrase = err.phrase)
        self.rest_response.data = err.data
      except Exception as ex:
        self.rest_response.status = RestStatus(
          is_ok = False,
          code = 500,
          phrase = "Request processing error " + str(ex)
        )
    self.send_error()


  def send_success(self):
    self.handler.send_rest_response(self.rest_response)


  def send_error(self):
    self.handler.send_rest_response(self.rest_response)

