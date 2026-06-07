import logging
import sys
import re
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


def setup_logger(name: str = "app") -> logging.Logger:
  logger = logging.getLogger(name)

  if logger.handlers:
    return logger

  logger.setLevel(logging.DEBUG)

  formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
  )

  console_handler = logging.StreamHandler(sys.stdout)
  console_handler.setFormatter(formatter)
  logger.addHandler(console_handler)

  return logger


def setup_request_logger(name: str = "requests") -> logging.Logger:
  """Setup logger for HTTP requests with daily rotation."""
  logger = logging.getLogger(name)

  if logger.handlers:
    return logger

  logger.setLevel(logging.INFO)

  logs_dir = Path("logs")
  logs_dir.mkdir(exist_ok=True)

  file_handler = TimedRotatingFileHandler(
    filename=str(logs_dir / "requests.log"),
    when="midnight",
    interval=1,
    backupCount=30,
    encoding="utf-8"
  )

  file_handler.suffix = "%Y-%m-%d"
  
  def namer(name):
    match = re.match(r"^(.*/requests)\.log\.(\d{4}-\d{2}-\d{2})$", str(name))
    if match:
      return f"{match.group(1)}.{match.group(2)}.log"
    return name
  
  file_handler.namer = namer
  
  formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
  )

  file_handler.setFormatter(formatter)
  logger.addHandler(file_handler)

  return logger
