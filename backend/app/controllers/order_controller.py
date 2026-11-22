from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.security import CurrentUser, get_current_user
from app.schemas.order_schema import ORDER_STATUSES, OrderCreate, OrderStatusUpdate
from app.repositories.order_repository import OrderRepository
from app.repositories.settings_repository import SettingsRepository

router = APIRouter(prefix="/orders", tags=["Orders"])


def _is_customer_order(order, current_user: CurrentUser) -> bool:
    if order.customer_id is not None:
        return order.customer_id == current_user.id
    # customer_id sütunu eklenmeden önce verilmiş eski siparişler
    return order.customer_name == current_user.full_name


@router.get("")
def get_orders(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Admin tüm siparişleri, müşteri yalnızca kendi siparişlerini görür."""
    repo = OrderRepository(db)
    if current_user.is_admin:
        return repo.get_all_orders()
    return repo.get_customer_orders(current_user.id, current_user.full_name)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_order(
    data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Yeni bir sipariş oluşturur ve stok miktarını düşer."""
    repo = OrderRepository(db)

    customer_id = None
    if not current_user.is_admin:
        if not SettingsRepository(db).get().accept_orders:
            raise HTTPException(
                status_code=403,
                detail="Mağazamız şu anda sipariş kabul etmiyor. Lütfen daha sonra tekrar deneyin.",
            )
        # Müşteri yalnızca kendi adına sipariş verebilir
        data = data.model_copy(update={"customer_name": current_user.full_name})
        customer_id = current_user.id

    try:
        return repo.create_order(data, user_name=current_user.full_name, customer_id=customer_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print("SİPARİŞ OLUŞTURMA HATASI:", str(e))
        raise HTTPException(status_code=500, detail="Sipariş oluşturulurken bir hata meydana geldi.")


# Hem PUT hem PATCH isteklerini ve hem Body hem Query Parametresini destekler
@router.patch("/{order_id}/status")
@router.put("/{order_id}/status")
def update_order_status(
    order_id: int,
    data: Optional[OrderStatusUpdate] = None,
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Sipariş durumunu günceller ("Onay Bekliyor", "Hazırlanıyor", "Kargolandı", "Tamamlandı", "İptal").
    'İptal' durumunda stoku iade eder ve ödemeyi 'İade Edildi' yapar.
    'İptal' veya 'Tamamlandı' olan siparişlerin tekrar değiştirilmesini engeller.
    Müşteriler yalnızca kendi siparişlerini, onay beklerken iptal edebilir.
    """
    new_status = data.order_status if data else status
    if not new_status:
        raise HTTPException(status_code=400, detail="Geçerli bir sipariş durumu belirtilmelidir.")
    if new_status not in ORDER_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Geçersiz sipariş durumu. İzin verilenler: {', '.join(ORDER_STATUSES)}.",
        )

    repo = OrderRepository(db)
    order = repo.get_order_for_update(order_id)
    if not order or (not current_user.is_admin and not _is_customer_order(order, current_user)):
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı.")

    if not current_user.is_admin:
        if new_status != "İptal":
            raise HTTPException(status_code=403, detail="Sipariş durumunu yalnızca yönetici değiştirebilir.")
        if order.order_status != "Onay Bekliyor":
            raise HTTPException(
                status_code=400,
                detail="Yalnızca onay bekleyen siparişler iptal edilebilir. Lütfen bizimle iletişime geçin.",
            )

    try:
        return repo.update_order_status(order, new_status, user_name=current_user.full_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print("SİPARİŞ DURUMU GÜNCELLEME HATASI:", str(e))
        raise HTTPException(status_code=500, detail="Sipariş durumu güncellenirken bir hata oluştu.")
