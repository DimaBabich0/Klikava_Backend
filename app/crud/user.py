from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models import User, Role
from app.schemas import UserCreate
from app.auth import hash_password


def get_user_by_id(db: Session, user_id: int):
  return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
  return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str):
  return db.query(User).filter(User.username == username).first()


def create_user(db: Session, user: UserCreate):
  # Check if email or username already exists
  if get_user_by_email(db, user.email):
    raise ValueError("Email already exists")

  if get_user_by_username(db, user.username):
    raise ValueError("Username already exists")

  # Get default BUYER role
  buyer_role = db.query(Role).filter(Role.name == "BUYER").first()
  if not buyer_role:
    raise ValueError("Default BUYER role not found")

  # Hash password with salt
  password_hash, password_salt = hash_password(user.password)

  # Create new user
  db_user = User(
    username=user.username,
    name=user.name,
    email=user.email,
    password_hash=password_hash,
    password_salt=password_salt,
    birthday=user.birthday,
    status="active"
  )

  # Assign BUYER role
  db_user.roles.append(buyer_role)

  db.add(db_user)
  db.commit()
  db.refresh(db_user)
  return db_user


def authenticate_user(
    db: Session,
    email: str,
    password: str
  ):
  user = get_user_by_email(db, email)
  if not user or user.is_deleted():
    return False
  from app.auth import verify_password
  return verify_password(password, user.password_hash, user.password_salt), user
