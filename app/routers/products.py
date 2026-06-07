import os
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from sqlalchemy.orm import Session

from app.api.responses.response_rest import ResponseRest
from app.api.responses.rest_meta import RestMeta
from app.api.responses.rest_status import RestStatus
from app.crud import (
  create_product,
  create_product_picture,
  create_product_revision,
  create_product_variant,
  create_product_version,
  create_review,
  delete_product as crud_delete_product,
  delete_product_picture,
  delete_product_variant,
  delete_product_version,
  delete_review,
  get_product_by_id,
  get_product_by_slug,
  get_product_picture_by_id,
  get_product_pictures,
  get_product_reviews,
  get_product_variant_by_id,
  get_product_variants,
  get_product_version_by_id,
  get_product_versions,
  get_products,
  get_products_count,
  get_related_products,
  get_variant_price,
  record_product_view,
  set_product_status,
  update_product_picture,
  update_product_variant,
  update_product_version,
  update_review,
)
from app.database import get_db
from app.models import Product, ProductFeature, ProductPicture, ProductVariant, ProductVersion, Review, User
from app.schemas.product import (
  PRODUCT_STATUSES,
  ProductCreate,
  ProductPictureResponse,
  ProductPictureUpdate,
  ProductResponse,
  ProductStatusUpdate,
  ProductVariantCreate,
  ProductVariantResponse,
  ProductVariantUpdate,
  ProductVersionCreate,
  ProductVersionResponse,
  ProductVersionUpdate,
  ReviewCreate,
  ReviewResponse,
  ReviewUpdate,
)
from app.services.access_manager import AccessManager

router = APIRouter(prefix="/products", tags=["products"])
response = ResponseRest()


def _meta(action: str, message: str | None = None) -> RestMeta:
  return RestMeta(action=action, message=message)


def _is_product_manager(current_user: User, product: Product) -> bool:
  if current_user.is_admin() or current_user.is_moderator():
    return True
  return current_user.is_seller()


def _product_static_folder(product_id: int, version_id: int) -> Path:
  root = Path(__file__).resolve().parent.parent
  return root / "static" / "product_pictures" / str(product_id) / str(version_id)


def _active_version(product: Product) -> ProductVersion | None:
  if product.current_version:
    return product.current_version
  versions = [version for version in product.versions if version.deleted_at is None]
  if not versions:
    return None
  return max(versions, key=lambda version: version.created_at)


def _serialize_feature(feature: ProductFeature) -> dict:
  return {
    "id": feature.id,
    "feature_id": feature.feature_id,
    "feature": {
      "id": feature.feature.id,
      "title": feature.feature.title,
      "is_primary": getattr(feature.feature, "is_primary", False),
    } if getattr(feature, "feature", None) else None,
    "value": feature.value,
    "value_type": feature.value_type,
  }


def _serialize_picture(picture: ProductPicture) -> dict:
  return ProductPictureResponse.model_validate(picture).model_dump(mode="json")


def _serialize_variant(db: Session, product: Product, variant: ProductVariant, coupon_code: str | None = None) -> dict:
  price = get_variant_price(db, product, variant, coupon_code=coupon_code)
  return {
    "id": variant.id,
    "sku_code": variant.sku_code,
    "price": variant.price,
    "stock": variant.stock,
    "created_at": variant.created_at,
    "features": [
      _serialize_feature(feature)
      for feature in variant.product_features
      if feature.deleted_at is None
    ],
    "product": {
      "id": product.id,
      "seller_id": product.seller_id,
      "status": product.status,
    },
    "base_price": price["base_price"],
    "discount_amount": price["discount_amount"],
    "final_price": price["final_price"],
  }


