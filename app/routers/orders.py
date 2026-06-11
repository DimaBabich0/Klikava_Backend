import math
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.responses.response_rest import ResponseRest
from app.api.responses.rest_meta import RestMeta, RestPagination
from app.api.responses.rest_status import RestStatus
from app.crud import (
  get_order_by_id,
  get_user_orders,
  get_user_orders_count,
  get_orders,
  get_orders_count,
  create_order,
  update_order,
  delete_order,
  add_item_to_order,
  remove_item_from_order,
  update_order_item,
  get_order_items,
  get_order_item_by_id,
)
from app.database import get_db
from app.models import Order, User
from app.schemas.order import (
  OrderCreate,
  OrderItemCreate,
  OrderItemResponse,
  OrderItemUpdate,
  OrderResponse,
  OrderUpdate,
)
from app.services.access_manager import AccessManager

router = APIRouter(prefix="/orders", tags=["orders"])
response = ResponseRest()

# Valid order statuses
ORDER_STATUSES = ["pending", "processing", "shipped", "delivered", "cancelled"]


def _meta(action: str, message: str | None = None) -> RestMeta:
  return RestMeta(action=action, message=message)


def _can_read_order(current_user: User, order: Order) -> bool:
  """Check if user can read this order."""
  return current_user.id == order.user_id or current_user.is_admin() or current_user.is_moderator()


def _can_manage_order(current_user: User, order: Order) -> bool:
  """Check if user can manage this order."""
  return current_user.id == order.user_id or current_user.is_admin() or current_user.is_moderator()


def _serialize_order(order: Order) -> dict:
  """Serialize order with all items."""
  data = OrderResponse.model_validate(order).model_dump(mode="json")
  data["items"] = [
    OrderItemResponse.model_validate(item).model_dump(mode="json")
    for item in order.items
  ]
  return data


@router.get("", response_model=None)
def list_orders(
  status: str | None = Query(None),
  user_id: int | None = Query(None),
  per_page: int = Query(10, ge=1, le=100),
  page: int = Query(1, ge=1),
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """List orders with optional filtering. Admin/moderator can filter by user_id, others see only their orders."""
  # Check access - if not admin/moderator, show only their orders
  if not (current_user.is_admin() or current_user.is_moderator()):
    user_id = current_user.id
  
  # Validate status if provided
  if status and status not in ORDER_STATUSES:
    return response.error(
      status=RestStatus.bad_request_400,
      meta=_meta("list_orders", f"Invalid status. Must be one of: {', '.join(ORDER_STATUSES)}"),
      data=None,
    )

  total = get_orders_count(db, status=status, user_id=user_id)
  orders = get_orders(
    db,
    status=status,
    user_id=user_id,
    skip=(page - 1) * per_page,
    limit=per_page,
  )

  pagination = response.build_pagination(page, per_page, total)

  return response.success_pagination(
    status=RestStatus.ok_200,
    meta=RestMeta(
      action="list_orders",
      message=f"Orders found: {len(orders)}",
      pagination=pagination,
    ),
    data={"items": [_serialize_order(order) for order in orders]},
  )


@router.get("/{order_id}", response_model=None)
def get_order(
  order_id: int,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """Get order by ID."""
  order = get_order_by_id(db, order_id)
  if not order:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("get_order", "Order not found"),
      data=None,
    )

  if not _can_read_order(current_user, order):
    return response.error(
      status=RestStatus.forbidden_403,
      meta=_meta("get_order", "You don't have permission to view this order"),
      data=None,
    )

  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("get_order", "Order found"),
    data=_serialize_order(order),
  )


