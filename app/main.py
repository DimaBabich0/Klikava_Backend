from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from app.core.access_manager import AccessManager
from app.routers import user_router, product_router, health_router, seller_router, roles_router
from sqlalchemy import inspect

from contextlib import asynccontextmanager

from app.database import SessionLocal, engine, Base
from app.models import User, Role, Seller
from app.auth import hash_password, verify_password, create_token, decode_token
from app.init_db import init_db, seed_tables

@asynccontextmanager
async def lifespan(app: FastAPI):
  """Check database and initialize tables on application startup."""
  try:
    # Check database connection
    with engine.connect() as connection:
      print("--- Successful database connection ---")

    # Creating tables if they don't exist
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    if not existing_tables:
      print("--- Tables not found. Creating tables... ---")
      init_db()
      seed_tables()
      print("--- Tables initialized successfully ---")
    yield
  except Exception as e:
    print(f"--- Error during DB initialization: {e} ---")
    print(f"--- Backend failed to initialize ---")
    raise

app = FastAPI(title="Marketplace API", lifespan=lifespan)

# Add access manager for access control
app.middleware("http")(AccessManager.verify_request)

# Add controllers
app.include_router(health_router)
app.include_router(user_router, prefix="/users")
app.include_router(roles_router)
app.include_router(product_router)
app.include_router(seller_router)

# Add static files
app.mount("/static", StaticFiles(directory="app/static"), name="Static")


@app.get("/", include_in_schema=False)
async def root():
  """Redirect to API documentation"""
  return RedirectResponse(url="/docs")


def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()
