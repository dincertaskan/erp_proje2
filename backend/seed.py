"""Örnek veri yükler: kategoriler, ürünler ve birkaç sipariş.

Kullanım (backend klasöründe, venv aktifken):
    python seed.py

Tekrar çalıştırılabilir: var olan kategori ve ürünleri yeniden eklemez,
sipariş tablosu boşsa örnek siparişleri ekler.
"""

from app.core.database import Base, SessionLocal, engine
from app.models.erp import Category, Order, Product
from app.repositories.order_repository import OrderRepository
from app.schemas.order_schema import OrderCreate, OrderItemCreate

CATEGORIES = [
    ("Elektronik", "#6366f1"),
    ("Ofis Malzemeleri", "#ec4899"),
    ("Yedek Parça", "#10b981"),
]

# (ad, kategori, satış fiyatı, maliyet, stok, kritik stok sınırı, açıklama)
PRODUCTS = [
    ("Logitech MX Master 3S", "Elektronik", 3500.0, 2600.0, 12, 5, "Kablosuz ergonomik mouse"),
    ("Mekanik Klavye", "Elektronik", 2200.0, 1500.0, 4, 5, "TR Q düzen, RGB aydınlatmalı"),
    ("Ergonomik Ofis Koltuğu", "Ofis Malzemeleri", 4500.0, 3200.0, 15, 3, "Bel destekli, ayarlanabilir"),
    ("A4 Fotokopi Kağıdı (500'lü)", "Ofis Malzemeleri", 180.0, 120.0, 60, 20, None),
    ("USB-C Hub Multiport", "Yedek Parça", 750.0, 450.0, 2, 10, "HDMI, 3x USB-A, kart okuyucu"),
    ("65W USB-C Şarj Adaptörü", "Yedek Parça", 900.0, 600.0, 25, 8, None),
]

ORDERS = [
    OrderCreate(
        customer_name="Ayşe Yılmaz",
        payment_method="Kredi Kartı",
        items=[OrderItemCreate(product_id=0, quantity=1), OrderItemCreate(product_id=1, quantity=1)],
    ),
    OrderCreate(
        customer_name="Mehmet Demir",
        payment_method="Havale/EFT",
        items=[OrderItemCreate(product_id=3, quantity=5)],
    ),
]


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        categories = {}
        for name, color in CATEGORIES:
            category = db.query(Category).filter(Category.name == name).first()
            if not category:
                category = Category(name=name, color=color)
                db.add(category)
                db.flush()
            categories[name] = category

        products = []
        for name, cat_name, price, cost, stock, min_stock, description in PRODUCTS:
            product = db.query(Product).filter(Product.name == name).first()
            if not product:
                product = Product(
                    name=name,
                    category_id=categories[cat_name].id,
                    unit_price=price,
                    cost_price=cost,
                    stock=stock,
                    min_stock=min_stock,
                    description=description,
                )
                db.add(product)
                db.flush()
            products.append(product)
        db.commit()
        print(f"{len(categories)} kategori ve {len(products)} ürün hazır.")

        if db.query(Order).count() == 0:
            repo = OrderRepository(db)
            for order in ORDERS:
                # Listedeki sıra numaralarını gerçek ürün ID'lerine çevir
                items = [OrderItemCreate(product_id=products[i.product_id].id, quantity=i.quantity) for i in order.items]
                repo.create_order(order.model_copy(update={"items": items}), user_name="Seed")
            print(f"{len(ORDERS)} örnek sipariş eklendi.")
        else:
            print("Siparişler zaten var, örnek sipariş eklenmedi.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
