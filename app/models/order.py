from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text, ForeignKey, Table, DECIMAL
from sqlalchemy.orm import relationship
from app.database import Base


class Order(Base):
  __tablename__ = "orders"

  id = Column(Integer, primary_key=True, index=True)
  user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

  status = Column(String(50), nullable=False)
  delivery_price = Column(DECIMAL(10, 2), nullable=False)
  total_price = Column(DECIMAL(10, 2), nullable=False)

  paid_at = Column(DateTime, nullable=True)
  created_at = Column(DateTime, nullable=False)
  discount_item_id = Column(Integer, ForeignKey("discount_items.id"), nullable=True)

  user = relationship("User")
  items = relationship("OrderItem", back_populates="order")
  discount_item = relationship("DiscountItem")
