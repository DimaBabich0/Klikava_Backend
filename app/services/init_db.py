from datetime import datetime, timedelta
from decimal import Decimal

from app.models.product_picture import ProductPicture
from app.services.auth import hash_password
from app.database import SessionLocal, engine
from app.models import (
  Base,
  Category,
  Discount,
  DiscountItem,
  Feature,
  Order,
  OrderItem,
  Product,
  ProductFeature,
  ProductVariant,
  ProductVersion,
  ProductView,
  Review,
  Role,
  Seller,
  User,
  UserCreditCard,
  UserDeliveryAddress,
  UserRoles,
)


DEMO_PASSWORDS = {
  "admin_market_root": "AdminRoot#2026",
  "moderator_catalog_anna": "Moderator#2026",
  "seller_tech_nova": "TechNova#2026",
  "seller_byte_house": "ByteHouse#2026",
  "seller_home_craft": "HomeCraft#2026",
  "seller_sport_line": "SportLine#2026",
  "seller_kids_world": "KidsWorld#2026",
  "buyer_ivan_koval": "BuyerIvan#2026",
  "buyer_olena_melnyk": "BuyerOlena#2026",
  "buyer_dmytro_shev": "BuyerDmytro#2026",
  "applicant_seller_marta": "SellerApply#2026",
}


def init_db():
  """Initialize database schema."""
  Base.metadata.create_all(bind=engine)
  print("--- Database tables created ---")


def _get_role(db, name):
  return db.query(Role).filter(Role.name == name).first()


def _get_user_by_login(db, login):
  return db.query(UserRoles).filter(UserRoles.login == login).first()


def _ensure_user_role(db, user, role_name, login, password):
  role = _get_role(db, role_name)
  if not role:
    raise ValueError(f"Role {role_name} not found. Run seed_roles() first")

  existing_role = db.query(UserRoles).filter(
    UserRoles.user_id == user.id,
    UserRoles.role_id == role.id,
  ).first()
  if existing_role:
    return existing_role

  if _get_user_by_login(db, login):
    raise ValueError(f"Login {login} already exists")

  password_hash, password_salt = hash_password(password)
  user_role = UserRoles(
    user=user,
    role=role,
    login=login,
    password_hash=password_hash,
    password_salt=password_salt,
    status="active",
  )
  db.add(user_role)
  return user_role


def _create_user_with_roles(
  db,
  *,
  name,
  email,
  login,
  password,
  role_names,
  phone_number=None,
  birthday=None,
):
  user = db.query(User).filter(User.email == email).first()
  if not user:
    user = User(
      name=name,
      email=email,
      phone_number=phone_number,
      birthday=birthday,
    )
    db.add(user)
    db.flush()

  for role_name in role_names:
    role_login = login if role_name == role_names[0] else f"{login}.{role_name.lower()}"
    _ensure_user_role(db, user, role_name, role_login, password)

  return user


def seed_roles():
  """Seed default roles into the database"""
  db = SessionLocal()

  try:
    roles_data = [
      {
        "name": "ADMIN",
        "description": "Administrator with full system access",
        "create_level": 4,
        "read_level": 4,
        "update_level": 4,
        "deleted_level": 4,
      },
      {
        "name": "MODERATOR",
        "description": "Moderator with moderation capabilities",
        "create_level": 3,
        "read_level": 3,
        "update_level": 3,
        "deleted_level": 3,
      },
      {
        "name": "SELLER",
        "description": "Approved seller with product management capabilities",
        "create_level": 2,
        "read_level": 2,
        "update_level": 2,
        "deleted_level": 2,
      },
      {
        "name": "BUYER",
        "description": "Regular buyer user",
        "create_level": 1,
        "read_level": 1,
        "update_level": 1,
        "deleted_level": 1,
      },
    ]

    seeded_count = 0
    for role_data in roles_data:
      role = db.query(Role).filter(Role.name == role_data["name"]).first()
      if role:
        continue

      db.add(Role(**role_data))
      seeded_count += 1

    db.commit()
    print(f"--- Seeded {seeded_count} roles successfully ---")

  except Exception as e:
    db.rollback()
    print(f"--- Error seeding roles: {e} ---")
    raise
  finally:
    db.close()


