"""Örnek (sahte) veri yükler: kategoriler, ürünler, müşteri hesapları ve son 12 aya yayılmış siparişler.

Kullanım (backend klasöründe, venv aktifken):
    python seed.py

Tekrar çalıştırılabilir:
- Var olan kategori, ürün ve müşteriler (isim / e-posta eşleşmesiyle) yeniden eklenmez.
- Örnek siparişler yalnızca daha önce eklenmemişse eklenir.

Örnek müşteriler müşteri portalına giriş yapabilir:
    E-posta: listedeki adresler (ör. ayse.yilmaz@gmail.com)   Şifre: Musteri123!
"""

import random
from datetime import datetime, timedelta

import app.main  # noqa: F401  Tabloları/sütunları ve varsayılan yöneticiyi hazırlar
from app.core.database import SessionLocal
from app.models.erp import Category, Customer, Order, Product, StockMovement
from app.repositories.order_repository import OrderRepository
from app.schemas.order_schema import OrderCreate, OrderItemCreate
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository

SEED_NOTE = "[örnek veri]"
CUSTOMER_PASSWORD = "Musteri123!"
ORDER_COUNT = 180
DAYS_BACK = 365

CATEGORIES = [
    ("Elektronik", "#6366f1"),
    ("Ofis Malzemeleri", "#ec4899"),
    ("Yedek Parça", "#10b981"),
    ("Ağ Ürünleri", "#f59e0b"),
    ("Depolama", "#0ea5e9"),
]

# (ad, kategori, satış fiyatı, maliyet, başlangıç stoğu, kritik stok sınırı, açıklama)
PRODUCTS = [
    ("Logitech MX Master 3S", "Elektronik", 3500.0, 2600.0, 120, 10, "Kablosuz ergonomik mouse, 8K DPI sensör"),
    ("Mekanik Klavye", "Elektronik", 2200.0, 1500.0, 90, 10, "TR Q düzen, RGB aydınlatmalı, kırmızı switch"),
    ("27\" IPS Monitör", "Elektronik", 7800.0, 6100.0, 45, 5, "2560x1440 çözünürlük, 75 Hz, ince çerçeve"),
    ("Full HD Web Kamerası", "Elektronik", 1450.0, 950.0, 70, 8, "1080p, dahili mikrofon, otomatik odaklama"),
    ("Bluetooth Kulaklık", "Elektronik", 2600.0, 1750.0, 60, 8, "Aktif gürültü engelleme, 30 saat pil"),
    ("Ergonomik Ofis Koltuğu", "Ofis Malzemeleri", 4500.0, 3200.0, 40, 3, "Bel destekli, ayarlanabilir kolçak"),
    ("A4 Fotokopi Kağıdı (500'lü)", "Ofis Malzemeleri", 180.0, 120.0, 600, 50, "80 gr/m², beyaz"),
    ("Masa Düzenleyici Set", "Ofis Malzemeleri", 420.0, 260.0, 150, 15, "Kalemlik, evrak tepsisi ve not kutusu"),
    ("Tükenmez Kalem (50'li)", "Ofis Malzemeleri", 350.0, 210.0, 200, 20, "Mavi, 0.7 mm uç"),
    ("Ayarlanabilir Laptop Standı", "Ofis Malzemeleri", 950.0, 600.0, 80, 8, "Alüminyum, 6 kademeli yükseklik"),
    ("USB-C Hub Multiport", "Yedek Parça", 750.0, 450.0, 100, 10, "HDMI, 3x USB-A, SD kart okuyucu"),
    ("65W USB-C Şarj Adaptörü", "Yedek Parça", 900.0, 600.0, 90, 8, "GaN teknolojisi, hızlı şarj"),
    ("Laptop Bataryası", "Yedek Parça", 1850.0, 1250.0, 35, 5, "6 hücre, 4400 mAh"),
    ("2m HDMI Kablo", "Yedek Parça", 220.0, 120.0, 300, 25, "4K 60 Hz destekli"),
    ("Wi-Fi 6 Router", "Ağ Ürünleri", 3200.0, 2350.0, 40, 5, "AX3000, çift bant, 4 anten"),
    ("8 Port Gigabit Switch", "Ağ Ürünleri", 1100.0, 720.0, 55, 6, "Tak-çalıştır, metal kasa"),
    ("Cat6 Ethernet Kablosu (10m)", "Ağ Ürünleri", 260.0, 140.0, 250, 20, "Bakır, yassı tip"),
    ("1TB NVMe SSD", "Depolama", 2400.0, 1800.0, 70, 8, "3500 MB/s okuma hızı"),
    ("2TB Harici Disk", "Depolama", 2900.0, 2150.0, 50, 6, "USB 3.2, darbeye dayanıklı kasa"),
    ("64GB USB Bellek", "Depolama", 280.0, 160.0, 220, 20, "USB 3.0, metal gövde"),
]

