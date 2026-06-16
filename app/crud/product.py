from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import and_, asc, desc, func, or_
from sqlalchemy.orm import Session

from app.models import (
  Discount,
  Order,
  OrderItem,
  Product,
  ProductFeature,
  ProductPicture,
  ProductVariant,
  ProductVersion,
  ProductView,
  Review,
  ReviewPicture,
)
from app.models.review_picture import ReviewPicture
from app.schemas.product import PRODUCT_STATUSES


REVIEW_EDIT_WINDOW = timedelta(days=7)
COMPLETED_ORDER_STATUSES = {"completed", "delivered", "paid",
                            "finished", "COMPLETED", "DELIVERED", "PAID", "FINISHED"}


def _now():
  return datetime.now()


def _validate_product_status(status: str):
  if status not in PRODUCT_STATUSES:
    raise ValueError(f"status must be one of: {', '.join(PRODUCT_STATUSES)}")


def _validate_slug(db: Session, slug: str, version_id: int | None = None):
  query = db.query(ProductVersion).filter(
    ProductVersion.slug == slug,
    ProductVersion.deleted_at == None,
  )
  if version_id is not None:
    query = query.filter(ProductVersion.id != version_id)
  if query.first():
    raise ValueError("Version slug already exists")


def _next_version_number(db: Session, product_id: int) -> int:
  current = db.query(func.max(ProductVersion.version_number)).filter(
    ProductVersion.product_id == product_id
  ).scalar()
  return (current or 0) + 1


def _create_feature_rows(db: Session, variant: ProductVariant, features: list):
  for feature_data in features or []:
    if isinstance(feature_data, dict):
      payload = feature_data
    else:
      payload = feature_data.model_dump()
    db.add(
      ProductFeature(
        product_variant_id=variant.id,
        feature_id=payload["feature_id"],
        value=payload["value"],
        value_type=payload.get("value_type") or "string",
      )
    )


def _create_variant_rows(db: Session, version: ProductVersion, variants: list):
  for variant_data in variants or []:
    payload = variant_data if isinstance(
      variant_data, dict) else variant_data.model_dump()
    sku_code = payload["sku_code"]
    if db.query(ProductVariant).filter(
      ProductVariant.sku_code == sku_code,
      ProductVariant.deleted_at == None,
    ).first():
      raise ValueError("Variant SKU already exists")

    variant = ProductVariant(
      product_version_id=version.id,
      sku_code=sku_code,
      price=payload["price"],
      stock=payload.get("stock", 0),
    )
    db.add(variant)
    db.flush()
    _create_feature_rows(db, variant, payload.get("features", []))


def _create_picture_rows(db: Session, version: ProductVersion, pictures: list):
  for picture_data in pictures or []:
    payload = picture_data if isinstance(
      picture_data, dict) else picture_data.model_dump()
    original_url = payload.get("original_url") or payload.get("file_url")
    db.add(
      ProductPicture(
        product_version_id=version.id,
        file_url=payload.get("file_url") or original_url,
        original_url=original_url,
        preview_url=payload.get("preview_url"),
        thumbnail_url=payload.get("thumbnail_url"),
        sort_order=payload.get("sort_order", 0),
      )
    )


def _create_review_pictures(db: Session, review_id: int, pictures: list):
  for picture_data in pictures:
    payload = picture_data if isinstance(
      picture_data, dict) else picture_data.model_dump()
    original_url = payload.get("original_url") or payload.get("file_url")
    db.add(ReviewPicture(
      review_id=review_id,
      file_url=payload.get("file_url") or original_url,
      original_url=original_url,
      preview_url=payload.get("preview_url"),
      thumbnail_url=payload.get("thumbnail_url"),
      sort_order=payload.get("sort_order", 0),
    ))


def _create_version(
  db: Session,
  product_id: int,
  category_id: int | None,
  title: str,
  description: str | None,
  delivery_info: str | None,
  slug: str,
  variants: list | None = None,
  pictures: list | None = None,
) -> ProductVersion:
  _validate_slug(db, slug)
  version = ProductVersion(
    product_id=product_id,
    category_id=category_id,
    title=title,
    description=description,
    delivery_info=delivery_info,
    slug=slug,
    version_number=_next_version_number(db, product_id),
  )
  db.add(version)
  db.flush()
  _create_variant_rows(db, version, variants or [])
  _create_picture_rows(db, version, pictures or [])
  return version


