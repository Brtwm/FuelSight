from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.services.forecast_service import ForecastService


def get_forecast_service(session: Session = Depends(get_db_session)) -> ForecastService:
    return ForecastService(session)
