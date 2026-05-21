from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class UserCreditCard(Base):
  __tablename__ = "user_credit_cards"

  id = Column(Integer, primary_key=True, index=True)
  user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
  card_info_encrypted = Column(String(255), nullable=False)
  order_in_list = Column(Integer, nullable=False)
  created_at = Column(DateTime, default=datetime.now(), index=True)
  deleted_at = Column(DateTime, nullable=True)

  user = relationship("User", back_populates="credit_cards")