def _serialize_version(db: Session, product: Product, version: ProductVersion, coupon_code: str | None = None) -> dict:
  return {
    "id": version.id,
    "product_id": version.product_id,
    "category_id": version.category_id,
    "category": {
      "id": version.category.id,
      "title": version.category.title,
      "description": version.category.description,
    } if getattr(version, "category", None) else None,
    "title": version.title,
    "description": version.description,
    "delivery_info": version.delivery_info,
    "slug": version.slug,
    "version_number": version.version_number,
    "created_at": version.created_at,
    "variants": [
      _serialize_variant(db, product, variant, coupon_code=coupon_code)
      for variant in version.variants
      if variant.deleted_at is None
    ],
    "pictures": [
      _serialize_picture(picture)
      for picture in sorted(version.pictures, key=lambda item: item.sort_order)
      if picture.deleted_at is None
    ],
  }


def _serialize_product_brief(db: Session, product: Product) -> dict:
  version = _active_version(product)
  return {
    "id": product.id,
    "seller_id": product.seller_id,
    "status": product.status,
    "pageviews": product.pageviews,
    "average_rating": product.average_rating,
    "reviews_count": product.reviews_count,
    "sales_count": product.sales_count,
    "current_version": _serialize_version(db, product, version) if version else None,
  }


def _serialize_product(
  db: Session,
  product: Product,
  include_reviews: bool = False,
  include_related: bool = False,
  coupon_code: str | None = None,
) -> dict:
  version = _active_version(product)
  data = {
    "id": product.id,
    "seller_id": product.seller_id,
    "current_version_id": product.current_version_id,
    "status": product.status,
    "pageviews": product.pageviews,
    "unique_pageviews": product.unique_pageviews,
    "favorite_count": product.favorite_count,
    "order_count": product.order_count,
    "sales_count": product.sales_count,
    "average_rating": product.average_rating,
    "reviews_count": product.reviews_count,
    "created_at": product.created_at,
    "current_version": _serialize_version(db, product, version, coupon_code=coupon_code) if version else None,
    "seller": None,
    "reviews": [],
    "similar_products": [],
    "seller_products": [],
    "recommended_products": [],
  }

  if product.seller:
    data["seller"] = {
      "id": product.seller.id,
      "store_name": product.seller.store_name,
      "rating": product.seller.rating,
      "picture_url": product.seller.picture_url,
    }

  if include_reviews:
    data["reviews"] = [
      ReviewResponse.model_validate(review).model_dump(mode="json")
      for review in get_product_reviews(db, product.id, limit=20)
    ]

  if include_related:
    similar, seller_products, recommended = get_related_products(db, product)
    data["similar_products"] = [_serialize_product_brief(db, item) for item in similar]
    data["seller_products"] = [_serialize_product_brief(db, item) for item in seller_products]
    data["recommended_products"] = [_serialize_product_brief(db, item) for item in recommended]

  return ProductResponse.model_validate(data).model_dump(mode="json")


@router.post("", response_model=None)
def create(product_data: ProductCreate, db: Session = Depends(get_db), current_user: User = Depends(AccessManager.require_role("SELLER"))):
  """Create a product with its first version, variants, features and pictures."""
  try:
    new_product = create_product(
      db,
      seller_id=product_data.seller_id,
      status=product_data.status,
      category_id=product_data.category_id,
      title=product_data.title,
      description=product_data.description,
      delivery_info=product_data.delivery_info,
      slug=product_data.slug,
      variants=product_data.variants,
      pictures=product_data.pictures,
    )
    return response.success(
      status=RestStatus.created_201,
      meta=_meta("create_product", "Product created"),
      data=_serialize_product(db, new_product),
    )
  except ValueError as e:
    return response.error(
      status=RestStatus.bad_request_400,
      meta=_meta("create_product", str(e)),
      data=None,
    )


