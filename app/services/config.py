import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent.parent.parent
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
