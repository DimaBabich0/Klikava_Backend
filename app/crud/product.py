from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Product, ProductVersion, ProductVariant, ProductPicture


def create_product(db: Session, seller_id: int, status: str = "moderating") -> Product:
  product = Product(seller_id=seller_id, status=status)
  db.add(product)
  db.commit()
  db.refresh(product)
  return product


def get_product_by_id(db: Session, product_id: int):
  return (
    db.query(Product)
    .filter(Product.id == product_id)
    .filter(Product.deleted_at == None)
    .first()
  )


def get_product_by_slug(db: Session, slug: str):
  return (
    db.query(Product)
    .join(Product.versions)
    .filter(ProductVersion.slug == slug)
    .filter(ProductVersion.deleted_at == None)
    .first()
  )


def get_products(db: Session, skip: int = 0, limit: int = 100):
  return db.query(Product).filter(Product.deleted_at == None).offset(skip).limit(limit).all()


def get_products_count(db: Session):
  return db.query(Product).filter(Product.deleted_at == None).count()


def update_product(db: Session, product: Product, data: dict):
  for k, v in data.items():
    if hasattr(product, k) and v is not None:
      setattr(product, k, v)
  db.commit()
  db.refresh(product)
  return product


def delete_product(db: Session, product: Product, soft: bool = True):
  if soft:
    product.deleted_at = datetime.now()
    db.commit()
    db.refresh(product)
    return product
  else:
    db.delete(product)
    db.commit()
    return None


def search_products(db: Session, q: str, skip: int = 0, limit: int = 100):
  return db.query(Product).join(ProductVersion).filter(
    Product.deleted_at == None,
    ProductVersion.deleted_at == None,
    ProductVersion.title.ilike(f"%{q}%"),
  ).offset(skip).limit(limit).all()


def create_product_version(db: Session, product_id: int, category_id: int | None, title: str, description: str | None, slug: str) -> ProductVersion:
  if not db.query(Product).filter(Product.id == product_id, Product.deleted_at == None).first():
    raise ValueError("Product not found")

  if db.query(ProductVersion).filter(ProductVersion.slug == slug, ProductVersion.deleted_at == None).first():
    raise ValueError("Version slug already exists")

  version = ProductVersion(
    product_id=product_id,
    category_id=category_id,
    title=title,
    description=description,
    slug=slug,
  )
  db.add(version)
  db.commit()
  db.refresh(version)
  return version


def get_product_version_by_id(db: Session, version_id: int):
  return db.query(ProductVersion).filter(ProductVersion.id == version_id, ProductVersion.deleted_at == None).first()


def get_product_versions(db: Session, product_id: int, skip: int = 0, limit: int = 100):
  return db.query(ProductVersion).filter(ProductVersion.product_id == product_id, ProductVersion.deleted_at == None).order_by(ProductVersion.created_at.desc()).offset(skip).limit(limit).all()


def update_product_version(db: Session, version: ProductVersion, data: dict):
  for k, v in data.items():
    if hasattr(version, k) and v is not None:
      setattr(version, k, v)
  db.commit()
  db.refresh(version)
  return version


def delete_product_version(db: Session, version: ProductVersion, soft: bool = True):
  if soft:
    version.deleted_at = datetime.now()
    db.commit()
    db.refresh(version)
    return version
  else:
    db.delete(version)
    db.commit()
    return None


def create_product_variant(db: Session, version_id: int, sku_code: str, price: float, stock: int, discount: int = 0) -> ProductVariant:
  if db.query(ProductVariant).filter(ProductVariant.sku_code == sku_code, ProductVariant.deleted_at == None).first():
    raise ValueError("Variant SKU already exists")

  variant = ProductVariant(
    product_version_id=version_id,
    sku_code=sku_code,
    price=price,
    stock=stock,
    discount=discount,
  )
  db.add(variant)
  db.commit()
  db.refresh(variant)
  return variant


def get_product_variant_by_id(db: Session, variant_id: int):
  return db.query(ProductVariant).filter(ProductVariant.id == variant_id, ProductVariant.deleted_at == None).first()


def get_product_variants(db: Session, version_id: int, skip: int = 0, limit: int = 100):
  return db.query(ProductVariant).filter(ProductVariant.product_version_id == version_id, ProductVariant.deleted_at == None).all()


def update_product_variant(db: Session, variant: ProductVariant, data: dict):
  for k, v in data.items():
    if hasattr(variant, k) and v is not None:
      setattr(variant, k, v)
  db.commit()
  db.refresh(variant)
  return variant


def delete_product_variant(db: Session, variant: ProductVariant, soft: bool = True):
  if soft:
    variant.deleted_at = datetime.now()
    db.commit()
    db.refresh(variant)
    return variant
  else:
    db.delete(variant)
    db.commit()
    return None


def create_product_picture(db: Session, version_id: int, file_url: str, sort_order: int = 0) -> ProductPicture:
  picture = ProductPicture(
    product_version_id=version_id,
    file_url=file_url,
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
  for k, v in data.items():
    if hasattr(picture, k) and v is not None:
      setattr(picture, k, v)
  db.commit()
  db.refresh(picture)
  return picture


def delete_product_picture(db: Session, picture: ProductPicture, soft: bool = True):
  if soft:
    picture.deleted_at = datetime.now()
    db.commit()
    db.refresh(picture)
    return picture
  else:
    db.delete(picture)
    db.commit()
    return None
