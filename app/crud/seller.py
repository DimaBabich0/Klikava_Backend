from sqlalchemy.orm import Session
from app.models import Seller
from app.schemas import SellerCreate


def create_seller(db: Session, seller: SellerCreate, user_id: int):
  if get_seller_by_user_id(db, user_id):
    raise ValueError("User already has a seller profile")

  if db.query(Seller).filter(Seller.store_name == seller.store_name).first():
    raise ValueError("Store name already exists")

  db_seller = Seller(
    user_id=user_id,
    store_name=seller.store_name,
    description=seller.description,
    rating=0.0
  )
  db.add(db_seller)
  db.commit()
  db.refresh(db_seller)
  return db_seller


def get_seller_by_id(db: Session, seller_id: int):
  return db.query(Seller).filter(Seller.id == seller_id).first()


def get_seller_by_user_id(db: Session, user_id: int):
  return db.query(Seller).filter(Seller.user_id == user_id).first()


def get_sellers(db: Session, skip: int = 0, limit: int = 100):
  return db.query(Seller).offset(skip).limit(limit).all()