def seed_users():
  """Seed demo users. Seller role is granted when seller profiles are created."""
  db = SessionLocal()

  try:
    users_data = [
      {
        "name": "Marketplace Administrator",
        "email": "admin.market.root@example.com",
        "login": "admin_market_root",
        "password": DEMO_PASSWORDS["admin_market_root"],
        "role_names": ["ADMIN"],
        "phone_number": "+380501110001",
      },
      {
        "name": "Anna Catalog Moderator",
        "email": "moderator.catalog.anna@example.com",
        "login": "moderator_catalog_anna",
        "password": DEMO_PASSWORDS["moderator_catalog_anna"],
        "role_names": ["MODERATOR"],
        "phone_number": "+380501110002",
      },
      {
        "name": "Tech Nova Manager",
        "email": "seller.tech.nova@example.com",
        "login": "seller_tech_nova",
        "password": DEMO_PASSWORDS["seller_tech_nova"],
        "role_names": ["BUYER"],
        "phone_number": "+380501110101",
      },
      {
        "name": "Byte House Manager",
        "email": "seller.byte.house@example.com",
        "login": "seller_byte_house",
        "password": DEMO_PASSWORDS["seller_byte_house"],
        "role_names": ["BUYER"],
        "phone_number": "+380501110102",
      },
      {
        "name": "Home Craft Manager",
        "email": "seller.home.craft@example.com",
        "login": "seller_home_craft",
        "password": DEMO_PASSWORDS["seller_home_craft"],
        "role_names": ["BUYER"],
        "phone_number": "+380501110103",
      },
      {
        "name": "Sport Line Manager",
        "email": "seller.sport.line@example.com",
        "login": "seller_sport_line",
        "password": DEMO_PASSWORDS["seller_sport_line"],
        "role_names": ["BUYER"],
        "phone_number": "+380501110104",
      },
      {
        "name": "Kids World Manager",
        "email": "seller.kids.world@example.com",
        "login": "seller_kids_world",
        "password": DEMO_PASSWORDS["seller_kids_world"],
        "role_names": ["BUYER"],
        "phone_number": "+380501110105",
      },
      {
        "name": "Ivan Koval",
        "email": "buyer.ivan.koval@example.com",
        "login": "buyer_ivan_koval",
        "password": DEMO_PASSWORDS["buyer_ivan_koval"],
        "role_names": ["BUYER"],
        "phone_number": "+380501112001",
        "birthday": datetime(1994, 5, 14),
      },
      {
        "name": "Olena Melnyk",
        "email": "buyer.olena.melnyk@example.com",
        "login": "buyer_olena_melnyk",
        "password": DEMO_PASSWORDS["buyer_olena_melnyk"],
        "role_names": ["BUYER"],
        "phone_number": "+380501112002",
        "birthday": datetime(1998, 9, 2),
      },
      {
        "name": "Dmytro Shevchenko",
        "email": "buyer.dmytro.shev@example.com",
        "login": "buyer_dmytro_shev",
        "password": DEMO_PASSWORDS["buyer_dmytro_shev"],
        "role_names": ["BUYER"],
        "phone_number": "+380501112003",
        "birthday": datetime(1991, 2, 20),
      },
      {
        "name": "Marta Seller Applicant",
        "email": "applicant.seller.marta@example.com",
        "login": "applicant_seller_marta",
        "password": DEMO_PASSWORDS["applicant_seller_marta"],
        "role_names": ["BUYER"],
        "phone_number": "+380501119001",
      },
    ]

    seeded_count = 0
    for user_data in users_data:
      existed = db.query(User).filter(User.email == user_data["email"]).first()
      _create_user_with_roles(db, **user_data)
      if not existed:
        seeded_count += 1

    db.commit()
    print(f"--- Seeded {seeded_count} users successfully ---")
    print("--- Demo credentials ---")
    for login, password in DEMO_PASSWORDS.items():
      print(f"{login}: {password}")

  except Exception as e:
    db.rollback()
    print(f"--- Error seeding users: {e} ---")
    raise
  finally:
    db.close()


def seed_admin_user():
  """Keep backward-compatible admin seed entry point."""
  seed_users()


def seed_user_profiles():
  """Seed delivery addresses and safe placeholder card data."""
  db = SessionLocal()

  try:
    profiles = {
      "buyer.ivan.koval@example.com": {
        "addresses": [
          "Kyiv, Khreshchatyk Street 1, apt. 24",
          "Kyiv, Peremohy Avenue 12",
        ],
        "cards": ["encrypted_demo_visa_ivan_2026"],
      },
      "buyer.olena.melnyk@example.com": {
        "addresses": ["Lviv, Rynok Square 10"],
        "cards": ["encrypted_demo_mastercard_olena_2026"],
      },
      "buyer.dmytro.shev@example.com": {
        "addresses": ["Odesa, Deribasivska Street 5"],
        "cards": ["encrypted_demo_visa_dmytro_2026"],
      },
    }

    address_count = 0
    card_count = 0
    for email, profile in profiles.items():
      user = db.query(User).filter(User.email == email).first()
      if not user:
        continue

      for address in profile["addresses"]:
        exists = db.query(UserDeliveryAddress).filter(
          UserDeliveryAddress.user_id == user.id,
          UserDeliveryAddress.address_line == address,
        ).first()
        if not exists:
          db.add(UserDeliveryAddress(user_id=user.id, address_line=address))
          address_count += 1

      for index, card_info in enumerate(profile["cards"], start=1):
        exists = db.query(UserCreditCard).filter(
          UserCreditCard.user_id == user.id,
          UserCreditCard.card_info_encrypted == card_info,
        ).first()
        if not exists:
          db.add(UserCreditCard(
            user_id=user.id,
            card_info_encrypted=card_info,
            order_in_list=index,
          ))
          card_count += 1

    db.commit()
    print(
      f"--- Seeded {address_count} addresses and {card_count} cards successfully ---")

  except Exception as e:
    db.rollback()
    print(f"--- Error seeding user profiles: {e} ---")
    raise
  finally:
    db.close()


