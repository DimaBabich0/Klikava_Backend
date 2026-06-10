from sqlalchemy.orm import Session
from app.models import User, Role, UserRoles
from app.schemas import UserCreate, UserUpdate
from app.services.auth import hash_password, verify_password


def get_user_by_id(db: Session, user_id: int):
  return db.query(User).filter(User.id == user_id).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
  return db.query(User).offset(skip).limit(limit).all()


def get_users_count(db: Session):
  return db.query(User).count()


def get_user_by_email(db: Session, email: str):
  return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str):
  return get_user_by_login(db, username)


def get_user_by_login(db: Session, login: str):
  user_role = db.query(UserRoles).filter(UserRoles.login == login).first()
  if not user_role:
    return None
  return user_role.user


def get_user_role_by_login(db: Session, login: str):
  return db.query(UserRoles).filter(UserRoles.login == login).first()


def create_user(db: Session, user: UserCreate):
  if get_user_by_email(db, user.email):
    raise ValueError("Email already exists")

  if get_user_role_by_login(db, user.login):
    raise ValueError("Login already exists")

  buyer_role = db.query(Role).filter(Role.name == "BUYER").first()
  if not buyer_role:
    raise ValueError("Default BUYER role not found")

  password_hash, password_salt = hash_password(user.password)

  db_user = User(
    name=user.name,
    email=user.email,
    phone_number=user.phone_number,
    birthday=user.birthday,
    avatar_url=user.avatar_url
  )

  db_user_role = UserRoles(
    user=db_user,
    role=buyer_role,
    login=user.login,
    password_hash=password_hash,
    password_salt=password_salt,
    status="active"
  )

  db.add(db_user)
  db.add(db_user_role)
  db.commit()
  db.refresh(db_user)
  return db_user


def update_user(db: Session, db_user: User, user_data: UserUpdate):
  update_data = user_data.model_dump(exclude_unset=True)

  new_email = update_data.get("email")
  if new_email and new_email != db_user.email:
    existing_user = get_user_by_email(db, new_email)
    if existing_user and existing_user.id != db_user.id:
      raise ValueError("Email already exists")
    db_user.email = new_email

  if "phone_number" in update_data:
    new_phone_number = update_data["phone_number"]
    if new_phone_number and new_phone_number != db_user.phone_number:
      existing_user = (
        db.query(User)
        .filter(User.phone_number == new_phone_number, User.id != db_user.id)
        .first()
      )
      if existing_user:
        raise ValueError("Phone number already exists")
    db_user.phone_number = new_phone_number

  if "name" in update_data:
    db_user.name = update_data["name"]

  if "birthday" in update_data:
    db_user.birthday = update_data["birthday"]

  if "avatar_url" in update_data:
    db_user.avatar_url = update_data["avatar_url"]

  if "password" in update_data:
    password_hash, password_salt = hash_password(update_data["password"])
    for user_role in db_user.user_roles:
      if not user_role.is_deleted():
        user_role.password_hash = password_hash
        user_role.password_salt = password_salt

  db.commit()
  db.refresh(db_user)
  return db_user


def ban_user(db: Session, db_user: User):
  for user_role in db_user.user_roles:
    if not user_role.is_deleted():
      user_role.status = "banned"

  db.commit()
  db.refresh(db_user)
  return db_user


def authenticate_user(
    db: Session,
    login_email: str,
    password: str
  ):
  if "@" in login_email:
    user_role = get_user_by_email(db, login_email)
    if user_role:
      login_email = user_role.user_roles[0].login
  user_role = get_user_role_by_login(db, login_email)
  if not user_role or user_role.is_deleted() or not user_role.is_active():
    return False, None

  is_valid = verify_password(
    password,
    user_role.password_hash,
    user_role.password_salt
  )
  return is_valid, user_role.user
