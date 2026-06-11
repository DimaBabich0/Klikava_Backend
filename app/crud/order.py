from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Order, OrderItem, User


def get_order_by_id(db: Session, order_id: int):
  """Get order by ID."""
  return db.query(Order).filter(Order.id == order_id).first()


def get_user_orders(db: Session, user_id: int, skip: int = 0, limit: int = 100):
  """Get all orders for a specific user."""
  return (
    db.query(Order)
    .filter(Order.user_id == user_id)
    .order_by(Order.created_at.desc())
    .offset(skip)
    .limit(limit)
    .all()
  )


def get_user_orders_count(db: Session, user_id: int):
  """Count total orders for a specific user."""
  return db.query(Order).filter(Order.user_id == user_id).count()


def get_orders(
  db: Session,
  status: str | None = None,
  user_id: int | None = None,
  skip: int = 0,
  limit: int = 100,
):
  """Get all orders with optional filtering."""
  query = db.query(Order)

  if status:
    query = query.filter(Order.status == status)
  
  if user_id:
    query = query.filter(Order.user_id == user_id)

  return query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()


def get_orders_count(db: Session, status: str | None = None, user_id: int | None = None):
  """Count total orders with optional filtering."""
  query = db.query(Order)

  if status:
    query = query.filter(Order.status == status)
  
  if user_id:
    query = query.filter(Order.user_id == user_id)

  return query.count()


def create_order(
  db: Session,
  user_id: int,
  status: str = "pending",
  delivery_price: float = 0.0,
  total_price: float = 0.0,
  discount_item_id: int | None = None,
):
  """Create a new order."""
  user = db.query(User).filter(User.id == user_id).first()
  if not user:
    raise ValueError("User not found")

  order = Order(
    user_id=user_id,
    status=status,
    delivery_price=delivery_price,
    total_price=total_price,
    discount_item_id=discount_item_id,
    created_at=datetime.now(),
  )
  db.add(order)
  db.commit()
  db.refresh(order)
  return order


def update_order(db: Session, order: Order, data: dict):
  """Update order fields."""
  for key, value in data.items():
    if hasattr(order, key) and value is not None:
      setattr(order, key, value)
  
  db.commit()
  db.refresh(order)
  return order


def delete_order(db: Session, order: Order):
  """Delete order and its items."""
  # Delete associated items
  db.query(OrderItem).filter(OrderItem.order_id == order.id).delete()
  db.delete(order)
  db.commit()
  return None


def add_item_to_order(
  db: Session,
  order_id: int,
  product_variant_id: int,
  quantity: int,
  price_snapshot: float | None = None,
  discount_snapshot: float | None = None,
  final_price_snapshot: float | None = None,
  discount_item_id: int | None = None,
):
  """Add item to order."""
  order = db.query(Order).filter(Order.id == order_id).first()
  if not order:
    raise ValueError("Order not found")

  # Check if item already exists in order
  existing_item = (
    db.query(OrderItem)
    .filter(
      OrderItem.order_id == order_id,
      OrderItem.product_variant_id == product_variant_id,
    )
    .first()
  )

  if existing_item:
    existing_item.quantity += quantity
    db.commit()
    db.refresh(existing_item)
    return existing_item

  order_item = OrderItem(
    order_id=order_id,
    product_variant_id=product_variant_id,
    quantity=quantity,
    price_snapshot=price_snapshot,
    discount_snapshot=discount_snapshot,
    final_price_snapshot=final_price_snapshot,
    discount_item_id=discount_item_id,
  )
  db.add(order_item)
  db.commit()
  db.refresh(order_item)
  return order_item


def remove_item_from_order(db: Session, order_item_id: int):
  """Remove item from order."""
  item = db.query(OrderItem).filter(OrderItem.id == order_item_id).first()
  if not item:
    raise ValueError("Order item not found")

  db.delete(item)
  db.commit()
  return None


def update_order_item(db: Session, order_item: OrderItem, data: dict):
  """Update order item."""
  for key, value in data.items():
    if hasattr(order_item, key) and value is not None:
      setattr(order_item, key, value)

  db.commit()
  db.refresh(order_item)
  return order_item


def get_order_items(db: Session, order_id: int):
  """Get all items in an order."""
  return (
    db.query(OrderItem)
    .filter(OrderItem.order_id == order_id)
    .all()
  )


def get_order_item_by_id(db: Session, item_id: int):
  """Get order item by ID."""
  return db.query(OrderItem).filter(OrderItem.id == item_id).first()
