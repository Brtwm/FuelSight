from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db_session
from app.services.chat_service import ChatService


def get_chat_service(
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> ChatService:
    return ChatService(session, settings=settings)
