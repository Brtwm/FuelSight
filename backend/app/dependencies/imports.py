from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.services.import_service import ImportService


def get_import_service(session: Session = Depends(get_db_session)) -> ImportService:
    return ImportService(session)