@router.get("", response_model=None)
def list_products(
  q: str | None = Query(None),
  category_id: int | None = Query(None),
  min_price: float | None = Query(None, ge=0),
  max_price: float | None = Query(None, ge=0),
  min_rating: float | None = Query(None, ge=0, le=5),
  has_discount: bool | None = Query(None),
  seller_id: int | None = Query(None),
  sort_by: str = Query("created_at", pattern="^(popularity|price|rating|created_at|sales)$"),
  sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
  per_page: int = Query(10, ge=1, le=100),
  page: int = Query(1, ge=1),
  coupon_code: str | None = Query(None),
  db: Session = Depends(get_db),
):
  """List public approved products with search, filters and sorting."""
  total = get_products_count(
    db,
    q=q,
    category_id=category_id,
    min_price=min_price,
    max_price=max_price,
    min_rating=min_rating,
    has_discount=has_discount,
    seller_id=seller_id,
  )
  products = get_products(
    db,
    skip=(page - 1) * per_page,
    limit=per_page,
    q=q,
    category_id=category_id,
    min_price=min_price,
    max_price=max_price,
    min_rating=min_rating,
    has_discount=has_discount,
    seller_id=seller_id,
    sort_by=sort_by,
    sort_dir=sort_dir,
  )
  pagination = response.build_pagination(page, per_page, total)

  return response.success_pagination(
    status=RestStatus.ok_200,
    meta=RestMeta(
      action="list_products",
      message=f"Products found: {len(products)}",
      pagination=pagination,
    ),
    data={"items": [_serialize_product(db, product, coupon_code=coupon_code) for product in products]},
  )


@router.patch("/admin/{product_id}/status", response_model=None)
def update_product_status(
  product_id: int,
  status_data: ProductStatusUpdate,
  db: Session = Depends(get_db),
  current_user: User = Depends(AccessManager.get_current_user),
):
  if not (current_user.is_admin() or current_user.is_moderator()):
    return response.forbidden("Only admin or moderator can update product status")

  product = get_product_by_id(db, product_id)
  if not product:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("update_product_status", "Product not found"),
      data=None,
    )

  try:
    updated = set_product_status(db, product, status_data.status)
  except ValueError as e:
    return response.error(
      status=RestStatus.bad_request_400,
      meta=_meta("update_product_status", str(e)),
      data=None,
    )

  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("update_product_status", "Product status updated"),
    data=_serialize_product(db, updated),
  )


@router.get("/{product_id_or_slug}", response_model=None)
def get_product(
  product_id_or_slug: str,
  request: Request,
  coupon_code: str | None = Query(None),
  db: Session = Depends(get_db),
):
  if product_id_or_slug.isdigit():
    product = get_product_by_id(db, int(product_id_or_slug), public_only=True)
    action = "get_product_by_id"
  else:
    product = get_product_by_slug(db, product_id_or_slug, public_only=True)
    action = "get_product_by_slug"

  if not product:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta(action, "Product not found"),
      data=None,
    )

  viewer_key = request.client.host if request.client else None
  product = record_product_view(db, product, viewer_key=viewer_key)

  return response.success(
    status=RestStatus.ok_200,
    meta=_meta(action, "Product found"),
    data=_serialize_product(
      db,
      product,
      include_reviews=True,
      include_related=True,
      coupon_code=coupon_code,
    ),
  )


@router.patch("/{product_id}", response_model=None)
def update_product(product_id: int, product_data: ProductVersionUpdate, db: Session = Depends(get_db), current_user: User = Depends(AccessManager.get_current_user)):
  """Create a new product version and send the product to moderation."""
  product = get_product_by_id(db, product_id)
  if not product:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("update_product", "Product not found"),
      data=None,
    )

  if not _is_product_manager(current_user, product):
    return response.error(
      status=RestStatus.forbidden_403,
      meta=_meta("update_product", "Only seller, admin or moderator can update product"),
      data=None,
    )

  try:
    updated = create_product_revision(db, product, product_data.model_dump(exclude_none=True))
  except ValueError as e:
    return response.error(
      status=RestStatus.bad_request_400,
      meta=_meta("update_product", str(e)),
      data=None,
    )

  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("update_product", "Product revision created and sent to moderation"),
    data=_serialize_product(db, updated),
  )


@router.delete("/{product_id}", response_model=None)
def delete_product(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(AccessManager.get_current_user)):
  product = get_product_by_id(db, product_id)
  if not product:
    return response.error(
      status=RestStatus.not_found_404,
      meta=_meta("delete_product", "Product not found"),
      data=None,
    )

  if not _is_product_manager(current_user, product):
    return response.error(
      status=RestStatus.forbidden_403,
      meta=_meta("delete_product", "Only seller, admin or moderator can delete product"),
      data=None,
    )

  deleted = crud_delete_product(db, product, soft=True)
  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("delete_product", "Product deleted"),
    data=_serialize_product(db, deleted),
  )


