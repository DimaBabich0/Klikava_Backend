from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
  __tablename__ = "users"

  id = Column(Integer, primary_key=True, index=True)
  name = Column(String(255), nullable=False)
  email = Column(String(255), unique=True, nullable=False, index=True)
  phone_number = Column(String(20), unique=True, nullable=True)
  birthday = Column(DateTime, nullable=True)
  avatar_url = Column(String(512), nullable=True)

  user_roles = relationship(
    "UserRoles",
    back_populates="user",
    cascade="all, delete-orphan"
  )
  roles = relationship(
    "Role",
    secondary="user_roles",
    back_populates="users",
    viewonly=True
  )
  credit_cards = relationship(
    "UserCreditCard",
    back_populates="user",
    cascade="all, delete-orphan"
  )
  delivery_addresses = relationship(
    "UserDeliveryAddress",
    back_populates="user",
    cascade="all, delete-orphan"
  )

  def is_deleted(self) -> bool:
    return all(user_role.is_deleted() for user_role in self.user_roles)

  def is_active(self) -> bool:
    return any(
      not user_role.is_deleted() and user_role.is_active()
      for user_role in self.user_roles
    )

  def is_seller(self) -> bool:
    return any(role.name == "SELLER" for role in self.roles)

  def is_admin(self) -> bool:
    return any(role.name == "ADMIN" for role in self.roles)

  def is_moderator(self) -> bool:
    return any(role.name == "MODERATOR" for role in self.roles)

  def get_primary_user_role(self):
    active_user_roles = [
      user_role for user_role in self.user_roles
      if not user_role.is_deleted() and user_role.is_active()
    ]
    if not active_user_roles:
      active_user_roles = [
        user_role for user_role in self.user_roles
        if not user_role.is_deleted()
      ]
    if not active_user_roles:
      active_user_roles = list(self.user_roles)
    if not active_user_roles:
      return None
    return sorted(active_user_roles, key=lambda user_role: user_role.created_at)[0]

  def get_primary_login(self) -> str | None:
    primary_user_role = self.get_primary_user_role()
    return primary_user_role.login if primary_user_role else None
