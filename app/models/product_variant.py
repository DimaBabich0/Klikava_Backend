from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from app.database import Base


class ProductVariant(Base):
  __tablename__ = "product_variants"

  id = Column(Integer, primary_key=True, index=True)
  product_version_id = Column(Integer, ForeignKey("product_versions.id", ondelete="CASCADE"), nullable=False, index=True)
  sku_code = Column(String(64), nullable=False, unique=True)
  price = Column(DECIMAL(10, 2), nullable=False)
  stock = Column(Integer, default=0, nullable=False)
  created_at = Column(DateTime, default=datetime.now, index=True)
  deleted_at = Column(DateTime, nullable=True)

  product_version = relationship("ProductVersion", back_populates="variants")
  product_features = relationship("ProductFeature", back_populates="product_variant")
