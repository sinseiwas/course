"""Create SQLite database tables for the library system."""

from app.db import Base, engine
from app.models import Book, Borrowing, Order, User  # noqa: F401


def main() -> None:
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully.")


if __name__ == "__main__":
    main()
