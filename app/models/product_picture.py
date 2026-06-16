from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class ProductPicture(Base):
	__tablename__ = "product_pictures"

	id = Column(Integer, primary_key=True, index=True)
	product_version_id = Column(Integer, ForeignKey("product_versions.id", ondelete="CASCADE"), nullable=False, index=True)
	file_url = Column(String(1024), nullable=True)
	original_url = Column(String(1024), nullable=True)
	preview_url = Column(String(1024), nullable=True)
	thumbnail_url = Column(String(1024), nullable=True)
	sort_order = Column(Integer, default=0, nullable=False)
	created_at = Column(DateTime, default=datetime.now, index=True)
	deleted_at = Column(DateTime, nullable=True)

	product_version = relationship("ProductVersion", back_populates="pictures")
