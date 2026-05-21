from datetime import datetime
from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text, ForeignKey, Table, DECIMAL
from sqlalchemy.orm import relationship
from app.database import Base


class DiscountItem(Base):
  __tablename__ = "discount_items"

  id = Column(Integer, primary_key=True, index=True)
  discount_id = Column(Integer, ForeignKey("discounts.id"), nullable=False)
  item_id = Column(Integer, ForeignKey("products.id"), nullable=False)
  other_item_id = Column(Integer, ForeignKey("products.id"), nullable=True)
  price = Column(DECIMAL(10, 2), nullable=True)

  product = relationship("Product", foreign_keys=[item_id])
  other_product = relationship("Product", foreign_keys=[other_item_id])
