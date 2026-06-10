import logging
import sys
import re
from datetime import datetime
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


class DailyRotatingFileHandler(TimedRotatingFileHandler):
  def __init__(self, log_dir: Path, stem: str = "requests", **kwargs):
    self.log_dir = log_dir
    self.stem = stem
    log_dir.mkdir(exist_ok=True)

    filename = str(
      log_dir / f"{stem}.{datetime.now().strftime('%Y-%m-%d')}.log")

    super().__init__(
      filename=filename,
      when="midnight",
      interval=1,
      **kwargs,
    )

    self.suffix = "%Y-%m-%d"
    self.namer = self._namer

  def _namer(self, default_name: str) -> str:
    match = re.match(
      rf"^(.*/{re.escape(self.stem)})\.\d{{4}}-\d{{2}}-\d{{2}}\.log\.(\d{{4}}-\d{{2}}-\d{{2}})$",
      default_name,
    )
    if match:
      return f"{match.group(1)}.{match.group(2)}.log"
    return default_name

  def doRollover(self):
    super().doRollover()
    self.baseFilename = str(
      self.log_dir / f"{self.stem}.{datetime.now().strftime('%Y-%m-%d')}.log"
    )


def setup_request_logger(name: str = "requests") -> logging.Logger:
  logger = logging.getLogger(name)

  if logger.handlers:
    return logger

  logger.setLevel(logging.INFO)

  file_handler = DailyRotatingFileHandler(
    log_dir=Path("logs"),
    stem="requests",
    backupCount=30,
    encoding="utf-8",
  )

  file_handler.setFormatter(logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
  ))

  logger.addHandler(file_handler)

  return logger
