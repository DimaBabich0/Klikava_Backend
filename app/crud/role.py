from sqlalchemy.orm import Session
from app.models import Role
from app.schemas.role import RoleCreate


def get_role_by_id(db: Session, role_id: int):
  return db.query(Role).filter(Role.id == role_id).first()


def get_role_by_name(db: Session, name: str):
  return db.query(Role).filter(Role.name == name).first()


def get_roles(db: Session, skip: int = 0, limit: int = 100):
  return db.query(Role).offset(skip).limit(limit).all()


def create_role(db: Session, role: RoleCreate):
  if get_role_by_name(db, role.name):
    raise ValueError("Role already exists")

  db_role = Role(name=role.name, description=role.description)
  db.add(db_role)
  db.commit()
  db.refresh(db_role)
  return db_role


def assign_role_to_user(db: Session, user_id: int, role_name: str):
  from app.models import User
  user = db.query(User).filter(User.id == user_id).first()
  role = get_role_by_name(db, role_name)
  if not user or not role:
    raise ValueError("User or role not found")
  if role not in user.roles:
    user.roles.append(role)
    db.commit()
  return user


def remove_role_from_user(db: Session, user_id: int, role_id: int):
  from app.models import User
  user = db.query(User).filter(User.id == user_id).first()
  role = get_role_by_id(db, role_id)
  if not user or not role:
    raise ValueError("User or role not found")
  if role in user.roles:
    user.roles.remove(role)
    db.commit()
  return user

def delete_role(db: Session, role_id: int):
  role = get_role_by_id(db, role_id)
  if not role:
    raise ValueError("Role not found")
  db.delete(role)
  db.commit()
