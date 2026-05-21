import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Database configuration from environment variables
NAME = os.getenv("NAME")
PASSWORD = os.getenv("PASSWORD")
ADDRESS = os.getenv("ADDRESS")
PORT = os.getenv("PORT")
DATABASE = os.getenv("DATABASE")
DEBUG_MODE = os.getenv("DEBUG_MODE")
SECRET_KEY = os.getenv("SECRET_KEY")
DATABASE_URL = f"mysql+pymysql://{NAME}:{PASSWORD}@{ADDRESS}:{PORT}/{DATABASE}"


if not DATABASE_URL:
  raise RuntimeError("DATABASE_URL must be set in .env")

engine = create_engine(
  DATABASE_URL,
  pool_pre_ping=True,
  future=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()
