import uuid
from typing import Optional
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, joinedload
from app.models.erp import Order, OrderItem, Product, StockMovement
from app.schemas.order_schema import OrderCreate

# Bu durumlara gelen siparişler kilitlenir, durumları bir daha değiştirilemez
LOCKED_STATUSES = ("İptal", "Tamamlandı")


def customer_order_filter(customer_id: int, customer_name: str):
    """Müşteriye ait siparişleri seçen filtre.

    Yeni siparişler customer_id ile bağlanır. customer_id sütunu eklenmeden önce verilmiş
    eski siparişler için isim eşleşmesine geri dönülür.
    """
    return or_(
        Order.customer_id == customer_id,
        and_(Order.customer_id.is_(None), Order.customer_name == customer_name),
    )


class OrderRepository:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def serialize(o: Order) -> dict:
        """Siparişi frontend'in beklediği sözlük yapısına çevirir."""
        items_payload = []
        for item in o.items:
            product = item.product
            items_payload.append({
                "id": item.id,
                "product_id": item.product_id,
                "product_name": product.name if product else "Bilinmeyen Ürün",
                "quantity": item.quantity,
                "unit_price": float(item.unit_price),
                "total_price": float(item.total_price),
                "image_url": product.image_url if product else None,
                # Frontend'de item.product.image_url ve item.product.name erişimini desteklemek için:
                "product": {
                    "id": product.id,
                    "name": product.name,
                    "image_url": product.image_url,
                } if product else None,
            })

        return {
            "id": o.id,
            "order_code": o.order_code,
            "customer_id": o.customer_id,
            "customer_name": o.customer_name,
            "total_price": float(o.total_price),
            "payment_method": o.payment_method,
            "payment_status": o.payment_status,
            "order_status": o.order_status,
            "note": o.note,
            "created_at": o.created_at,
            "updated_at": o.updated_at,
            "items": items_payload,
            "product_name": items_payload[0]["product_name"] if items_payload else "Çoklu Ürün",
            "quantity": sum(i["quantity"] for i in items_payload),
        }

    def _base_query(self):
        return self.db.query(Order).options(
            joinedload(Order.items).joinedload(OrderItem.product)
        )

    def get_all_orders(self) -> list[dict]:
        """Tüm siparişleri ürün detaylarıyla birlikte en yeniden en eskiye sıralayarak getirir."""
        orders = self._base_query().order_by(Order.id.desc()).all()
        return [self.serialize(o) for o in orders]

    def get_customer_orders(self, customer_id: int, customer_name: str) -> list[dict]:
        """Yalnızca ilgili müşterinin siparişlerini getirir."""
        orders = (
            self._base_query()
            .filter(customer_order_filter(customer_id, customer_name))
            .order_by(Order.id.desc())
            .all()
        )
        return [self.serialize(o) for o in orders]

    def get_order(self, order_id: int) -> Optional[Order]:
        return self._base_query().filter(Order.id == order_id).first()

    def get_order_for_update(self, order_id: int) -> Optional[Order]:
        """Siparişi satır kilidiyle getirir; aynı anda gelen iki iptal stoğu iki kez iade edemez."""
        return self.db.query(Order).filter(Order.id == order_id).with_for_update().first()

    def create_order(self, data: OrderCreate, user_name: str, customer_id: Optional[int] = None) -> dict:
        """Yeni sipariş oluşturur, stok miktarını düşer ve log kaydı oluşturur.

        Tüm işlem tek transaction içinde yapılır: herhangi bir üründe hata olursa
        stoklar ve sipariş kaydı birlikte geri alınır.
        """
        if not data.items:
            raise ValueError("Sipariş için en az 1 ürün seçilmelidir.")

        try:
            unique_code = f"#ORD-{uuid.uuid4().hex[:6].upper()}"
            new_order = Order(
                order_code=unique_code,
                customer_id=customer_id,
                customer_name=(data.customer_name or "").strip() or "Misafir Müşteri",
                total_price=0,
                payment_method=data.payment_method or "Kredi Kartı",
                payment_status="Ödendi",
                order_status="Onay Bekliyor",
                note=data.note,
            )
            self.db.add(new_order)
            self.db.flush()  # Sipariş ID'si kalemler için gerekli

            grand_total = 0.0
            for item_data in data.items:
                # with_for_update: aynı anda gelen iki sipariş aynı stoğu ikinci kez satamaz
                product = (
                    self.db.query(Product)
                    .filter(Product.id == item_data.product_id)
                    .with_for_update()
                    .first()
                )
                if not product or product.is_active is False:
                    raise ValueError(f"ID:{item_data.product_id} olan ürün bulunamadı veya satışta değil.")

                if product.stock < item_data.quantity:
                    raise ValueError(f"'{product.name}' için yetersiz stok! Mevcut: {product.stock} Adet")

                unit_price = float(product.unit_price)
                item_total = unit_price * item_data.quantity
                grand_total += item_total

                prev_stock = product.stock
                product.stock -= item_data.quantity

                self.db.add(StockMovement(
                    product_id=product.id,
                    user_name=user_name,
                    action_type="AZALT",
                    quantity=item_data.quantity,
                    previous_stock=prev_stock,
                    new_stock=product.stock,
                    description=f"{unique_code} kodlu sipariş oluşturuldu.",
                ))

                self.db.add(OrderItem(
                    order_id=new_order.id,
                    product_id=product.id,
                    quantity=item_data.quantity,
                    unit_price=unit_price,
                    unit_cost=float(product.cost_price or 0),
                    total_price=item_total,
                ))

            new_order.total_price = grand_total
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return self.serialize(self.get_order(new_order.id))

    def update_order_status(self, order: Order, new_status: str, user_name: str) -> dict:
        """
        Sipariş durumunu günceller.
        'İptal' veya 'Tamamlandı' olan siparişlerin durumunun tekrar değiştirilmesini engeller.
        'İptal' edildiğinde stoku otomatik iade eder ve ödeme durumunu 'İade Edildi' yapar.
        """
        old_status = order.order_status

        if old_status in LOCKED_STATUSES:
            raise ValueError(f"'{old_status}' durumundaki bir siparişin durumu daha sonra değiştirilemez.")

        if old_status == new_status:
            return self.serialize(order)

        try:
            order.order_status = new_status

            # İPTAL SENARYOSU (Para İadesi & Stok Geri Yükleme)
            if new_status == "İptal":
                order.payment_status = "İade Edildi"

                for item in order.items:
                    product = (
                        self.db.query(Product)
                        .filter(Product.id == item.product_id)
                        .with_for_update()
                        .first()
                    )
                    if product:
                        prev_stock = product.stock
                        product.stock += item.quantity

                        self.db.add(StockMovement(
                            product_id=product.id,
                            user_name=user_name,
                            action_type="ARTTIR",
                            quantity=item.quantity,
                            previous_stock=prev_stock,
                            new_stock=product.stock,
                            description=f"{order.order_code} kodlu sipariş iptal edildi. Stok iade alındı.",
                        ))

            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return self.serialize(self.get_order(order.id))