def seed_sellers():
  """Seed seller profiles and grant SELLER role after profile creation."""
  db = SessionLocal()

  try:
    sellers_data = [
      {
        "user_email": "seller.tech.nova@example.com",
        "store_name": "TechNova",
        "description": "Mobile phones, gadgets, and premium electronics.",
        "picture_url": "/static/sellers/technova.png",
        "rating": 4.8,
      },
      {
        "user_email": "seller.byte.house@example.com",
        "store_name": "ByteHouse",
        "description": "Computers, tablets, networking, and storage devices.",
        "picture_url": "/static/sellers/bytehouse.png",
        "rating": 4.7,
      },
      {
        "user_email": "seller.home.craft@example.com",
        "store_name": "HomeCraft",
        "description": "Home appliances, furniture, tools, and garden goods.",
        "picture_url": "/static/sellers/homecraft.png",
        "rating": 4.6,
      },
      {
        "user_email": "seller.sport.line@example.com",
        "store_name": "SportLine",
        "description": "Sports, outdoor, fitness, luggage, and entertainment.",
        "picture_url": "/static/sellers/sportline.png",
        "rating": 4.5,
      },
      {
        "user_email": "seller.kids.world@example.com",
        "store_name": "KidsWorld",
        "description": "Mother and kids products, toys, pet products, and food.",
        "picture_url": "/static/sellers/kidsworld.png",
        "rating": 4.4,
      },
    ]

    seeded_count = 0
    for seller_data in sellers_data:
      seller = db.query(Seller).filter(
        Seller.store_name == seller_data["store_name"]
      ).first()
      if seller:
        continue

      user = db.query(User).filter(
        User.email == seller_data["user_email"]).first()
      if not user:
        raise ValueError(f"Seller user {seller_data['user_email']} not found")

      _ensure_user_role(
        db,
        user,
        "SELLER",
        f"seller.user.{user.id}",
        f"{seller_data['store_name']}SellerRole#2026",
      )

      db.add(Seller(
        parent_id=seller_data.get("parent_id"),
        picture_url=seller_data["picture_url"],
        store_name=seller_data["store_name"],
        description=seller_data["description"],
        rating=seller_data["rating"],
      ))
      seeded_count += 1

    db.commit()
    print(f"--- Seeded {seeded_count} sellers successfully ---")

  except Exception as e:
    db.rollback()
    print(f"--- Error seeding sellers: {e} ---")
    raise
  finally:
    db.close()


def seed_categories():
  """Seed marketplace categories and subcategories."""
  db = SessionLocal()

  try:
    categories_data = [
      {
        "title": "Mobile Phones",
        "description": "Phones, mobile accessories, parts, SIM cards, and satellite phones.",
        "children": [
          "Mobile Phones",
          "Mobile Phone Accessories",
          "Mobile Phone Parts",
          "Sim Cards",
          "Satellite Phones",
        ],
      },
      {
        "title": "Computers",
        "description": "Computers, tablets, networking, servers, storage, and parts.",
        "children": [
          "Laptops",
          "Tablets",
          "Desktops & AIO",
          "Networking",
          "Servers & Industrial Computer",
          "Storage Device",
          "Computer Parts & Accessories",
        ],
      },
      {"title": "Electronics"},
      {"title": "Home Appliances"},
      {"title": "Home Improvement & Tools"},
      {"title": "Security & Protection"},
      {"title": "Automobiles & Motorcycles"},
      {"title": "Home, Garden & Office"},
      {"title": "Furniture"},
      {"title": "Clothing"},
      {"title": "Shoes"},
      {"title": "Accessories"},
      {"title": "Luggage & Bags"},
      {"title": "Sports & Entertainment"},
      {"title": "Mother & Kids"},
      {"title": "Toys & Hobbies"},
      {"title": "Beaty & Health"},
      {"title": "Pet Products"},
      {"title": "Food"},
    ]

    seeded_count = 0
    order = 100
    for category_data in categories_data:
      parent = db.query(Category).filter(
        Category.title == category_data["title"],
        Category.parent_id.is_(None),
      ).first()
      if not parent:
        parent = Category(
          title=category_data["title"],
          description=category_data.get("description"),
          order_in_price=order,
        )
        db.add(parent)
        db.flush()
        seeded_count += 1

      for child_title in category_data.get("children", []):
        child = db.query(Category).filter(
          Category.title == child_title,
          Category.parent_id == parent.id,
        ).first()
        if child:
          continue
        db.add(Category(
          parent_id=parent.id,
          title=child_title,
          description=f"{child_title} catalog section.",
          order_in_price=order + 1,
        ))
        seeded_count += 1

      order += 100

    db.commit()
    print(f"--- Seeded {seeded_count} categories successfully ---")

  except Exception as e:
    db.rollback()
    print(f"--- Error seeding categories: {e} ---")
    raise
  finally:
    db.close()


