from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.services.analytics_service import AnalyticsService


def get_analytics_service(session: Session = Depends(get_db_session)) -> AnalyticsService:
    return AnalyticsService(session)
