# 1. 使用官方輕量級 Python 鏡像
FROM python:3.11-slim

# 2. 設定容器內的工作目錄
WORKDIR /app

# 3. 設定環境變數
# 防止 Python 產生 .pyc 檔案
ENV PYTHONDONTWRITEBYTECODE=1
# 確保日誌直接輸出到終端機，方便 Cloud Run 監控
ENV PYTHONUNBUFFERED=1
# Cloud Run 預設監聽埠
ENV PORT=8080

# 4. 安裝系統依賴（僅安裝執行 pymysql 所需的最小基礎套件）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 5. 安裝 Python 套件
# 先複製 requirements.txt 以利用 Docker 的快取機制 (Caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# 6. 複製專案程式碼
# 將本地的 app 目錄複製到容器的 /app/app
COPY ./app ./app

# 7. 建立上傳檔案目錄（確保 app.mount 運作正常）
RUN mkdir -p uploads

# 8. 啟動指令
# --host 0.0.0.0：必須設定為此值才能讓外部存取容器
# --port 8080：對應 Cloud Run 的預設埠
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]