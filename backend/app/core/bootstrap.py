"""Uygulama başlarken çalışan kurulum adımları."""
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.database import SessionLocal
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import AdminCreate
from app.services.auth_service import AuthService


def _print_box(lines: list[str]) -> None:
    width = max(len(line) for line in lines) + 4
    print("\n" + "=" * width)
    for line in lines:
        print(f"  {line}")
    print("=" * width + "\n", flush=True)


def ensure_default_admin() -> None:
    """Varsayılan yönetici hesabı (ADMIN_EMAIL) yoksa oluşturur.

    Hesap zaten varsa hiçbir şeye dokunulmaz; şifresi sonradan değiştirildiyse sıfırlanmaz.
    Varsayılan bilgiler config.py içinde, .env ile değiştirilebilir.
    """
    email = settings.ADMIN_EMAIL
    db = SessionLocal()
    try:
        repo = UserRepository(db)
        if repo.get_by_email(email):
            return
        if repo.get_customer_by_email(email):
            print(f"UYARI: {email} bir müşteri hesabına ait; otomatik yönetici oluşturulmadı.")
            return

        # Not: Varsayılan şifre kayıt formundaki şifre kurallarından muaf tutulur (bilinçli tercih).
        # Bu yüzden AdminCreate şemasının şifre doğrulaması yerine model_construct kullanılıyor.
        admin_data = AdminCreate.model_construct(
            full_name=settings.ADMIN_NAME,
            email=email,
            password=settings.ADMIN_PASSWORD,
        )
        service = AuthService(repo)
        try:
            repo.create_user(admin_data, service.hash_password(settings.ADMIN_PASSWORD))
        except IntegrityError:
            # Birden fazla süreç aynı anda başlarsa hesabı diğeri oluşturmuş olabilir
            db.rollback()
            return

        _print_box([
            "Varsayılan yönetici hesabı oluşturuldu",
            f"E-posta : {email}",
            f"Şifre   : {settings.ADMIN_PASSWORD}",
            "Güvenlik için giriş yaptıktan sonra Ayarlar > Şifre Değiştir",
            "bölümünden şifreyi değiştirmeniz önerilir.",
        ])
    finally:
        db.close()
