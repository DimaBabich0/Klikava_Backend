from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.responses.response_rest import ResponseRest
from app.api.responses.rest_meta import RestMeta
from app.api.responses.rest_status import RestStatus
from app.crud import (
  create_shipment,
  delete_shipment,
  get_order_by_id,
  get_shipment_by_id,
  get_shipments_by_order,
  get_shipments_count_by_order,
  update_shipment,
)
from app.database import get_db
from app.models import Order, Shipment, User
from app.schemas import (
  ShipmentCreate,
  ShipmentResponse,
  ShipmentUpdate,
)
from app.services.access_manager import AccessManager

router = APIRouter(prefix="/orders/{order_id}/shipments", tags=["shipments"])
response = ResponseRest()


def _meta(action: str, message: str | None = None) -> RestMeta:
  return RestMeta(action=action, message=message)


def _can_manage_order(current_user: User, order: Order) -> bool:
  return current_user.id == order.user_id or current_user.is_admin() or current_user.is_moderator()


def _serialize_shipment(shipment: Shipment) -> dict:
  return ShipmentResponse.model_validate(shipment).model_dump(mode="json")


@router.get("", response_model=None)
def list_shipments(
  order_id: int,
  per_page: int = Query(10, ge=1, le=100),
  page: int = Query(1, ge=1),
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """List shipments for an order."""
  order = get_order_by_id(db, order_id)
  if not order:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("list_shipments", "Order not found"),
      data=None,
    )

  if not _can_manage_order(current_user, order):
    return response.forbidden("Only order owner, admin or moderator can list shipments")

  total = get_shipments_count_by_order(db, order_id)
  shipments = get_shipments_by_order(db, order_id, skip=(page - 1) * per_page, limit=per_page)
  pagination = response.build_pagination(page, per_page, total)

  return response.success_pagination(
    status=RestStatus.ok_200,
    meta=RestMeta(
      action="list_shipments",
      message=f"Shipments found: {len(shipments)}",
      pagination=pagination,
    ),
    data={"items": [_serialize_shipment(s) for s in shipments]},
  )


@router.get("/{shipment_id}", response_model=None)
def get_shipment(
  order_id: int,
  shipment_id: int,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """Get a specific shipment."""
  order = get_order_by_id(db, order_id)
  if not order:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("get_shipment", "Order not found"),
      data=None,
    )

  if not _can_manage_order(current_user, order):
    return response.forbidden("Only order owner, admin or moderator can get shipment")

  shipment = get_shipment_by_id(db, shipment_id)
  if not shipment or shipment.order_id != order_id:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("get_shipment", "Shipment not found"),
      data=None,
    )

  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("get_shipment", "Shipment found"),
    data=_serialize_shipment(shipment),
  )


@router.post("", response_model=None)
def create_shipment_endpoint(
  order_id: int,
  shipment_data: ShipmentCreate,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """Create a new shipment for an order."""
  order = get_order_by_id(db, order_id)
  if not order:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("create_shipment", "Order not found"),
      data=None,
    )

  if not _can_manage_order(current_user, order):
    return response.forbidden("Only order owner, admin or moderator can create shipments")

  try:
    shipment = create_shipment(
      db,
      order_id,
      shipment_data.status,
      shipment_data.tracking_number,
      shipment_data.created_at,
    )
  except ValueError as e:
    return response.error(
      status=RestStatus.bad_request_400,
      meta=_meta("create_shipment", str(e)),
      data=None,
    )

  return response.success(
    status=RestStatus.created_201,
    meta=_meta("create_shipment", "Shipment created"),
    data=_serialize_shipment(shipment),
  )


@router.patch("/{shipment_id}", response_model=None)
def update_shipment_endpoint(
  order_id: int,
  shipment_id: int,
  shipment_data: ShipmentUpdate,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """Update shipment data."""
  order = get_order_by_id(db, order_id)
  if not order:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("update_shipment", "Order not found"),
      data=None,
    )

  if not _can_manage_order(current_user, order):
    return response.forbidden("Only order owner, admin or moderator can update shipment")

  shipment = get_shipment_by_id(db, shipment_id)
  if not shipment or shipment.order_id != order_id:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("update_shipment", "Shipment not found"),
      data=None,
    )

  updated = update_shipment(db, shipment, shipment_data.model_dump(exclude_none=True))
  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("update_shipment", "Shipment updated"),
    data=_serialize_shipment(updated),
  )


@router.delete("/{shipment_id}", response_model=None)
def delete_shipment_endpoint(
  order_id: int,
  shipment_id: int,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """Delete a shipment."""
  order = get_order_by_id(db, order_id)
  if not order:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("delete_shipment", "Order not found"),
      data=None,
    )

  if not _can_manage_order(current_user, order):
    return response.forbidden("Only order owner, admin or moderator can delete shipment")

  shipment = get_shipment_by_id(db, shipment_id)
  if not shipment or shipment.order_id != order_id:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("delete_shipment", "Shipment not found"),
      data=None,
    )

  delete_shipment(db, shipment)
  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("delete_shipment", "Shipment deleted"),
    data=None,
  )


