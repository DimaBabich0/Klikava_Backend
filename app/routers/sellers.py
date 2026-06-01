from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Seller, User
from app.schemas import SellerCreate, SellerResponse
from app.services.access_manager import AccessManager
from app.crud import create_seller

router = APIRouter(prefix="/sellers", tags=["sellers"])


@router.post("", response_model=SellerResponse, status_code=status.HTTP_201_CREATED)
def create_seller_endpoint(
  seller_data: SellerCreate,
  current_user: User = Depends(AccessManager.get_current_user),
  db: Session = Depends(get_db)
):
  """Create a seller profile and grant SELLER role to the current user."""

  try:
    new_seller = create_seller(db, seller_data, current_user)
    return new_seller
  except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))


@router.get("/{seller_id}", response_model=SellerResponse)
def get_seller(seller_id: int, db: Session = Depends(get_db)):
  """Get seller information by ID."""

  seller = db.query(Seller).filter(Seller.id == seller_id).first()
  if not seller:
    raise HTTPException(status_code=404, detail="Seller not found")

  return seller


@router.get("", response_model=list[SellerResponse])
def list_sellers(
  skip: int = 0,
  limit: int = 100,
  db: Session = Depends(get_db)
):
  """List all sellers with pagination."""

  sellers = db.query(Seller).offset(skip).limit(limit).all()
  return sellers


@router.patch("/{seller_id}", response_model=SellerResponse)
def update_seller(
  seller_id: int,
  seller_data: SellerCreate,
  current_user: User = Depends(AccessManager.get_current_user),
  db: Session = Depends(get_db)
):
  """Update seller profile. Seller role or admin only."""

  seller = db.query(Seller).filter(Seller.id == seller_id).first()
  if not seller:
    raise HTTPException(status_code=404, detail="Seller not found")

  if not current_user.is_seller() and not current_user.is_admin():
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="User must have SELLER role or ADMIN role to update a seller profile"
    )

  if seller_data.store_name and seller_data.store_name != seller.store_name:
    if db.query(Seller).filter(Seller.store_name == seller_data.store_name).first():
      raise HTTPException(status_code=400, detail="Store name already exists")
    seller.store_name = seller_data.store_name

  if seller_data.description is not None:
    seller.description = seller_data.description

  if seller_data.picture_url is not None:
    seller.picture_url = seller_data.picture_url

  if seller_data.parent_id is not None:
    if seller_data.parent_id == seller.id:
      raise HTTPException(status_code=400, detail="Seller cannot be its own parent")
    if not db.query(Seller).filter(Seller.id == seller_data.parent_id).first():
      raise HTTPException(status_code=400, detail="Parent seller not found")
    seller.parent_id = seller_data.parent_id

  db.commit()
  db.refresh(seller)

  return seller
