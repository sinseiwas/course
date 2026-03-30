from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.order import OrderStatus


class OrderCreate(BaseModel):
    book_id: int


class OrderRead(BaseModel):
    id: int
    user_id: int
    book_id: int
    order_date: datetime
    status: OrderStatus

    model_config = ConfigDict(from_attributes=True)
