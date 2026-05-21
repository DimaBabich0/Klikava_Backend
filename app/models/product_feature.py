from datetime import datetime
from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.database import Base


class ProductFeature(Base):
  __tablename__ = "product_features"

  id = Column(Integer, primary_key=True, index=True)
  product_variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=False, index=True)
  feature_id = Column(Integer, ForeignKey("features.id", ondelete="CASCADE"), nullable=False, index=True)

  value = Column(String(255), nullable=False)
  value_type = Column(String(50), nullable=False)
  created_at = Column(DateTime, default=datetime.now(), index=True)
  deleted_at = Column(DateTime, nullable=True)


  product_variant = relationship("ProductVariant", back_populates="product_features")
  feature = relationship("Feature", back_populates="product_features")
