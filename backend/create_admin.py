"""Komut satırından yönetici (admin) hesabı oluşturur.

Kayıt sayfası yalnızca müşteri hesabı açar. Sistemde hiç yönetici yokken (ör. yeni kurulumda)
ilk yönetici bu betikle oluşturulur; sonraki yöneticiler panelde Profil sayfasından eklenebilir.

Kullanım (backend klasöründe, venv aktifken):
    python create_admin.py
"""

import getpass
import sys

from fastapi import HTTPException
from pydantic import ValidationError

from app.core.database import Base, SessionLocal, engine
from app.models import erp, user  # noqa: F401  (tabloların tanımlı olması için)
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import AdminCreate
from app.services.auth_service import AuthService


def main() -> int:
    Base.metadata.create_all(bind=engine)

    print("Yeni yönetici hesabı oluşturuluyor.\n")
    full_name = input("Ad Soyad: ").strip()
    email = input("E-posta: ").strip()
    password = getpass.getpass("Şifre: ")
    if password != getpass.getpass("Şifre (tekrar): "):
        print("\nHata: Şifreler eşleşmiyor.")
        return 1

    try:
        admin_data = AdminCreate(full_name=full_name, email=email, password=password)
    except ValidationError as e:
        print(f"\nHata: {e.errors()[0]['msg'].removeprefix('Value error, ')}")
        return 1

    db = SessionLocal()
    try:
        admin = AuthService(UserRepository(db)).create_admin(admin_data)
        print(f"\nYönetici oluşturuldu: {admin.full_name} <{admin.email}>")
        return 0
    except HTTPException as e:
        print(f"\nHata: {e.detail}")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
