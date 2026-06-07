from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import Discount
from app.schemas.discount import DISCOUNT_TARGET_TYPES, DISCOUNT_TYPES


def get_discount_by_id(db: Session, discount_id: int):
  return db.query(Discount).filter(Discount.id == discount_id).first()


def get_discounts(db: Session, active_only: bool = False, skip: int = 0, limit: int = 100):
  query = db.query(Discount)
  if active_only:
    now = datetime.now()
    query = query.filter(
      Discount.is_active == True,
      Discount.start_date <= now,
      Discount.end_date >= now,
    )
  return query.order_by(Discount.start_date.desc()).offset(skip).limit(limit).all()


def get_discounts_count(db: Session, active_only: bool = False):
  query = db.query(Discount)
  if active_only:
    now = datetime.now()
    query = query.filter(
      Discount.is_active == True,
      Discount.start_date <= now,
      Discount.end_date >= now,
    )
  return query.count()


def _validate_discount_payload(data: dict):
  start_date = data.get("start_date")
  end_date = data.get("end_date")
  if start_date and end_date and end_date <= start_date:
    raise ValueError("end_date must be after start_date")

  discount_type = data.get("discount_type")
  if discount_type and discount_type not in DISCOUNT_TYPES:
    raise ValueError(f"discount_type must be one of: {', '.join(DISCOUNT_TYPES)}")

  target_type = data.get("target_type")
  if target_type and target_type not in DISCOUNT_TARGET_TYPES:
    raise ValueError(f"target_type must be one of: {', '.join(DISCOUNT_TARGET_TYPES)}")

  value = data.get("value")
  if value is not None and Decimal(value) < 0:
    raise ValueError("value must be greater than or equal to 0")

  if discount_type in ("PERCENTAGE", None) and value is not None and Decimal(value) > 100:
    raise ValueError("percentage discount value cannot exceed 100")


def create_discount(
  db: Session,
  name: str,
  description: str | None,
  start_date: datetime,
  end_date: datetime,
  discount_type: str,
  value: Decimal,
  coupon_code: str | None,
  target_type: str,
  target_id: int,
  is_active: bool = True,
):
  data = {
    "start_date": start_date,
    "end_date": end_date,
    "discount_type": discount_type,
    "value": value,
    "target_type": target_type,
  }
  _validate_discount_payload(data)

  if coupon_code and db.query(Discount).filter(Discount.coupon_code == coupon_code).first():
    raise ValueError("coupon_code already exists")

  discount = Discount(
    name=name,
    description=description,
    start_date=start_date,
    end_date=end_date,
    discount_type=discount_type,
    value=value,
    coupon_code=coupon_code,
    target_type=target_type,
    target_id=target_id,
    is_active=is_active,
    discount_percentage=value if discount_type == "PERCENTAGE" else None,
    price=value if discount_type == "FIXED" else None,
  )
  db.add(discount)
  db.commit()
  db.refresh(discount)
  return discount


def update_discount(db: Session, discount: Discount, data: dict):
  merged = {
    "start_date": data.get("start_date", discount.start_date),
    "end_date": data.get("end_date", discount.end_date),
    "discount_type": data.get("discount_type", discount.discount_type),
    "value": data.get("value", discount.value),
    "target_type": data.get("target_type", discount.target_type),
  }
  _validate_discount_payload(merged)

  coupon_code = data.get("coupon_code")
  if coupon_code and coupon_code != discount.coupon_code:
    if db.query(Discount).filter(Discount.coupon_code == coupon_code).first():
      raise ValueError("coupon_code already exists")

  for key, value in data.items():
    if hasattr(discount, key) and value is not None:
      setattr(discount, key, value)

  if "discount_type" in data or "value" in data:
    discount.discount_percentage = discount.value if discount.discount_type == "PERCENTAGE" else None
    discount.price = discount.value if discount.discount_type == "FIXED" else None

  db.commit()
  db.refresh(discount)
  return discount


def delete_discount(db: Session, discount: Discount):
  db.delete(discount)
  db.commit()
  return None