def create_product(
  db: Session,
  seller_id: int,
  status: str = "PENDING",
  category_id: int | None = None,
  title: str | None = None,
  description: str | None = None,
  delivery_info: str | None = None,
  slug: str | None = None,
  variants: list | None = None,
  pictures: list | None = None,
) -> Product:
  _validate_product_status(status)

  product = Product(seller_id=seller_id, status=status)
  db.add(product)
  db.flush()

  if title and slug:
    version = _create_version(
      db,
      product_id=product.id,
      category_id=category_id,
      title=title,
      description=description,
      delivery_info=delivery_info,
      slug=slug,
      variants=variants or [],
      pictures=pictures or [],
    )
    if status == "APPROVED":
      product.current_version_id = version.id

  db.commit()
  db.refresh(product)
  return product


def get_product_by_id(db: Session, product_id: int, public_only: bool = False):
  query = db.query(Product).filter(
    Product.id == product_id, Product.deleted_at == None)
  if public_only:
    query = query.filter(Product.status == "APPROVED",
                         Product.current_version_id != None)
  return query.first()


def get_product_by_slug(db: Session, slug: str, public_only: bool = False):
  query = (
    db.query(Product)
    .join(ProductVersion, ProductVersion.product_id == Product.id)
    .filter(ProductVersion.slug == slug)
    .filter(ProductVersion.deleted_at == None)
    .filter(Product.deleted_at == None)
  )
  if public_only:
    query = query.filter(Product.status == "APPROVED",
                         Product.current_version_id == ProductVersion.id)
  return query.first()


def _base_product_query(
  db: Session,
  q: str | None = None,
  category_id: int | None = None,
  min_price: Decimal | None = None,
  max_price: Decimal | None = None,
  min_rating: float | None = None,
  has_discount: bool | None = None,
  seller_id: int | None = None,
):
  query = (
    db.query(Product)
    .join(ProductVersion, Product.current_version_id == ProductVersion.id)
    .join(ProductVariant, ProductVersion.id == ProductVariant.product_version_id)
    .filter(
      Product.deleted_at == None,
      Product.status == "APPROVED",
      ProductVersion.deleted_at == None,
      ProductVariant.deleted_at == None,
    )
  )

  if q:
    like = f"%{q}%"
    query = query.filter(or_(
      ProductVersion.title.ilike(like),
      ProductVersion.description.ilike(like),
      ProductVariant.sku_code.ilike(like),
    ))
  if category_id is not None:
    query = query.filter(ProductVersion.category_id == category_id)
  if min_price is not None:
    query = query.filter(ProductVariant.price >= min_price)
  if max_price is not None:
    query = query.filter(ProductVariant.price <= max_price)
  if min_rating is not None:
    query = query.filter(Product.average_rating >= min_rating)
  if seller_id is not None:
    query = query.filter(Product.seller_id == seller_id)
  if has_discount:
    now = _now()
    query = query.filter(or_(
      db.query(Discount.id).filter(
        Discount.is_active == True,
        Discount.start_date <= now,
        Discount.end_date >= now,
        Discount.target_type == "PRODUCT",
        Discount.target_id == Product.id,
      ).exists(),
      db.query(Discount.id).filter(
        Discount.is_active == True,
        Discount.start_date <= now,
        Discount.end_date >= now,
        Discount.target_type == "CATEGORY",
        Discount.target_id == ProductVersion.category_id,
      ).exists(),
      db.query(Discount.id).filter(
        Discount.is_active == True,
        Discount.start_date <= now,
        Discount.end_date >= now,
        Discount.target_type == "SELLER",
        Discount.target_id == Product.seller_id,
      ).exists(),
    ))

  return query


