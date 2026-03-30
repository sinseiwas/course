from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base, get_db
from app.main import app
from app.models.user import User, UserRole
from app.services.auth import hash_password


SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_library.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture(autouse=True)
def setup_database() -> Generator[None, None, None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def seeded_users(db_session: Session) -> dict[str, User]:
    users = {
        "admin": User(
            full_name="Admin",
            email="admin@test.local",
            password_hash=hash_password("admin123"),
            role=UserRole.ADMIN,
        ),
        "librarian": User(
            full_name="Librarian",
            email="librarian@test.local",
            password_hash=hash_password("librarian123"),
            role=UserRole.LIBRARIAN,
        ),
        "reader": User(
            full_name="Reader",
            email="reader@test.local",
            password_hash=hash_password("reader123"),
            role=UserRole.READER,
        ),
    }
    db_session.add_all(users.values())
    db_session.commit()
    return users
