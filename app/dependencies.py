from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.user import User, UserRole


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/auth/login"})
    user = db.get(User, user_id)
    if not user:
        request.session.clear()
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/auth/login"})
    return user


def require_role(*roles: UserRole) -> Callable:
    def wrapper(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return current_user

    return wrapper


def add_flash(request: Request, level: str, message: str) -> None:
    messages = request.session.setdefault("_flash_messages", [])
    messages.append({"level": level, "text": message})
    request.session["_flash_messages"] = messages


def template_context(request: Request, current_user: User | None = None, **extra: object) -> dict[str, object]:
    messages = request.session.pop("_flash_messages", [])
    return {
        "request": request,
        "current_user": current_user,
        "flash_messages": messages,
        **extra,
    }
