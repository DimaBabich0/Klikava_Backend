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
  create_product, get_product_by_id, get_product_by_slug, get_products, get_products_count,
  update_product as crud_update_product, delete_product as crud_delete_product, search_products,
  create_product_version, get_product_version_by_id, get_product_versions,
  update_product_version, delete_product_version,
  create_product_variant, get_product_variant_by_id, get_product_variants,
  update_product_variant, delete_product_variant,
  create_product_picture, get_product_picture_by_id, get_product_pictures,
  update_product_picture, delete_product_picture,
)
from app.database import get_db
from app.models import Product, User, ProductVersion, ProductVariant
from app.schemas.product import (
  ProductCreate, ProductUpdate, ProductResponse, ProductVersionResponse,
  ProductVersionCreate, ProductVersionUpdate,
  ProductVariantCreate, ProductVariantUpdate, ProductVariantResponse,
  ProductPictureUpdate, ProductPictureResponse,
)
from app.services.access_manager import AccessManager

router = APIRouter(prefix="/products", tags=["products"])
response = ResponseRest()


def _meta(action: str, message: str | None = None) -> RestMeta:
  return RestMeta(action=action, message=message)


def _serialize_product(product: Product) -> dict:
  # base product fields
  base = ProductResponse.model_validate(product).model_dump(mode="json")

  # find current (latest non-deleted) version
  versions = [v for v in getattr(
    product, "versions", []) if v.deleted_at is None]
  current_version = None
  if versions:
    current = max(versions, key=lambda v: v.created_at)
    # rely on Pydantic to serialize nested variants and pictures
    current_version = ProductVersionResponse.model_validate(
      current).model_dump(mode="json")

  base["current_version"] = current_version
  return base


def _is_product_manager(current_user: User, product: Product) -> bool:
  if current_user.is_admin() or current_user.is_moderator():
    return True
  return current_user.is_seller()


def _product_static_folder(product_id: int, version_id: int) -> Path:
  root = Path(__file__).resolve().parent.parent
  return root / "static" / "product_pictures" / str(product_id) / str(version_id)


@router.post("", response_model=None)
def create(product_data: ProductCreate, db: Session = Depends(get_db), current_user: User | None = Depends(AccessManager.require_role("SELLER"))):
  """Create a new product. SELLER role required."""
  try:
    new_product = create_product(
      db, seller_id=product_data.seller_id, status=product_data.status)
    return response.success(
      status=RestStatus.created_201,
      meta=_meta("create_product", "Product created"),
      data=_serialize_product(new_product),
    )
  except ValueError as e:
    return response.error(
      status=RestStatus.bad_request_400,
      meta=_meta("create_product", str(e)),
      data=None,
    )


@router.get("", response_model=None)
def list_products(
  per_page: int = Query(10, ge=1, le=100),
  page: int = Query(1, ge=1),
  db: Session = Depends(get_db),
):
  """List products (public)."""
  total = get_products_count(db)
  products = get_products(db, skip=(page - 1) * per_page, limit=per_page)
  pagination = response.build_pagination(page, per_page, total)

  return response.success_pagination(
    status=RestStatus.ok_200,
    meta=RestMeta(
      action="list_products",
      message=f"Products found: {len(products)}",
      pagination=pagination,
    ),
    data={"items": [_serialize_product(p) for p in products]},
  )


@router.get("/search", response_model=None)
def search(q: str = Query(..., min_length=1), skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)):
  """Search products by title (searches product versions' titles)."""
  products = search_products(db, q, skip=skip, limit=limit)
  total = len(products)
  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("search_products", f"Products found: {total}"),
    data={
      "items": [_serialize_product(p) for p in products],
      "skip": skip,
      "limit": limit,
      "total": total,
    },
  )


@router.get("/{product_id_or_slug}", response_model=None)
def get_product(product_id_or_slug: str, db: Session = Depends(get_db)):
  if product_id_or_slug.isdigit():
    product = get_product_by_id(db, int(product_id_or_slug))
    action = "get_product_by_id"
  else:
    product = get_product_by_slug(db, product_id_or_slug)
    action = "get_product_by_slug"

  if not product:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta(action, "Product not found"),
      data=None,
    )

  return response.success(
    status=RestStatus.ok_200,
    meta=_meta(action, "Product found"),
    data=_serialize_product(product),
  )


