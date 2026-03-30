from datetime import date

from pydantic import BaseModel, ConfigDict

from app.models.borrowing import BorrowingStatus


class BorrowingCreate(BaseModel):
    order_id: int


class BorrowingRead(BaseModel):
    id: int
    user_id: int
    book_id: int
    borrow_date: date
    due_date: date
    return_date: date | None
    status: BorrowingStatus

    model_config = ConfigDict(from_attributes=True)
