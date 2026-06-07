from datetime import datetime
from sqlalchemy import Column, DECIMAL, ForeignKey, Integer, String, DateTime, Float
from sqlalchemy.orm import relationship
from app.database import Base


class Product(Base):
  __tablename__ = "products"

  id = Column(Integer, primary_key=True, index=True)
  seller_id = Column(Integer, ForeignKey("sellers.id", ondelete="CASCADE"), nullable=False, index=True)
  current_version_id = Column(
    Integer,
    ForeignKey("product_versions.id", use_alter=True, name="fk_products_current_version"),
    nullable=True,
    index=True,
  )
  status = Column(String(50), default="DRAFT", nullable=False, index=True)
  pageviews = Column(Integer, default=0, nullable=False)
  unique_pageviews = Column(Integer, default=0, nullable=False)
  favorite_count = Column(Integer, default=0, nullable=False)
  order_count = Column(Integer, default=0, nullable=False)
  sales_count = Column(Integer, default=0, nullable=False)
  average_rating = Column(Float, default=0.0, nullable=False)
  reviews_count = Column(Integer, default=0, nullable=False)
  created_at = Column(DateTime, default=datetime.now, index=True)
  updated_at = Column(DateTime, nullable=True)
  deleted_at = Column(DateTime, nullable=True)

  seller = relationship("Seller", back_populates="products")
  versions = relationship(
    "ProductVersion",
    back_populates="product",
    foreign_keys="ProductVersion.product_id",
  )
  current_version = relationship(
    "ProductVersion",
    foreign_keys=[current_version_id],
    post_update=True,
  )
  views = relationship("ProductView", back_populates="product")