CUSTOMERS = [
    ("Ayşe Yılmaz", "ayse.yilmaz@gmail.com"),
    ("Mehmet Demir", "mehmet.demir@hotmail.com"),
    ("Zeynep Kaya", "zeynep.kaya@gmail.com"),
    ("Can Öztürk", "can.ozturk@outlook.com"),
    ("Elif Şahin", "elif.sahin@gmail.com"),
    ("Burak Çelik", "burak.celik@yandex.com"),
    ("Selin Arslan", "selin.arslan@gmail.com"),
    ("Emre Koç", "emre.koc@hotmail.com"),
    ("Deniz Aydın", "deniz.aydin@icloud.com"),
    ("Merve Doğan", "merve.dogan@gmail.com"),
    ("Oğuz Kurt", "oguz.kurt@outlook.com"),
    ("Gizem Polat", "gizem.polat@gmail.com"),
]

PAYMENT_METHODS = ["Kredi Kartı"] * 6 + ["Havale/EFT"] * 3 + ["Kapıda Ödeme"]


def _status_for_age(days_ago: int) -> str:
    """Siparişin yaşına göre gerçekçi bir durum seçer (eski siparişler çoğunlukla tamamlanmış)."""
    if days_ago > 14:
        choices = [("Tamamlandı", 85), ("İptal", 10), ("Kargolandı", 5)]
    elif days_ago > 3:
        choices = [("Kargolandı", 40), ("Tamamlandı", 35), ("Hazırlanıyor", 15), ("İptal", 10)]
    else:
        choices = [("Onay Bekliyor", 50), ("Hazırlanıyor", 30), ("Kargolandı", 15), ("İptal", 5)]
    statuses, weights = zip(*choices)
    return random.choices(statuses, weights=weights)[0]


def seed_catalog(db) -> list[Product]:
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
    return products


def seed_customers(db) -> list[Customer]:
    auth = AuthService(UserRepository(db))
    password_hash = auth.hash_password(CUSTOMER_PASSWORD)
    customers = []
    added = 0
    for i, (name, email) in enumerate(CUSTOMERS):
        customer = auth.user_repo.get_customer_by_email(email)
        if not customer:
            customer = Customer(
                name=name,
                email=email,
                password_hash=password_hash,
                is_active=True,
                created_at=datetime.now() - timedelta(days=DAYS_BACK + 30 - i * 25),
            )
            db.add(customer)
            added += 1
        customers.append(customer)
    db.commit()
    print(f"{len(customers)} müşteri hazır ({added} yeni). Şifre: {CUSTOMER_PASSWORD}")
    return customers


def seed_orders(db, products: list[Product], customers: list[Customer]) -> None:
    if db.query(Order).filter(Order.note == SEED_NOTE).count() > 0:
        print("Örnek siparişler zaten eklenmiş, tekrar eklenmedi.")
        return

    now = datetime.now()
    # Yakın tarihlere daha çok sipariş düşsün diye dağılım yeniye doğru ağırlıklı
    order_dates = sorted(
        now - timedelta(days=int(DAYS_BACK * random.random() ** 1.6), hours=random.randint(0, 12), minutes=random.randint(0, 59))
        for _ in range(ORDER_COUNT)
    )
    # Bazı ürünler daha popüler olsun
    product_weights = [random.uniform(0.5, 3.0) for _ in products]

    repo = OrderRepository(db)
    created = skipped = 0
    for created_at in order_dates:
        customer = random.choice(customers)
        chosen = set()
        for _ in range(random.choices([1, 2, 3], weights=[55, 30, 15])[0]):
            chosen.add(random.choices(range(len(products)), weights=product_weights)[0])
        items = [
            OrderItemCreate(
                product_id=products[i].id,
                quantity=random.choices([1, 2, 3, 5], weights=[60, 25, 10, 5])[0],
            )
            for i in chosen
        ]
        data = OrderCreate(
            customer_name=customer.name,
            payment_method=random.choice(PAYMENT_METHODS),
            items=items,
            note=SEED_NOTE,
        )
        try:
            result = repo.create_order(data, user_name=customer.name, customer_id=customer.id)
        except ValueError:
            skipped += 1  # Stok yetmediyse bu sipariş atlanır
            continue

        order = db.get(Order, result["id"])
        days_ago = (now - created_at).days
        status = _status_for_age(days_ago)
        if status == "İptal":
            # İptal mantığı stoğu iade eder ve hareket kaydı oluşturur
            repo.update_order_status(order, "İptal", user_name="Sistem Yöneticisi")
            order = db.get(Order, result["id"])
        else:
            order.order_status = status

        order.created_at = created_at
        order.updated_at = min(now, created_at + timedelta(days=random.randint(0, 5), hours=random.randint(1, 8)))
        # Stok hareketlerinin tarihi de siparişin tarihine çekilir
        db.query(StockMovement).filter(StockMovement.description.contains(order.order_code)).update(
            {StockMovement.created_at: created_at}, synchronize_session=False
        )
        db.commit()
        created += 1

    print(f"{created} örnek sipariş eklendi" + (f" ({skipped} tanesi stok yetmediği için atlandı)." if skipped else "."))


def seed() -> None:
    random.seed(42)  # Her çalıştırmada aynı veri üretilsin
    db = SessionLocal()
    try:
        products = seed_catalog(db)
        customers = seed_customers(db)
        seed_orders(db, products, customers)
    finally:
        db.close()


if __name__ == "__main__":
    seed()
