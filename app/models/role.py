from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


class Role(Base):
  __tablename__ = "roles"

  id = Column(Integer, primary_key=True, index=True)
  name = Column(String(50), unique=True, nullable=False, index=True)
  description = Column(String(255), nullable=True)
  
  create_level = Column(Integer, default=1, nullable=False)
  read_level = Column(Integer, default=1, nullable=False)
  update_level = Column(Integer, default=1, nullable=False)
  deleted_level = Column(Integer, default=1, nullable=False)

  created_at = Column(DateTime, default=datetime.now, nullable=False)
  deleted_at = Column(DateTime, nullable=True)

  user_roles = relationship(
    "UserRoles",
    back_populates="role",
    cascade="all, delete-orphan"
  )
  users = relationship(
    "User",
    secondary="user_roles",
    back_populates="roles",
    viewonly=True
  )
