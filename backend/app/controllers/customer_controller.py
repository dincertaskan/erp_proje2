from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import CurrentUser, require_admin
from app.repositories.customer_repository import CustomerRepository

router = APIRouter(prefix="/customers", tags=["Customers"])


class CustomerStatusUpdate(BaseModel):
    is_active: bool


@router.get("")
def get_customers(db: Session = Depends(get_db), _: CurrentUser = Depends(require_admin)):
    """Sistemdeki tüm müşterileri ve sipariş özetlerini getirir."""
    repo = CustomerRepository(db)
    return repo.get_all_customers()


@router.patch("/{customer_id}/status")
def update_customer_status(
    customer_id: int,
    data: CustomerStatusUpdate,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_admin),
):
    """Müşteri hesabını aktif/pasif yapar. Pasif müşteriler sisteme giriş yapamaz."""
    customer = CustomerRepository(db).set_active(customer_id, data.is_active)
    if not customer:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı.")
    return customer
