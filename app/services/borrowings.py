from datetime import date, timedelta

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.models.book import Book
from app.models.borrowing import Borrowing, BorrowingStatus
from app.models.order import Order, OrderStatus
from app.models.user import User, UserRole


def refresh_overdue_statuses(db: Session) -> None:
    today = date.today()
    overdue_items = db.scalars(
        select(Borrowing).where(
            Borrowing.status == BorrowingStatus.ACTIVE,
            Borrowing.return_date.is_(None),
            Borrowing.due_date < today,
        )
    ).all()
    for item in overdue_items:
        item.status = BorrowingStatus.OVERDUE
    if overdue_items:
        db.commit()


def list_borrowings_stmt(current_user: User) -> Select[tuple[Borrowing]]:
    stmt = (
        select(Borrowing)
        .options(joinedload(Borrowing.book), joinedload(Borrowing.user))
        .order_by(Borrowing.borrow_date.desc(), Borrowing.id.desc())
    )
    if current_user.role == UserRole.READER:
        stmt = stmt.where(Borrowing.user_id == current_user.id)
    return stmt


def get_borrowing(db: Session, borrowing_id: int) -> Borrowing | None:
    return db.scalar(
        select(Borrowing)
        .options(joinedload(Borrowing.book), joinedload(Borrowing.user))
        .where(Borrowing.id == borrowing_id)
    )


def create_borrowing_from_order(db: Session, order: Order) -> Borrowing:
    if order.status != OrderStatus.APPROVED:
        raise ValueError("Выдачу можно оформить только для подтвержденного заказа")
    existing = db.scalar(
        select(Borrowing).where(
            Borrowing.user_id == order.user_id,
            Borrowing.book_id == order.book_id,
            Borrowing.return_date.is_(None),
        )
    )
    if existing:
        raise ValueError("По этому заказу уже оформлена активная выдача")

    book = order.book
    if book.available_copies <= 0:
        raise ValueError("Нет доступных экземпляров книги")

    borrowing = Borrowing(
        user_id=order.user_id,
        book_id=order.book_id,
        borrow_date=date.today(),
        due_date=date.today() + timedelta(days=settings.borrow_days),
        status=BorrowingStatus.ACTIVE,
    )
    book.available_copies -= 1
    db.add(borrowing)
    db.commit()
    db.refresh(borrowing)
    return borrowing


def return_borrowing(db: Session, borrowing: Borrowing) -> Borrowing:
    if borrowing.status == BorrowingStatus.RETURNED:
        raise ValueError("Эта книга уже возвращена")

    borrowing.return_date = date.today()
    borrowing.status = BorrowingStatus.RETURNED
    book = db.get(Book, borrowing.book_id)
    if book:
        book.available_copies += 1
    db.commit()
    db.refresh(borrowing)
    return borrowing


def dashboard_stats(db: Session) -> dict[str, object]:
    refresh_overdue_statuses(db)
    popular_books = db.execute(
        select(Book.title, func.count(Borrowing.id).label("borrow_count"))
        .join(Borrowing, Borrowing.book_id == Book.id)
        .group_by(Book.id)
        .order_by(func.count(Borrowing.id).desc(), Book.title.asc())
        .limit(5)
    ).all()

    return {
        "users_count": db.scalar(select(func.count(User.id))) or 0,
        "books_count": db.scalar(select(func.count(Book.id))) or 0,
        "active_orders_count": db.scalar(
            select(func.count(Order.id)).where(Order.status == OrderStatus.PENDING)
        )
        or 0,
        "active_borrowings_count": db.scalar(
            select(func.count(Borrowing.id)).where(Borrowing.status == BorrowingStatus.ACTIVE)
        )
        or 0,
        "overdue_borrowings_count": db.scalar(
            select(func.count(Borrowing.id)).where(Borrowing.status == BorrowingStatus.OVERDUE)
        )
        or 0,
        "popular_books": popular_books,
    }
