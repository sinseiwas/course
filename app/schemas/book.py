from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BookBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    author: str = Field(min_length=1, max_length=255)
    year: int = Field(ge=0, le=2100)
    category: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=4000)
    total_copies: int = Field(ge=1, le=999)
    available_copies: int = Field(ge=0, le=999)

    @model_validator(mode="after")
    def validate_copies(self) -> "BookBase":
        if self.available_copies > self.total_copies:
            raise ValueError("Available copies cannot exceed total copies")
        return self


class BookCreate(BookBase):
    pass


class BookUpdate(BookBase):
    pass


class BookRead(BookBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
