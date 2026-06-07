from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.responses.response_rest import ResponseRest
from app.api.responses.rest_meta import RestMeta
from app.api.responses.rest_status import RestStatus
from app.crud import (
  create_discount,
  delete_discount,
  get_discount_by_id,
  get_discounts,
  get_discounts_count,
  update_discount,
)
from app.database import get_db
from app.models import Discount, User
from app.schemas import (
  DiscountCreate,
  DiscountResponse,
  DiscountUpdate,
)
from app.services.access_manager import AccessManager

router = APIRouter(prefix="/discounts", tags=["discounts"])
response = ResponseRest()


def _meta(action: str, message: str | None = None) -> RestMeta:
  return RestMeta(action=action, message=message)


def _serialize_discount(discount: Discount) -> dict:
  return DiscountResponse.model_validate(discount).model_dump(mode="json")


def _can_manage_discounts(current_user: User) -> bool:
  return current_user.is_admin() or current_user.is_moderator()


@router.get("", response_model=None)
def list_discounts(
  active_only: bool = Query(False),
  per_page: int = Query(10, ge=1, le=100),
  page: int = Query(1, ge=1),
  db: Session = Depends(get_db),
):
  total = get_discounts_count(db, active_only)
  discounts = get_discounts(db, active_only, skip=(page - 1) * per_page, limit=per_page)
  pagination = response.build_pagination(page, per_page, total)

  return response.success_pagination(
    status=RestStatus.ok_200,
    meta=RestMeta(
      action="list_discounts",
      message=f"Discounts found: {len(discounts)}",
      pagination=pagination,
    ),
    data={"items": [_serialize_discount(d) for d in discounts]},
  )


@router.get("/{discount_id}", response_model=None)
def get_discount(
  discount_id: int,
  db: Session = Depends(get_db),
):
  discount = get_discount_by_id(db, discount_id)
  if not discount:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("get_discount", "Discount not found"),
      data=None,
    )

  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("get_discount", "Discount found"),
    data=_serialize_discount(discount),
  )


@router.post("", response_model=None)
def create_discount_endpoint(
  discount_data: DiscountCreate,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  if not _can_manage_discounts(current_user):
    return response.forbidden("Only admin or moderator can create discounts")

  try:
    discount = create_discount(
      db,
      name=discount_data.name,
      description=discount_data.description,
      start_date=discount_data.start_date,
      end_date=discount_data.end_date,
      discount_type=discount_data.discount_type,
      value=discount_data.value,
      coupon_code=discount_data.coupon_code,
      target_type=discount_data.target_type,
      target_id=discount_data.target_id,
      is_active=discount_data.is_active,
    )
  except ValueError as e:
    return response.error(
      status=RestStatus.bad_request_400,
      meta=_meta("create_discount", str(e)),
      data=None,
    )

  return response.success(
    status=RestStatus.created_201,
    meta=_meta("create_discount", "Discount created"),
    data=_serialize_discount(discount),
  )


@router.patch("/{discount_id}", response_model=None)
def update_discount_endpoint(
  discount_id: int,
  discount_data: DiscountUpdate,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  if not _can_manage_discounts(current_user):
    return response.forbidden("Only admin or moderator can update discounts")

  discount = get_discount_by_id(db, discount_id)
  if not discount:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("update_discount", "Discount not found"),
      data=None,
    )

  try:
    updated = update_discount(db, discount, discount_data.model_dump(exclude_none=True))
  except ValueError as e:
    return response.error(
      status=RestStatus.bad_request_400,
      meta=_meta("update_discount", str(e)),
      data=None,
    )

  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("update_discount", "Discount updated"),
    data=_serialize_discount(updated),
  )


@router.delete("/{discount_id}", response_model=None)
def delete_discount_endpoint(
  discount_id: int,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  if not _can_manage_discounts(current_user):
    return response.forbidden("Only admin or moderator can delete discounts")

  discount = get_discount_by_id(db, discount_id)
  if not discount:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("delete_discount", "Discount not found"),
      data=None,
    )

  delete_discount(db, discount)
  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("delete_discount", "Discount deleted"),
    data={"id": discount_id},
  )


def _forbidden(action: str, message: str):
  return response.error(
    status=RestStatus.forbidden_403,
    meta=_meta(action, message),
    data=None,
  )