def seed_features():
  """Seed product features used by variants."""
  db = SessionLocal()

  try:
    features_data = [
      ("Brand", True),
      ("Color", True),
      ("Storage", True),
      ("Memory", True),
      ("Screen", False),
      ("Material", False),
      ("Weight", False),
      ("Size", False),
      ("Warranty", False),
      ("Power", False),
    ]

    seeded_count = 0
    for title, is_primary in features_data:
      feature = db.query(Feature).filter(Feature.title == title).first()
      if feature:
        continue
      db.add(Feature(title=title, is_primary=is_primary))
      seeded_count += 1

    db.commit()
    print(f"--- Seeded {seeded_count} features successfully ---")

  except Exception as e:
    db.rollback()
    print(f"--- Error seeding features: {e} ---")
    raise
  finally:
    db.close()


def _product_rows():
  return [
    ("iPhone 15", "Mobile Phones", "TechNova", "Apple",
     "Black", "128 GB", Decimal("899.00"), 24),
    ("Galaxy S24", "Mobile Phones", "TechNova",
     "Samsung", "Gray", "256 GB", Decimal("849.00"), 30),
    ("Pixel 8", "Mobile Phones", "TechNova", "Google",
     "Hazel", "128 GB", Decimal("699.00"), 18),
    ("Xiaomi 14", "Mobile Phones", "TechNova", "Xiaomi",
     "Green", "256 GB", Decimal("649.00"), 35),
    ("Rugged Satellite Phone", "Satellite Phones", "TechNova",
     "Iridium", "Orange", "32 GB", Decimal("1199.00"), 6),
    ("Fast Charger 65W", "Mobile Phone Accessories", "TechNova",
     "Baseus", "White", "65 W", Decimal("39.00"), 120),
    ("Magnetic Power Bank", "Mobile Phone Accessories", "TechNova",
     "Anker", "Black", "10000 mAh", Decimal("59.00"), 80),
    ("OLED Phone Screen", "Mobile Phone Parts", "TechNova",
     "FixPro", "Black", "6.1 inch", Decimal("129.00"), 40),
    ("Travel Sim Europe", "Sim Cards", "TechNova",
     "WorldSim", "Blue", "20 GB", Decimal("24.00"), 200),
    ("MacBook Air 13", "Laptops", "ByteHouse", "Apple",
     "Silver", "256 GB", Decimal("1099.00"), 15),
    ("ThinkPad E14", "Laptops", "ByteHouse", "Lenovo",
     "Black", "512 GB", Decimal("799.00"), 22),
    ("ZenBook 14", "Laptops", "ByteHouse", "Asus",
     "Blue", "1 TB", Decimal("999.00"), 16),
    ("iPad Air", "Tablets", "ByteHouse", "Apple",
     "Purple", "256 GB", Decimal("749.00"), 20),
    ("Galaxy Tab S9", "Tablets", "ByteHouse", "Samsung",
     "Graphite", "128 GB", Decimal("699.00"), 25),
    ("Office Desktop AIO", "Desktops & AIO", "ByteHouse",
     "HP", "White", "512 GB", Decimal("699.00"), 12),
    ("Mesh Router AX3000", "Networking", "ByteHouse",
     "TP-Link", "White", "AX3000", Decimal("119.00"), 45),
    ("NAS Storage 4 Bay", "Storage Device", "ByteHouse",
     "Synology", "Black", "4 Bay", Decimal("549.00"), 10),
    ("Server RAM 32GB", "Computer Parts & Accessories", "ByteHouse",
     "Kingston", "Green", "32 GB", Decimal("89.00"), 75),
    ("Industrial Mini PC", "Servers & Industrial Computer",
     "ByteHouse", "Intel", "Black", "512 GB", Decimal("429.00"), 9),
    ("Wireless Earbuds Pro", "Electronics", "TechNova",
     "Sony", "Black", "ANC", Decimal("149.00"), 60),
    ("Smart TV 55", "Electronics", "TechNova", "LG",
     "Black", "55 inch", Decimal("599.00"), 14),
    ("Robot Vacuum S7", "Home Appliances", "HomeCraft",
     "Roborock", "White", "5200 mAh", Decimal("399.00"), 18),
    ("Kitchen Blender 1200W", "Home Appliances", "HomeCraft",
     "Bosch", "Silver", "1200 W", Decimal("129.00"), 35),
    ("Air Fryer XL", "Home Appliances", "HomeCraft",
     "Philips", "Black", "6 L", Decimal("159.00"), 28),
    ("Cordless Drill Set", "Home Improvement & Tools",
     "HomeCraft", "Makita", "Blue", "18 V", Decimal("189.00"), 24),
    ("Laser Distance Meter", "Home Improvement & Tools",
     "HomeCraft", "Bosch", "Green", "40 m", Decimal("79.00"), 42),
    ("Smart Door Lock", "Security & Protection", "HomeCraft",
     "Aqara", "Black", "WiFi", Decimal("219.00"), 20),
    ("Dash Camera 4K", "Automobiles & Motorcycles", "TechNova",
     "70mai", "Black", "4K", Decimal("129.00"), 33),
    ("Car Vacuum Cleaner", "Automobiles & Motorcycles",
     "HomeCraft", "Xiaomi", "Gray", "120 W", Decimal("49.00"), 50),
    ("Office Chair Ergo", "Furniture", "HomeCraft",
     "ErgoLine", "Black", "M", Decimal("239.00"), 18),
    ("Standing Desk", "Furniture", "HomeCraft",
     "FlexiSpot", "Oak", "140 cm", Decimal("349.00"), 11),
    ("Garden Tool Kit", "Home, Garden & Office", "HomeCraft",
     "Gardena", "Green", "12 pcs", Decimal("69.00"), 40),
    ("Men Hoodie Basic", "Clothing", "SportLine",
     "UrbanFit", "Navy", "L", Decimal("39.00"), 90),
    ("Women Jacket Lite", "Clothing", "SportLine",
     "Columbia", "Red", "M", Decimal("99.00"), 32),
    ("Running Shoes Air", "Shoes", "SportLine",
     "Nike", "Black", "42", Decimal("129.00"), 40),
    ("Leather Belt", "Accessories", "SportLine",
     "Pierre Cardin", "Brown", "110 cm", Decimal("29.00"), 70),
    ("Travel Backpack 35L", "Luggage & Bags", "SportLine",
     "Osprey", "Blue", "35 L", Decimal("119.00"), 24),
    ("Yoga Mat Pro", "Sports & Entertainment", "SportLine",
     "Manduka", "Green", "183 cm", Decimal("69.00"), 55),
    ("Dumbbell Set 20kg", "Sports & Entertainment", "SportLine",
     "FitPro", "Black", "20 kg", Decimal("99.00"), 27),
    ("Baby Stroller Urban", "Mother & Kids", "KidsWorld",
     "Kinderkraft", "Gray", "One Size", Decimal("249.00"), 15),
    ("Baby Monitor HD", "Mother & Kids", "KidsWorld",
     "Motorola", "White", "5 inch", Decimal("139.00"), 21),
    ("Wooden Train Set", "Toys & Hobbies", "KidsWorld",
     "Brio", "Multi", "50 pcs", Decimal("59.00"), 36),
    ("RC Car Monster", "Toys & Hobbies", "KidsWorld",
     "Maisto", "Red", "1:18", Decimal("49.00"), 31),
    ("Electric Toothbrush", "Beaty & Health", "KidsWorld",
     "Oral-B", "White", "Pro", Decimal("79.00"), 64),
    ("Vitamin Complex", "Beaty & Health", "KidsWorld",
     "Solgar", "Yellow", "60 pcs", Decimal("24.00"), 100),
    ("Cat Food Salmon", "Pet Products", "KidsWorld",
     "Royal Canin", "Pink", "2 kg", Decimal("27.00"), 88),
    ("Dog Harness Reflective", "Pet Products", "KidsWorld",
     "Trixie", "Black", "M", Decimal("19.00"), 72),
    ("Coffee Beans Arabica", "Food", "KidsWorld",
     "Lavazza", "Brown", "1 kg", Decimal("22.00"), 95),
    ("Olive Oil Extra", "Food", "KidsWorld",
     "Monini", "Green", "1 L", Decimal("18.00"), 80),
    ("Wireless Mouse Silent", "Computer Parts & Accessories",
     "ByteHouse", "Logitech", "Black", "USB", Decimal("34.00"), 110),
  ]


