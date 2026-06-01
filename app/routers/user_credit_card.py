from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.responses.response_rest import ResponseRest
from app.api.responses.rest_meta import RestMeta
from app.api.responses.rest_status import RestStatus
from app.crud import (
  create_user_credit_card,
  delete_user_credit_card,
  get_user_by_id,
  get_user_credit_card_by_id,
  get_user_credit_cards,
  get_user_credit_cards_count,
  update_user_credit_card,
)
from app.database import get_db
from app.models import User, UserCreditCard
from app.schemas import (
  UserCreditCardCreate,
  UserCreditCardResponse,
  UserCreditCardUpdate,
)
from app.services.access_manager import AccessManager

router = APIRouter(prefix="/users/{user_id}/credit_cards", tags=["user_credit_cards"])
response = ResponseRest()


def _meta(action: str, message: str | None = None) -> RestMeta:
  return RestMeta(action=action, message=message)


def _can_manage_credit_cards(current_user: User, user_id: int) -> bool:
  return current_user.id == user_id or current_user.is_admin() or current_user.is_moderator()


def _serialize_card(card: UserCreditCard) -> dict:
  return UserCreditCardResponse.model_validate(card).model_dump(mode="json")


@router.get("", response_model=None)
def list_credit_cards(
  user_id: int,
  per_page: int = Query(10, ge=1, le=100),
  page: int = Query(1, ge=1),
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """List credit cards for a user."""
  if not _can_manage_credit_cards(current_user, user_id):
    return response.forbidden("Only owner, admin or moderator can list credit cards")

  user = get_user_by_id(db, user_id)
  if not user:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("list_credit_cards", "User not found"),
      data=None,
    )

  total = get_user_credit_cards_count(db, user_id)
  cards = get_user_credit_cards(db, user_id, skip=(page - 1) * per_page, limit=per_page)
  pagination = response.build_pagination(page, per_page, total)

  return response.success_pagination(
    status=RestStatus.ok_200,
    meta=RestMeta(
      action="list_credit_cards",
      message=f"Credit cards found: {len(cards)}",
      pagination=pagination,
    ),
    data={"items": [_serialize_card(card) for card in cards]},
  )


@router.get("/{card_id}", response_model=None)
def get_credit_card(
  user_id: int,
  card_id: int,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """Get a specific credit card by ID."""
  if not _can_manage_credit_cards(current_user, user_id):
    return response.forbidden("Only owner, admin or moderator can get credit cards")

  user = get_user_by_id(db, user_id)
  if not user:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("get_credit_card", "User not found"),
      data=None,
    )

  card = get_user_credit_card_by_id(db, card_id)
  if not card or card.user_id != user_id:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("get_credit_card", "Credit card not found"),
      data=None,
    )

  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("get_credit_card", "Credit card found"),
    data=_serialize_card(card),
  )


@router.post("", response_model=None)
def create_credit_card(
  user_id: int,
  card_data: UserCreditCardCreate,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """Create a new credit card entry for a user."""
  if not _can_manage_credit_cards(current_user, user_id):
    return response.forbidden("Only owner, admin or moderator can create credit cards")

  user = get_user_by_id(db, user_id)
  if not user:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("create_credit_card", "User not found"),
      data=None,
    )

  card = create_user_credit_card(
    db,
    user_id,
    card_data.card_info_encrypted,
    card_data.order_in_list,
  )
  return response.success(
    status=RestStatus.created_201,
    meta=_meta("create_credit_card", "Credit card created"),
    data=_serialize_card(card),
  )


@router.patch("/{card_id}", response_model=None)
def update_credit_card(
  user_id: int,
  card_id: int,
  card_data: UserCreditCardUpdate,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """Update a credit card entry."""
  if not _can_manage_credit_cards(current_user, user_id):
    return response.forbidden("Only owner, admin or moderator can update credit cards")

  user = get_user_by_id(db, user_id)
  if not user:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("update_credit_card", "User not found"),
      data=None,
    )

  card = get_user_credit_card_by_id(db, card_id)
  if not card or card.user_id != user_id:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("update_credit_card", "Credit card not found"),
      data=None,
    )

  updated = update_user_credit_card(db, card, card_data.model_dump(exclude_none=True))
  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("update_credit_card", "Credit card updated"),
    data=_serialize_card(updated),
  )


@router.delete("/{card_id}", response_model=None)
def delete_credit_card(
  user_id: int,
  card_id: int,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """Delete a credit card entry."""
  if not _can_manage_credit_cards(current_user, user_id):
    return response.forbidden("Only owner, admin or moderator can delete credit cards")

  user = get_user_by_id(db, user_id)
  if not user:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("delete_credit_card", "User not found"),
      data=None,
    )

  card = get_user_credit_card_by_id(db, card_id)
  if not card or card.user_id != user_id:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("delete_credit_card", "Credit card not found"),
      data=None,
    )

  deleted = delete_user_credit_card(db, card)
  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("delete_credit_card", "Credit card deleted"),
    data=_serialize_card(deleted),
  )