def get_products(
  db: Session,
  skip: int = 0,
  limit: int = 100,
  q: str | None = None,
  category_id: int | None = None,
  min_price: Decimal | None = None,
  max_price: Decimal | None = None,
  min_rating: float | None = None,
  has_discount: bool | None = None,
  seller_id: int | None = None,
  sort_by: str = "created_at",
  sort_dir: str = "desc",
):
  query = _base_product_query(
    db,
    q=q,
    category_id=category_id,
    min_price=min_price,
    max_price=max_price,
    min_rating=min_rating,
    has_discount=has_discount,
    seller_id=seller_id,
  )
  query = query.group_by(Product.id)

  direction = asc if sort_dir == "asc" else desc
  if sort_by == "price":
    query = query.order_by(direction(func.min(ProductVariant.price)))
  elif sort_by == "rating":
    query = query.order_by(direction(Product.average_rating))
  elif sort_by == "popularity":
    query = query.order_by(direction(Product.pageviews))
  elif sort_by == "sales":
    query = query.order_by(direction(Product.sales_count))
  else:
    query = query.order_by(direction(Product.created_at))

  return query.offset(skip).limit(limit).all()


def get_products_count(
  db: Session,
  q: str | None = None,
  category_id: int | None = None,
  min_price: Decimal | None = None,
  max_price: Decimal | None = None,
  min_rating: float | None = None,
  has_discount: bool | None = None,
  seller_id: int | None = None,
):
  query = _base_product_query(
    db,
    q=q,
    category_id=category_id,
    min_price=min_price,
    max_price=max_price,
    min_rating=min_rating,
    has_discount=has_discount,
    seller_id=seller_id,
  )
  return query.with_entities(func.count(func.distinct(Product.id))).scalar() or 0


def update_product(db: Session, product: Product, data: dict):
  if "status" in data and data["status"]:
    _validate_product_status(data["status"])
    product.status = data["status"]
    if product.status != "APPROVED":
      product.updated_at = _now()
      db.commit()
      db.refresh(product)
      return product

  for key in ("pageviews",):
    if key in data and data[key] is not None:
      setattr(product, key, data[key])

  product.updated_at = _now()
  db.commit()
  db.refresh(product)
  return product


def create_product_revision(db: Session, product: Product, data: dict):
  source = product.current_version or (
    db.query(ProductVersion)
    .filter(ProductVersion.product_id == product.id, ProductVersion.deleted_at == None)
    .order_by(ProductVersion.created_at.desc())
    .first()
  )
  if not source:
    required = ("category_id", "title", "slug")
    if any(data.get(field) is None for field in required):
      raise ValueError(
        "category_id, title and slug are required for the first product version")

  title = data.get("title") or source.title
  slug = data.get(
    "slug") or f"{source.slug}-v{_next_version_number(db, product.id)}"
  version = _create_version(
    db,
    product_id=product.id,
    category_id=data.get(
      "category_id", source.category_id if source else None),
    title=title,
    description=data.get(
      "description", source.description if source else None),
    delivery_info=data.get(
      "delivery_info", source.delivery_info if source else None),
    slug=slug,
    variants=data.get("variants") if data.get(
      "variants") is not None else _clone_variants(source),
    pictures=data.get("pictures") if data.get(
      "pictures") is not None else _clone_pictures(source),
  )
  product.status = "PENDING"
  product.updated_at = _now()
  db.commit()
  db.refresh(product)
  db.refresh(version)
  return product


def _clone_variants(version: ProductVersion | None) -> list[dict]:
  if not version:
    return []
  payload = []
  for variant in version.variants:
    if variant.deleted_at is not None:
      continue
    payload.append({
      "sku_code": f"{variant.sku_code}-v{_now().strftime('%Y%m%d%H%M%S')}",
      "price": variant.price,
      "stock": variant.stock,
      "features": [
        {
          "feature_id": feature.feature_id,
          "value": feature.value,
          "value_type": feature.value_type,
        }
        for feature in variant.product_features
        if feature.deleted_at is None
      ],
    })
  return payload


def _clone_pictures(version: ProductVersion | None) -> list[dict]:
  if not version:
    return []
  return [
    {
      "file_url": picture.file_url,
      "original_url": picture.original_url,
      "preview_url": picture.preview_url,
      "thumbnail_url": picture.thumbnail_url,
      "sort_order": picture.sort_order,
    }
    for picture in version.pictures
    if picture.deleted_at is None
  ]


