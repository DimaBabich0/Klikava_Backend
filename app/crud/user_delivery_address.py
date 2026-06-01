from datetime import datetime
from sqlalchemy.orm import Session
from app.models import UserDeliveryAddress


def get_user_delivery_address_by_id(db: Session, address_id: int):
  return (
    db.query(UserDeliveryAddress)
    .filter(UserDeliveryAddress.id == address_id)
    .filter(UserDeliveryAddress.deleted_at == None)
    .first()
  )


def get_user_delivery_addresses(db: Session, user_id: int, skip: int = 0, limit: int = 100):
  return (
    db.query(UserDeliveryAddress)
    .filter(UserDeliveryAddress.user_id == user_id)
    .filter(UserDeliveryAddress.deleted_at == None)
    .order_by(UserDeliveryAddress.created_at.desc())
    .offset(skip)
    .limit(limit)
    .all()
  )


def get_user_delivery_addresses_count(db: Session, user_id: int):
  return (
    db.query(UserDeliveryAddress)
    .filter(UserDeliveryAddress.user_id == user_id)
    .filter(UserDeliveryAddress.deleted_at == None)
    .count()
  )


def create_user_delivery_address(db: Session, user_id: int, address_line: str):
  address = UserDeliveryAddress(
    user_id=user_id,
    address_line=address_line,
  )
  db.add(address)
  db.commit()
  db.refresh(address)
  return address


def update_user_delivery_address(db: Session, address: UserDeliveryAddress, data: dict):
  for key, value in data.items():
    if hasattr(address, key) and value is not None:
      setattr(address, key, value)
  db.commit()
  db.refresh(address)
  return address


def delete_user_delivery_address(db: Session, address: UserDeliveryAddress, soft: bool = True):
  if soft:
    address.deleted_at = datetime.now()
    db.commit()
    db.refresh(address)
    return address
  db.delete(address)
  db.commit()
  return None
