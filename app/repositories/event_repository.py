# app/repositories/event_repository.py
from typing import List, Optional
from sqlmodel import Session, select, col
from sqlalchemy.orm import selectinload # 這是解決效能問題的關鍵

# 引入模型
from app.models.event_model import Event, EventStatus

class EventRepository:
    def __init__(self, session: Session):
        """
        依賴注入 (Dependency Injection):
        Repository 不需要知道資料庫怎麼連線，它只要一個已經連好的 session。
        """
        self.session = session

    # 取得活動列表
    def get_list(self, skip: int = 0, limit: int = 10) -> List[Event]:
        """
        取得活動列表
        條件：未軟刪除 + 已發布 + 依照發布時間排序
        """
        statement = (
            select(Event)
            # 1. 過濾軟刪除 (deleted_at 為 Null 代表未刪除)
            .where(Event.deleted_at == None)
            # 2. 過濾狀態 (只顯示已發布)
            .where(Event.status == EventStatus.PUBLISHED)
            # 3. 預先載入關聯資料 (Eager Loading)
            # 如果不寫這個，Service 層跑迴圈讀取 event.category 時，會瘋狂連資料庫
            .options(
                selectinload(Event.category),
                selectinload(Event.translations),
                # 列表頁可能需要縮圖，所以先把附件也抓出來 (視情況優化)
                selectinload(Event.attachments)
            )
            # 4. 排序 (最新發布的在前面)
            .order_by(col(Event.published_at).desc())
            # 5. 分頁
            .offset(skip)
            .limit(limit)
        )
        
        results = self.session.exec(statement).all()
        return results

    # 取得單一活動詳情
    def get_by_id(self, event_id: int) -> Optional[Event]:
        """
        取得單一活動詳情
        """
        statement = (
            select(Event)
            .where(Event.id == event_id)
            .where(Event.deleted_at == None) # 同樣要檢查軟刪除
            .where(Event.status == EventStatus.PUBLISHED)
            # 詳情頁需要所有關聯資料
            .options(
                selectinload(Event.category),
                selectinload(Event.translations),
                selectinload(Event.attachments)
            )
        )
        
        result = self.session.exec(statement).first()
        return result