@router.patch("/{product_id}", response_model=None)
def update_product(product_id: int, product_data: ProductUpdate, db: Session = Depends(get_db), current_user: User | None = Depends(AccessManager.get_current_user)):
  """Update product. Owner (seller) or admin required."""
  product = get_product_by_id(db, product_id)
  if not product:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("update_product", "Product not found"),
      data=None,
    )

  # Basic permission: allow if current user is admin/moderator or has SELLER role
  if not (current_user.is_admin() or current_user.is_moderator() or current_user.is_seller()):
    return response.error(
      status=RestStatus.forbidden_403,
      meta=_meta("update_product",
                 "Only seller, admin or moderator can update product"),
      data=None,
    )

  updated = crud_update_product(
    db, product, product_data.model_dump(exclude_none=True))
  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("update_product", "Product updated"),
    data=_serialize_product(updated),
  )


@router.delete("/{product_id}", response_model=None)
def delete_product(product_id: int, db: Session = Depends(get_db), current_user: User | None = Depends(AccessManager.get_current_user)):
  """Delete (soft) product. Owner (seller) or admin required."""
  product = get_product_by_id(db, product_id)
  if not product:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("delete_product", "Product not found"),
      data=None,
    )

  if not (current_user.is_admin() or current_user.is_moderator() or current_user.is_seller()):
    return response.error(
      status=RestStatus.forbidden_403,
      meta=_meta("delete_product",
                 "Only seller, admin or moderator can delete product"),
      data=None,
    )

  deleted = crud_delete_product(db, product, soft=True)
  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("delete_product", "Product deleted"),
    data=_serialize_product(deleted),
  )


@router.get("/{product_id}/versions", response_model=None)
def list_product_versions(product_id: int, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)):
  """List product versions."""
  versions = get_product_versions(db, product_id, skip=skip, limit=limit)
  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("list_product_versions", f"Versions found: {len(versions)}"),
    data={
      "items": [ProductVersionResponse.model_validate(v).model_dump(mode="json") for v in versions],
      "skip": skip,
      "limit": limit,
    },
  )


@router.post("/{product_id}/versions", response_model=None)
def create_product_version_endpoint(product_id: int, version_data: ProductVersionCreate, db: Session = Depends(get_db), current_user: User | None = Depends(AccessManager.get_current_user)):
  """Create a new product version. Seller or admin only."""
  product = get_product_by_id(db, product_id)
  if not product:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("create_product_version", "Product not found"),
      data=None,
    )

  if not _is_product_manager(current_user, product):
    return response.error(
      status=RestStatus.forbidden_403,
      meta=_meta("create_product_version",
                 "Only seller, admin or moderator can create product versions"),
      data=None,
    )

  try:
    version = create_product_version(
      db,
      product_id=product_id,
      category_id=version_data.category_id,
      title=version_data.title,
      description=version_data.description,
      slug=version_data.slug,
    )
    return response.success(
      status=RestStatus.created_201,
      meta=_meta("create_product_version", "Product version created"),
      data=ProductVersionResponse.model_validate(
        version).model_dump(mode="json"),
    )
  except ValueError as e:
    return response.error(
      status=RestStatus.bad_request_400,
      meta=_meta("create_product_version", str(e)),
      data=None,
    )


@router.get("/{product_id}/versions/{version_id}", response_model=None)
def get_product_version(product_id: int, version_id: int, db: Session = Depends(get_db)):
  """Get a specific version."""
  version = get_product_version_by_id(db, version_id)
  if not version or version.product_id != product_id:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("get_product_version", "Product version not found"),
      data=None,
    )

  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("get_product_version", "Product version found"),
    data=ProductVersionResponse.model_validate(
      version).model_dump(mode="json"),
  )


