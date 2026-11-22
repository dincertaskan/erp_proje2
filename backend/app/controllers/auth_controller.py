import os
import shutil
import time
from fastapi import APIRouter, Depends, status, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from typing import List
from app.core.security import CurrentUser, get_current_user, require_admin
from app.schemas.user_schema import AdminCreate, UserCreate, UserLogin, UserResponse, Token
from app.schemas.settings_schema import PasswordChange
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])

# Yüklenen dosyanın uzantısı, kullanıcının verdiği dosya adından değil içerik türünden belirlenir
ALLOWED_AVATAR_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5 MB


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    user_repo = UserRepository(db)
    return AuthService(user_repo)


def _profile_response(current_user: CurrentUser):
    if current_user.kind == "customer":
        return AuthService._customer_to_response(current_user.record)
    return current_user.record


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, auth_service: AuthService = Depends(get_auth_service)):
    return auth_service.register_user(user_data)


@router.get("/admins", response_model=List[UserResponse])
def list_admins(
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_admin),
):
    """Sistemdeki yönetici hesaplarını listeler."""
    return UserRepository(db).get_admins()


@router.post("/admins", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_admin(
    admin_data: AdminCreate,
    auth_service: AuthService = Depends(get_auth_service),
    _: CurrentUser = Depends(require_admin),
):
    """Yeni yönetici hesabı oluşturur. Yalnızca giriş yapmış bir yönetici kullanabilir."""
    return auth_service.create_admin(admin_data)


@router.post("/login", response_model=Token)
def login(login_data: UserLogin, auth_service: AuthService = Depends(get_auth_service)):
    return auth_service.login_user(login_data)


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: CurrentUser = Depends(get_current_user)):
    """Token sahibi kullanıcının profil bilgilerini döner."""
    return _profile_response(current_user)


@router.post("/change-password")
def change_password(
    data: PasswordChange,
    current_user: CurrentUser = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Giriş yapmış kullanıcının şifresini değiştirir."""
    auth_service.change_password(current_user.record, data.current_password, data.new_password)
    return {"message": "Şifreniz başarıyla değiştirildi."}


@router.post("/upload-avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    file_ext = ALLOWED_AVATAR_TYPES.get(file.content_type)
    if not file_ext:
        raise HTTPException(status_code=400, detail="Lütfen sadece JPG, PNG veya WEBP formatında resim yükleyin.")

    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > MAX_AVATAR_SIZE:
        raise HTTPException(status_code=400, detail="Profil fotoğrafı en fazla 5 MB olabilir.")

    avatar_dir = settings.UPLOAD_DIR / "avatars"
    os.makedirs(avatar_dir, exist_ok=True)

    # Aynı isimli iki kullanıcının dosyaları çakışmasın diye dosya adı hesap türü + ID ile oluşturulur
    filename = f"avatar_{current_user.kind}_{current_user.id}.{file_ext}"
    file_path = avatar_dir / filename

    # Farklı uzantıyla kaydedilmiş eski fotoğrafı temizle
    for ext in ALLOWED_AVATAR_TYPES.values():
        old_path = avatar_dir / f"avatar_{current_user.kind}_{current_user.id}.{ext}"
        if ext != file_ext and old_path.exists():
            old_path.unlink()

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # ?v=... eki, dosya adı aynı kalsa da tarayıcının eski fotoğrafı önbellekten göstermesini engeller
    avatar_url = f"/uploads/avatars/{filename}?v={int(time.time())}"
    record = db.merge(current_user.record)
    record.avatar_url = avatar_url
    db.commit()

    return {"message": "Profil fotoğrafı başarıyla yüklendi", "avatar_url": avatar_url}
