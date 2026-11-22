from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import CurrentUser, require_admin
from app.repositories.settings_repository import SettingsRepository
from app.schemas.settings_schema import AppSettings, PublicSettings

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("/public", response_model=PublicSettings)
def get_public_settings(db: Session = Depends(get_db)):
    """Kayıt ve sepet sayfalarının ihtiyaç duyduğu, giriş gerektirmeyen ayarlar."""
    return SettingsRepository(db).get()


@router.get("", response_model=AppSettings)
def get_settings(db: Session = Depends(get_db), _: CurrentUser = Depends(require_admin)):
    return SettingsRepository(db).get()


@router.put("", response_model=AppSettings)
def update_settings(
    data: AppSettings,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_admin),
):
    return SettingsRepository(db).save(data)
