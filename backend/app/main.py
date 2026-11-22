import os
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from app.controllers import (
    auth_controller,
    dashboard_controller,
    inventory_controller,
    order_controller,
    customer_controller,
    notification_controller,
    report_controller,
    settings_controller,
)
from app.core.database import Base, engine
from app.core.config import settings
from app.core.bootstrap import ensure_default_admin

# Model dosyalarını yüklüyoruz
from app.models.user import User
from app.models.erp import Category, Customer, Product, Sale, StockMovement, Order, OrderItem, AppSetting
from sqlalchemy import text

# Yüklemelerin yapılacağı dizini otomatik oluşturur
os.makedirs(settings.UPLOAD_DIR / "avatars", exist_ok=True)

# Veritabanı tablolarını oluşturur
Base.metadata.create_all(bind=engine)

# create_all mevcut tablolara yeni sütun eklemez; sonradan eklenen sütunları burada ekliyoruz
with engine.begin() as conn:
    conn.execute(text("ALTER TABLE customers ADD COLUMN IF NOT EXISTS password_hash VARCHAR"))
    conn.execute(text("ALTER TABLE customers ADD COLUMN IF NOT EXISTS avatar_url VARCHAR"))
    conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS customer_id INTEGER REFERENCES customers(id)"))
    conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP"))
    conn.execute(text("UPDATE orders SET updated_at = created_at WHERE updated_at IS NULL"))
    conn.execute(text("ALTER TABLE order_items ADD COLUMN IF NOT EXISTS unit_cost NUMERIC(10, 2)"))

# Gerekirse otomatik yönetici hesabı oluşturur (ayrıntılar: app/core/bootstrap.py)
ensure_default_admin()

app = FastAPI(title="ERP System API")

origins = settings.CORS_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic doğrulama hatalarını kullanıcıya gösterilebilecek tek bir Türkçe mesaja çevirir
_VALIDATION_MESSAGES = {
    "missing": "Bu alan zorunludur.",
    "greater_than": "Değer {gt} değerinden büyük olmalıdır.",
    "greater_than_equal": "Değer {ge} veya daha büyük olmalıdır.",
    "string_too_short": "En az {min_length} karakter olmalıdır.",
    "too_short": "En az {min_length} öğe seçilmelidir.",
    "string_too_long":"Bu alan en fazla {max_length} karakter olabilir.",
    "int_parsing": "Geçerli bir tam sayı girin.",
    "float_parsing": "Geçerli bir sayı girin.",
    "value_error": "{error}",
    "literal_error": "Geçersiz seçim. İzin verilen değerler: {expected}.",
    "string_pattern_mismatch": "Değer beklenen formatta değil.",
}


def _validation_message(error: dict) -> str:
    template = _VALIDATION_MESSAGES.get(error.get("type"))
    ctx = error.get("ctx") or {}
    if template:
        try:
            message = template.format(**{k: str(v) for k, v in ctx.items()})
        except (KeyError, IndexError):
            message = error.get("msg", "Geçersiz veri.")
    else:
        message = error.get("msg", "Geçersiz veri.")
    # Model seviyesindeki doğrulamalarda alan adı yoktur; alan bazlı hatalarda alan adını ekleriz
    field = ".".join(str(p) for p in error.get("loc", [])[1:])
    if field and error.get("type") != "value_error":
        return f"{field}: {message}"
    return message


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    detail = _validation_message(errors[0]) if errors else "Geçersiz istek."
    return JSONResponse(status_code=422, content={"detail": detail})


# Statik görsel dosyalarını dışarı sunma
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Router Bağlantıları
app.include_router(auth_controller.router)
app.include_router(dashboard_controller.router)
app.include_router(inventory_controller.router)
app.include_router(order_controller.router)
app.include_router(customer_controller.router)
app.include_router(notification_controller.router)
app.include_router(report_controller.router)
app.include_router(settings_controller.router)


@app.get("/")
def read_root():
    return {"message": "ERP Backend API çalışıyor!"}
