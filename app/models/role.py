from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.database import Base

# Association table for many-to-many User-Role relationship
user_roles = Table(
  "user_roles",
  Base.metadata,
  Column("user_id", Integer, ForeignKey(
    "users.id", ondelete="CASCADE"), primary_key=True),
  Column("role_id", Integer, ForeignKey(
    "roles.id", ondelete="CASCADE"), primary_key=True),
  Column("created_at", DateTime, default=datetime.now(), nullable=False),
)


class Role(Base):
  __tablename__ = "roles"

  id = Column(Integer, primary_key=True, index=True)
  name = Column(String(50), unique=True, nullable=False, index=True)
  description = Column(Text, nullable=True)
  created_at = Column(DateTime, default=datetime.now(), nullable=False)

  users = relationship("User", secondary=user_roles, back_populates="roles")
