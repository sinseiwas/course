from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import add_flash, get_current_user, require_role, template_context
from app.models.borrowing import Borrowing
from app.models.order import OrderStatus
from app.models.user import User, UserRole
from app.response import wants_json
from app.schemas.order import OrderRead
from app.services import books as book_service
from app.services import orders as order_service
from app.templating import templates


router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("")
def list_orders(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    orders = db.scalars(order_service.list_orders_stmt(current_user)).unique().all()
    active_pairs = {
        (user_id, book_id)
        for user_id, book_id in db.execute(
            select(Borrowing.user_id, Borrowing.book_id).where(Borrowing.return_date.is_(None))
        ).all()
    }
    for order in orders:
        order.has_active_borrowing = (order.user_id, order.book_id) in active_pairs
    if wants_json(request):
        return [OrderRead.model_validate(order) for order in orders]
    return templates.TemplateResponse(request, "orders.html", template_context(request, current_user, orders=orders))


@router.post("")
async def create_order(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    form = await request.form()
    book_id = int(request.query_params.get("book_id") or form.get("book_id") or 0)
    if not book_id:
        raise HTTPException(status_code=422, detail="book_id is required")
    book = book_service.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    try:
        order = order_service.create_order(db, current_user, book)
    except ValueError as exc:
        if wants_json(request):
            return JSONResponse({"detail": str(exc)}, status_code=400)
        add_flash(request, "error", str(exc))
        return RedirectResponse(url=f"/books/{book_id}", status_code=303)
    if wants_json(request):
        return JSONResponse(OrderRead.model_validate(order).model_dump(mode="json"), status_code=201)
    add_flash(request, "success", "Заказ создан")
    return RedirectResponse(url="/orders", status_code=303)


def _get_order_or_404(db: Session, order_id: int):
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.post("/{order_id}/approve")
def approve_order(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.LIBRARIAN, UserRole.ADMIN)),
):
    order = _get_order_or_404(db, order_id)
    try:
        order = order_service.change_order_status(db, order, OrderStatus.APPROVED)
    except ValueError as exc:
        return JSONResponse({"detail": str(exc)}, status_code=400) if wants_json(request) else RedirectResponse(url="/orders", status_code=303)
    if wants_json(request):
        return OrderRead.model_validate(order)
    add_flash(request, "success", "Заказ подтвержден")
    return RedirectResponse(url="/orders", status_code=303)


@router.post("/{order_id}/reject")
def reject_order(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.LIBRARIAN, UserRole.ADMIN)),
):
    order = _get_order_or_404(db, order_id)
    try:
        order = order_service.change_order_status(db, order, OrderStatus.REJECTED)
    except ValueError as exc:
        if wants_json(request):
            return JSONResponse({"detail": str(exc)}, status_code=400)
        add_flash(request, "error", str(exc))
        return RedirectResponse(url="/orders", status_code=303)
    if wants_json(request):
        return OrderRead.model_validate(order)
    add_flash(request, "success", "Заказ отклонен")
    return RedirectResponse(url="/orders", status_code=303)


@router.post("/{order_id}/cancel")
def cancel_order(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = _get_order_or_404(db, order_id)
    try:
        order = order_service.cancel_order(db, order, current_user)
    except ValueError as exc:
        if wants_json(request):
            return JSONResponse({"detail": str(exc)}, status_code=400)
        add_flash(request, "error", str(exc))
        return RedirectResponse(url="/orders", status_code=303)
    if wants_json(request):
        return OrderRead.model_validate(order)
    add_flash(request, "success", "Заказ отменен")
    return RedirectResponse(url="/orders", status_code=303)
