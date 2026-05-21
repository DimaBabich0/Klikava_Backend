from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text, ForeignKey, Table, DECIMAL
from sqlalchemy.orm import relationship
from app.database import Base


class Payment(Base):
  __tablename__ = "payments"

  id = Column(Integer, primary_key=True, index=True)
  order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
  amount = Column(DECIMAL(10, 2), nullable=False)
  transaction_id = Column(String(100), nullable=False)
  created_at = Column(DateTime, nullable=False)

  order = relationship("Order")

