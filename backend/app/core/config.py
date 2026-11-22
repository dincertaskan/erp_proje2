import os
from pathlib import Path
from dotenv import load_dotenv

# backend/ klasörü — uygulama hangi klasörden başlatılırsa başlatılsın aynı yolları kullanırız
BASE_DIR = Path(__file__).resolve().parents[2]

# .env dosyasını her zaman backend/.env konumundan yükle
load_dotenv(BASE_DIR / ".env")


def _normalize_database_url(url: str | None) -> str:
    if not url:
        raise RuntimeError(
            "DATABASE_URL tanımlı değil. backend/.env dosyasına veritabanı adresinizi girin."
        )
    # Sürücü belirtilmemişse (postgresql:// veya postgres://) psycopg 3 kullan.
    # postgresql+psycopg:// ve postgresql+psycopg2:// adresleri olduğu gibi çalışır;
    # iki sürücü de requirements.txt içinde kurulu.
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


def _require_secret_key(value: str | None) -> str:
    if not value:
        raise RuntimeError(
            "SECRET_KEY tanımlı değil. backend/.env dosyasına uzun ve rastgele bir SECRET_KEY girin."
        )
    return value


class Settings:
    DATABASE_URL: str = _normalize_database_url(os.getenv("DATABASE_URL"))
    SECRET_KEY: str = _require_secret_key(os.getenv("SECRET_KEY"))
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    # Virgülle ayrılmış ek frontend adresleri (ör. http://192.168.1.20:5173)
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        *[o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()],
    ]

    # Backend başlarken bu e-postayla bir hesap yoksa otomatik oluşturulur (bkz. app/core/bootstrap.py).
    # Var olan hesaba dokunulmaz. İstenirse .env dosyasında ADMIN_EMAIL / ADMIN_PASSWORD / ADMIN_NAME ile değiştirilebilir.
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "").strip() or "admin@gmail.com"
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "") or "admin123"
    ADMIN_NAME: str = os.getenv("ADMIN_NAME", "").strip() or "Sistem Yöneticisi"


settings = Settings()
