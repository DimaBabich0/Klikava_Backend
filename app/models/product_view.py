from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base


class ProductView(Base):
  __tablename__ = "product_views"

  id = Column(Integer, primary_key=True, index=True)
  product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
  user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
  viewer_key = Column(String(128), nullable=True, index=True)
  viewed_at = Column(DateTime, default=datetime.now, nullable=False, index=True)

  product = relationship("Product", back_populates="views")
  user = relationship("User")