@router.post("", response_model=None)
def create_order_endpoint(
  order_data: OrderCreate,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """Create a new order."""
  try:
    # Calculate total price from items
    total_price = order_data.delivery_price

    # Create order
    order = create_order(
      db,
      user_id=current_user.id,
      status="pending",
      delivery_price=order_data.delivery_price,
      total_price=0.0,  # Will be updated
      discount_item_id=order_data.discount_item_id,
    )

    # Add items to order
    item_total = 0.0
    for item_data in order_data.items:
      try:
        order_item = add_item_to_order(
          db,
          order.id,
          item_data.product_variant_id,
          item_data.quantity,
          price_snapshot=item_data.price_snapshot,
          discount_snapshot=item_data.discount_snapshot,
          final_price_snapshot=item_data.final_price_snapshot,
          discount_item_id=item_data.discount_item_id,
        )
        if item_data.final_price_snapshot:
          item_total += item_data.final_price_snapshot * item_data.quantity
        elif item_data.price_snapshot:
          item_total += item_data.price_snapshot * item_data.quantity

      except ValueError as e:
        # If item addition fails, delete order and return error
        delete_order(db, order)
        return response.error(
          status=RestStatus.bad_request_400,
          meta=_meta("create_order", f"Error adding item: {str(e)}"),
          data=None,
        )

    # Update total price
    total_price = item_total + order_data.delivery_price
    order = update_order(
      db,
      order,
      {"total_price": total_price},
    )

    # Refresh order to get all items
    db.refresh(order)

    return response.success(
      status=RestStatus.created_201,
      meta=_meta("create_order", "Order created"),
      data=_serialize_order(order),
    )

  except ValueError as e:
    return response.error(
      status=RestStatus.bad_request_400,
      meta=_meta("create_order", str(e)),
      data=None,
    )


@router.post("/{order_id}/items", response_model=None)
def add_item_endpoint(
  order_id: int,
  item_data: OrderItemCreate,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """Add item to order. Only possible if order is still pending and user is the owner."""
  order = get_order_by_id(db, order_id)
  if not order:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("add_item", "Order not found"),
      data=None,
    )

  if not _can_manage_order(current_user, order):
    return response.error(
      status=RestStatus.forbidden_403,
      meta=_meta("add_item", "You don't have permission to modify this order"),
      data=None,
    )

  if order.status != "pending":
    return response.error(
      status=RestStatus.bad_request_400,
      meta=_meta("add_item", "Cannot add items to order that is not pending"),
      data=None,
    )

  try:
    order_item = add_item_to_order(
      db,
      order_id,
      item_data.product_variant_id,
      item_data.quantity,
      price_snapshot=item_data.price_snapshot,
      discount_snapshot=item_data.discount_snapshot,
      final_price_snapshot=item_data.final_price_snapshot,
      discount_item_id=item_data.discount_item_id,
    )

    # Update order total price
    items = get_order_items(db, order_id)
    total_price = order.delivery_price
    for item in items:
      if item.final_price_snapshot:
        total_price += item.final_price_snapshot * item.quantity
      elif item.price_snapshot:
        total_price += item.price_snapshot * item.quantity

    update_order(db, order, {"total_price": total_price})
    db.refresh(order)

    return response.success(
      status=RestStatus.created_201,
      meta=_meta("add_item", "Item added to order"),
      data=_serialize_order(order),
    )

  except ValueError as e:
    return response.error(
      status=RestStatus.bad_request_400,
      meta=_meta("add_item", str(e)),
      data=None,
    )


@router.patch("/{order_id}/items/{item_id}", response_model=None)
def update_item_endpoint(
  order_id: int,
  item_id: int,
  item_data: OrderItemUpdate,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """Update order item (quantity). Only possible if order is still pending."""
  order = get_order_by_id(db, order_id)
  if not order:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("update_item", "Order not found"),
      data=None,
    )

  if not _can_manage_order(current_user, order):
    return response.error(
      status=RestStatus.forbidden_403,
      meta=_meta("update_item", "You don't have permission to modify this order"),
      data=None,
    )

  if order.status != "pending":
    return response.error(
      status=RestStatus.bad_request_400,
      meta=_meta("update_item", "Cannot modify items in order that is not pending"),
      data=None,
    )

  order_item = get_order_item_by_id(db, item_id)
  if not order_item or order_item.order_id != order_id:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("update_item", "Order item not found"),
      data=None,
    )

  try:
    updated_item = update_order_item(
      db,
      order_item,
      item_data.model_dump(exclude_none=True),
    )

    # Update order total price
    items = get_order_items(db, order_id)
    total_price = order.delivery_price
    for item in items:
      if item.final_price_snapshot:
        total_price += item.final_price_snapshot * item.quantity
      elif item.price_snapshot:
        total_price += item.price_snapshot * item.quantity

    update_order(db, order, {"total_price": total_price})
    db.refresh(order)

    return response.success(
      status=RestStatus.ok_200,
      meta=_meta("update_item", "Item updated"),
      data=_serialize_order(order),
    )

  except ValueError as e:
    return response.error(
      status=RestStatus.bad_request_400,
      meta=_meta("update_item", str(e)),
      data=None,
    )


