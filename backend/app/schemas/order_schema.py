from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from datetime import datetime

# Sistemde geçerli sipariş durumları
ORDER_STATUSES = ("Onay Bekliyor", "Hazırlanıyor", "Kargolandı", "Tamamlandı", "İptal")
OrderStatus = Literal["Onay Bekliyor", "Hazırlanıyor", "Kargolandı", "Tamamlandı", "İptal"]


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    customer_name: Optional[str] = Field(default="Misafir Müşteri", max_length=100)
    payment_method: Optional[str] = Field(default="Kredi Kartı", max_length=50)
    items: List[OrderItemCreate] = Field(min_length=1)
    note: Optional[str] = None


class OrderStatusUpdate(BaseModel):
    order_status: OrderStatus


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    total_price: float

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: int
    order_code: str
    customer_name: str
    total_price: float
    payment_method: str
    payment_status: str
    order_status: str
    note: Optional[str]
    created_at: datetime
    items: List[OrderItemResponse] = []

    class Config:
        from_attributes = True
