from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Seller(Base):
  __tablename__ = "sellers"

  id = Column(Integer, primary_key=True, index=True)
  parent_id = Column(Integer, ForeignKey("sellers.id", ondelete="SET NULL"), nullable=True)
  picture_url = Column(String(255), nullable=True)
  store_name = Column(String(64), nullable=False, unique=True)
  description = Column(String(255), nullable=True)
  rating = Column(Float, default=0.0, nullable=False)
  created_at = Column(DateTime, default=datetime.now, index=True)
  deleted_at = Column(DateTime, nullable=True)

  parent = relationship("Seller", remote_side=[id], backref="children")
  products = relationship("Product", back_populates="seller")
