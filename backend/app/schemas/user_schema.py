from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional

def validate_full_name(value: str) -> str:
    value = value.strip()
    if len(value) < 2:
        raise ValueError("Ad soyad en az 2 karakter olmalıdır.")
    return value


def validate_password_strength(password: str) -> str:
    """Kayıt sayfasındaki şifre kurallarının sunucu tarafındaki karşılığı."""
    if len(password) < 8:
        raise ValueError("Şifre en az 8 karakter olmalıdır.")
    if not any(c.isupper() for c in password):
        raise ValueError("Şifre en az bir büyük harf içermelidir (A-Z).")
    if not any(c.islower() for c in password):
        raise ValueError("Şifre en az bir küçük harf içermelidir (a-z).")
    if not any(c.isdigit() for c in password):
        raise ValueError("Şifre en az bir rakam içermelidir (0-9).")
    if not any(not c.isalnum() and not c.isspace() for c in password):
        raise ValueError("Şifre en az bir özel karakter içermelidir (örn: !, @, #, $, %).")
    return password


class UserCreate(BaseModel):
    """Herkese açık kayıt formu. Bu formla yalnızca müşteri hesabı açılabilir."""
    full_name: str = Field(max_length=100)
    email: EmailStr
    password: str
    # Eski istemcilerle uyumluluk için duruyor; 'admin' gönderilirse kayıt reddedilir
    role: Optional[str] = "customer"

    @field_validator("full_name")
    @classmethod
    def strip_full_name(cls, value: str) -> str:
        return validate_full_name(value)

    @field_validator("password")
    @classmethod
    def check_password(cls, value: str) -> str:
        return validate_password_strength(value)


class AdminCreate(BaseModel):
    """Mevcut bir yöneticinin yeni yönetici eklemesi için kullanılır."""
    full_name: str = Field(max_length=100)
    email: EmailStr
    password: str

    @field_validator("full_name")
    @classmethod
    def strip_full_name(cls, value: str) -> str:
        return validate_full_name(value)

    @field_validator("password")
    @classmethod
    def check_password(cls, value: str) -> str:
        return validate_password_strength(value)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str
    is_active: bool
    avatar_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    full_name: str
    role: str
    avatar_url: Optional[str] = None