@router.patch("/{product_id}/versions/{version_id}", response_model=None)
def update_product_version_endpoint(product_id: int, version_id: int, version_data: ProductVersionUpdate, db: Session = Depends(get_db), current_user: User | None = Depends(AccessManager.get_current_user)):
  """Update a product version."""
  product = get_product_by_id(db, product_id)
  version = get_product_version_by_id(db, version_id)
  if not product or not version or version.product_id != product_id:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("update_product_version", "Product version not found"),
      data=None,
    )

  if not _is_product_manager(current_user, product):
    return response.error(
      status=RestStatus.forbidden_403,
      meta=_meta("update_product_version",
                 "Only seller, admin or moderator can update product versions"),
      data=None,
    )

  updated = update_product_version(
    db, version, version_data.model_dump(exclude_none=True))
  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("update_product_version", "Product version updated"),
    data=ProductVersionResponse.model_validate(
      updated).model_dump(mode="json"),
  )


@router.delete("/{product_id}/versions/{version_id}", response_model=None)
def delete_product_version_endpoint(product_id: int, version_id: int, db: Session = Depends(get_db), current_user: User | None = Depends(AccessManager.get_current_user)):
  """Delete a product version."""
  product = get_product_by_id(db, product_id)
  version = get_product_version_by_id(db, version_id)
  if not product or not version or version.product_id != product_id:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("delete_product_version", "Product version not found"),
      data=None,
    )

  if not _is_product_manager(current_user, product):
    return response.error(
      status=RestStatus.forbidden_403,
      meta=_meta("delete_product_version",
                 "Only seller, admin or moderator can delete product versions"),
      data=None,
    )

  deleted = delete_product_version(db, version, soft=True)
  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("delete_product_version", "Product version deleted"),
    data=ProductVersionResponse.model_validate(
      deleted).model_dump(mode="json"),
  )


@router.get("/{product_id}/versions/{version_id}/variants", response_model=None)
def list_product_variants(product_id: int, version_id: int, db: Session = Depends(get_db)):
  """List variants for a product version."""
  version = get_product_version_by_id(db, version_id)
  if not version or version.product_id != product_id:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("list_product_variants", "Product version not found"),
      data=None,
    )

  variants = get_product_variants(db, version_id)
  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("list_product_variants", f"Variants found: {len(variants)}"),
    data=[ProductVariantResponse.model_validate(
      v).model_dump(mode="json") for v in variants],
  )


@router.post("/{product_id}/versions/{version_id}/variants", response_model=None)
def create_product_variant_endpoint(product_id: int, version_id: int, variant_data: ProductVariantCreate, db: Session = Depends(get_db), current_user: User | None = Depends(AccessManager.get_current_user)):
  """Create a new variant for a version."""
  product = get_product_by_id(db, product_id)
  version = get_product_version_by_id(db, version_id)
  if not product or not version or version.product_id != product_id:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("create_product_variant", "Product version not found"),
      data=None,
    )

  if not _is_product_manager(current_user, product):
    return response.error(
      status=RestStatus.forbidden_403,
      meta=_meta("create_product_variant",
                 "Only seller, admin or moderator can create variants"),
      data=None,
    )

  try:
    variant = create_product_variant(
      db,
      version_id=version_id,
      sku_code=variant_data.sku_code,
      price=variant_data.price,
      stock=variant_data.stock,
      discount=variant_data.discount,
    )
    return response.success(
      status=RestStatus.created_201,
      meta=_meta("create_product_variant", "Product variant created"),
      data=ProductVariantResponse.model_validate(
        variant).model_dump(mode="json"),
    )
  except ValueError as e:
    return response.error(
      status=RestStatus.bad_request_400,
      meta=_meta("create_product_variant", str(e)),
      data=None,
    )


@router.get("/{product_id}/versions/{version_id}/variants/{variant_id}", response_model=None)
def get_product_variant(product_id: int, version_id: int, variant_id: int, db: Session = Depends(get_db)):
  """Get a single variant."""
  version = get_product_version_by_id(db, version_id)
  variant = get_product_variant_by_id(db, variant_id)
  if not version or not variant or version.product_id != product_id or variant.product_version_id != version_id:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("get_product_variant", "Product variant not found"),
      data=None,
    )

  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("get_product_variant", "Product variant found"),
    data=ProductVariantResponse.model_validate(
      variant).model_dump(mode="json"),
  )


