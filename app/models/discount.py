from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text, ForeignKey, Table, DECIMAL
from sqlalchemy.orm import relationship
from app.database import Base


class Discount(Base):
  __tablename__ = "discounts"

  id = Column(Integer, primary_key=True, index=True)
  name = Column(String(100), nullable=False)
  description = Column(Text, nullable=True)
  
  start_date = Column(DateTime, nullable=False)
  end_date = Column(DateTime, nullable=False)
  
  discount_percentage = Column(DECIMAL(4, 2), nullable=False)
  price = Column(DECIMAL(10, 2), nullable=True)
