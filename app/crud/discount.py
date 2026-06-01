from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models import Discount


def get_discount_by_id(db: Session, discount_id: int):
  return db.query(Discount).filter(Discount.id == discount_id).first()


def get_discounts(db: Session, active_only: bool = False, skip: int = 0, limit: int = 100):
  query = db.query(Discount)
  if active_only:
    now = datetime.now()
    query = query.filter(Discount.start_date <= now, Discount.end_date >= now)
  return query.order_by(Discount.start_date.desc()).offset(skip).limit(limit).all()


def get_discounts_count(db: Session, active_only: bool = False):
  query = db.query(Discount)
  if active_only:
    now = datetime.now()
    query = query.filter(Discount.start_date <= now, Discount.end_date >= now)
  return query.count()


def create_discount(
  db: Session,
  name: str,
  description: str | None,
  start_date: datetime,
  end_date: datetime,
  discount_percentage: Decimal,
  price: Decimal | None = None,
):
  if end_date <= start_date:
    raise ValueError("end_date must be after start_date")

  discount = Discount(
    name=name,
    description=description,
    start_date=start_date,
    end_date=end_date,
    discount_percentage=discount_percentage,
    price=price,
  )
  db.add(discount)
  db.commit()
  db.refresh(discount)
  return discount


def update_discount(db: Session, discount: Discount, data: dict):
  start_date = data.get("start_date", discount.start_date)
  end_date = data.get("end_date", discount.end_date)
  if start_date and end_date and end_date <= start_date:
    raise ValueError("end_date must be after start_date")

  for key, value in data.items():
    if hasattr(discount, key) and value is not None:
      setattr(discount, key, value)

  db.commit()
  db.refresh(discount)
  return discount


def delete_discount(db: Session, discount: Discount):
  db.delete(discount)
  db.commit()
  return None
