class RestLink:
  def __init__(self, name: str, num: int, url: str):
    self.name = name
    self.num = num
    self.url = url

  def __json__(self):
    return {
      "name": self.name,
      "num": self.num,
      "url": self.url
    }
