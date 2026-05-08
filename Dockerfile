FROM python:3.12-slim

WORKDIR /app

# 安裝相依
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製所有檔案
COPY . .

# 確保 start.sh 可執行
RUN chmod +x start.sh

# Railway / Render / Fly 會自動帶入 PORT 環境變數
EXPOSE 8000

# 用 start.sh 啟動 (內含 seed + uvicorn)
CMD ["./start.sh"]
