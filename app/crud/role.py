from sqlalchemy.orm import Session
from app.models import Role, UserRoles
from app.schemas.role import RoleCreate, RoleUpdate
from app.services.auth import hash_password


def get_role_by_id(db: Session, role_id: int):
  return db.query(Role).filter(Role.id == role_id).first()


def get_role_by_name(db: Session, name: str):
  return db.query(Role).filter(Role.name == name).first()


def get_roles(db: Session, skip: int = 0, limit: int = 100):
  return db.query(Role).offset(skip).limit(limit).all()


def create_role(db: Session, role: RoleCreate):
  if get_role_by_name(db, role.name):
    raise ValueError("Role already exists")

  db_role = Role(
    name=role.name,
    description=role.description,
    create_level=role.create_level,
    read_level=role.read_level,
    update_level=role.update_level,
    deleted_level=role.deleted_level
  )
  db.add(db_role)
  db.commit()
  db.refresh(db_role)
  return db_role


def assign_role_to_user(db: Session, user_id: int, role_name: str, login: str, password: str):
  from app.models import User
  user = db.query(User).filter(User.id == user_id).first()
  role = get_role_by_name(db, role_name)
  if not user or not role:
    raise ValueError("User or role not found")

  existing_user_role = db.query(UserRoles).filter(
    UserRoles.user_id == user_id,
    UserRoles.role_id == role.id
  ).first()
  if existing_user_role:
    raise ValueError("User already has this role")

  if db.query(UserRoles).filter(UserRoles.login == login).first():
    raise ValueError("Login already exists")

  password_hash, password_salt = hash_password(password)
  user_role = UserRoles(
    user=user,
    role=role,
    login=login,
    password_hash=password_hash,
    password_salt=password_salt,
    status="active"
  )
  db.add(user_role)
  db.commit()
  db.refresh(user)
  return user


def remove_role_from_user(db: Session, user_id: int, role_name: str):
  from app.models import User
  user = db.query(User).filter(User.id == user_id).first()
  role = get_role_by_name(db, role_name)
  if not user or not role:
    raise ValueError("User or role not found")

  user_role = db.query(UserRoles).filter(
    UserRoles.user_id == user_id,
    UserRoles.role_id == role.id
  ).first()
  if not user_role:
    raise ValueError("User does not have this role")

  db.delete(user_role)
  db.commit()
  db.refresh(user)
  return user


def delete_role(db: Session, role_id: int):
  role = get_role_by_id(db, role_id)
  if not role:
    raise ValueError("Role not found")
  db.delete(role)
  db.commit()


def update_role(db: Session, role: Role, role_data: RoleUpdate):
  for field, value in role_data.model_dump(exclude_unset=True).items():
    if field == "name" and value != role.name:
      if get_role_by_name(db, value):
        raise ValueError("Role with this name already exists")
    setattr(role, field, value)
  db.commit()
  db.refresh(role)
  return role


def delete_role(db: Session, role: Role):  # принимает объект, не id
  from datetime import datetime
  role.deleted_at = datetime.now()
  db.commit()
  db.refresh(role)
  return role
