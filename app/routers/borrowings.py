from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import add_flash, get_current_user, require_role, template_context
from app.models.user import User, UserRole
from app.response import wants_json
from app.schemas.borrowing import BorrowingRead
from app.services import borrowings as borrowing_service
from app.services import orders as order_service
from app.templating import templates


router = APIRouter(prefix="/borrowings", tags=["borrowings"])


@router.get("")
def list_borrowings(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    borrowing_service.refresh_overdue_statuses(db)
    borrowings = db.scalars(borrowing_service.list_borrowings_stmt(current_user)).unique().all()
    if wants_json(request):
        return [BorrowingRead.model_validate(item) for item in borrowings]
    return templates.TemplateResponse(
        request,
        "borrowings.html",
        template_context(request, current_user, borrowings=borrowings),
    )


@router.post("")
async def create_borrowing(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.LIBRARIAN, UserRole.ADMIN)),
):
    form = await request.form()
    order_id = int(request.query_params.get("order_id") or form.get("order_id") or 0)
    next_url = request.query_params.get("next") or form.get("next") or "/borrowings"
    if not order_id:
        raise HTTPException(status_code=422, detail="order_id is required")
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    try:
        borrowing = borrowing_service.create_borrowing_from_order(db, order)
    except ValueError as exc:
        if wants_json(request):
            return JSONResponse({"detail": str(exc)}, status_code=400)
        add_flash(request, "error", str(exc))
        return RedirectResponse(url=str(next_url), status_code=303)
    if wants_json(request):
        return JSONResponse(BorrowingRead.model_validate(borrowing).model_dump(mode="json"), status_code=201)
    add_flash(request, "success", "Выдача оформлена")
    return RedirectResponse(url=str(next_url), status_code=303)


@router.post("/{borrowing_id}/return")
def return_borrowing(
    borrowing_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.LIBRARIAN, UserRole.ADMIN)),
):
    borrowing = borrowing_service.get_borrowing(db, borrowing_id)
    if not borrowing:
        raise HTTPException(status_code=404, detail="Borrowing not found")
    try:
        borrowing = borrowing_service.return_borrowing(db, borrowing)
    except ValueError as exc:
        if wants_json(request):
            return JSONResponse({"detail": str(exc)}, status_code=400)
        add_flash(request, "error", str(exc))
        return RedirectResponse(url="/borrowings", status_code=303)
    if wants_json(request):
        return BorrowingRead.model_validate(borrowing)
    add_flash(request, "success", "Возврат оформлен")
    return RedirectResponse(url="/borrowings", status_code=303)
