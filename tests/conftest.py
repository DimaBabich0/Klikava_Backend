from datetime import datetime

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.services.access_manager as access_manager_module
from app.database import Base, get_db
from app.models import Role, User, UserRoles
from app.routers.users import router as users_router
from app.services.access_manager import AccessManager
from app.services.auth import create_token, hash_password


SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
  SQLALCHEMY_DATABASE_URL,
  connect_args={"check_same_thread": False},
  poolclass=StaticPool,
  future=True,
)
TestingSessionLocal = sessionmaker(
  autocommit=False,
  autoflush=False,
  expire_on_commit=False,
  bind=engine,
)


@pytest.fixture()
def db_session():
  Base.metadata.drop_all(bind=engine)
  Base.metadata.create_all(bind=engine)
  session = TestingSessionLocal()

  try:
    seed_auth_data(session)
    yield session
  finally:
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(monkeypatch, db_session):
  monkeypatch.setattr(access_manager_module, "DEBUG_MODE", "false")

  app = FastAPI()
  app.middleware("http")(AccessManager.verify_request)
  app.include_router(users_router)

  @app.get("/admin-only")
  def admin_only(current_user: User = Depends(AccessManager.require_role("ADMIN"))):
    return {"user_id": current_user.id}

  def override_get_db():
    yield db_session

  app.dependency_overrides[get_db] = override_get_db

  with TestClient(app) as test_client:
    yield test_client

  app.dependency_overrides.clear()


def seed_auth_data(db):
  roles = {
    name: Role(name=name, description=f"{name.title()} role")
    for name in ("BUYER", "ADMIN", "MODERATOR", "SELLER")
  }
  db.add_all(roles.values())
  db.flush()

  create_test_user(db, "buyer", "buyer@example.com", ["BUYER"])
  create_test_user(db, "other", "other@example.com", ["BUYER"])
  create_test_user(db, "admin", "admin@example.com", ["ADMIN"])
  create_test_user(db, "moderator", "moderator@example.com", ["MODERATOR"])
  create_test_user(db, "seller", "seller@example.com", ["SELLER"])
  create_test_user(db, "banned", "banned@example.com", ["BUYER"], status="banned")
  create_test_user(db, "deleted", "deleted@example.com", ["BUYER"], deleted=True)

  db.commit()


def create_test_user(
  db,
  login: str,
  email: str,
  role_names: list[str],
  status: str = "active",
  deleted: bool = False,
) -> User:
  user = User(name=login.title(), email=email)
  db.add(user)
  db.flush()

  for index, role_name in enumerate(role_names):
    password_hash, password_salt = hash_password("password123")
    role = db.query(Role).filter(Role.name == role_name).one()
    db.add(
      UserRoles(
        user_id=user.id,
        role_id=role.id,
        login=login if index == 0 else f"{login}_{role_name.lower()}",
        password_hash=password_hash,
        password_salt=password_salt,
        status=status,
        deleted_at=datetime.utcnow() if deleted else None,
      )
    )

  db.flush()
  db.refresh(user)
  return user


def get_user(db, login: str) -> User:
  return (
    db.query(User)
    .join(UserRoles)
    .filter(UserRoles.login == login)
    .one()
  )


def auth_headers(user: User, expires_delta=None) -> dict[str, str]:
  token = create_token(
    {
      "sub": str(user.id),
      "roles": [role.name for role in user.roles],
    },
    expires_delta=expires_delta,
  )
  return {"Authorization": f"Bearer {token}"}
