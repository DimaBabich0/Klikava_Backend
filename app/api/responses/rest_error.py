class RestError(Exception):
  def __init__(self,
               code:int=500,
               phrase:str="Internal Server Error",
               data:str|None=None):
    self.code = code
    self.phrase = phrase
    self.data = data

