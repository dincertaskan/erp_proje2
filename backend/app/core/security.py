from dataclasses import dataclass
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.erp import Customer
from app.models.user import User

# auto_error=False: token yoksa FastAPI'nin İngilizce 403 mesajı yerine kendi 401 mesajımızı döneriz
bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    """İsteği yapan oturum sahibi (users tablosundaki admin veya customers tablosundaki müşteri)."""
    id: int
    full_name: str
    email: str
    role: str
    kind: str  # "user" -> users tablosu, "customer" -> customers tablosu
    record: Any  # Veritabanındaki User veya Customer nesnesi

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Oturumunuz geçersiz veya süresi dolmuş. Lütfen tekrar giriş yapın.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _from_user(user: User) -> CurrentUser:
    return CurrentUser(user.id, user.full_name, user.email, user.role or "admin", "user", user)


def _from_customer(customer: Customer) -> CurrentUser:
    return CurrentUser(customer.id, customer.name, customer.email, "customer", "customer", customer)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> CurrentUser:
    if credentials is None:
        raise _unauthorized()

    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise _unauthorized()

    email = payload.get("sub")
    if not email:
        raise _unauthorized()

    kind = payload.get("kind")

    # "kind" bilgisi olmayan eski token'lar için giriş sırasıyla aynı sırada aranır (önce users, sonra customers)
    if kind in (None, "user"):
        user = db.query(User).filter(User.email == email).first()
        if user:
            if user.is_active is False:
                raise _unauthorized()
            return _from_user(user)

    if kind in (None, "customer"):
        customer = db.query(Customer).filter(func.lower(Customer.email) == email.lower()).first()
        if customer:
            if customer.is_active is False:
                raise _unauthorized()
            return _from_customer(customer)

    raise _unauthorized()


def require_admin(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yönetici yetkisi gerekiyor.",
        )
    return current_user
