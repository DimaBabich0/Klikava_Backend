from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Feature


def get_feature_by_id(db: Session, feature_id: int):
  return (
    db.query(Feature)
    .filter(Feature.id == feature_id)
    .filter(Feature.deleted_at == None)
    .first()
  )


def get_features(db: Session, is_primary: bool | None = None, skip: int = 0, limit: int = 100):
  query = db.query(Feature).filter(Feature.deleted_at == None)
  if is_primary is not None:
    query = query.filter(Feature.is_primary == is_primary)
  return query.order_by(Feature.title.asc()).offset(skip).limit(limit).all()


def get_features_count(db: Session, is_primary: bool | None = None):
  query = db.query(Feature).filter(Feature.deleted_at == None)
  if is_primary is not None:
    query = query.filter(Feature.is_primary == is_primary)
  return query.count()


def create_feature(db: Session, title: str, is_primary: bool = False):
  feature = Feature(title=title, is_primary=is_primary)
  db.add(feature)
  db.commit()
  db.refresh(feature)
  return feature


def update_feature(db: Session, feature: Feature, data: dict):
  for key, value in data.items():
    if hasattr(feature, key) and value is not None:
      setattr(feature, key, value)

  db.commit()
  db.refresh(feature)
  return feature


def delete_feature(db: Session, feature: Feature):
  feature.deleted_at = datetime.now()
  db.commit()
  db.refresh(feature)
  return feature
