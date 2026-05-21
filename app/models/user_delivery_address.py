from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class UserDeliveryAddress(Base):
  __tablename__ = "user_delivery_addresses"

  id = Column(Integer, primary_key=True, index=True)
  user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
  address_line = Column(String(255), nullable=False)
  created_at = Column(DateTime, default=datetime.now(), index=True)
  deleted_at = Column(DateTime, nullable=True)

  user = relationship("User", back_populates="delivery_addresses")

