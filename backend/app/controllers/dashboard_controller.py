from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_admin
from app.schemas.dashboard_schema import DashboardDataResponse
from app.repositories.dashboard_repository import DashboardRepository
from app.services.dashboard_service import DashboardService

# Panel verileri yalnızca yöneticilere açıktır
router = APIRouter(prefix="/dashboard", tags=["Dashboard"], dependencies=[Depends(require_admin)])

def get_dashboard_service(db: Session = Depends(get_db)) -> DashboardService:
    repo = DashboardRepository(db)
    return DashboardService(repo)

@router.get("/stats", response_model=DashboardDataResponse)
def get_stats(service: DashboardService = Depends(get_dashboard_service)):
    return service.get_dashboard_summary()

@router.get("/categories")
def get_categories(service: DashboardService = Depends(get_dashboard_service)):
    return service.repo.get_all_categories()

@router.get("/products")
def get_products(service: DashboardService = Depends(get_dashboard_service)):
    return service.repo.get_all_products()