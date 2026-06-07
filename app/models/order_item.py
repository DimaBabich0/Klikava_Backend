from sqlalchemy import Column, Integer, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from app.database import Base


class OrderItem(Base):
  __tablename__ = "order_items"

  id = Column(Integer, primary_key=True, index=True)
  order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
  product_variant_id = Column(Integer, ForeignKey("product_variants.id"), nullable=False)
  quantity = Column(Integer, nullable=False)
  discount_item_id = Column(Integer, ForeignKey("discount_items.id"), nullable=True)
  price_snapshot = Column(DECIMAL(10, 2), nullable=True)
  discount_snapshot = Column(DECIMAL(10, 2), nullable=True)
  final_price_snapshot = Column(DECIMAL(10, 2), nullable=True)

  order = relationship("Order", back_populates="items")
  product_variant = relationship("ProductVariant")