def seed_products():
  """Seed sellers' products, product versions, variants, and feature values."""
  db = SessionLocal()

  try:
    category_by_title = {
      category.title: category for category in db.query(Category).all()}
    seller_by_name = {
      seller.store_name: seller for seller in db.query(Seller).all()}
    feature_by_title = {
      feature.title: feature for feature in db.query(Feature).all()}

    seeded_products = 0
    seeded_variants = 0
    for index, row in enumerate(_product_rows(), start=1):
      title, category_title, seller_name, brand, color, spec, price, stock = row
      seller = seller_by_name[seller_name]
      category = category_by_title[category_title]
      slug = title.lower().replace("&", "and").replace(" ", "-").replace(".", "")
      sku = f"DEMO-{index:03d}"

      variant = db.query(ProductVariant).filter(
        ProductVariant.sku_code == sku).first()
      if variant:
        continue

      product = Product(seller_id=seller.id,
                        status="APPROVED",
                        pageviews=index * 7,
                        unique_pageviews=index * 5)
      db.add(product)
      db.flush()
      seeded_products += 1

      version = ProductVersion(
        product_id=product.id,
        category_id=category.id,
        title=title[:32],
        description=f"{title} from {seller_name}. Demo catalog product.",
        delivery_info="Standard delivery in 2-5 business days.",
        slug=slug[:64],
        version_number=1,
      )
      db.add(version)
      db.flush()
      product.current_version_id = version.id

      variant = ProductVariant(
        product_version_id=version.id,
        sku_code=sku,
        price=price,
        stock=stock,
      )
      db.add(variant)
      db.flush()
      seeded_variants += 1

      feature_values = [
        ("Brand", brand, "text"),
        ("Color", color, "text"),
        ("Storage" if "GB" in spec or "TB" in spec else "Size", spec, "text"),
        ("Warranty", "24 months", "text"),
      ]
      for feature_title, value, value_type in feature_values:
        db.add(ProductFeature(
          product_variant_id=variant.id,
          feature_id=feature_by_title[feature_title].id,
          value=value,
          value_type=value_type,
        ))

    db.commit()
    print(
      f"--- Seeded {seeded_products} products and {seeded_variants} variants successfully ---")

  except Exception as e:
    db.rollback()
    print(f"--- Error seeding products: {e} ---")
    raise
  finally:
    db.close()


