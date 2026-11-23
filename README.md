# ERP Yönetim Sistemi

Ürün, stok, sipariş ve müşteri süreçlerini tek panelden yöneten web tabanlı bir ERP uygulaması. Yöneticiler için bir yönetim paneli, müşteriler için ürünlere göz atıp sipariş verebilecekleri bir müşteri portalı içerir.

- **Backend:** FastAPI + SQLAlchemy + PostgreSQL, JWT ile kimlik doğrulama
- **Frontend:** React 19 + Vite + Tailwind CSS, grafikler için Recharts

## Özellikler

### Yönetici paneli

- **Dashboard:** Satış, sipariş ve stok özetleri; kategori ve ürün bazlı grafikler
- **Ürünler ve kategoriler:** Ürün ekleme, düzenleme ve silme, kategori oluşturma, ürün detay sayfası
- **Envanter:** Stok giriş/çıkış düzeltmeleri, ürün bazında stok hareket geçmişi, kritik stok sınırı
- **Siparişler:** Tüm siparişleri listeleme ve durumlarını güncelleme
- **Müşteriler:** Müşteri listesi, hesapları aktif veya pasif yapma
- **Raporlar:** Seçilen tarih aralığında satış raporu; önceki döneme göre değişim, en çok satan ürünler. 62 günü aşan aralıklar aylık gruplanır.
- **Ayarlar:** Firma bilgileri (unvan, adres, vergi dairesi/no), varsayılan kritik stok sınırı, yeni kayıtları ve sipariş alımını açıp kapatma
- **Yönetici hesapları:** Profil sayfasından yeni yönetici ekleme

### Müşteri portalı

- Kayıt olma ve giriş yapma
- Ürünlere göz atma, sepete ekleme ve sipariş verme
- Kendi siparişlerini ve durumlarını takip etme

### Ortak

- Profil sayfası, şifre değiştirme, profil fotoğrafı yükleme
- Bildirimler: Yöneticiye onay bekleyen siparişler ve kritik stoklar, müşteriye sipariş durumu değişiklikleri bildirilir
- Doğrulama hataları backend'den Türkçe ve okunabilir mesajlar olarak döner

**Sipariş durumları:** `Onay Bekliyor` → `Hazırlanıyor` → `Kargolandı` → `Tamamlandı` (veya `İptal`)

## Proje yapısı

```
erp_proje2/
├── backend/
│   ├── app/
│   │   ├── controllers/    # API uç noktaları (router'lar)
│   │   ├── core/           # Ayarlar, veritabanı bağlantısı, güvenlik, başlangıç adımları
│   │   ├── models/         # SQLAlchemy modelleri
│   │   ├── repositories/   # Veritabanı erişim katmanı
│   │   ├── schemas/        # Pydantic şemaları
│   │   ├── services/       # İş mantığı
│   │   └── main.py         # FastAPI uygulaması
│   ├── create_admin.py     # Komut satırından yönetici oluşturma
│   ├── seed.py             # Örnek veri yükleme
│   └── requirements.txt
└── frontend/
    └── src/
        ├── api/            # Axios istemcisi ve yardımcıları
        ├── component/      # Layout, Sidebar, Header, ProtectedRoute vb.
        ├── context/        # Bildirim context'i
        ├── pages/          # Sayfalar (yönetici ve müşteri)
        └── utils/          # Rota ve doğrulama yardımcıları
```

## Gereksinimler

- Python 3.10 veya üzeri
- Node.js 20.19 veya üzeri (Vite 8 için)
- PostgreSQL

## Kurulum

### 1. Veritabanı

PostgreSQL'de uygulama için boş bir veritabanı oluşturun:

```sql
CREATE DATABASE erp_db;
```

Tablolar backend ilk kez başlatıldığında otomatik oluşturulur.

### 2. Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

`backend/.env` dosyasını oluşturun:

```env
# Zorunlu
DATABASE_URL=postgresql://kullanici:sifre@localhost:5432/erp_db
SECRET_KEY=uzun-ve-rastgele-bir-deger

# İsteğe bağlı
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
CORS_ORIGINS=http://192.168.1.20:5173
ADMIN_EMAIL=admin@gmail.com
ADMIN_PASSWORD=admin123
ADMIN_NAME=Sistem Yöneticisi
```