@router.get("/{product_id}/reviews", response_model=None)
def list_reviews(product_id: int, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)):
  product = get_product_by_id(db, product_id, public_only=True)
  if not product:
    return response.error(status=RestStatus.not_found_404, meta=_meta("list_reviews", "Product not found"), data=None)

  reviews = get_product_reviews(db, product_id, skip=skip, limit=limit)
  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("list_reviews", f"Reviews found: {len(reviews)}"),
    data={"items": [ReviewResponse.model_validate(review).model_dump(mode="json") for review in reviews]},
  )


@router.post("/{product_id}/reviews", response_model=None)
def create_review_endpoint(product_id: int, review_data: ReviewCreate, db: Session = Depends(get_db), current_user: User = Depends(AccessManager.get_current_user)):
  product = get_product_by_id(db, product_id, public_only=True)
  if not product:
    return response.error(status=RestStatus.not_found_404, meta=_meta("create_review", "Product not found"), data=None)

  try:
    review = create_review(
      db,
      user_id=current_user.id,
      product_id=product_id,
      product_variant_id=review_data.product_variant_id,
      rating=review_data.rating,
      comment=review_data.comment,
    )
  except ValueError as e:
    return response.error(status=RestStatus.bad_request_400, meta=_meta("create_review", str(e)), data=None)

  return response.success(
    status=RestStatus.created_201,
    meta=_meta("create_review", "Review created"),
    data=ReviewResponse.model_validate(review).model_dump(mode="json"),
  )


@router.patch("/{product_id}/reviews/{review_id}", response_model=None)
def update_review_endpoint(product_id: int, review_id: int, review_data: ReviewUpdate, db: Session = Depends(get_db), current_user: User = Depends(AccessManager.get_current_user)):
  review = db.query(Review).filter(Review.id == review_id, Review.deleted_at == None).first()
  if not review or review.user_id != current_user.id:
    return response.error(status=RestStatus.not_found_404, meta=_meta("update_review", "Review not found"), data=None)

  try:
    updated = update_review(db, review, product_id, rating=review_data.rating, comment=review_data.comment)
  except ValueError as e:
    return response.error(status=RestStatus.bad_request_400, meta=_meta("update_review", str(e)), data=None)

  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("update_review", "Review updated"),
    data=ReviewResponse.model_validate(updated).model_dump(mode="json"),
  )


@router.delete("/{product_id}/reviews/{review_id}", response_model=None)
def delete_review_endpoint(product_id: int, review_id: int, db: Session = Depends(get_db), current_user: User = Depends(AccessManager.get_current_user)):
  review = db.query(Review).filter(Review.id == review_id, Review.deleted_at == None).first()
  if not review or review.user_id != current_user.id:
    return response.error(status=RestStatus.not_found_404, meta=_meta("delete_review", "Review not found"), data=None)

  deleted = delete_review(db, review, product_id)
  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("delete_review", "Review deleted"),
    data=ReviewResponse.model_validate(deleted).model_dump(mode="json"),
  )


@router.get("/{product_id}/versions", response_model=None)
def list_product_versions(product_id: int, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)):
  versions = get_product_versions(db, product_id, skip=skip, limit=limit)
  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("list_product_versions", f"Versions found: {len(versions)}"),
    data={"items": [ProductVersionResponse.model_validate(version).model_dump(mode="json") for version in versions]},
  )