def seed_product_pictures():
  """Seed product pictures for demo products."""
  db = SessionLocal()

  DEMO_PICTURES_BASE = "/static/product_pictures/demo"

  # SKU -> list of filenames (in sort_order)
  pictures_map = {
    "DEMO-001": ["iphone-15-1.webp", "iphone-15-2.webp", "iphone-15-3.webp"],
    "DEMO-002": ["galaxy-s24-1.webp", "galaxy-s24-2.webp", "galaxy-s24-3.webp"],
    "DEMO-003": ["pixel-8-1.webp", "pixel-8-2.webp", "pixel-8-3.webp"],
    "DEMO-004": ["xiaomi-14-1.webp", "xiaomi-14-2.webp", "xiaomi-14-3.webp"],
    "DEMO-005": ["rugged-satellite-phone.webp"],
    "DEMO-006": ["fast-charger-65w.webp"],
    "DEMO-007": ["magnetic-power-bank.webp"],
    "DEMO-008": ["oled-phone-screen.webp"],
    "DEMO-009": ["travel-sim-europe.webp"],
    "DEMO-010": ["macbook-air-13.webp"],
    "DEMO-011": ["thinkpad-e14.webp"],
    "DEMO-012": ["zenbook-14-1.webp", "zenbook-14-2.webp"],
    "DEMO-013": ["ipad-air-1.webp", "ipad-air-2.webp"],
    "DEMO-014": ["galaxy-tab-s9-1.webp", "galaxy-tab-s9-2.webp", "galaxy-tab-s9-3.webp"],
    "DEMO-015": ["desktop-aio.webp"],
    "DEMO-016": ["router-ax3000.webp"],
    "DEMO-017": ["nas-storage.webp"],
    "DEMO-018": ["ram-32gb.webp"],
    "DEMO-019": ["desktop-aio.webp"],
    "DEMO-020": ["sony-earbuds-pro.webp", "sony-earbuds-pro-1.webp"],
    "DEMO-021": ["lg-tv.webp"],
    "DEMO-022": ["robot-vacuum.webp"],
    "DEMO-023": ["kitchen-blender-1.webp", "kitchen-blender-2.webp", "kitchen-blender-3.webp"],
    "DEMO-024": ["air-fryer-philips-1.webp", "air-fryer-philips-2.webp", "air-fryer-philips-3.webp", "air-fryer-philips-4.webp"],
    "DEMO-025": ["drill-set.webp"],
    "DEMO-026": ["laser-distance-meter-1.webp", "laser-distance-meter-2.webp"],
    "DEMO-027": ["smart-lock-door-1.webp", "smart-lock-door-2.webp"],
    "DEMO-028": ["dash-camera-4k.webp"],
    "DEMO-029": ["car-vacuum-cleaner.webp"],
    "DEMO-030": ["office-chair.webp"],
    "DEMO-031": ["standing-desk.webp"],
    "DEMO-032": ["garden-tool-kit.webp"],
    "DEMO-033": ["men-hoodie.webp"],
    "DEMO-034": ["women-jacket-1.webp", "women-jacket-2.webp"],
    "DEMO-035": ["shoes-nike-1.webp", "shoes-nike-2.webp"],
    "DEMO-036": ["belt.webp"],
    "DEMO-037": ["backpack-35l.webp"],
    "DEMO-038": ["yoga-mat.webp"],
    "DEMO-039": ["dumbbell-set-20kg.webp"],
    "DEMO-040": ["baby-stroller.webp"],
    "DEMO-041": ["baby-monitor.webp"],
    "DEMO-042": ["train-set.webp"],
    "DEMO-043": ["rc-car-monster.webp"],
    "DEMO-044": ["electric-toothbrush-oral.webp"],
    "DEMO-045": ["vitamin-complex.webp"],
    "DEMO-046": ["cat-food.webp"],
    "DEMO-047": ["dog-harness-reflective.webp"],
    "DEMO-048": ["coffee-beans.webp"],
    "DEMO-049": ["olive-oil.webp"],
    "DEMO-050": ["wireless-mouse.webp"],
  }

  try:
    variant_by_sku = {
      v.sku_code: v
      for v in db.query(ProductVariant).filter(
        ProductVariant.sku_code.like("DEMO-%")
      ).all()
    }

    seeded_count = 0
    for sku, filenames in pictures_map.items():
      variant = variant_by_sku.get(sku)
      if not variant:
        print(f"  WARNING: variant {sku} not found, skipping")
        continue

      version_id = variant.product_version_id

      existing = db.query(ProductPicture).filter(
        ProductPicture.product_version_id == version_id
      ).first()
      if existing:
        continue

      for sort_order, filename in enumerate(filenames):
        file_url = f"{DEMO_PICTURES_BASE}/{filename}"
        db.add(ProductPicture(
          product_version_id=version_id,
          file_url=file_url,
          original_url=file_url,
          preview_url=file_url,
          thumbnail_url=file_url,
          sort_order=sort_order,
        ))
        seeded_count += 1

    db.commit()
    print(f"--- Seeded {seeded_count} product pictures successfully ---")

  except Exception as e:
    db.rollback()
    print(f"--- Error seeding product pictures: {e} ---")
    raise
  finally:
    db.close()

