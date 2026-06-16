from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base


class Review(Base):
  __tablename__ = "reviews"

  id = Column(Integer, primary_key=True, index=True)
  user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
  product_variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=False, index=True)
  rating = Column(Integer, nullable=False)
  comment = Column(String(1024), nullable=True)
  created_at = Column(DateTime, default=datetime.now, nullable=False, index=True)
  updated_at = Column(DateTime, nullable=True)
  deleted_at = Column(DateTime, nullable=True)

  user = relationship("User")
  product_variant = relationship("ProductVariant")
  pictures = relationship("ReviewPicture", back_populates="review", cascade="all, delete-orphan")
  