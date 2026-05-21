from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.database import Base


class Product(Base):
  __tablename__ = "products"

  id = Column(Integer, primary_key=True, index=True)
  seller_id = Column(Integer, ForeignKey("sellers.id", ondelete="CASCADE"), nullable=False, index=True)
  status = Column(String(50), default="moderating", nullable=False)
  pageviews = Column(Integer, default=0, nullable=False)
  created_at = Column(DateTime, default=datetime.now(), index=True)
  deleted_at = Column(DateTime, nullable=True)

  seller = relationship("Seller", back_populates="products")
  versions = relationship("ProductVersion", back_populates="product")
