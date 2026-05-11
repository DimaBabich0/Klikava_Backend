from fastapi import APIRouter, HTTPException, status, Depends
from app.api.responses.rest_response import RestResponse
from app.services.access_manager import AccessManager

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/{product_id}", response_model=None)
async def get_product(
  product_id: int,
  current_user: dict = Depends(AccessManager.get_current_user)
):
  """Get product"""
  # Integration with your models.py and database.py
  from app.database import get_db
  from app.models import Product

  db = get_db()
  product = db.query(Product).filter(Product.id == product_id).first()
  if not product:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

  return RestResponse(
    success=True,
    data={"id": product.id, "name": product.name},
    message="Product retrieved successfully"
  )
