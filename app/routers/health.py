from fastapi import APIRouter, HTTPException, status
from app.init_db import init_db, seed_tables, delete_all_data

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
  """Health check endpoint."""
  return {"status": "ok"}

@router.post("/reset-db", include_in_schema=False)
def reset_db(Password: str):
  if Password != "your_secret_password":
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid password")
  delete_all_data()
  init_db()
  seed_tables()
  return {"message": "Database recreated"}