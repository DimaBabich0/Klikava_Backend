from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Order, Shipment


def get_order_by_id(db: Session, order_id: int):
  return db.query(Order).filter(Order.id == order_id).first()


def get_shipment_by_id(db: Session, shipment_id: int):
  return db.query(Shipment).filter(Shipment.id == shipment_id).first()


def get_shipments_by_order(db: Session, order_id: int, skip: int = 0, limit: int = 100):
  return (
    db.query(Shipment)
    .filter(Shipment.order_id == order_id)
    .order_by(Shipment.created_at.desc())
    .offset(skip)
    .limit(limit)
    .all()
  )


def get_shipments_count_by_order(db: Session, order_id: int):
  return db.query(Shipment).filter(Shipment.order_id == order_id).count()


def create_shipment(db: Session, order_id: int, status: str, tracking_number: str | None = None, created_at: datetime | None = None):
  if not db.query(Order).filter(Order.id == order_id).first():
    raise ValueError("Order not found")

  if created_at is None:
    created_at = datetime.now()

  shipment = Shipment(
    order_id=order_id,
    status=status,
    tracking_number=tracking_number,
    created_at=created_at,
  )
  db.add(shipment)
  db.commit()
  db.refresh(shipment)
  return shipment


def update_shipment(db: Session, shipment: Shipment, data: dict):
  for key, value in data.items():
    if hasattr(shipment, key) and value is not None:
      setattr(shipment, key, value)
  db.commit()
  db.refresh(shipment)
  return shipment


def delete_shipment(db: Session, shipment: Shipment):
  db.delete(shipment)
  db.commit()
  return None
