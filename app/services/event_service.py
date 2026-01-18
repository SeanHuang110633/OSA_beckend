# app/services/event_service.py
from typing import List, Optional
from fastapi import HTTPException
from sqlmodel import Session
from app.models.event_model import Event, EventStatus
from app.schemas.event_schema import EventListView, EventDetailView, CategoryPublic, AttachmentPublic
from app.repositories.event_repository import EventRepository

class EventService:
    # 初始化 Service，注入 Repository
    def __init__(self, repository: EventRepository):
        self.repository = repository

    def get_events(self, locale: str, page: int = 1, page_size: int = 10) -> List[EventListView]:
        """
        取得活動列表 (包含多語系轉換邏輯)
        參數：
        - locale: 語言代碼 (如 "zh-TW", "en-US")
        - page: 頁碼 (從 1 開始)
        - page_size: 每頁筆數
        返迴：
        List[EventListView]: 活動列表 DTO 清單
        """
        # 1. 計算分頁位移
        skip = (page - 1) * page_size
        
        # 2. 從資料庫撈取原始資料 (List[Event])
        # Repository 應該要負責處理 filter (如 status=PUBLISHED)
        raw_events = self.repository.get_list(skip=skip, limit=page_size)

        # 3. 資料轉換 (Mapping)
        # 使用 List Comprehension 將每一個 Event 物件轉成 EventListView
        return [
            self._transform_to_list_view(event, locale) 
            for event in raw_events
        ]

    def get_event_detail(self, event_id: int, locale: str) -> EventDetailView:
        """
        取得單一活動詳情
        參數：
        - event_id: 活動 ID
        - locale: 語言代碼
        返迴：
        EventDetailView: 活動詳情 DTO
        """
        # 1. 從資料庫撈取原始資料
        event = self.repository.get_by_id(event_id)

        # 2. 錯誤處理：找不到資料
        if not event:
            # Service 層通常拋出業務異常，讓 Router 層去接
            # 這裡為了簡單，直接用 FastAPI 的 HTTPException
            raise HTTPException(status_code=404, detail="Event not found")

        # 3. 資料轉換：轉成詳情 DTO
        return self._transform_to_detail_view(event, locale)

    # ==========================================
    # Private Helpers (DTO 轉換邏輯)
    # ==========================================

    # 取得對應語言的翻譯
    def _get_translation(self, event: Event, locale: str):
        """
        邏輯：
        1. 嘗試尋找符合 locale 的翻譯
        2. 如果找不到，退而求其次找 'zh-TW' (預設)
        3. 再找不到，直接拿第一筆 (Fallback)
        4. 真的都沒有，回傳空物件避免報錯
        """
        # Python 的 next() 語法：在 list 中尋找第一個符合條件的元素
        translation = next((t for t in event.translations if t.locale == locale), None)
        
        if not translation and event.translations:
            # 降級策略 (Fallback)：如果指定語言沒有，試著給繁體中文，或是隨便給一個
            translation = next((t for t in event.translations if t.locale == "zh-TW"), event.translations[0])
            
        return translation
    
    # 取得 JSON 欄位的多語系文字
    def _get_json_text(self, data_dict: dict, locale: str, default: str = "Unknown") -> str:
        """
        專門處理 JSON 欄位的多語系取值小工具
        """
        if not data_dict:
            return default
            
        # 1. 找指定的語言
        # 2. 找不到就找繁中
        # 3. 再找不到就回傳預設值
        return data_dict.get(locale) or data_dict.get("zh-TW") or default
    
    # 轉換為列表用 DTO 
    def _transform_to_list_view(self, event: Event, locale: str) -> EventListView:
        """
        將 DB Event 轉換為 EventListView (列表用 DTO)
        """
        # 1. 取得對應語言的翻譯
        trans = self._get_translation(event, locale)
        
        # 2. 處理可能沒有翻譯的情況
        title = trans.title if trans else "No Translation"
        
        # 3. 處理分類資訊 (CategoryPublic)
        # 注意：這裡假設 category.names 是一個 Dict，我們也要取對應語言

        # 取得分類名稱
        cat_name = self._get_json_text(event.category.names, locale, default="No Category")
        
        # 組裝分類 DTO
        category_dto = CategoryPublic(
            slug=event.category.slug,
            name=cat_name
        )

        # 4. 處理 Organizer Info (JSON -> Dict)
        # 因為 DB 定義就是 JSON，SQLModel 會自動轉成 Dict，直接用即可
        # 如果是 None，DTO 有定義 Optional，所以沒問題

        return EventListView(
            id=event.id,
            # 合成 slug，目的是讓前端路由好用一些
            slug=f"{event.category.slug}-{event.id}", 
            title=title,
            category=category_dto,
            published_at=event.published_at,
            organizer_info=event.organizer_info
        )

    # 轉換為詳情用 DTO
    def _transform_to_detail_view(self, event: Event, locale: str) -> EventDetailView:
        """
        將 DB Event 轉換為 EventDetailView (詳情用 DTO)
        """
        # 1. 先利用上面的邏輯，取得基礎欄位
        base_view = self._transform_to_list_view(event, locale)
        
        # 2. 取得對應語言的翻譯 (為了拿 content 和 location)
        trans = self._get_translation(event, locale)
        
        # 3. 轉換附件 (List[EventAttachment] -> List[AttachmentPublic])
        
        attachment_dtos = [
            AttachmentPublic(
                type=att.type, 
                title=att.title,
                path=att.path
            ) for att in event.attachments
        ]

        # 4. 組裝完整 DTO
        # 使用 model_dump() 把 base_view 轉成 dict，再解包塞進去
        return EventDetailView(
            **base_view.model_dump(),
            content=trans.content if trans else None,
            location=trans.location if trans else None,
            attachments=attachment_dtos
        )