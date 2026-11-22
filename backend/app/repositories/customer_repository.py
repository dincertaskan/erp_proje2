from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.erp import Customer, Order
from app.repositories.order_repository import customer_order_filter


class CustomerRepository:
    def __init__(self, db: Session):
        self.db = db

    def _serialize(self, c: Customer) -> dict:
        # Müşterinin iptal edilmemiş siparişlerinin sayısı ve toplam harcaması
        order_stats = self.db.query(
            func.count(Order.id).label("order_count"),
            func.coalesce(func.sum(Order.total_price), 0).label("total_spent")
        ).filter(
            customer_order_filter(c.id, c.name),
            Order.order_status != "İptal"
        ).first()

        return {
            "id": c.id,
            "full_name": c.name,
            "email": c.email,
            "is_active": c.is_active if c.is_active is not None else True,
            "created_at": c.created_at,
            "avatar_url": c.avatar_url,
            "total_orders": order_stats.order_count if order_stats else 0,
            "total_spent": float(order_stats.total_spent) if order_stats else 0.0
        }

    def get_all_customers(self) -> list[dict]:
        customers = self.db.query(Customer).order_by(Customer.id.desc()).all()
        return [self._serialize(c) for c in customers]

    def set_active(self, customer_id: int, is_active: bool) -> Optional[dict]:
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return None
        customer.is_active = is_active
        self.db.commit()
        self.db.refresh(customer)
        return self._serialize(customer)
