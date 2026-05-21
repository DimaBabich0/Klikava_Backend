from datetime import datetime
from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.database import Base


class Feature(Base):
  __tablename__ = "features"

  id = Column(Integer, primary_key=True, index=True)
  title = Column(String(32), nullable=False)
  is_primary = Column(Boolean, default=False, nullable=False)
  created_at = Column(DateTime, default=datetime.now(), index=True)
  deleted_at = Column(DateTime, nullable=True)

  product_features = relationship("ProductFeature", back_populates="feature")
