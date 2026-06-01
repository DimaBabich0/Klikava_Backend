import os
import shutil
from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.api.responses.response_rest import ResponseRest
from app.api.responses.rest_meta import RestMeta
from app.api.responses.rest_status import RestStatus
from app.crud import (
  create_product_picture,
  delete_product_picture,
  get_product_by_id,
  get_product_picture_by_id,
  get_product_pictures,
  get_product_version_by_id,
  get_user_by_id,
  update_product_picture,
)
from app.database import get_db
from app.models import Product, ProductVersion, ProductPicture, User
from app.schemas import (
  ProductPictureResponse,
  ProductPictureUpdate,
)
from app.services.access_manager import AccessManager

router = APIRouter(prefix="/pictures", tags=["pictures"])
response = ResponseRest()


def _meta(action: str, message: str | None = None) -> RestMeta:
  return RestMeta(action=action, message=message)


def _is_product_manager(current_user: User | None, product: Product) -> bool:
  if current_user is None:
    return False
  if current_user.is_admin() or current_user.is_moderator():
    return True
  return current_user.is_seller()


def _picture_static_folder(product_id: int, version_id: int) -> Path:
  root = Path(__file__).resolve().parent.parent
  return root / "static" / "product_pictures" / str(product_id) / str(version_id)


def _serialize_picture(picture: ProductPicture) -> dict:
  return ProductPictureResponse.model_validate(picture).model_dump(mode="json")


def _user_picture_static_folder(user_id: int) -> Path:
  root = Path(__file__).resolve().parent.parent
  return root / "static" / "user_pictures" / str(user_id)


def _can_manage_user_pictures(current_user: User, user_id: int) -> bool:
  return current_user.id == user_id or current_user.is_admin() or current_user.is_moderator()


@router.get("/products/{product_id}/versions/{version_id}", response_model=None)
def list_product_pictures(
  product_id: int,
  version_id: int,
  skip: int = Query(0, ge=0),
  limit: int = Query(100, ge=1, le=500),
  db: Session = Depends(get_db),
):
  """List pictures for a product version."""
  version = get_product_version_by_id(db, version_id)
  if not version or version.product_id != product_id:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("list_product_pictures", "Product version not found"),
      data=None,
    )

  pictures = get_product_pictures(db, version_id, skip=skip, limit=limit)
  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("list_product_pictures", f"Pictures found: {len(pictures)}"),
    data=[_serialize_picture(p) for p in pictures],
  )


@router.post("/products/{product_id}/versions/{version_id}", response_model=None)
def upload_product_picture(
  product_id: int,
  version_id: int,
  file: UploadFile = File(...),
  sort_order: int = Query(0, ge=0),
  db: Session = Depends(get_db),
  current_user: User | None = Depends(AccessManager.get_current_user),
):
  """Upload a picture for a product version."""
  product = get_product_by_id(db, product_id)
  version = get_product_version_by_id(db, version_id)
  if not product or not version or version.product_id != product_id:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("upload_product_picture", "Product version not found"),
      data=None,
    )

  if not _is_product_manager(current_user, product):
    return response.error(
      status=RestStatus.forbidden_403,
      meta=_meta("upload_product_picture",
                 "Only seller, admin or moderator can upload pictures"),
      data=None,
    )

  upload_dir = _picture_static_folder(product_id, version_id)
  os.makedirs(upload_dir, exist_ok=True)
  filename = f"{uuid4().hex}_{Path(file.filename).name}"
  destination = upload_dir / filename
  with destination.open("wb") as buffer:
    shutil.copyfileobj(file.file, buffer)

  file_url = f"/static/product_pictures/{product_id}/{filename}"
  picture = create_product_picture(db, version_id, file_url, sort_order)
  return response.success(
    status=RestStatus.created_201,
    meta=_meta("upload_product_picture", "Product picture uploaded"),
    data=_serialize_picture(picture),
  )


@router.patch("/products/{product_id}/versions/{version_id}/{picture_id}", response_model=None)
def update_product_picture_endpoint(
  product_id: int,
  version_id: int,
  picture_id: int,
  picture_data: ProductPictureUpdate,
  db: Session = Depends(get_db),
  current_user: User | None = Depends(AccessManager.get_current_user),
):
  """Update picture metadata."""
  product = get_product_by_id(db, product_id)
  version = get_product_version_by_id(db, version_id)
  picture = get_product_picture_by_id(db, picture_id)
  if not product or not version or not picture or version.product_id != product_id or picture.product_version_id != version_id:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("update_product_picture", "Product picture not found"),
      data=None,
    )

  if not _is_product_manager(current_user, product):
    return response.error(
      status=RestStatus.forbidden_403,
      meta=_meta("update_product_picture",
                 "Only seller, admin or moderator can update pictures"),
      data=None,
    )

  updated = update_product_picture(
    db, picture, picture_data.model_dump(exclude_none=True))
  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("update_product_picture", "Product picture updated"),
    data=_serialize_picture(updated),
  )


