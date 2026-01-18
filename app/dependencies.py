# app/dependencies.py
# 統一處理依賴注入的工廠函式

from fastapi import Depends
from sqlmodel import Session
from app.core.database import get_session
from app.repositories.event_repository import EventRepository
from app.services.event_service import EventService

# event_service 依賴注入工廠 (Dependency Injection Factory)
def get_event_service(session: Session = Depends(get_session)) -> EventService:
    return EventService(EventRepository(session))