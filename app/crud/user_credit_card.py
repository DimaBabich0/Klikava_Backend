from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models import UserCreditCard


def get_user_credit_card_by_id(db: Session, card_id: int):
  return (
    db.query(UserCreditCard)
    .filter(UserCreditCard.id == card_id)
    .filter(UserCreditCard.deleted_at == None)
    .first()
  )


def get_user_credit_cards(db: Session, user_id: int, skip: int = 0, limit: int = 100):
  return (
    db.query(UserCreditCard)
    .filter(UserCreditCard.user_id == user_id)
    .filter(UserCreditCard.deleted_at == None)
    .order_by(UserCreditCard.order_in_list.asc(), UserCreditCard.created_at.desc())
    .offset(skip)
    .limit(limit)
    .all()
  )


def get_user_credit_cards_count(db: Session, user_id: int):
  return (
    db.query(UserCreditCard)
    .filter(UserCreditCard.user_id == user_id)
    .filter(UserCreditCard.deleted_at == None)
    .count()
  )


def get_user_credit_cards_max_order(db: Session, user_id: int):
  return db.query(func.max(UserCreditCard.order_in_list)).filter(
    UserCreditCard.user_id == user_id,
    UserCreditCard.deleted_at == None,
  ).scalar() or 0


def create_user_credit_card(db: Session, user_id: int, card_info_encrypted: str, order_in_list: int | None = None):
  if order_in_list is None:
    order_in_list = get_user_credit_cards_max_order(db, user_id) + 1

  card = UserCreditCard(
    user_id=user_id,
    card_info_encrypted=card_info_encrypted,
    order_in_list=order_in_list,
  )
  db.add(card)
  db.commit()
  db.refresh(card)
  return card


def update_user_credit_card(db: Session, card: UserCreditCard, data: dict):
  for key, value in data.items():
    if hasattr(card, key) and value is not None:
      setattr(card, key, value)
  db.commit()
  db.refresh(card)
  return card


def delete_user_credit_card(db: Session, card: UserCreditCard, soft: bool = True):
  if soft:
    card.deleted_at = datetime.now()
    db.commit()
    db.refresh(card)
    return card
  db.delete(card)
  db.commit()
  return None