@router.post("/{product_id}/versions", response_model=None)
def create_product_version_endpoint(product_id: int, version_data: ProductVersionCreate, db: Session = Depends(get_db), current_user: User = Depends(AccessManager.get_current_user)):
  product = get_product_by_id(db, product_id)
  if not product:
    return response.error(status=RestStatus.not_found_404, meta=_meta("create_product_version", "Product not found"), data=None)
  if not _is_product_manager(current_user, product):
    return response.forbidden("Only seller, admin or moderator can create product versions")

  try:
    version = create_product_version(
      db,
      product_id=product_id,
      category_id=version_data.category_id,
      title=version_data.title,
      description=version_data.description,
      delivery_info=version_data.delivery_info,
      slug=version_data.slug,
    )
    for variant in version_data.variants:
      create_product_variant(db, version.id, variant.sku_code, variant.price, variant.stock, features=variant.features)
    for picture in version_data.pictures:
      create_product_picture(
        db,
        version.id,
        file_url=picture.file_url,
        original_url=picture.original_url,
        preview_url=picture.preview_url,
        thumbnail_url=picture.thumbnail_url,
        sort_order=picture.sort_order,
      )
  except ValueError as e:
    return response.error(status=RestStatus.bad_request_400, meta=_meta("create_product_version", str(e)), data=None)

  return response.success(
    status=RestStatus.created_201,
    meta=_meta("create_product_version", "Product version created"),
    data=_serialize_version(db, product, version),
  )


@router.get("/{product_id}/versions/{version_id}", response_model=None)
def get_product_version(product_id: int, version_id: int, db: Session = Depends(get_db)):
  version = get_product_version_by_id(db, version_id)
  product = get_product_by_id(db, product_id)
  if not product or not version or version.product_id != product_id:
    return response.error(status=RestStatus.not_found_404, meta=_meta("get_product_version", "Product version not found"), data=None)

  return response.success(status=RestStatus.ok_200, meta=_meta("get_product_version", "Product version found"), data=_serialize_version(db, product, version))


@router.patch("/{product_id}/versions/{version_id}", response_model=None)
def update_product_version_endpoint(product_id: int, version_id: int, version_data: ProductVersionUpdate, db: Session = Depends(get_db), current_user: User = Depends(AccessManager.get_current_user)):
  product = get_product_by_id(db, product_id)
  version = get_product_version_by_id(db, version_id)
  if not product or not version or version.product_id != product_id:
    return response.error(status=RestStatus.not_found_404, meta=_meta("update_product_version", "Product version not found"), data=None)
  if not _is_product_manager(current_user, product):
    return response.forbidden("Only seller, admin or moderator can update product versions")

  try:
    updated = update_product_version(db, version, version_data.model_dump(exclude_none=True))
  except ValueError as e:
    return response.error(status=RestStatus.bad_request_400, meta=_meta("update_product_version", str(e)), data=None)
  return response.success(status=RestStatus.ok_200, meta=_meta("update_product_version", "New product version created"), data=_serialize_product(db, updated))


@router.delete("/{product_id}/versions/{version_id}", response_model=None)
def delete_product_version_endpoint(product_id: int, version_id: int, db: Session = Depends(get_db), current_user: User = Depends(AccessManager.get_current_user)):
  product = get_product_by_id(db, product_id)
  version = get_product_version_by_id(db, version_id)
  if not product or not version or version.product_id != product_id:
    return response.error(status=RestStatus.not_found_404, meta=_meta("delete_product_version", "Product version not found"), data=None)
  if not _is_product_manager(current_user, product):
    return response.forbidden("Only seller, admin or moderator can delete product versions")

  deleted = delete_product_version(db, version, soft=True)
  return response.success(status=RestStatus.ok_200, meta=_meta("delete_product_version", "Product version deleted"), data=ProductVersionResponse.model_validate(deleted).model_dump(mode="json"))


@router.get("/{product_id}/versions/{version_id}/variants", response_model=None)
def list_product_variants(product_id: int, version_id: int, db: Session = Depends(get_db)):
  product = get_product_by_id(db, product_id)
  version = get_product_version_by_id(db, version_id)
  if not product or not version or version.product_id != product_id:
    return response.error(status=RestStatus.not_found_404, meta=_meta("list_product_variants", "Product version not found"), data=None)

  variants = get_product_variants(db, version_id)
  return response.success(
    status=RestStatus.ok_200,
    meta=_meta("list_product_variants", f"Variants found: {len(variants)}"),
    data=[_serialize_variant(db, product, variant) for variant in variants],
  )