| Değişken | Açıklama |
| --- | --- |
| `DATABASE_URL` | PostgreSQL bağlantı adresi. Sürücü belirtilmezse psycopg 3 kullanılır. |
| `SECRET_KEY` | JWT imzalama anahtarı. Tanımlı değilse uygulama başlamaz. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Oturum süresi (dakika). Varsayılan: 60 |
| `CORS_ORIGINS` | `localhost:5173` dışındaki frontend adresleri, virgülle ayrılır |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` / `ADMIN_NAME` | Otomatik oluşturulan varsayılan yönetici hesabının bilgileri |

Sunucuyu başlatın:

```bash
uvicorn app.main:app --reload
```

API `http://127.0.0.1:8000` adresinde çalışır. Etkileşimli API dokümantasyonu için `http://127.0.0.1:8000/docs` adresini açın.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Uygulama `http://localhost:5173` adresinde açılır.

Backend farklı bir adreste çalışıyorsa `frontend/.env` dosyasında belirtin:

```env
VITE_API_URL=http://127.0.0.1:8000
```

## İlk giriş

Backend ilk başladığında `ADMIN_EMAIL` adresiyle bir hesap yoksa varsayılan yönetici hesabı oluşturulur ve bilgileri konsola yazılır:

- **E-posta:** `admin@gmail.com`
- **Şifre:** `admin123`

Hesap zaten varsa ona dokunulmaz. Giriş yaptıktan sonra şifreyi **Ayarlar > Şifre Değiştir** bölümünden değiştirmeniz önerilir.

Komut satırından ayrıca yönetici oluşturmak için (`backend` klasöründe, venv aktifken):

```bash
python create_admin.py
```

Kayıt sayfası yalnızca müşteri hesabı açar.

## Örnek veri

Denemek için örnek kategoriler, 20 ürün, müşteri hesapları ve son 12 aya yayılmış yaklaşık 180 sipariş yüklemek isterseniz:

```bash
cd backend
python seed.py
```

Betik tekrar çalıştırılabilir; var olan kayıtları yeniden eklemez. Örnek müşteriler müşteri portalına `Musteri123!` şifresiyle giriş yapabilir (ör. `ayse.yilmaz@gmail.com`).

## API özeti

Tüm uç noktaların ayrıntıları `/docs` adresinde bulunur.

| Önek | Açıklama | Erişim |
| --- | --- | --- |
| `/auth` | Kayıt, giriş, oturum bilgisi, şifre değiştirme, avatar yükleme, yönetici yönetimi | Karışık |
| `/dashboard` | Özet istatistikler, kategori ve ürün verileri | Yönetici |
| `/inventory` | Kategoriler, ürünler, stok düzeltme ve hareket geçmişi | Karışık |
| `/orders` | Sipariş listeleme, oluşturma, durum güncelleme | Giriş yapmış kullanıcı |
| `/customers` | Müşteri listesi ve hesap durumu | Yönetici |
| `/notifications` | Role göre bildirimler | Giriş yapmış kullanıcı |
| `/reports` | Satış raporları | Yönetici |
| `/settings` | Uygulama ayarları (`/settings/public` herkese açık) | Karışık |

Kimlik doğrulama `Authorization: Bearer <token>` başlığıyla yapılır. Yüklenen dosyalar `/uploads` altından sunulur.

## Komutlar

| Komut | Konum | Açıklama |
| --- | --- | --- |
| `uvicorn app.main:app --reload` | `backend/` | Geliştirme sunucusunu başlatır |
| `python seed.py` | `backend/` | Örnek veri yükler |
| `python create_admin.py` | `backend/` | Yeni yönetici hesabı oluşturur |
| `npm run dev` | `frontend/` | Geliştirme sunucusunu başlatır |
| `npm run build` | `frontend/` | Üretim derlemesi alır (`dist/`) |
| `npm run preview` | `frontend/` | Derlemeyi yerelde önizler |
| `npm run lint` | `frontend/` | Oxlint ile kod denetimi yapar |
