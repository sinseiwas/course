from datetime import date, timedelta

from app.models.book import Book
from app.models.borrowing import Borrowing, BorrowingStatus
from app.models.order import Order, OrderStatus


def login(client, email, password):
    client.post("/auth/login", data={"email": email, "password": password})


def test_reader_can_create_order(client, db_session, seeded_users):
    book = Book(
        title="Тестовая книга",
        author="Автор",
        year=2022,
        category="Категория",
        description="Описание",
        total_copies=2,
        available_copies=2,
    )
    db_session.add(book)
    db_session.commit()

    login(client, "reader@test.local", "reader123")
    response = client.post("/orders", params={"book_id": book.id}, follow_redirects=False)
    assert response.status_code == 303

    order = db_session.query(Order).filter(Order.book_id == book.id).first()
    assert order is not None
    assert order.status == OrderStatus.PENDING


def test_librarian_can_approve_order(client, db_session, seeded_users):
    book = Book(
        title="Тестовая книга",
        author="Автор",
        year=2022,
        category="Категория",
        description="Описание",
        total_copies=2,
        available_copies=2,
    )
    db_session.add(book)
    db_session.flush()

    order = Order(user_id=seeded_users["reader"].id, book_id=book.id, status=OrderStatus.PENDING)
    db_session.add(order)
    db_session.commit()

    login(client, "librarian@test.local", "librarian123")
    response = client.post(f"/orders/{order.id}/approve", follow_redirects=False)
    assert response.status_code == 303

    db_session.refresh(order)
    assert order.status == OrderStatus.APPROVED


def test_duplicate_borrowing_redirects_back_to_orders_with_error(client, db_session, seeded_users):
    book = Book(
        title="Выданная книга",
        author="Автор",
        year=2022,
        category="Категория",
        description="Описание",
        total_copies=2,
        available_copies=1,
    )
    db_session.add(book)
    db_session.flush()

    order = Order(user_id=seeded_users["reader"].id, book_id=book.id, status=OrderStatus.APPROVED)
    db_session.add(order)
    db_session.flush()

    borrowing = Borrowing(
        user_id=seeded_users["reader"].id,
        book_id=book.id,
        borrow_date=date.today(),
        due_date=date.today() + timedelta(days=14),
        status=BorrowingStatus.ACTIVE,
    )
    db_session.add(borrowing)
    db_session.commit()

    login(client, "librarian@test.local", "librarian123")
    response = client.post(
        "/borrowings",
        data={"order_id": order.id, "next": "/orders"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/orders"


def test_orders_page_hides_issue_button_for_active_borrowing(client, db_session, seeded_users):
    book = Book(
        title="Уже выданная книга",
        author="Автор",
        year=2022,
        category="Категория",
        description="Описание",
        total_copies=2,
        available_copies=1,
    )
    db_session.add(book)
    db_session.flush()

    order = Order(user_id=seeded_users["reader"].id, book_id=book.id, status=OrderStatus.APPROVED)
    db_session.add(order)
    db_session.flush()

    db_session.add(
        Borrowing(
            user_id=seeded_users["reader"].id,
            book_id=book.id,
            borrow_date=date.today(),
            due_date=date.today() + timedelta(days=14),
            status=BorrowingStatus.ACTIVE,
        )
    )
    db_session.commit()

    login(client, "librarian@test.local", "librarian123")
    response = client.get("/orders")

    assert response.status_code == 200
    assert "Уже выдана" in response.text
    assert 'name="order_id" value="%s"' % order.id not in response.text
