from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Category


def get_category_by_id(db: Session, category_id: int):
  return (
    db.query(Category)
    .filter(Category.id == category_id)
    .filter(Category.deleted_at == None)
    .first()
  )


def get_categories(db: Session, parent_id: int | None = None, skip: int = 0, limit: int = 100):
  query = db.query(Category).filter(Category.deleted_at == None)
  if parent_id is None:
    query = query.filter(Category.parent_id.is_(None))
  else:
    query = query.filter(Category.parent_id == parent_id)
  return query.order_by(Category.order_in_price.asc(), Category.title.asc()).offset(skip).limit(limit).all()


def get_categories_count(db: Session, parent_id: int | None = None):
  query = db.query(Category).filter(Category.deleted_at == None)
  if parent_id is None:
    query = query.filter(Category.parent_id.is_(None))
  else:
    query = query.filter(Category.parent_id == parent_id)
  return query.count()


def create_category(db: Session, title: str, description: str | None = None, parent_id: int | None = None, order_in_price: int | None = None):
  if parent_id is not None:
    parent = db.query(Category).filter(Category.id == parent_id, Category.deleted_at == None).first()
    if not parent:
      raise ValueError("Parent category not found")

  category = Category(
    title=title,
    description=description,
    parent_id=parent_id,
    order_in_price=order_in_price,
  )
  db.add(category)
  db.commit()
  db.refresh(category)
  return category


def update_category(db: Session, category: Category, data: dict):
  if "parent_id" in data:
    parent_id = data["parent_id"]
    if parent_id is not None and parent_id != category.id:
      parent = db.query(Category).filter(Category.id == parent_id, Category.deleted_at == None).first()
      if not parent:
        raise ValueError("Parent category not found")
      category.parent_id = parent_id
    elif parent_id is None:
      category.parent_id = None

  for key, value in data.items():
    if key == "parent_id":
      continue
    if hasattr(category, key) and value is not None:
      setattr(category, key, value)

  db.commit()
  db.refresh(category)
  return category


def delete_category(db: Session, category: Category, soft: bool = True):
  if soft:
    category.deleted_at = datetime.now()
    db.commit()
    db.refresh(category)
    return category
  db.delete(category)
  db.commit()
  return None
