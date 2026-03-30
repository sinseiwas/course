from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_role, template_context
from app.models.user import UserRole
from app.response import wants_json
from app.services.borrowings import dashboard_stats
from app.templating import templates


router = APIRouter(tags=["dashboard"])


@router.get("/")
def root(request: Request):
    if wants_json(request):
        return {"message": "Library system is running", "open": "/auth/login"}
    return RedirectResponse(url="/auth/login", status_code=303)


@router.get("/dashboard")
def get_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.ADMIN)),
):
    stats = dashboard_stats(db)
    if wants_json(request):
        return stats
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        template_context(request, current_user, stats=stats),
    )