@router.post("/{product_id}/versions/{version_id}/variants", response_model=None)
def create_product_variant_endpoint(product_id: int, version_id: int, variant_data: ProductVariantCreate, db: Session = Depends(get_db), current_user: User = Depends(AccessManager.get_current_user)):
  product = get_product_by_id(db, product_id)
  version = get_product_version_by_id(db, version_id)
  if not product or not version or version.product_id != product_id:
    return response.error(status=RestStatus.not_found_404, meta=_meta("create_product_variant", "Product version not found"), data=None)
  if not _is_product_manager(current_user, product):
    return response.forbidden("Only seller, admin or moderator can create variants")

  try:
    variant = create_product_variant(db, version_id, variant_data.sku_code, variant_data.price, variant_data.stock, features=variant_data.features)
  except ValueError as e:
    return response.error(status=RestStatus.bad_request_400, meta=_meta("create_product_variant", str(e)), data=None)

  return response.success(status=RestStatus.created_201, meta=_meta("create_product_variant", "Product variant created"), data=_serialize_variant(db, product, variant))


@router.get("/{product_id}/versions/{version_id}/variants/{variant_id}", response_model=None)
def get_product_variant(product_id: int, version_id: int, variant_id: int, db: Session = Depends(get_db)):
  product = get_product_by_id(db, product_id)
  version = get_product_version_by_id(db, version_id)
  variant = get_product_variant_by_id(db, variant_id)
  if not product or not version or not variant or version.product_id != product_id or variant.product_version_id != version_id:
    return response.error(status=RestStatus.not_found_404, meta=_meta("get_product_variant", "Product variant not found"), data=None)

  return response.success(status=RestStatus.ok_200, meta=_meta("get_product_variant", "Product variant found"), data=_serialize_variant(db, product, variant))


@router.patch("/{product_id}/versions/{version_id}/variants/{variant_id}", response_model=None)
def update_product_variant_endpoint(product_id: int, version_id: int, variant_id: int, variant_data: ProductVariantUpdate, db: Session = Depends(get_db), current_user: User = Depends(AccessManager.get_current_user)):
  product = get_product_by_id(db, product_id)
  version = get_product_version_by_id(db, version_id)
  variant = get_product_variant_by_id(db, variant_id)
  if not product or not version or not variant or version.product_id != product_id or variant.product_version_id != version_id:
    return response.error(status=RestStatus.not_found_404, meta=_meta("update_product_variant", "Product variant not found"), data=None)
  if not _is_product_manager(current_user, product):
    return response.forbidden("Only seller, admin or moderator can update variants")

  try:
    updated = update_product_variant(db, variant, variant_data.model_dump(exclude_none=True))
  except ValueError as e:
    return response.error(status=RestStatus.bad_request_400, meta=_meta("update_product_variant", str(e)), data=None)
  return response.success(status=RestStatus.ok_200, meta=_meta("update_product_variant", "Product variant updated"), data=_serialize_variant(db, product, updated))


@router.delete("/{product_id}/versions/{version_id}/variants/{variant_id}", response_model=None)
def delete_product_variant_endpoint(product_id: int, version_id: int, variant_id: int, db: Session = Depends(get_db), current_user: User = Depends(AccessManager.get_current_user)):
  product = get_product_by_id(db, product_id)
  version = get_product_version_by_id(db, version_id)
  variant = get_product_variant_by_id(db, variant_id)
  if not product or not version or not variant or version.product_id != product_id or variant.product_version_id != version_id:
    return response.error(status=RestStatus.not_found_404, meta=_meta("delete_product_variant", "Product variant not found"), data=None)
  if not _is_product_manager(current_user, product):
    return response.forbidden("Only seller, admin or moderator can delete variants")

  deleted = delete_product_variant(db, variant, soft=True)
  return response.success(status=RestStatus.ok_200, meta=_meta("delete_product_variant", "Product variant deleted"), data=_serialize_variant(db, product, deleted))


