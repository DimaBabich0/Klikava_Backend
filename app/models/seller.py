from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Seller(Base):
  __tablename__ = "sellers"

  id = Column(Integer, primary_key=True, index=True)
  user_id = Column(Integer, ForeignKey(
    "users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
  store_name = Column(String(255), nullable=False, unique=True)
  description = Column(Text, nullable=True)
  rating = Column(Float, default=0.0, nullable=False)
  created_at = Column(DateTime, default=datetime.now(), index=True)

  user = relationship("User", back_populates="sellers")