def seed_discounts():
  """Seed discounts and discount items linked to product variants."""
  db = SessionLocal()

  try:
    now = datetime.now()
    discounts_data = [
      {
        "name": "Mobile Launch Sale",
        "description": "Launch discount for selected mobile phones.",
        "start_date": now - timedelta(days=7),
        "end_date": now + timedelta(days=30),
        "discount_type": "PERCENTAGE",
        "value": Decimal("10.00"),
        "target_type": "CATEGORY",
        "target_title": "Mobile Phones",
      },
      {
        "name": "Computer Weekend",
        "description": "Weekend computer deals.",
        "start_date": now - timedelta(days=2),
        "end_date": now + timedelta(days=14),
        "discount_type": "PERCENTAGE",
        "value": Decimal("15.00"),
        "target_type": "SELLER",
        "target_title": "ByteHouse",
      },
      {
        "name": "Home Bundle",
        "description": "Bundle discount for home appliances.",
        "start_date": now - timedelta(days=1),
        "end_date": now + timedelta(days=45),
        "discount_type": "PERCENTAGE",
        "value": Decimal("8.00"),
        "target_type": "CATEGORY",
        "target_title": "Home Appliances",
      },
    ]

    seeded_discounts = 0
    for discount_data in discounts_data:
      discount = db.query(Discount).filter(
        Discount.name == discount_data["name"]).first()
      if discount:
        continue
      target_title = discount_data.pop("target_title")
      target_type = discount_data["target_type"]
      if target_type == "CATEGORY":
        target = db.query(Category).filter(
          Category.title == target_title).first()
      else:
        target = db.query(Seller).filter(
          Seller.store_name == target_title).first()
      if not target:
        raise ValueError(f"Discount target {target_title} not found")
      db.add(Discount(
        **discount_data,
        target_id=target.id,
        discount_percentage=discount_data["value"] if discount_data["discount_type"] == "PERCENTAGE" else None,
      ))
      seeded_discounts += 1
    db.flush()

    product_id_by_sku = {
      variant.sku_code: variant
      for variant in db.query(ProductVariant).filter(ProductVariant.sku_code.like("DEMO-%")).all()
    }
    discount_by_name = {
      discount.name: discount for discount in db.query(Discount).all()}
    items_data = [
      ("Mobile Launch Sale", "DEMO-001", None, Decimal("819.00")),
      ("Mobile Launch Sale", "DEMO-002", None, Decimal("779.00")),
      ("Computer Weekend", "DEMO-010", None, Decimal("999.00")),
      ("Computer Weekend", "DEMO-011", None, Decimal("719.00")),
      ("Home Bundle", "DEMO-022", "DEMO-023", Decimal("499.00")),
    ]

    seeded_items = 0
    for discount_name, sku, other_sku, price in items_data:
      product_id = product_id_by_sku[sku].product_version.product_id
      other_product_id = (
        product_id_by_sku[other_sku].product_version.product_id
        if other_sku
        else None
      )
      discount = discount_by_name[discount_name]
      exists = db.query(DiscountItem).filter(
        DiscountItem.discount_id == discount.id,
        DiscountItem.item_id == product_id,
      ).first()
      if exists:
        continue
      db.add(DiscountItem(
        discount_id=discount.id,
        item_id=product_id,
        other_item_id=other_product_id,
        price=price,
      ))
      seeded_items += 1

    db.commit()
    print(
      f"--- Seeded {seeded_discounts} discounts and {seeded_items} discount items successfully ---")

  except Exception as e:
    db.rollback()
    print(f"--- Error seeding discounts: {e} ---")
    raise
  finally:
    db.close()


