from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserBase(BaseModel):
    full_name: str = Field(min_length=3, max_length=255)
    email: EmailStr
    role: UserRole = UserRole.READER


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=128)


class UserUpdate(BaseModel):
    full_name: str = Field(min_length=3, max_length=255)
    email: EmailStr
    role: UserRole
    password: str | None = Field(default=None, min_length=6, max_length=128)


class UserRead(UserBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
