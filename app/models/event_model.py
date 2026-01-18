# app/models/event_model.py
from typing import Optional, Dict, List
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import JSON, UniqueConstraint, ForeignKey, Text  # 處理 JSON 欄位
from datetime import datetime  # 處理時間
from enum import IntEnum, Enum # 處理狀態碼 & 附件類型
from app.models.constants import EventStatus, AttachmentType

# 1. 定義 EventCategory 模型
class EventCategory(SQLModel, table=True):
    __tablename__ = "event_categories"  # 指定資料庫表名稱，對應 table name

    # id: 對應 INT UNSIGNED NOT NULL AUTO_INCREMENT
    # Optional 是因為在建立物件尚未存入 DB 前，id 是 None
    id: Optional[int] = Field(default=None, primary_key=True)

    # slug: 對應 VARCHAR(50), unique
    slug: str = Field(max_length=50, unique=True, schema_extra={"comment": "網址友善的唯一識別碼"})

    # names: 對應 JSON NOT NULL
    # 這裡我們使用 Python 的 Dict 對應 JSON
    # 重點：必須傳入 sa_type=JSON 告訴 SQLAlchemy 這是一個 JSON 欄位
    names: Dict[str, str] = Field(default={}, sa_type=JSON, schema_extra={"comment": "支援多語系名稱"})

    # is_active: 對應 TINYINT(1)，在 Python 中對應 bool
    is_active: bool = Field(default=True, schema_extra={"comment": "1:啟用, 0:停用"})

    # sort_order: 對應 INT
    sort_order: int = Field(default=0, schema_extra={"comment": "控制在介面上的顯示順序"})

    # Relationship: 一個分類有多個活動
    # List["Event"] 表示一個分類下會有多個活動
    events: List["Event"] = Relationship(back_populates="category")

# 2. 定義 Event 模型
class Event(SQLModel, table=True):
    __tablename__ = "events"

    # id: 對應 BIGINT UNSIGNED
    # 雖然 Python 只有 int，但 SQLAlchemy 底層能處理 BIGINT
    id: Optional[int] = Field(default=None, primary_key=True)

    # category_id: 外鍵
    # 重點：foreign_key="表名稱.欄位名稱"
    category_id: int = Field(foreign_key="event_categories.id") # 這也是為什麼要先定義 EventCategory

    # status: 狀態
    # 這裡我們直接使用剛剛定義的 EventStatus 型別，SQLModel 會自動存成整數
    status: int = Field(
        default=0, 
        schema_extra={"comment": "0:草稿, 1:發布, 2:封存"}
    )

    # --- 時間欄位 ---
    # 對應 DATETIME，在 Python 中使用 datetime
    starts_at: Optional[datetime] = Field(default=None)
    ends_at: Optional[datetime] = Field(default=None)
    published_at: Optional[datetime] = Field(default=None)

    # --- JSON 欄位 ---
    # organizer_info: 存主辦單位資訊
    organizer_info: Optional[Dict] = Field(default=None, sa_type=JSON, schema_extra={"comment": "主辦單位資訊，存 JSON 格式"})

    # --- Boolean 標記 ---
    # TINYINT(1) 在 SQLModel/FastAPI 中通常直接對應 bool
    is_target: bool = Field(default=False)
    is_featured: bool = Field(default=False)

    # --- 系統時間欄位 ---
    # 這裡我們使用 default_factory=datetime.now，讓 Python 在建立物件時自動填入當前時間
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    
    # updated_at 的自動更新通常由資料庫層級 (ON UPDATE CURRENT_TIMESTAMP) 處理
    # 但為了讓 Python 物件也能拿到值，我們先設為 Optional
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)
    
    # 邏輯刪除欄位
    deleted_at: Optional[datetime] = Field(default=None)

    # Relationship: 多個活動屬於一個分類
    # 這不是資料庫欄位，這是一個 Python 物件
    category: Optional[EventCategory] = Relationship(back_populates="events")
    # Relationship: 一個活動有多個翻譯
    # 這裡使用 cascade="all, delete-orphan" 來同步 Python 層面的刪除行為(當活動刪除時，相關翻譯也會被刪除)
    translations: List["EventTranslation"] = Relationship(
        back_populates="event", 
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    # Relationship: 一個活動有多個附件
    attachments: List["EventAttachment"] = Relationship(
        back_populates="event", 
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "order_by": "EventAttachment.sort_order" # 預設依 sort_order 排序(升冪)
            }
    )


# 3. 定義 EventTranslation 模型
class EventTranslation(SQLModel, table=True):
    __tablename__ = "event_translations"
    
    # 設定複合唯一鍵：(event_id + locale) 必須是唯一的，因為一個活動在同一語言只能有一筆翻譯
    __table_args__ = (
        UniqueConstraint("event_id", "locale", name="uniq_event_locale"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    
    # 外鍵：連結回主表
    # ondelete="CASCADE" 是為了配合資料庫的設定，當主活動刪除時，翻譯也一起刪除
    event_id: int = Field(
        sa_column_args=[ForeignKey("events.id", ondelete="CASCADE")]
    )
    
    # 語言代碼 (如 zh-TW)
    locale: str = Field(default="zh-TW", max_length=10)

    # 內容欄位
    title: str = Field(max_length=255)
    
    # content 對應 MEDIUMTEXT
    # 我們使用 sa_type=Text 告訴資料庫這是長文本，而不只是 VARCHAR
    content: Optional[str] = Field(default=None, sa_type=Text)
    
    location: Optional[str] = Field(default="")

    # --- 關聯屬性 (Relationship) ---
    # 這是 Python 物件層面的連結，對應回 Event
    event: Optional["Event"] = Relationship(back_populates="translations")

# 4. 定義 EventAttachment 模型
class EventAttachment(SQLModel, table=True):
    __tablename__ = "event_attachments"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    # 外鍵：連結回主表 Events
    event_id: int = Field(
        sa_column_args=[ForeignKey("events.id", ondelete="CASCADE")]
    )

    # # 類型：使用剛剛定義的 AttachmentType
    # # SQLModel 會自動驗證傳入的值是否為 'image', 'file', 'link' 其中之一
    # type: AttachmentType = Field()
    # ✅ 修改後的寫法：直接定義為 str
    # 這樣 SQLAlchemy 就會把它當作普通的 VARCHAR 字串讀出來，不會報錯
    type: str = Field(schema_extra={"comment": "image, file, link"})

    # 路徑：存 URL 或檔案路徑
    path: str = Field(max_length=500, schema_extra={"comment": "檔案路徑 或 URL"})
    
    # 標題：顯示用文字
    title: Optional[str] = Field(default="", max_length=255)
    
    # 排序
    sort_order: int = Field(default=0)

    # --- 關聯屬性 ---
    # 連結回 Event
    event: Optional["Event"] = Relationship(back_populates="attachments")