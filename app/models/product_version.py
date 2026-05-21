from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.database import Base


class ProductVersion(Base):
  __tablename__ = "product_versions"

  id = Column(Integer, primary_key=True, index=True)
  product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
  category_id = Column(Integer, ForeignKey("categories.id"))
  title = Column(String(32), nullable=False)
  description = Column(Text, nullable=True)
  slug = Column(String(64), nullable=False, unique=True)
  created_at = Column(DateTime, default=datetime.now(), index=True)
  deleted_at = Column(DateTime, nullable=True)

  product = relationship("Product", back_populates="versions")
  category = relationship("Category", back_populates="product_versions")
  variants = relationship("ProductVariant", back_populates="product_version")
