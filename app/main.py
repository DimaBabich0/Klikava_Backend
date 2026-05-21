from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from app.services.access_manager import AccessManager
from app.routers import health_router, user_router, seller_router, roles_router
from sqlalchemy import inspect
from contextlib import asynccontextmanager
from app.database import SessionLocal, engine, Base
from app.services.init_db import init_db, seed_tables


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
app.include_router(user_router)
app.include_router(roles_router)
# app.include_router(product_router)
app.include_router(seller_router)

# Add static files
app.mount("/static", StaticFiles(directory="app/static"), name="Static")

# Redirect from root point to API docs
@app.get("/", include_in_schema=False)
def root():
  """Redirect to API documentation"""
  return RedirectResponse(url="/docs")


def _is_public_openapi_path(path: str) -> bool:
  for public_route in AccessManager.PUBLIC_ROUTES:
    if path == public_route or (
      public_route != "/" and path.startswith(public_route)
    ):
      return True
  return False


def custom_openapi():
  if app.openapi_schema:
    return app.openapi_schema

  openapi_schema = get_openapi(
    title=app.title,
    version="1.0.0",
    routes=app.routes,
  )

  components = openapi_schema.setdefault("components", {})
  security_schemes = components.setdefault("securitySchemes", {})
  security_schemes["BearerAuth"] = {
    "type": "http",
    "scheme": "bearer",
    "bearerFormat": "JWT",
  }

  for path, path_item in openapi_schema.get("paths", {}).items():
    if _is_public_openapi_path(path):
      continue

    for operation in path_item.values():
      if isinstance(operation, dict):
        operation["security"] = [{"BearerAuth": []}]

  app.openapi_schema = openapi_schema
  return app.openapi_schema


app.openapi = custom_openapi
