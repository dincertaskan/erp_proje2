from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Literal, Optional
from datetime import datetime

# KATEGORİ ŞEMALARI
class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    color: Optional[str] = Field(default="#6366f1", pattern=r"^#[0-9A-Fa-f]{6}$")

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Kategori adı boş olamaz.")
        return value

class CategoryResponse(BaseModel):
    id: int
    name: str
    color: Optional[str] = None

    class Config:
        from_attributes = True

# STOK HAREKET VE DÜZENLEME ŞEMALARI
class StockAdjustmentCreate(BaseModel):
    # İşlemi yapan kişi artık token'dan alınır; alan geriye dönük uyumluluk için duruyor
    user_name: Optional[str] = None
    action_type: Literal["ARTTIR", "AZALT"]
    quantity: int = Field(gt=0)
    description: Optional[str] = None

class StockMovementResponse(BaseModel):
    id: int
    user_name: str
    action_type: str
    quantity: int
    previous_stock: Optional[int] = None
    new_stock: Optional[int] = None
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

def _clean_product_name(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    value = value.strip()
    if not value:
        raise ValueError("Ürün adı boş olamaz.")
    return value


class ProductCreate(BaseModel):
    name: str = Field(max_length=200)
    category_id: int
    unit_price: float = Field(ge=0)
    cost_price: Optional[float] = Field(default=0.0, ge=0)
    stock: Optional[int] = Field(default=0, ge=0)
    min_stock: Optional[int] = Field(default=5, ge=0)
    image_url: Optional[str] = None
    description: Optional[str] = None

    @field_validator("name")
    @classmethod
    def clean_name(cls, value):
        return _clean_product_name(value)

    @model_validator(mode='after')
    def validate_prices(self):
        if self.unit_price < (self.cost_price or 0):
            raise ValueError("Satış fiyatı maliyet fiyatından düşük olamaz.")
        return self

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=200)
    category_id: Optional[int] = None
    unit_price: Optional[float] = Field(default=None, ge=0)
    cost_price: Optional[float] = Field(default=None, ge=0)
    min_stock: Optional[int] = Field(default=None, ge=0)
    image_url: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("name")
    @classmethod
    def clean_name(cls, value):
        return _clean_product_name(value)

    @model_validator(mode='after')
    def validate_prices(self):
        if self.unit_price is not None and self.cost_price is not None:
            if self.unit_price < self.cost_price:
                raise ValueError("Satış fiyatı maliyet fiyatından düşük olamaz.")
        return self

class ProductDetailResponse(BaseModel):
    id: int
    name: str
    category_id: int
    category_name: Optional[str] = None
    unit_price: float
    cost_price: float
    stock: int
    min_stock: int
    image_url: Optional[str] = None
    is_critical: Optional[bool] = False
    is_active: Optional[bool] = True
    description: Optional[str] = None

    class Config:
        from_attributes = True