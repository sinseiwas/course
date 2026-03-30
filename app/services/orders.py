from sqlalchemy import Select, and_, select
from sqlalchemy.orm import Session, joinedload

from app.models.book import Book
from app.models.order import Order, OrderStatus
from app.models.user import User, UserRole


ACTIVE_ORDER_STATUSES = (OrderStatus.PENDING, OrderStatus.APPROVED)


def list_orders_stmt(current_user: User) -> Select[tuple[Order]]:
    stmt = select(Order).options(joinedload(Order.book), joinedload(Order.user)).order_by(Order.order_date.desc())
    if current_user.role == UserRole.READER:
        stmt = stmt.where(Order.user_id == current_user.id)
    return stmt


def get_order(db: Session, order_id: int) -> Order | None:
    return db.scalar(
        select(Order)
        .options(joinedload(Order.book), joinedload(Order.user))
        .where(Order.id == order_id)
    )


def create_order(db: Session, user: User, book: Book) -> Order:
    existing = db.scalar(
        select(Order).where(
            and_(
                Order.user_id == user.id,
                Order.book_id == book.id,
                Order.status.in_(ACTIVE_ORDER_STATUSES),
            )
        )
    )
    if existing:
        raise ValueError("You already have an active order for this book")

    order = Order(user_id=user.id, book_id=book.id, status=OrderStatus.PENDING)
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def change_order_status(db: Session, order: Order, status: OrderStatus) -> Order:
    if order.status not in {OrderStatus.PENDING, OrderStatus.APPROVED}:
        raise ValueError("Order status cannot be changed anymore")
    order.status = status
    db.commit()
    db.refresh(order)
    return order


def cancel_order(db: Session, order: Order, user: User) -> Order:
    if order.user_id != user.id and user.role == UserRole.READER:
        raise ValueError("You cannot cancel another user's order")
    if order.status != OrderStatus.PENDING:
        raise ValueError("Only pending orders can be cancelled")
    order.status = OrderStatus.CANCELLED
    db.commit()
    db.refresh(order)
    return order
