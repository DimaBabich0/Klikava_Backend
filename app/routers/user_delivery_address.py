from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.responses.response_rest import ResponseRest
from app.api.responses.rest_meta import RestMeta
from app.api.responses.rest_status import RestStatus
from app.crud import (
  create_user_delivery_address,
  delete_user_delivery_address,
  get_user_by_id,
  get_user_delivery_address_by_id,
  get_user_delivery_addresses,
  get_user_delivery_addresses_count,
  update_user_delivery_address,
)
from app.database import get_db
from app.models import User, UserDeliveryAddress
from app.schemas import (
  UserDeliveryAddressCreate,
  UserDeliveryAddressResponse,
  UserDeliveryAddressUpdate,
)
from app.services.access_manager import AccessManager

router = APIRouter(prefix="/users/{user_id}/delivery_addresses", tags=["user_delivery_addresses"])
response = ResponseRest()


def _meta(action: str, message: str | None = None) -> RestMeta:
  return RestMeta(action=action, message=message)


def _can_manage_delivery_addresses(current_user: User, user_id: int) -> bool:
  return current_user.id == user_id or current_user.is_admin() or current_user.is_moderator()


def _serialize_address(address: UserDeliveryAddress) -> dict:
  return UserDeliveryAddressResponse.model_validate(address).model_dump(mode="json")


@router.get("", response_model=None)
def list_delivery_addresses(
  user_id: int,
  per_page: int = Query(10, ge=1, le=100),
  page: int = Query(1, ge=1),
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """List delivery addresses for a user."""
  if not _can_manage_delivery_addresses(current_user, user_id):
    return response.forbidden("Only owner, admin or moderator can list delivery addresses")

  user = get_user_by_id(db, user_id)
  if not user:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("list_delivery_addresses", "User not found"),
      data=None,
    )

  total = get_user_delivery_addresses_count(db, user_id)
  addresses = get_user_delivery_addresses(db, user_id, skip=(page - 1) * per_page, limit=per_page)
  pagination = response.build_pagination(page, per_page, total)

  return response.success_pagination(
    status=RestStatus.ok_200,
    meta=RestMeta(
      action="list_delivery_addresses",
      message=f"Delivery addresses found: {len(addresses)}",
      pagination=pagination,
    ),
    data={"items": [_serialize_address(addr) for addr in addresses]},
  )


@router.get("/{address_id}", response_model=None)
def get_delivery_address(
  user_id: int,
  address_id: int,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """Get a specific delivery address by ID."""
  if not _can_manage_delivery_addresses(current_user, user_id):
    return response.forbidden("Only owner, admin or moderator can get delivery addresses")

  user = get_user_by_id(db, user_id)
  if not user:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("get_delivery_address", "User not found"),
      data=None,
    )

  address = get_user_delivery_address_by_id(db, address_id)
  if not address or address.user_id != user_id:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("get_delivery_address", "Delivery address not found"),
      data=None,
    )

  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("get_delivery_address", "Delivery address found"),
    data=_serialize_address(address),
  )


@router.post("", response_model=None)
def create_delivery_address(
  user_id: int,
  address_data: UserDeliveryAddressCreate,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """Create a new delivery address for a user."""
  if not _can_manage_delivery_addresses(current_user, user_id):
    return response.forbidden("Only owner, admin or moderator can create delivery addresses")

  user = get_user_by_id(db, user_id)
  if not user:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("create_delivery_address", "User not found"),
      data=None,
    )

  address = create_user_delivery_address(db, user_id, address_data.address_line)
  return response.success(
    status=RestStatus.created_201,
    meta=_meta("create_delivery_address", "Delivery address created"),
    data=_serialize_address(address),
  )


@router.patch("/{address_id}", response_model=None)
def update_delivery_address(
  user_id: int,
  address_id: int,
  address_data: UserDeliveryAddressUpdate,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """Update a delivery address."""
  if not _can_manage_delivery_addresses(current_user, user_id):
    return response.forbidden("Only owner, admin or moderator can update delivery addresses")

  user = get_user_by_id(db, user_id)
  if not user:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("update_delivery_address", "User not found"),
      data=None,
    )

  address = get_user_delivery_address_by_id(db, address_id)
  if not address or address.user_id != user_id:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("update_delivery_address", "Delivery address not found"),
      data=None,
    )

  updated = update_user_delivery_address(db, address, address_data.model_dump(exclude_none=True))
  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("update_delivery_address", "Delivery address updated"),
    data=_serialize_address(updated),
  )


@router.delete("/{address_id}", response_model=None)
def delete_delivery_address(
  user_id: int,
  address_id: int,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """Delete a delivery address."""
  if not _can_manage_delivery_addresses(current_user, user_id):
    return response.forbidden("Only owner, admin or moderator can delete delivery addresses")

  user = get_user_by_id(db, user_id)
  if not user:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("delete_delivery_address", "User not found"),
      data=None,
    )

  address = get_user_delivery_address_by_id(db, address_id)
  if not address or address.user_id != user_id:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("delete_delivery_address", "Delivery address not found"),
      data=None,
    )

  deleted = delete_user_delivery_address(db, address)
  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("delete_delivery_address", "Delivery address deleted"),
    data=_serialize_address(deleted),
  )


