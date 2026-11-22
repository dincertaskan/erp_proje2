from pydantic import BaseModel, Field, field_validator


class AppSettings(BaseModel):
    """Admin panelinden yönetilen uygulama ayarları."""

    # Firma bilgileri (fatura başlığında kullanılır)
    company_name: str = Field(default="ERP Yönetim Sistemi", max_length=120)
    company_address: str = Field(default="", max_length=300)
    company_phone: str = Field(default="", max_length=40)
    company_email: str = Field(default="", max_length=120)
    tax_office: str = Field(default="", max_length=80)
    tax_number: str = Field(default="", max_length=20)

    # Mağaza ayarları
    default_min_stock: int = Field(default=5, ge=0, le=100000)
    allow_registration: bool = True
    accept_orders: bool = True

    @field_validator(
        "company_name", "company_address", "company_phone",
        "company_email", "tax_office", "tax_number",
    )
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("company_name")
    @classmethod
    def require_company_name(cls, value: str) -> str:
        if not value:
            raise ValueError("Firma adı boş olamaz.")
        return value

    @field_validator("company_email")
    @classmethod
    def check_email(cls, value: str) -> str:
        if value and ("@" not in value or "." not in value.split("@")[-1]):
            raise ValueError("Geçerli bir firma e-posta adresi girin.")
        return value


class PublicSettings(BaseModel):
    """Giriş yapmamış kullanıcıların da görebileceği ayarlar."""
    company_name: str
    allow_registration: bool
    accept_orders: bool


class PasswordChange(BaseModel):
    current_password: str
    new_password: str
