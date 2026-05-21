from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class UserRoles(Base):
  __tablename__ = "user_roles"

  user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
  role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)

  login = Column(String(255), unique=True, nullable=False, index=True)
  password_hash = Column(String(255), nullable=False)
  password_salt = Column(String(255), nullable=False)

  status = Column(String(50), default="active", nullable=False)
  picture_url = Column(String(255), nullable=True)
  
  created_at = Column(DateTime, default=datetime.now, index=True)
  deleted_at = Column(DateTime, nullable=True)

  user = relationship("User", back_populates="user_roles")
  role = relationship("Role", back_populates="user_roles")

  def is_deleted(self) -> bool:
    return self.deleted_at is not None

  def is_active(self) -> bool:
    if self.status != "active":
      return False
    return True

  def deactivate(self):
    self.status = "inactive"

  def activate(self):
    self.status = "active"
