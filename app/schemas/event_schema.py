from typing import List, Optional, Dict
from pydantic import BaseModel
from datetime import datetime

# 注意：這裡我們繼承 Pydantic 的 BaseModel，而不是 SQLModel
# 因為這些 DTO 不需要對應資料庫表格 (table=True)，它們純粹是資料容器


# 活動類別、附件定義 : 方便後面組裝
# A. 類別顯示用 (只給最基本的)
class CategoryPublic(BaseModel):
    slug: str
    name: str  # 處理過後的多語系名稱 (原本是json格式，處理後只回傳單一語系所以是str)

# B. 附件顯示用
class AttachmentPublic(BaseModel):
    type: str  # image, file, link
    title: str  # 處理過後的多語系標題 (原本是json格式，處理後只回傳單一語系所以是str)
    path: str

# =========================================================
# 主活動顯示用 DTO 定義
# =========================================================

# 活動列表
class EventListView(BaseModel):
    id: int
    slug: str  # 前端做路由連結需要 (例如 /events/speech ; 這個 slug 來自 category 表)
    
    # --- 扁平化的欄位 (從關聯表抓出來的) ---
    title: str           # 從 translations 表取出的標題
    category: CategoryPublic # 內含 name 與 slug
    
    # --- 主表原有欄位 ---
    published_at: Optional[datetime]
    organizer_info: Optional[Dict] # JSON 直接轉成 Dictionary

# 活動詳情
class EventDetailView(EventListView):
    # 繼承了 id, title, category, published_at, organizer_info
    
    # --- 詳情頁專屬欄位 ---
    content: Optional[str] = None # 文章內容 (HTML)
    location: Optional[str] = None
    
    # 附件列表 (預設為空 list，避免前端拿到 null 報錯)
    attachments: List[AttachmentPublic] = []