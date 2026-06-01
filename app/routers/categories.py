from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.responses.response_rest import ResponseRest
from app.api.responses.rest_meta import RestMeta
from app.api.responses.rest_status import RestStatus
from app.crud import (
  create_category,
  delete_category,
  get_category_by_id,
  get_categories,
  get_categories_count,
  update_category,
)
from app.database import get_db
from app.models import Category, User
from app.schemas import (
  CategoryCreate,
  CategoryResponse,
  CategoryUpdate,
)
from app.services.access_manager import AccessManager

router = APIRouter(prefix="/categories", tags=["categories"])
response = ResponseRest()


def _meta(action: str, message: str | None = None) -> RestMeta:
  return RestMeta(action=action, message=message)


def _can_manage_categories(current_user: User) -> bool:
  return current_user.is_admin() or current_user.is_moderator()


def _serialize_category(category: Category) -> dict:
  return CategoryResponse.model_validate(category).model_dump(mode="json")


@router.get("", response_model=None)
def list_categories(
  parent_id: int | None = Query(None),
  per_page: int = Query(10, ge=1, le=100),
  page: int = Query(1, ge=1),
  db: Session = Depends(get_db),
):
  """List categories."""
  total = get_categories_count(db, parent_id)
  categories = get_categories(db, parent_id, skip=(page - 1) * per_page, limit=per_page)
  pagination = response.build_pagination(page, per_page, total)

  return response.success_pagination(
    status=RestStatus.ok_200,
    meta=RestMeta(
      action="list_categories",
      message=f"Categories found: {len(categories)}",
      pagination=pagination,
    ),
    data={"items": [_serialize_category(cat) for cat in categories]},
  )


@router.get("/{category_id}", response_model=None)
def get_category(
  category_id: int,
  db: Session = Depends(get_db),
):
  """Get category by ID."""
  category = get_category_by_id(db, category_id)
  if not category:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("get_category", "Category not found"),
      data=None,
    )

  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("get_category", "Category found"),
    data=_serialize_category(category),
  )


@router.post("", response_model=None)
def create_category_endpoint(
  category_data: CategoryCreate,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """Create a new category."""
  if not _can_manage_categories(current_user):
    return response.forbidden("Only admin or moderator can create categories")

  try:
    category = create_category(
      db,
      title=category_data.title,
      description=category_data.description,
      parent_id=category_data.parent_id,
      order_in_price=category_data.order_in_price,
    )
  except ValueError as e:
    return response.error(
      status=RestStatus.bad_request_400,
      meta=_meta("create_category", str(e)),
      data=None,
    )

  return response.success(
    status=RestStatus.created_201,
    meta=_meta("create_category", "Category created"),
    data=_serialize_category(category),
  )


@router.patch("/{category_id}", response_model=None)
def update_category_endpoint(
  category_id: int,
  category_data: CategoryUpdate,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """Update a category."""
  if not _can_manage_categories(current_user):
    return response.forbidden("Only admin or moderator can update categories")

  category = get_category_by_id(db, category_id)
  if not category:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("update_category", "Category not found"),
      data=None,
    )

  try:
    updated = update_category(db, category, category_data.model_dump(exclude_none=True))
  except ValueError as e:
    return response.error(
      status=RestStatus.bad_request_400,
      meta=_meta("update_category", str(e)),
      data=None,
    )

  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("update_category", "Category updated"),
    data=_serialize_category(updated),
  )


@router.delete("/{category_id}", response_model=None)
def delete_category_endpoint(
  category_id: int,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  """Delete a category."""
  if not _can_manage_categories(current_user):
    return response.forbidden("Only admin or moderator can delete categories")

  category = get_category_by_id(db, category_id)
  if not category:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("delete_category", "Category not found"),
      data=None,
    )

  deleted = delete_category(db, category)
  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("delete_category", "Category deleted"),
    data=_serialize_category(deleted),
  )


def _can_read_user(current_user: User, user_id: int) -> bool:
  return current_user.id == user_id or current_user.is_admin() or current_user.is_moderator()


def _can_manage_users(current_user: User) -> bool:
  return current_user.is_admin() or current_user.is_moderator()

