from fastapi import APIRouter, Depends
from services.forecast_service import ForecastService
from services.dataset_service import DatasetService
from auth.dependencies import get_current_user
router = APIRouter()
@router.get("/forecast")
def get_forecast(service: ForecastService = Depends()):
    return service.generate_forecast()
@router.post("/dataset/upload")
def upload_dataset(service: DatasetService = Depends()):
    return service.upload_dataset()
@router.get("/report")
def get_report(service: ForecastService = Depends()):
    return service.generate_report()
