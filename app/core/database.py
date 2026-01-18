import os, ssl
from typing import Generator
from sqlmodel import create_engine, SQLModel, Session
from dotenv import load_dotenv


# 1. 載入環境變數
load_dotenv()

# 2. 取得連線字串
# 改回純粹從環境變數讀取，不留 SQLite 預設值
DATABASE_URL = os.getenv("DATABASE_URL")

# 2.1 確保 DATABASE_URL 存在
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in .env file or environment variables")

# 這些只是為了aiven，後續上線不用管它們
# --- (核心修改) 建立自定義 SSL Context ---
# 目的：允許加密連線，但跳過對 Aiven 自簽名憑證的驗證
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE    

# 3. 建立 Engine
# pool_recycle=3600: 每小時自動回收連線，防止 MySQL 閒置過久斷線
# pool_pre_ping=True: 針對 Aiven 雲端資料庫建議開啟，連線前會先測試有效性
# echo=True: 開發時顯示 SQL，上線部署時可改為 False
engine = create_engine(
    DATABASE_URL, 
    echo=True, 
    pool_recycle=3600,
    pool_pre_ping=True,
    # 將 ssl_context 傳入 connect_args
    connect_args={"ssl": ssl_context}
)

# 4. 建立資料庫和表格
def create_db_and_tables():
    # =========================================================
    # [重要] 必須在這裡 import 所有的 Model
    # =========================================================
    from app.models.event_model import Event, EventCategory, EventTranslation, EventAttachment
    
    # 開始建立表格
    SQLModel.metadata.create_all(engine)

# 5. 提供資料庫會話 (Dependency)
def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session