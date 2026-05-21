import secrets

from sqlalchemy.orm import Session
from app.services.auth import hash_password
from app.models import Role, Seller, User, UserRoles
from app.schemas import SellerCreate


def _assign_seller_role(db: Session, user: User):
  seller_role = db.query(Role).filter(Role.name == "SELLER").first()
  if not seller_role:
    raise ValueError("SELLER role not found")

  existing_role = db.query(UserRoles).filter(
    UserRoles.user_id == user.id,
    UserRoles.role_id == seller_role.id,
  ).first()
  if existing_role:
    return

  login = f"seller.user.{user.id}"
  if db.query(UserRoles).filter(UserRoles.login == login).first():
    raise ValueError("Generated seller login already exists")

  password_hash, password_salt = hash_password(secrets.token_urlsafe(32))
  db.add(UserRoles(
    user=user,
    role=seller_role,
    login=login,
    password_hash=password_hash,
    password_salt=password_salt,
    status="active",
  ))


def create_seller(db: Session, seller: SellerCreate, user: User):
  if db.query(Seller).filter(Seller.store_name == seller.store_name).first():
    raise ValueError("Store name already exists")

  if seller.parent_id and not get_seller_by_id(db, seller.parent_id):
    raise ValueError("Parent seller not found")

  db_seller = Seller(
    parent_id=seller.parent_id,
    picture_url=seller.picture_url,
    store_name=seller.store_name,
    description=seller.description,
    rating=0.0
  )
  db.add(db_seller)
  _assign_seller_role(db, user)
  db.commit()
  db.refresh(db_seller)
  return db_seller


def get_seller_by_id(db: Session, seller_id: int):
  return db.query(Seller).filter(Seller.id == seller_id).first()


def get_sellers(db: Session, skip: int = 0, limit: int = 100):
  return db.query(Seller).offset(skip).limit(limit).all()