@router.delete("/{order_id}/items/{item_id}", response_model=None)
def remove_item_endpoint(
  order_id: int,
  item_id: int,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """Remove item from order. Only possible if order is still pending."""
  order = get_order_by_id(db, order_id)
  if not order:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("remove_item", "Order not found"),
      data=None,
    )

  if not _can_manage_order(current_user, order):
    return response.error(
      status=RestStatus.forbidden_403,
      meta=_meta("remove_item", "You don't have permission to modify this order"),
      data=None,
    )

  if order.status != "pending":
    return response.error(
      status=RestStatus.bad_request_400,
      meta=_meta("remove_item", "Cannot remove items from order that is not pending"),
      data=None,
    )

  order_item = get_order_item_by_id(db, item_id)
  if not order_item or order_item.order_id != order_id:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("remove_item", "Order item not found"),
      data=None,
    )

  try:
    remove_item_from_order(db, item_id)

    # Update order total price
    items = get_order_items(db, order_id)
    total_price = order.delivery_price
    for item in items:
      if item.final_price_snapshot:
        total_price += item.final_price_snapshot * item.quantity
      elif item.price_snapshot:
        total_price += item.price_snapshot * item.quantity

    update_order(db, order, {"total_price": total_price})
    db.refresh(order)

    return response.success(
      status=RestStatus.ok_200,
      meta=_meta("remove_item", "Item removed"),
      data=_serialize_order(order),
    )

  except ValueError as e:
    return response.error(
      status=RestStatus.bad_request_400,
      meta=_meta("remove_item", str(e)),
      data=None,
    )


@router.patch("/{order_id}", response_model=None)
def update_order_endpoint(
  order_id: int,
  order_data: OrderUpdate,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """Update order status. Users can cancel if status is pending and sellers haven't accepted yet.
  Admin/moderator can update any field."""
  order = get_order_by_id(db, order_id)
  if not order:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("update_order", "Order not found"),
      data=None,
    )

  if not _can_manage_order(current_user, order):
    return response.error(
      status=RestStatus.forbidden_403,
      meta=_meta("update_order", "You don't have permission to modify this order"),
      data=None,
    )

  # Regular users can only cancel orders in pending status
  is_admin_or_mod = current_user.is_admin() or current_user.is_moderator()
  if not is_admin_or_mod:
    if order_data.status and order_data.status != "cancelled":
      return response.error(
        status=RestStatus.forbidden_403,
        meta=_meta("update_order", "Users can only cancel pending orders"),
        data=None,
      )
    if order_data.status == "cancelled" and order.status != "pending":
      return response.error(
        status=RestStatus.bad_request_400,
        meta=_meta("update_order", "Cannot cancel order that is not pending"),
        data=None,
      )

  # Validate status if provided
  if order_data.status and order_data.status not in ORDER_STATUSES:
    return response.error(
      status=RestStatus.bad_request_400,
      meta=_meta("update_order", f"Invalid status. Must be one of: {', '.join(ORDER_STATUSES)}"),
      data=None,
    )

  try:
    updated_order = update_order(
      db,
      order,
      order_data.model_dump(exclude_none=True),
    )

    return response.success(
      status=RestStatus.ok_200,
      meta=_meta("update_order", "Order updated"),
      data=_serialize_order(updated_order),
    )

  except ValueError as e:
    return response.error(
      status=RestStatus.bad_request_400,
      meta=_meta("update_order", str(e)),
      data=None,
    )


@router.delete("/{order_id}", response_model=None)
def delete_order_endpoint(
  order_id: int,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """Delete order. Only admin/moderator or order owner if pending."""
  order = get_order_by_id(db, order_id)
  if not order:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("delete_order", "Order not found"),
      data=None,
    )

  is_admin_or_mod = current_user.is_admin() or current_user.is_moderator()
  is_owner = current_user.id == order.user_id

  if not (is_admin_or_mod or is_owner):
    return response.error(
      status=RestStatus.forbidden_403,
      meta=_meta("delete_order", "You don't have permission to delete this order"),
      data=None,
    )

  # Regular users can only delete pending orders
  if not is_admin_or_mod and order.status != "pending":
    return response.error(
      status=RestStatus.bad_request_400,
      meta=_meta("delete_order", "Cannot delete order that is not pending"),
      data=None,
    )

  try:
    delete_order(db, order)
    return response.success(
      status=RestStatus.ok_200,
      meta=_meta("delete_order", "Order deleted"),
      data=None,
    )

  except ValueError as e:
    return response.error(
      status=RestStatus.bad_request_400,
      meta=_meta("delete_order", str(e)),
      data=None,
    )

