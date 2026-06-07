from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from app.services.access_manager import AccessManager
from app.routers import health_router, user_router, user_delivery_address_router, user_credit_card_router, pictures_router, shipment_router, categories_router, discounts_router, features_router, seller_router, roles_router, product_router, logs_router
from sqlalchemy import inspect
from contextlib import asynccontextmanager
from app.database import SessionLocal, engine, Base
from app.services.init_db import init_db, seed_tables
from app.services.config import CORS_ORIGINS
from app.services.logger import setup_logger, setup_request_logger
import time

logger = setup_logger(__name__)
request_logger = setup_request_logger("requests")

@asynccontextmanager
async def lifespan(app: FastAPI):
  """Check database and initialize tables on application startup."""
  try:
    # Check database connection
    with engine.connect() as connection:
      logger.info("Successful database connection")

    # Creating tables if they don't exist
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    if not existing_tables:
      logger.info("--- Tables not found. Creating tables... ---")
      init_db()
      seed_tables()
      logger.info("--- Tables initialized successfully ---")
    yield
  except Exception as e:
    logger.error(f"--- Error during DB initialization: {e} ---")
    logger.error(f"--- Backend failed to initialize ---")
    raise

app = FastAPI(title="Marketplace API", lifespan=lifespan)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
  """Middleware to log all HTTP requests with detailed information."""
  start_time = time.time()
  
  # Get request details
  client_host = request.client.host if request.client else "unknown"
  client_port = request.client.port if request.client else "unknown"
  method = request.method
  path = request.url.path
  query_params = str(dict(request.query_params)) if request.query_params else ""
  
  # Process request
  response = await call_next(request)
  
  # Calculate processing time
  process_time = time.time() - start_time
  
  # Get status code (works with different response types)
  status_code = getattr(response, "status_code", 500)
  status_text = "OK" if 200 <= status_code < 300 else ("Redirect" if 300 <= status_code < 400 else ("Client Error" if 400 <= status_code < 500 else "Server Error"))
  
  log_message = (
    f"{client_host}:{client_port} - {method} {path} - "
    f"Status: {status_code} {status_text} - "
    f"Time: {process_time:.3f}s"
  )
  if query_params and query_params != "{}":
    log_message += f" - Params: {query_params}"
  
  if status_code < 300:
    request_logger.info(log_message)
  elif status_code < 400:
    request_logger.info(log_message)
  elif status_code < 500:
    request_logger.warning(log_message)
  else:
    request_logger.error(log_message)
  
  return response

# Add access manager for access control
app.middleware("http")(AccessManager.verify_request)

# Add CORS for browser clients
app.add_middleware(
  CORSMiddleware,
  allow_origins=CORS_ORIGINS,
  allow_credentials="*" not in CORS_ORIGINS,
  allow_methods=["*"],
  allow_headers=["*"],
)

# Add controllers
app.include_router(health_router)
app.include_router(user_router)
app.include_router(user_delivery_address_router)
app.include_router(user_credit_card_router)
app.include_router(pictures_router)
app.include_router(shipment_router)
app.include_router(categories_router)
app.include_router(discounts_router)
app.include_router(features_router)
app.include_router(roles_router)
app.include_router(product_router)
app.include_router(seller_router)
app.include_router(logs_router)

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