@router.get("/{product_id}/versions/{version_id}/pictures", response_model=None)
def list_product_pictures(product_id: int, version_id: int, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)):
  version = get_product_version_by_id(db, version_id)
  if not version or version.product_id != product_id:
    return response.error(status=RestStatus.not_found_404, meta=_meta("list_product_pictures", "Product version not found"), data=None)

  pictures = get_product_pictures(db, version_id, skip=skip, limit=limit)
  return response.success(status=RestStatus.ok_200, meta=_meta("list_product_pictures", f"Pictures found: {len(pictures)}"), data=[_serialize_picture(picture) for picture in pictures])


@router.post("/{product_id}/versions/{version_id}/pictures", response_model=None)
def upload_product_picture(product_id: int, version_id: int, file: UploadFile = File(...), sort_order: int = Query(0, ge=0), db: Session = Depends(get_db), current_user: User = Depends(AccessManager.get_current_user)):
  product = get_product_by_id(db, product_id)
  version = get_product_version_by_id(db, version_id)
  if not product or not version or version.product_id != product_id:
    return response.error(status=RestStatus.not_found_404, meta=_meta("upload_product_picture", "Product version not found"), data=None)
  if not _is_product_manager(current_user, product):
    return response.forbidden("Only seller, admin or moderator can upload pictures")

  upload_dir = _product_static_folder(product_id, version_id)
  os.makedirs(upload_dir, exist_ok=True)
  filename = f"{uuid4().hex}_{Path(file.filename).name}"
  destination = upload_dir / filename
  with destination.open("wb") as buffer:
    shutil.copyfileobj(file.file, buffer)

  file_url = f"/static/product_pictures/{product_id}/{version_id}/{filename}"
  picture = create_product_picture(db, version_id, file_url=file_url, original_url=file_url, sort_order=sort_order)
  return response.success(status=RestStatus.created_201, meta=_meta("upload_product_picture", "Product picture uploaded"), data=_serialize_picture(picture))


@router.patch("/{product_id}/versions/{version_id}/pictures/{picture_id}", response_model=None)
def update_product_picture_endpoint(product_id: int, version_id: int, picture_id: int, picture_data: ProductPictureUpdate, db: Session = Depends(get_db), current_user: User = Depends(AccessManager.get_current_user)):
  product = get_product_by_id(db, product_id)
  version = get_product_version_by_id(db, version_id)
  picture = get_product_picture_by_id(db, picture_id)
  if not product or not version or not picture or version.product_id != product_id or picture.product_version_id != version_id:
    return response.error(status=RestStatus.not_found_404, meta=_meta("update_product_picture", "Product picture not found"), data=None)
  if not _is_product_manager(current_user, product):
    return response.forbidden("Only seller, admin or moderator can update pictures")

  updated = update_product_picture(db, picture, picture_data.model_dump(exclude_none=True))
  return response.success(status=RestStatus.ok_200, meta=_meta("update_product_picture", "Product picture updated"), data=_serialize_picture(updated))


@router.delete("/{product_id}/versions/{version_id}/pictures/{picture_id}", response_model=None)
def delete_product_picture_endpoint(product_id: int, version_id: int, picture_id: int, db: Session = Depends(get_db), current_user: User = Depends(AccessManager.get_current_user)):
  product = get_product_by_id(db, product_id)
  version = get_product_version_by_id(db, version_id)
  picture = get_product_picture_by_id(db, picture_id)
  if not product or not version or not picture or version.product_id != product_id or picture.product_version_id != version_id:
    return response.error(status=RestStatus.not_found_404, meta=_meta("delete_product_picture", "Product picture not found"), data=None)
  if not _is_product_manager(current_user, product):
    return response.forbidden("Only seller, admin or moderator can delete pictures")

  deleted = delete_product_picture(db, picture, soft=True)
  return response.success(status=RestStatus.ok_200, meta=_meta("delete_product_picture", "Product picture deleted"), data=_serialize_picture(deleted))
