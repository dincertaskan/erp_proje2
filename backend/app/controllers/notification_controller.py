from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import CurrentUser, get_current_user
from app.models.erp import Order, Product
from app.repositories.order_repository import customer_order_filter

router = APIRouter(prefix="/notifications", tags=["Notifications"])

# Müşteriye gösterilecek sipariş durum mesajları
CUSTOMER_STATUS_MESSAGES = {
    "Hazırlanıyor": "{code} kodlu siparişiniz onaylandı ve hazırlanıyor.",
    "Kargolandı": "{code} kodlu siparişiniz kargoya verildi.",
    "Tamamlandı": "{code} kodlu siparişiniz teslim edildi.",
    "İptal": "{code} kodlu siparişiniz iptal edildi, ödemeniz iade edildi.",
}

CUSTOMER_LOOKBACK_DAYS = 30
MAX_NOTIFICATIONS = 50


def _fmt(dt: datetime | None) -> str:
    return (dt or datetime.now()).strftime("%Y-%m-%d %H:%M")


def _admin_notifications(db: Session) -> list[dict]:
    notifications = []

    pending_orders = (
        db.query(Order)
        .filter(Order.order_status == "Onay Bekliyor")
        .order_by(Order.created_at.desc())
        .limit(MAX_NOTIFICATIONS)
        .all()
    )
    for o in pending_orders:
        notifications.append({
            # ID durumla birlikte üretilir; okundu işaretlenen bildirim aynı durum için tekrar gelmez
            "id": f"order-{o.id}-pending",
            "type": "order",
            "text": f"{o.order_code} kodlu yeni sipariş onay bekliyor ({o.customer_name}).",
            "date": _fmt(o.created_at),
            "link": "/orders",
        })

    critical_products = (
        db.query(Product)
        .filter(Product.stock <= Product.min_stock, Product.is_active.isnot(False))
        .order_by(Product.stock.asc())
        .limit(MAX_NOTIFICATIONS)
        .all()
    )
    now = _fmt(None)
    for p in critical_products:
        notifications.append({
            # Stok değiştikçe yeni bir bildirim oluşur
            "id": f"stock-{p.id}-{p.stock}",
            "type": "stock",
            "text": f"'{p.name}' ürününün stoğu kritik seviyede ({p.stock} / min. {p.min_stock}).",
            "date": now,
            "link": "/inventory",
        })

    return notifications


def _customer_notifications(db: Session, current_user: CurrentUser) -> list[dict]:
    since = datetime.now() - timedelta(days=CUSTOMER_LOOKBACK_DAYS)
    orders = (
        db.query(Order)
        .filter(
            customer_order_filter(current_user.id, current_user.full_name),
            Order.order_status != "Onay Bekliyor",
            Order.updated_at >= since,
        )
        .order_by(Order.updated_at.desc())
        .limit(MAX_NOTIFICATIONS)
        .all()
    )
    notifications = []
    for o in orders:
        template = CUSTOMER_STATUS_MESSAGES.get(o.order_status)
        if not template:
            continue
        notifications.append({
            "id": f"order-{o.id}-{o.order_status}",
            "type": "order",
            "text": template.format(code=o.order_code),
            "date": _fmt(o.updated_at or o.created_at),
            "link": "/portal/siparisler",
        })
    return notifications


@router.get("")
def get_notifications(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Admin: onay bekleyen siparişler ve kritik stoklar. Müşteri: sipariş durum değişiklikleri."""
    if current_user.is_admin:
        return _admin_notifications(db)
    return _customer_notifications(db, current_user)