def seed_cart_orders():
  """Seed buyer orders in cart status."""
  db = SessionLocal()

  try:
    carts_data = [
      ("buyer.ivan.koval@example.com", ["DEMO-001", "DEMO-036"], [1, 1]),
      ("buyer.olena.melnyk@example.com", ["DEMO-023", "DEMO-038"], [1, 2]),
      ("buyer.dmytro.shev@example.com", ["DEMO-050", "DEMO-016"], [1, 1]),
    ]

    variant_by_sku = {
      variant.sku_code: variant
      for variant in db.query(ProductVariant).filter(ProductVariant.sku_code.like("DEMO-%")).all()
    }
    seeded_count = 0
    for email, skus, quantities in carts_data:
      user = db.query(User).filter(User.email == email).first()
      if not user:
        continue

      existing_cart = db.query(Order).filter(
        Order.user_id == user.id,
        Order.status == "cart",
      ).first()
      if existing_cart:
        continue

      total_price = Decimal("0.00")
      variants = []
      for sku, quantity in zip(skus, quantities):
        variant = variant_by_sku[sku]
        variants.append((variant, quantity))
        total_price += variant.price * quantity

      order = Order(
        user_id=user.id,
        status="cart",
        delivery_price=Decimal("0.00"),
        total_price=total_price,
        created_at=datetime.now(),
      )
      db.add(order)
      db.flush()

      for variant, quantity in variants:
        db.add(OrderItem(
          order_id=order.id,
          product_variant_id=variant.id,
          quantity=quantity,
          price_snapshot=variant.price,
          discount_snapshot=Decimal("0.00"),
          final_price_snapshot=variant.price,
        ))

      seeded_count += 1

    db.commit()
    print(f"--- Seeded {seeded_count} cart orders successfully ---")

  except Exception as e:
    db.rollback()
    print(f"--- Error seeding cart orders: {e} ---")
    raise
  finally:
    db.close()


def seed_product_views():
  """Seed product views for analytics."""
  db = SessionLocal()

  try:
    products = db.query(Product).limit(10).all()
    users = db.query(User).filter(User.email.like("buyer%")).all()

    seeded_count = 0
    for product in products:
      for user in users[:2]:
        view = ProductView(
          product_id=product.id,
          user_id=user.id,
          viewer_key=None,
          viewed_at=datetime.now() - timedelta(hours=1),
        )
        db.add(view)
        seeded_count += 1

    db.commit()
    print(f"--- Seeded {seeded_count} product views successfully ---")

  except Exception as e:
    db.rollback()
    print(f"--- Error seeding product views: {e} ---")
    raise
  finally:
    db.close()


def seed_reviews():
  """Seed product reviews."""
  db = SessionLocal()

  try:
    variants = db.query(ProductVariant).filter(
      ProductVariant.sku_code.like("DEMO-%")).limit(5).all()
    users = db.query(User).filter(User.email.like("buyer%")).all()

    reviews_data = [
      {"rating": 5, "comment": "Excellent product, highly recommended!"},
      {"rating": 4, "comment": "Good quality, fast delivery."},
      {"rating": 5, "comment": "Perfect! Exactly as described."},
      {"rating": 3, "comment": "Average product, could be better."},
      {"rating": 4, "comment": "Very satisfied with my purchase."},
    ]

    seeded_count = 0
    for idx, variant in enumerate(variants):
      for user_idx, user in enumerate(users):
        review = Review(
          user_id=user.id,
          product_variant_id=variant.id,
          rating=reviews_data[(idx + user_idx) % len(reviews_data)]["rating"],
          comment=reviews_data[(idx + user_idx) %
                               len(reviews_data)]["comment"],
          created_at=datetime.now() - timedelta(days=idx + user_idx),
        )
        db.add(review)
        seeded_count += 1

    db.commit()
    print(f"--- Seeded {seeded_count} reviews successfully ---")

  except Exception as e:
    db.rollback()
    print(f"--- Error seeding reviews: {e} ---")
    raise
  finally:
    db.close()


def seed_tables():
  """Seed initial data into the database."""
  seed_roles()
  seed_users()
  seed_user_profiles()
  seed_sellers()
  seed_categories()
  seed_features()
  seed_products()
  seed_product_pictures()
  seed_discounts()
  seed_cart_orders()
  seed_product_views()
  seed_reviews()


def delete_all_data():
  """Delete all data from the database."""
  db = SessionLocal()

  try:
    for table in reversed(Base.metadata.sorted_tables):
      print(f"Deleting data from table: {table.name}")
      db.execute(table.delete())
    db.commit()
    print("--- All data deleted successfully ---")
  except Exception as e:
    db.rollback()
    print(f"--- Error deleting data: {e} ---")
    raise
  finally:
    db.close()
