from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.services.kpi_service import KpiService


def get_kpi_service(session: Session = Depends(get_db_session)) -> KpiService:
    return KpiService(session)
