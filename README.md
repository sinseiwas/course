# Автоматизированная информационная система библиотеки учебного заведения

Демонстрационный учебный проект на FastAPI, который автоматизирует базовые процессы библиотеки: учет пользователей, каталог книг, поиск литературы, оформление заказов, операции выдачи и возврата, контроль экземпляров и простую статистику.

## Стек технологий

- Python 3.11+
- FastAPI
- SQLAlchemy 2.x
- SQLite
- Jinja2 Templates
- Pydantic
- Uvicorn
- Passlib + bcrypt
- pytest

## Возможности системы

- роли `reader`, `librarian`, `admin`
- вход по email и паролю
- каталог книг и карточка книги
- поиск по названию, автору, категории и году
- CRUD книг
- CRUD пользователей
- создание заказов и их обработка
- выдача и возврат литературы
- просмотр истории выдач
- автоматическая отметка просроченных выдач
- страница статистики для администратора
- REST API и веб-интерфейс на одних и тех же маршрутах

## Роли

- `reader`:
  просмотр каталога, поиск, создание заказов, просмотр своих заказов и выдач
- `librarian`:
  все возможности читателя, просмотр пользователей, подтверждение или отклонение заказов, оформление выдачи и возврата
- `admin`:
  все возможности библиотекаря, управление пользователями и книгами, просмотр статистики

## Структура проекта

```text
library_system/
├── app/
│   ├── main.py
│   ├── db.py
│   ├── models/
│   │   ├── user.py
│   │   ├── book.py
│   │   ├── order.py
│   │   └── borrowing.py
│   ├── schemas/
│   │   ├── user.py
│   │   ├── book.py
│   │   ├── order.py
│   │   └── borrowing.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── books.py
│   │   ├── orders.py
│   │   ├── borrowings.py
│   │   └── dashboard.py
│   ├── services/
│   │   ├── auth.py
│   │   ├── books.py
│   │   ├── orders.py
│   │   └── borrowings.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── books.html
│   │   ├── book_detail.html
│   │   ├── orders.html
│   │   ├── borrowings.html
│   │   ├── users.html
│   │   └── dashboard.html
│   └── static/
│       └── styles.css
├── tests/
│   ├── test_auth.py
│   ├── test_books.py
│   └── test_orders.py
├── init_db.py
├── seed_data.py
├── requirements.txt
├── README.md
└── .env.example
```

## Установка и запуск

1. Создайте виртуальное окружение:

```bash
python -m venv .venv
```

2. Активируйте его.

Linux/macOS:

```bash
source .venv/bin/activate
```

Windows:

```bat
.venv\Scripts\activate
```

3. Установите зависимости:

```bash
pip install -r requirements.txt
```

4. Создайте базу данных:

```bash
python init_db.py
```

5. Заполните базу тестовыми данными:

```bash
python seed_data.py
```

6. Запустите сервер:

```bash
uvicorn app.main:app --reload
```

7. Откройте в браузере:

```text
http://127.0.0.1:8000
```

## Тестовые учетные записи

- Администратор:
  `admin@library.local` / `admin123`
- Библиотекарь:
  `librarian@library.local` / `librarian123`
- Читатель 1:
  `reader1@library.local` / `reader123`
- Читатель 2:
  `reader2@library.local` / `reader123`

## Пример запуска

```bash
python init_db.py
python seed_data.py
uvicorn app.main:app --reload
```

## Основные маршруты

- `POST /auth/login`
- `GET /auth/logout`
- `GET /books`
- `GET /books/{book_id}`
- `GET /books/search`
- `POST /books`
- `PUT /books/{book_id}`
- `DELETE /books/{book_id}`
- `GET /orders`
- `POST /orders`
- `POST /orders/{order_id}/approve`
- `POST /orders/{order_id}/reject`
- `POST /orders/{order_id}/cancel`
- `GET /borrowings`
- `POST /borrowings`
- `POST /borrowings/{borrowing_id}/return`
- `GET /users`
- `POST /users`
- `PUT /users/{user_id}`
- `DELETE /users/{user_id}`
- `GET /dashboard`

## Тесты

Запуск:

```bash
pytest
```

## Примечания

- База данных SQLite создается локально в файле `library.db`.
- Регистрация через публичную форму не реализована намеренно: пользователи создаются seed-скриптом или через админ-панель.
- Для проверки API можно использовать параметр `?format=json` или заголовок `Accept: application/json`.
