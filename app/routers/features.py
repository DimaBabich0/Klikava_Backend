from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.responses.response_rest import ResponseRest
from app.api.responses.rest_meta import RestMeta
from app.api.responses.rest_status import RestStatus
from app.crud import (
  create_feature,
  delete_feature,
  get_feature_by_id,
  get_features,
  get_features_count,
  update_feature,
)
from app.database import get_db
from app.models import Feature, User
from app.schemas import (
  FeatureCreate,
  FeatureResponse,
  FeatureUpdate,
)
from app.services.access_manager import AccessManager

router = APIRouter(prefix="/features", tags=["features"])
response = ResponseRest()


def _meta(action: str, message: str | None = None) -> RestMeta:
  return RestMeta(action=action, message=message)


def _serialize_feature(feature: Feature) -> dict:
  return FeatureResponse.model_validate(feature).model_dump(mode="json")


def _can_manage_features(current_user: User) -> bool:
  return current_user.is_admin() or current_user.is_moderator()


@router.get("", response_model=None)
def list_features(
  is_primary: bool | None = Query(None),
  per_page: int = Query(10, ge=1, le=100),
  page: int = Query(1, ge=1),
  db: Session = Depends(get_db),
):
  total = get_features_count(db, is_primary)
  features = get_features(db, is_primary, skip=(page - 1) * per_page, limit=per_page)
  pagination = response.build_pagination(page, per_page, total)

  return response.success_pagination(
    status=RestStatus.ok_200,
    meta=RestMeta(
      action="list_features",
      message=f"Features found: {len(features)}",
      pagination=pagination,
    ),
    data={"items": [_serialize_feature(f) for f in features]},
  )


@router.get("/{feature_id}", response_model=None)
def get_feature(
  feature_id: int,
  db: Session = Depends(get_db),
):
  feature = get_feature_by_id(db, feature_id)
  if not feature:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("get_feature", "Feature not found"),
      data=None,
    )

  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("get_feature", "Feature found"),
    data=_serialize_feature(feature),
  )


@router.post("", response_model=None)
def create_feature_endpoint(
  feature_data: FeatureCreate,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  if not _can_manage_features(current_user):
    return response.forbidden("Only admin or moderator can create features")

  feature = create_feature(
    db,
    title=feature_data.title,
    is_primary=feature_data.is_primary,
  )

  return response.success(
    status=RestStatus.created_201,
    meta=_meta("create_feature", "Feature created"),
    data=_serialize_feature(feature),
  )


@router.patch("/{feature_id}", response_model=None)
def update_feature_endpoint(
  feature_id: int,
  feature_data: FeatureUpdate,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  if not _can_manage_features(current_user):
    return response.forbidden("Only admin or moderator can update features")

  feature = get_feature_by_id(db, feature_id)
  if not feature:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("update_feature", "Feature not found"),
      data=None,
    )

  updated = update_feature(db, feature, feature_data.model_dump(exclude_none=True))
  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("update_feature", "Feature updated"),
    data=_serialize_feature(updated),
  )


@router.delete("/{feature_id}", response_model=None)
def delete_feature_endpoint(
  feature_id: int,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  if not _can_manage_features(current_user):
    return response.forbidden("Only admin or moderator can delete features")

  feature = get_feature_by_id(db, feature_id)
  if not feature:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("delete_feature", "Feature not found"),
      data=None,
    )

  deleted = delete_feature(db, feature)
  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("delete_feature", "Feature deleted"),
    data=_serialize_feature(deleted),
  )