@router.patch("/{product_id}/versions/{version_id}/variants/{variant_id}", response_model=None)
def update_product_variant_endpoint(product_id: int, version_id: int, variant_id: int, variant_data: ProductVariantUpdate, db: Session = Depends(get_db), current_user: User | None = Depends(AccessManager.get_current_user)):
  """Update a product variant."""
  product = get_product_by_id(db, product_id)
  version = get_product_version_by_id(db, version_id)
  variant = get_product_variant_by_id(db, variant_id)
  if not product or not version or not variant or version.product_id != product_id or variant.product_version_id != version_id:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("update_product_variant", "Product variant not found"),
      data=None,
    )

  if not _is_product_manager(current_user, product):
    return response.error(
      status=RestStatus.forbidden_403,
      meta=_meta("update_product_variant",
                 "Only seller, admin or moderator can update variants"),
      data=None,
    )

  updated = update_product_variant(
    db, variant, variant_data.model_dump(exclude_none=True))
  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("update_product_variant", "Product variant updated"),
    data=ProductVariantResponse.model_validate(
      updated).model_dump(mode="json"),
  )


@router.delete("/{product_id}/versions/{version_id}/variants/{variant_id}", response_model=None)
def delete_product_variant_endpoint(product_id: int, version_id: int, variant_id: int, db: Session = Depends(get_db), current_user: User | None = Depends(AccessManager.get_current_user)):
  """Delete a product variant."""
  product = get_product_by_id(db, product_id)
  version = get_product_version_by_id(db, version_id)
  variant = get_product_variant_by_id(db, variant_id)
  if not product or not version or not variant or version.product_id != product_id or variant.product_version_id != version_id:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("delete_product_variant", "Product variant not found"),
      data=None,
    )

  if not _is_product_manager(current_user, product):
    return response.error(
      status=RestStatus.forbidden_403,
      meta=_meta("delete_product_variant",
                 "Only seller, admin or moderator can delete variants"),
      data=None,
    )

  deleted = delete_product_variant(db, variant, soft=True)
  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("delete_product_variant", "Product variant deleted"),
    data=ProductVariantResponse.model_validate(
      deleted).model_dump(mode="json"),
  )


@router.get("/{product_id}/versions/{version_id}/pictures", response_model=None)
def list_product_pictures(product_id: int, version_id: int, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)):
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
    data=[ProductPictureResponse.model_validate(
      p).model_dump(mode="json") for p in pictures],
  )


@router.post("/{product_id}/versions/{version_id}/pictures", response_model=None)
def upload_product_picture(product_id: int, version_id: int, file: UploadFile = File(...), sort_order: int = Query(0, ge=0), db: Session = Depends(get_db), current_user: User | None = Depends(AccessManager.get_current_user)):
  """Upload a picture for a version."""
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

  upload_dir = _product_static_folder(product_id, version_id)
  os.makedirs(upload_dir, exist_ok=True)
  filename = f"{uuid4().hex}_{Path(file.filename).name}"
  destination = upload_dir / filename
  with destination.open("wb") as buffer:
    shutil.copyfileobj(file.file, buffer)

  file_url = f"/static/product_pictures/{product_id}/{version_id}/{filename}"
  picture = create_product_picture(db, version_id, file_url, sort_order)
  return response.success(
    status=RestStatus.created_201,
    meta=_meta("upload_product_picture", "Product picture uploaded"),
    data=ProductPictureResponse.model_validate(
      picture).model_dump(mode="json"),
  )


@router.patch("/{product_id}/versions/{version_id}/pictures/{picture_id}", response_model=None)
def update_product_picture_endpoint(product_id: int, version_id: int, picture_id: int, picture_data: ProductPictureUpdate, db: Session = Depends(get_db), current_user: User | None = Depends(AccessManager.get_current_user)):
  """Update picture sort order."""
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
    data=ProductPictureResponse.model_validate(
      updated).model_dump(mode="json"),
  )


@router.delete("/{product_id}/versions/{version_id}/pictures/{picture_id}", response_model=None)
def delete_product_picture_endpoint(product_id: int, version_id: int, picture_id: int, db: Session = Depends(get_db), current_user: User | None = Depends(AccessManager.get_current_user)):
  """Delete a picture."""
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
    data=ProductPictureResponse.model_validate(
      deleted).model_dump(mode="json"),
  )
