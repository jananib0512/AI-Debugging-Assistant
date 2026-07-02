from fastapi import APIRouter, Depends

from app.middleware.auth_middleware import require_auth
from app.models.user import User
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
def get_dashboard_stats(
    current_user: User = Depends(require_auth),
    service: DashboardService = Depends(DashboardService),
):
    return service.get_stats(user_id=current_user.id)
