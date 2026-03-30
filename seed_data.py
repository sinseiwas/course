"""Seed the local SQLite database with demo data."""

from datetime import date, timedelta

from sqlalchemy import select

from app.db import SessionLocal
from app.models import Book, Borrowing, Order, User
from app.models.borrowing import BorrowingStatus
from app.models.order import OrderStatus
from app.models.user import UserRole
from app.services.auth import hash_password


BOOKS = [
    ("Базы данных", "К. Дж. Дейт", 2019, "Информатика"),
    ("Чистый код", "Роберт Мартин", 2018, "Программирование"),
    ("Алгоритмы", "Томас Кормен", 2020, "Алгоритмы"),
    ("Операционные системы", "Эндрю Таненбаум", 2017, "Информатика"),
    ("Компьютерные сети", "Эндрю Таненбаум", 2016, "Сети"),
    ("Искусственный интеллект", "Стюарт Рассел", 2021, "AI"),
    ("Python для анализа данных", "Уэс Маккинни", 2022, "Python"),
    ("Теория вероятностей", "А. Н. Колмогоров", 2014, "Математика"),
    ("Линейная алгебра", "Гилберт Странг", 2015, "Математика"),
    ("Инженерия программного обеспечения", "Иэн Соммервилл", 2019, "Разработка"),
]


def main() -> None:
    db = SessionLocal()
    try:
        if db.scalar(select(User).limit(1)):
            print("Database already contains data. Seed skipped.")
            return

        admin = User(
            full_name="Администратор системы",
            email="admin@library.local",
            password_hash=hash_password("admin123"),
            role=UserRole.ADMIN,
        )
        librarian = User(
            full_name="Мария Библиотекарь",
            email="librarian@library.local",
            password_hash=hash_password("librarian123"),
            role=UserRole.LIBRARIAN,
        )
        reader1 = User(
            full_name="Иван Читатель",
            email="reader1@library.local",
            password_hash=hash_password("reader123"),
            role=UserRole.READER,
        )
        reader2 = User(
            full_name="Анна Студентка",
            email="reader2@library.local",
            password_hash=hash_password("reader123"),
            role=UserRole.READER,
        )
        db.add_all([admin, librarian, reader1, reader2])
        db.flush()

        books = []
        for index, (title, author, year, category) in enumerate(BOOKS, start=1):
            total = 2 if index % 2 == 0 else 3
            available = total - 1 if index in {1, 2, 3} else total
            books.append(
                Book(
                    title=title,
                    author=author,
                    year=year,
                    category=category,
                    description=f"Учебное издание по дисциплине «{category}».",
                    total_copies=total,
                    available_copies=available,
                )
            )
        db.add_all(books)
        db.flush()

        orders = [
            Order(user_id=reader1.id, book_id=books[0].id, status=OrderStatus.APPROVED),
            Order(user_id=reader1.id, book_id=books[1].id, status=OrderStatus.PENDING),
            Order(user_id=reader2.id, book_id=books[2].id, status=OrderStatus.REJECTED),
            Order(user_id=reader2.id, book_id=books[3].id, status=OrderStatus.CANCELLED),
        ]
        db.add_all(orders)
        db.flush()

        borrowings = [
            Borrowing(
                user_id=reader1.id,
                book_id=books[0].id,
                borrow_date=date.today() - timedelta(days=5),
                due_date=date.today() + timedelta(days=9),
                status=BorrowingStatus.ACTIVE,
            ),
            Borrowing(
                user_id=reader2.id,
                book_id=books[2].id,
                borrow_date=date.today() - timedelta(days=21),
                due_date=date.today() - timedelta(days=7),
                status=BorrowingStatus.OVERDUE,
            ),
            Borrowing(
                user_id=reader2.id,
                book_id=books[4].id,
                borrow_date=date.today() - timedelta(days=30),
                due_date=date.today() - timedelta(days=16),
                return_date=date.today() - timedelta(days=10),
                status=BorrowingStatus.RETURNED,
            ),
        ]
        db.add_all(borrowings)
        db.commit()
        print("Seed data created successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