@router.delete("/products/{product_id}/versions/{version_id}/{picture_id}", response_model=None)
def delete_product_picture_endpoint(
  product_id: int,
  version_id: int,
  picture_id: int,
  db: Session = Depends(get_db),
  current_user: User | None = Depends(AccessManager.get_current_user),
):
  """Delete a product picture."""
  product = get_product_by_id(db, product_id)
  version = get_product_version_by_id(db, version_id)
  picture = get_product_picture_by_id(db, picture_id)
  if not product or not version or not picture or version.product_id != product_id or picture.product_version_id != version_id:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("delete_product_picture", "Product picture not found"),
      data=None,
    )

  if not _is_product_manager(current_user, product):
    return response.error(
      status=RestStatus.forbidden_403,
      meta=_meta("delete_product_picture",
                 "Only seller, admin or moderator can delete pictures"),
      data=None,
    )

  deleted = delete_product_picture(db, picture, soft=True)
  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("delete_product_picture", "Product picture deleted"),
    data=_serialize_picture(deleted),
  )


@router.get("/users/{user_id}", response_model=None)
def get_user_avatar(
  user_id: int,
  db: Session = Depends(get_db),
):
  user = get_user_by_id(db, user_id)
  if not user:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("get_user_avatar", "User not found"),
      data=None,
    )

  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("get_user_avatar", "User avatar fetched"),
    data={"avatar_url": user.avatar_url},
  )


@router.post("/users/{user_id}", response_model=None)
def upload_user_avatar(
  user_id: int,
  file: UploadFile = File(...),
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  user = get_user_by_id(db, user_id)
  if not user:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("upload_user_avatar", "User not found"),
      data=None,
    )

  if not _can_manage_user_pictures(current_user, user_id):
    return response.error(
      status=RestStatus.forbidden_403,
      meta=_meta("upload_user_avatar",
                 "Only the user, admin or moderator can upload avatar"),
      data=None,
    )

  upload_dir = _user_picture_static_folder(user_id)
  os.makedirs(upload_dir, exist_ok=True)
  filename = f"{uuid4().hex}_{Path(file.filename).name}"
  destination = upload_dir / filename
  with destination.open("wb") as buffer:
    shutil.copyfileobj(file.file, buffer)

  file_url = f"/static/user_pictures/{filename}"
  user.avatar_url = file_url
  db.commit()
  db.refresh(user)

  return response.success(
    status=RestStatus.created_201,
    meta=_meta("upload_user_avatar", "User avatar uploaded"),
    data={"avatar_url": user.avatar_url},
  )


@router.patch("/users/{user_id}", response_model=None)
def update_user_avatar(
  user_id: int,
  file: UploadFile = File(...),
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  user = get_user_by_id(db, user_id)
  if not user:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("update_user_avatar", "User not found"),
      data=None,
    )

  if not _can_manage_user_pictures(current_user, user_id):
    return response.error(
      status=RestStatus.forbidden_403,
      meta=_meta("update_user_avatar",
                 "Only the user, admin or moderator can update avatar"),
      data=None,
    )

  upload_dir = _user_picture_static_folder(user_id)
  os.makedirs(upload_dir, exist_ok=True)
  filename = f"{uuid4().hex}_{Path(file.filename).name}"
  destination = upload_dir / filename
  with destination.open("wb") as buffer:
    shutil.copyfileobj(file.file, buffer)

  file_url = f"/static/user_pictures/{filename}"
  user.avatar_url = file_url
  db.commit()
  db.refresh(user)

  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("update_user_avatar", "User avatar updated"),
    data={"avatar_url": user.avatar_url},
  )


@router.delete("/users/{user_id}", response_model=None)
def delete_user_avatar(
  user_id: int,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  user = get_user_by_id(db, user_id)
  if not user:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("delete_user_avatar", "User not found"),
      data=None,
    )

  if not _can_manage_user_pictures(current_user, user_id):
    return response.error(
      status=RestStatus.forbidden_403,
      meta=_meta("delete_user_avatar",
                 "Only the user, admin or moderator can delete avatar"),
      data=None,
    )

  if user.avatar_url:
    avatar_path = Path(__file__).resolve().parent.parent / user.avatar_url.lstrip("/")
    try:
      if avatar_path.exists():
        avatar_path.unlink()
    except Exception:
      pass

  user.avatar_url = None
  db.commit()
  db.refresh(user)

  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("delete_user_avatar", "User avatar deleted"),
    data={"avatar_url": None},
  )