def set_product_status(db: Session, product: Product, status: str):
  _validate_product_status(status)
  product.status = status
  product.updated_at = _now()
  if status == "APPROVED":
    latest_version = (
      db.query(ProductVersion)
      .filter(ProductVersion.product_id == product.id, ProductVersion.deleted_at == None)
      .order_by(ProductVersion.created_at.desc())
      .first()
    )
    if not latest_version:
      raise ValueError("Product has no version to approve")
    product.current_version_id = latest_version.id
  db.commit()
  db.refresh(product)
  return product


def delete_product(db: Session, product: Product, soft: bool = True):
  if soft:
    product.deleted_at = _now()
    product.updated_at = _now()
    db.commit()
    db.refresh(product)
    return product
  db.delete(product)
  db.commit()
  return None


def search_products(db: Session, q: str, skip: int = 0, limit: int = 100):
  return get_products(db, skip=skip, limit=limit, q=q)


def create_product_version(db: Session, product_id: int, category_id: int | None, title: str, description: str | None, slug: str, delivery_info: str | None = None) -> ProductVersion:
  product = get_product_by_id(db, product_id)
  if not product:
    raise ValueError("Product not found")

  version = _create_version(
    db,
    product_id=product_id,
    category_id=category_id,
    title=title,
    description=description,
    delivery_info=delivery_info,
    slug=slug,
  )
  product.status = "PENDING"
  product.updated_at = _now()
  db.commit()
  db.refresh(version)
  return version


def get_product_version_by_id(db: Session, version_id: int):
  return db.query(ProductVersion).filter(ProductVersion.id == version_id, ProductVersion.deleted_at == None).first()


def get_product_versions(db: Session, product_id: int, skip: int = 0, limit: int = 100):
  return db.query(ProductVersion).filter(ProductVersion.product_id == product_id, ProductVersion.deleted_at == None).order_by(ProductVersion.created_at.desc()).offset(skip).limit(limit).all()


def update_product_version(db: Session, version: ProductVersion, data: dict):
  product = get_product_by_id(db, version.product_id)
  if not product:
    raise ValueError("Product not found")
  return create_product_revision(db, product, data)


def delete_product_version(db: Session, version: ProductVersion, soft: bool = True):
  if soft:
    version.deleted_at = _now()
    db.commit()
    db.refresh(version)
    return version
  db.delete(version)
  db.commit()
  return None


def create_product_variant(db: Session, version_id: int, sku_code: str, price: Decimal, stock: int, discount: int = 0, features: list | None = None) -> ProductVariant:
  if db.query(ProductVariant).filter(ProductVariant.sku_code == sku_code, ProductVariant.deleted_at == None).first():
    raise ValueError("Variant SKU already exists")

  variant = ProductVariant(
    product_version_id=version_id,
    sku_code=sku_code,
    price=price,
    stock=stock,
  )
  db.add(variant)
  db.flush()
  _create_feature_rows(db, variant, features or [])
  db.commit()
  db.refresh(variant)
  return variant


def get_product_variant_by_id(db: Session, variant_id: int):
  return db.query(ProductVariant).filter(ProductVariant.id == variant_id, ProductVariant.deleted_at == None).first()


def get_product_variants(db: Session, version_id: int, skip: int = 0, limit: int = 100):
  return db.query(ProductVariant).filter(ProductVariant.product_version_id == version_id, ProductVariant.deleted_at == None).offset(skip).limit(limit).all()


def update_product_variant(db: Session, variant: ProductVariant, data: dict):
  for key in ("sku_code", "price", "stock"):
    if key in data and data[key] is not None:
      if key == "sku_code" and data[key] != variant.sku_code:
        if db.query(ProductVariant).filter(ProductVariant.sku_code == data[key], ProductVariant.deleted_at == None).first():
          raise ValueError("Variant SKU already exists")
      setattr(variant, key, data[key])

  if data.get("features") is not None:
    for feature in variant.product_features:
      feature.deleted_at = _now()
    db.flush()
    _create_feature_rows(db, variant, data["features"])

  db.commit()
  db.refresh(variant)
  return variant


def delete_product_variant(db: Session, variant: ProductVariant, soft: bool = True):
  if soft:
    variant.deleted_at = _now()
    db.commit()
    db.refresh(variant)
    return variant
  db.delete(variant)
  db.commit()
  return None


