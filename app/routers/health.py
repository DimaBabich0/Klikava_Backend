from fastapi import APIRouter, HTTPException, status
from app.services.init_db import init_db, seed_tables, delete_all_data
from app.services.config import SECRET_KEY
from app.api.responses.response_rest import ResponseRest
from app.api.responses.rest_meta import RestMeta
from app.api.responses.rest_status import RestStatus
router = APIRouter(tags=["health"])
response = ResponseRest()

def _meta(action: str, message: str | None = None) -> RestMeta:
  return RestMeta(action=action, message=message)

@router.get("/health")
def health_check():
  """Health check endpoint."""
  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("health_check", "API is healthy"),
    data={"status": "ok", "message": "API is healthy"}
  )

@router.post("/reset-db", include_in_schema=False)
def reset_db(Password: str):
  if Password != SECRET_KEY:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid password")
  delete_all_data()
  init_db()
  seed_tables()
  return {"message": "Database recreated"}
