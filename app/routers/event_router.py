# app/routers/event_router.py
from typing import List
from fastapi import APIRouter, Depends, Query, Path
from sqlmodel import Session

# 1. 引入必要元件
from app.core.database import get_session  
from app.schemas.event_schema import EventListView, EventDetailView
from app.services.event_service import EventService
from app.repositories.event_repository import EventRepository
from app.dependencies import get_event_service

# 2. 定義 Router
# prefix="/events": 所有這個檔案裡的 API 都會以 /events 開頭
# tags=["Events"]: 在 Swagger UI 文件中分類標籤
router = APIRouter(prefix="/events", tags=["Events"])

# ==========================================
# API Endpoints
# ==========================================
@router.get("/", response_model=List[EventListView])
def read_events(
    # Query Parameters (?key=value)
    locale: str = Query("zh-TW", max_length=10, description="語言代碼 (zh-TW, en-US)"),
    page: int = Query(1, ge=1, description="頁碼，從 1 開始"),
    size: int = Query(10, ge=1, le=100, description="每頁筆數 (Max: 100)"),
    # 注入 Service
    service: EventService = Depends(get_event_service)
):
    """
    取得活動列表 (支援分頁與多語系)
    """
    # 這裡直接呼叫 Service，不需要管資料庫怎麼查、DTO 怎麼轉
    return service.get_events(locale=locale, page=page, page_size=size)


@router.get("/{event_id}", response_model=EventDetailView)
def read_event_detail(
    # Path Parameters (/events/1)
    event_id: int = Path(..., description="活動 ID"),
    # Query Parameters
    locale: str = Query("zh-TW", description="語言代碼"),
    # 注入 Service
    service: EventService = Depends(get_event_service)
):
    """
    取得單一活動詳情
    """
    # 如果找不到，Service 層會拋出 HTTPException，這裡不需要 try-except
    return service.get_event_detail(event_id=event_id, locale=locale)