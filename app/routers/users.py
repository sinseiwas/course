from pydantic import ValidationError

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import add_flash, require_role, template_context
from app.forms import format_validation_error
from app.models.user import UserRole
from app.response import wants_json
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services import users as user_service
from app.templating import templates


router = APIRouter(prefix="/users", tags=["users"])


@router.get("")
def list_users(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.LIBRARIAN, UserRole.ADMIN)),
):
    users = db.scalars(user_service.list_users_stmt()).all()
    if wants_json(request):
        return [UserRead.model_validate(user) for user in users]
    return templates.TemplateResponse(request, "users.html", template_context(request, current_user, users=users))


@router.get("/new")
def new_user_page(
    request: Request,
    current_user=Depends(require_role(UserRole.ADMIN)),
):
    return templates.TemplateResponse(
        request,
        "user_form.html",
        template_context(request, current_user, user=None, action="/users", submit_label="Добавить пользователя"),
    )


@router.post("")
def create_user(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: UserRole = Form(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.ADMIN)),
):
    try:
        payload = UserCreate(full_name=full_name, email=email, password=password, role=role)
        user = user_service.create_user(db, payload)
    except ValidationError as exc:
        if wants_json(request):
            return JSONResponse({"detail": exc.errors()}, status_code=422)
        add_flash(request, "error", format_validation_error(exc))
        return RedirectResponse(url="/users/new", status_code=303)
    except ValueError as exc:
        if wants_json(request):
            return JSONResponse({"detail": str(exc)}, status_code=400)
        add_flash(request, "error", str(exc))
        return RedirectResponse(url="/users/new", status_code=303)
    if wants_json(request):
        return JSONResponse(UserRead.model_validate(user).model_dump(mode="json"), status_code=201)
    add_flash(request, "success", "Пользователь создан")
    return RedirectResponse(url="/users", status_code=303)


@router.get("/{user_id}/edit")
def edit_user_page(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.ADMIN)),
):
    user = user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse(
        request,
        "user_form.html",
        template_context(request, current_user, user=user, action=f"/users/{user.id}", submit_label="Сохранить"),
    )


@router.put("/{user_id}")
@router.post("/{user_id}")
def update_user(
    user_id: int,
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(""),
    role: UserRole = Form(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.ADMIN)),
):
    user = user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        payload = UserUpdate(full_name=full_name, email=email, password=password or None, role=role)
        user = user_service.update_user(db, user, payload)
    except ValidationError as exc:
        if wants_json(request):
            return JSONResponse({"detail": exc.errors()}, status_code=422)
        add_flash(request, "error", format_validation_error(exc))
        return RedirectResponse(url=f"/users/{user_id}/edit", status_code=303)
    except ValueError as exc:
        if wants_json(request):
            return JSONResponse({"detail": str(exc)}, status_code=400)
        add_flash(request, "error", str(exc))
        return RedirectResponse(url=f"/users/{user_id}/edit", status_code=303)
    if wants_json(request):
        return UserRead.model_validate(user)
    add_flash(request, "success", "Пользователь обновлен")
    return RedirectResponse(url="/users", status_code=303)


@router.delete("/{user_id}")
@router.post("/{user_id}/delete")
def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.ADMIN)),
):
    user = user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        message = "Нельзя удалить самого себя"
        if wants_json(request):
            return JSONResponse({"detail": message}, status_code=400)
        add_flash(request, "error", message)
        return RedirectResponse(url="/users", status_code=303)
    user_service.delete_user(db, user)
    if wants_json(request):
        return {"message": "User deleted"}
    add_flash(request, "success", "Пользователь удален")
    return RedirectResponse(url="/users", status_code=303)
