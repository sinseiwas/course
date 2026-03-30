from pathlib import Path
import os

from pydantic import BaseModel


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "Library Information System")
    secret_key: str = os.getenv("SECRET_KEY", "change-me-in-production")
    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'library.db'}")
    session_cookie: str = os.getenv("SESSION_COOKIE", "library_session")
    borrow_days: int = int(os.getenv("BORROW_DAYS", "14"))


settings = Settings()
