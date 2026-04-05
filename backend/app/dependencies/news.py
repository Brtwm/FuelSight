from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.services.news_service import NewsService


def get_news_service(session: Session = Depends(get_db_session)) -> NewsService:
    return NewsService(session)
