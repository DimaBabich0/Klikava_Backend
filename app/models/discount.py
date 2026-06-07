from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text, DECIMAL
from app.database import Base


class Discount(Base):
  __tablename__ = "discounts"

  id = Column(Integer, primary_key=True, index=True)
  name = Column(String(100), nullable=False)
  description = Column(Text, nullable=True)
  
  start_date = Column(DateTime, nullable=False)
  end_date = Column(DateTime, nullable=False)

  discount_type = Column(String(20), default="PERCENTAGE", nullable=False, index=True)
  value = Column(DECIMAL(10, 2), nullable=False)
  coupon_code = Column(String(64), nullable=True, unique=True)
  target_type = Column(String(20), nullable=False, index=True)
  target_id = Column(Integer, nullable=False, index=True)
  is_active = Column(Boolean, default=True, nullable=False)

  discount_percentage = Column(DECIMAL(4, 2), nullable=True)
  price = Column(DECIMAL(10, 2), nullable=True)
