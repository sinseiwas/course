from app.models.book import Book


def login_as_admin(client):
    client.post("/auth/login", data={"email": "admin@test.local", "password": "admin123"})


def test_admin_can_create_book(client, db_session, seeded_users):
    login_as_admin(client)
    response = client.post(
        "/books",
        data={
            "title": "Новая книга",
            "author": "Автор",
            "year": 2024,
            "category": "Тест",
            "description": "Описание",
            "total_copies": 5,
            "available_copies": 5,
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert db_session.query(Book).filter(Book.title == "Новая книга").count() == 1


def test_reader_cannot_open_create_book_page(client, seeded_users):
    client.post("/auth/login", data={"email": "reader@test.local", "password": "reader123"})
    response = client.get("/books/new")
    assert response.status_code == 403
