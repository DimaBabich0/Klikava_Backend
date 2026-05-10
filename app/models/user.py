from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from .role import user_roles  # Import the association table


class User(Base):
  __tablename__ = "users"

  id = Column(Integer, primary_key=True, index=True)
  username = Column(String(255), unique=True, nullable=False, index=True)
  name = Column(String(255), nullable=False)
  email = Column(String(255), unique=True, nullable=False, index=True)
  password_hash = Column(String(255), nullable=False)
  password_salt = Column(String(255), nullable=False)
  status = Column(String(50), default="active", nullable=False)
  birthday = Column(DateTime, nullable=True)
  created_at = Column(DateTime, default=datetime.now(), index=True)
  deleted_at = Column(DateTime, nullable=True)

  roles = relationship("Role", secondary=user_roles, back_populates="users")
  sellers = relationship("Seller", back_populates="user", uselist=False)

  def is_deleted(self) -> bool:
    return self.deleted_at is not None

  def is_seller(self) -> bool:
    return any(role.name == "SELLER" for role in self.roles)

  def is_admin(self) -> bool:
    return any(role.name == "ADMIN" for role in self.roles)

  def is_moderator(self) -> bool:
    return any(role.name == "MODERATOR" for role in self.roles)
