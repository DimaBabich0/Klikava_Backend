from importlib.metadata.diagnose import inspect
from app.database import engine, SessionLocal
from app.models import Base, Role, User
from app.auth import hash_password


def init_db():
  """Initialize database schema"""
  Base.metadata.create_all(bind=engine)
  print("--- Database tables created ---")


def seed_roles():
  """Seed default roles into the database"""
  db = SessionLocal()

  try:
    # Check if roles already exist
    existing_roles = db.query(Role).count()
    if existing_roles > 0:
      print("--- Roles already seeded, skipping... ---")
      return

    # Define default roles
    roles_data = [
      {
        "name": "ADMIN",
        "description": "Administrator with full system access"
      },
      {
        "name": "MODERATOR",
        "description": "Moderator with moderation capabilities"
      },
      {
        "name": "BUYER",
        "description": "Regular buyer user"
      }
    ]

    # Create roles
    for role_data in roles_data:
      role = Role(
        name=role_data["name"],
        description=role_data["description"]
      )
      db.add(role)

    db.commit()
    print(f"--- Seeded {len(roles_data)} roles successfully ---")

  except Exception as e:
    db.rollback()
    print(f"--- Error seeding roles: {e} ---")
    raise
  finally:
    db.close()


def seed_admin_user():
  """Seed a default admin user"""
  db = SessionLocal()

  try:
    # Check if admin already exists
    admin = db.query(User).filter(User.username == "admin").first()
    if admin:
      print("--- Admin user already exists, skipping... ---")
      return

    # Get ADMIN role
    admin_role = db.query(Role).filter(Role.name == "ADMIN").first()
    if not admin_role:
      print("--- ADMIN role not found. Run seed_roles() first. ---")
      return

    # Create admin user
    password_hash, password_salt = hash_password("admin123")

    admin_user = User(
      username="admin",
      name="Administrator",
      email="admin@example.com",
      password_hash=password_hash,
      password_salt=password_salt,
      status="active"
    )

    admin_user.roles.append(admin_role)

    db.add(admin_user)
    db.commit()

    print("--- Admin user created successfully ---")
    print("Username: admin")
    print("Password: admin123")
    print("Email: admin@example.com")

  except Exception as e:
    db.rollback()
    print(f"--- Error creating admin user: {e} ---")
    raise
  finally:
    db.close()


def seed_tables():
  """Seed initial data into the database"""
  seed_roles()
  seed_admin_user()


def delete_all_data():
  """Delete all data from the database"""
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
