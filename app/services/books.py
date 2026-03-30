from sqlalchemy import Select, and_, select
from sqlalchemy.orm import Session

from app.models.book import Book
from app.schemas.book import BookCreate, BookUpdate


def build_book_query(
    title: str | None = None,
    author: str | None = None,
    category: str | None = None,
    year: int | None = None,
) -> Select[tuple[Book]]:
    filters = []
    if title:
        filters.append(Book.title.ilike(f"%{title.strip()}%"))
    if author:
        filters.append(Book.author.ilike(f"%{author.strip()}%"))
    if category:
        filters.append(Book.category.ilike(f"%{category.strip()}%"))
    if year:
        filters.append(Book.year == year)

    stmt = select(Book)
    if filters:
        stmt = stmt.where(and_(*filters))
    return stmt.order_by(Book.title.asc())


def get_book(db: Session, book_id: int) -> Book | None:
    return db.get(Book, book_id)


def create_book(db: Session, payload: BookCreate) -> Book:
    book = Book(**payload.model_dump())
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def update_book(db: Session, book: Book, payload: BookUpdate) -> Book:
    for field, value in payload.model_dump().items():
        setattr(book, field, value)
    db.commit()
    db.refresh(book)
    return book


def delete_book(db: Session, book: Book) -> None:
    db.delete(book)
    db.commit()