def create_product_picture(
  db: Session,
  version_id: int,
  file_url: str | None = None,
  sort_order: int = 0,
  original_url: str | None = None,
  preview_url: str | None = None,
  thumbnail_url: str | None = None,
) -> ProductPicture:
  original_url = original_url or file_url
  picture = ProductPicture(
    product_version_id=version_id,
    file_url=file_url or original_url,
    original_url=original_url,
    preview_url=preview_url,
    thumbnail_url=thumbnail_url,
    sort_order=sort_order,
  )
  db.add(picture)
  db.commit()
  db.refresh(picture)
  return picture


def get_product_picture_by_id(db: Session, picture_id: int):
  return db.query(ProductPicture).filter(ProductPicture.id == picture_id, ProductPicture.deleted_at == None).first()


def get_product_pictures(db: Session, version_id: int, skip: int = 0, limit: int = 100):
  return db.query(ProductPicture).filter(ProductPicture.product_version_id == version_id, ProductPicture.deleted_at == None).order_by(ProductPicture.sort_order.asc()).offset(skip).limit(limit).all()


def update_product_picture(db: Session, picture: ProductPicture, data: dict):
  for key, value in data.items():
    if hasattr(picture, key) and value is not None:
      setattr(picture, key, value)
  if picture.original_url and not picture.file_url:
    picture.file_url = picture.original_url
  db.commit()
  db.refresh(picture)
  return picture


def delete_product_picture(db: Session, picture: ProductPicture, soft: bool = True):
  if soft:
    picture.deleted_at = _now()
    db.commit()
    db.refresh(picture)
    return picture
  db.delete(picture)
  db.commit()
  return None


def _discount_amount(price: Decimal, discount: Discount) -> Decimal:
  value = Decimal(discount.value)
  if discount.discount_type == "PERCENTAGE":
    return min(price, (price * value / Decimal("100")).quantize(Decimal("0.01")))
  if discount.discount_type in ("FIXED", "COUPON"):
    return min(price, value)
  return Decimal("0.00")


def get_best_discount(db: Session, product: Product, price: Decimal, coupon_code: str | None = None):
  version = product.current_version
  if not version:
    return None, Decimal("0.00")

  now = _now()
  query = db.query(Discount).filter(
    Discount.is_active == True,
    Discount.start_date <= now,
    Discount.end_date >= now,
    or_(
      and_(Discount.target_type == "PRODUCT",
           Discount.target_id == product.id),
      and_(Discount.target_type == "CATEGORY",
           Discount.target_id == version.category_id),
      and_(Discount.target_type == "SELLER",
           Discount.target_id == product.seller_id),
    ),
  )
  if coupon_code:
    query = query.filter(
      or_(Discount.discount_type != "COUPON", Discount.coupon_code == coupon_code))
  else:
    query = query.filter(Discount.discount_type != "COUPON")

  best_discount = None
  best_amount = Decimal("0.00")
  for discount in query.all():
    amount = _discount_amount(Decimal(price), discount)
    if amount > best_amount:
      best_discount = discount
      best_amount = amount
  return best_discount, best_amount


def get_variant_price(db: Session, product: Product, variant: ProductVariant, coupon_code: str | None = None):
  base_price = Decimal(variant.price)
  discount, discount_amount = get_best_discount(
    db, product, base_price, coupon_code=coupon_code)
  return {
    "base_price": base_price,
    "discount_id": discount.id if discount else None,
    "discount_amount": discount_amount,
    "final_price": max(Decimal("0.00"), base_price - discount_amount),
  }


def record_product_view(db: Session, product: Product, user_id: int | None = None, viewer_key: str | None = None):
  product.pageviews += 1
  if viewer_key:
    exists = db.query(ProductView).filter(
      ProductView.product_id == product.id,
      ProductView.viewer_key == viewer_key,
    ).first()
    if not exists:
      product.unique_pageviews += 1
  db.add(ProductView(product_id=product.id,
         user_id=user_id, viewer_key=viewer_key))
  db.commit()
  db.refresh(product)
  return product


def get_related_products(db: Session, product: Product, limit: int = 4):
  version = product.current_version
  if not version:
    return [], [], []

  similar = get_products(db, limit=limit, category_id=version.category_id)
  seller_products = get_products(db, limit=limit, seller_id=product.seller_id)
  recommended = get_products(db, limit=limit, sort_by="popularity")

  def strip_current(items):
    return [item for item in items if item.id != product.id][:limit]

  return strip_current(similar), strip_current(seller_products), strip_current(recommended)


