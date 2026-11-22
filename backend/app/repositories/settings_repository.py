import json
from sqlalchemy.orm import Session
from app.models.erp import AppSetting
from app.schemas.settings_schema import AppSettings


class SettingsRepository:
    """Ayarlar app_settings tablosunda anahtar/değer olarak saklanır.

    Tabloda olmayan anahtarlar AppSettings şemasındaki varsayılan değerlerle doldurulur;
    böylece yeni bir ayar eklendiğinde veritabanı göçü gerekmez.
    """

    def __init__(self, db: Session):
        self.db = db

    def get(self) -> AppSettings:
        stored = {}
        for row in self.db.query(AppSetting).all():
            if row.key in AppSettings.model_fields:
                try:
                    stored[row.key] = json.loads(row.value)
                except (TypeError, ValueError):
                    continue
        try:
            return AppSettings(**stored)
        except ValueError:
            # Bozuk bir kayıt varsa uygulama çalışmaya devam etsin diye varsayılanlara dönülür
            return AppSettings()

    def save(self, settings: AppSettings) -> AppSettings:
        for key, value in settings.model_dump().items():
            row = self.db.get(AppSetting, key)
            encoded = json.dumps(value, ensure_ascii=False)
            if row:
                row.value = encoded
            else:
                self.db.add(AppSetting(key=key, value=encoded))
        self.db.commit()
        return self.get()
