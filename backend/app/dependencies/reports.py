from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.services.executive_report_service import ExecutiveReportService


def get_executive_report_service(
    session: Session = Depends(get_db_session),
) -> ExecutiveReportService:
    return ExecutiveReportService(session)
