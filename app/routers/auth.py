from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import add_flash, get_current_user, template_context
from app.response import wants_json
from app.services.auth import authenticate_user
from app.templating import templates


router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
def login_page(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse(url="/books", status_code=303)
    return templates.TemplateResponse(request, "login.html", template_context(request))


@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, email, password)
    if not user:
        if wants_json(request):
            return JSONResponse({"detail": "Invalid credentials"}, status_code=401)
        add_flash(request, "error", "Неверный email или пароль")
        return RedirectResponse(url="/auth/login", status_code=303)

    request.session["user_id"] = user.id
    if wants_json(request):
        return {"message": "Logged in", "user_id": user.id, "role": user.role.value}
    add_flash(request, "success", "Вход выполнен")
    return RedirectResponse(url="/books", status_code=303)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    if wants_json(request):
        return {"message": "Logged out"}
    return RedirectResponse(url="/auth/login", status_code=303)


@router.get("/me")
def me(current_user=Depends(get_current_user)):
    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "role": current_user.role.value,
    }
