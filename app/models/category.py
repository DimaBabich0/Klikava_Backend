from datetime import datetime
from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.database import Base


class Category(Base):
  __tablename__ = "categories"

  id = Column(Integer, primary_key=True, index=True)
  parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
  title = Column(String(100), nullable=False)
  description = Column(Text, nullable=True)
  order_in_price = Column(Integer, default=9999, nullable=True)
  created_at = Column(DateTime, default=datetime.now(), index=True)
  deleted_at = Column(DateTime, nullable=True)

  product_versions = relationship("ProductVersion", back_populates="category")
