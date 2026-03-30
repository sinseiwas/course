from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.auth import hash_password


def list_users_stmt() -> Select[tuple[User]]:
    return select(User).order_by(User.created_at.desc())


def get_user(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower().strip()))


def create_user(db: Session, payload: UserCreate) -> User:
    user = User(
        full_name=payload.full_name.strip(),
        email=payload.email.lower().strip(),
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("A user with this email already exists") from exc
    db.refresh(user)
    return user


def update_user(db: Session, user: User, payload: UserUpdate) -> User:
    user.full_name = payload.full_name.strip()
    user.email = payload.email.lower().strip()
    user.role = payload.role
    if payload.password:
        user.password_hash = hash_password(payload.password)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("A user with this email already exists") from exc
    db.refresh(user)
    return user


def delete_user(db: Session, user: User) -> None:
    db.delete(user)
    db.commit()