def _product_id_for_variant(variant: ProductVariant) -> int:
  return variant.product_version.product_id


def user_has_completed_order_for_variant(db: Session, user_id: int, product_variant_id: int) -> bool:
  return db.query(OrderItem).join(Order).filter(
    Order.user_id == user_id,
    Order.status.in_(COMPLETED_ORDER_STATUSES),
    OrderItem.product_variant_id == product_variant_id,
  ).first() is not None


def user_has_review_for_product(db: Session, user_id: int, product_id: int, review_id: int | None = None) -> bool:
  query = db.query(Review).join(ProductVariant).join(ProductVersion).filter(
    Review.user_id == user_id,
    Review.deleted_at == None,
    ProductVersion.product_id == product_id,
  )
  if review_id is not None:
    query = query.filter(Review.id != review_id)
  return query.first() is not None


def recalculate_product_rating(db: Session, product_id: int):
  stats = db.query(
    func.avg(Review.rating),
    func.count(Review.id),
  ).join(ProductVariant).join(ProductVersion).filter(
    ProductVersion.product_id == product_id,
    Review.deleted_at == None,
  ).one()

  product = get_product_by_id(db, product_id)
  if product:
    product.average_rating = float(stats[0] or 0)
    product.reviews_count = int(stats[1] or 0)
    product.updated_at = _now()
    db.commit()
    db.refresh(product)
  return product


def get_product_reviews(
  db: Session,
  product_id: int,
  skip: int = 0,
  limit: int = 100,
  min_rating: int | None = None,
  max_rating: int | None = None,
  sort_by: str = "created_at",
  sort_dir: str = "desc",
  with_count: bool = False,
):
  query = (
    db.query(Review)
    .join(ProductVariant)
    .join(ProductVersion)
    .filter(
      ProductVersion.product_id == product_id,
      Review.deleted_at == None,
    )
  )

  if min_rating is not None:
    query = query.filter(Review.rating >= min_rating)
  if max_rating is not None:
    query = query.filter(Review.rating <= max_rating)

  direction = asc if sort_dir == "asc" else desc
  order_col = Review.rating if sort_by == "rating" else Review.created_at
  query = query.order_by(direction(order_col))

  if with_count:
    total = query.with_entities(func.count(Review.id)).scalar() or 0
    return total, query.offset(skip).limit(limit).all()

  return query.offset(skip).limit(limit).all()


def create_review(db: Session, user_id: int, product_id: int, product_variant_id: int, rating: int, comment: str | None, pictures: list | None = None):
  variant = get_product_variant_by_id(db, product_variant_id)
  if not variant or _product_id_for_variant(variant) != product_id:
    raise ValueError("Product variant not found")
  if user_has_review_for_product(db, user_id, product_id):
    raise ValueError("User has already reviewed this product")
  if not user_has_completed_order_for_variant(db, user_id, product_variant_id):
    raise ValueError("Review is allowed only after a completed order")

  review = Review(
    user_id=user_id,
    product_variant_id=product_variant_id,
    rating=rating,
    comment=comment,
  )
  db.add(review)
  db.flush()
  _create_review_pictures(db, review.id, pictures or [])
  db.commit()
  db.refresh(review)
  recalculate_product_rating(db, product_id)
  return review


def update_review(db: Session, review: Review, product_id: int, rating: int | None = None, comment: str | None = None):
  if review.created_at + REVIEW_EDIT_WINDOW < _now():
    raise ValueError("Review edit window has expired")
  if rating is not None:
    review.rating = rating
  if comment is not None:
    review.comment = comment
  review.updated_at = _now()
  db.commit()
  db.refresh(review)
  recalculate_product_rating(db, product_id)
  return review


def delete_review(db: Session, review: Review, product_id: int):
  review.deleted_at = _now()
  db.commit()
  db.refresh(review)
  recalculate_product_rating(db, product_id)
  return review


def get_review_by_id(db: Session, review_id: int):
  return db.query(Review).filter(
    Review.id == review_id,
    Review.deleted_at == None,
  ).first()
