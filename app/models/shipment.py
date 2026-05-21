from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text, ForeignKey, Table, DECIMAL
from sqlalchemy.orm import relationship
from app.database import Base


class Shipment(Base):
  __tablename__ = "shipments"

  id = Column(Integer, primary_key=True, index=True)
  order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
  tracking_number = Column(String(100), nullable=True)
  status = Column(String(50), nullable=False)
  created_at = Column(DateTime, nullable=False)

  order = relationship("Order")
