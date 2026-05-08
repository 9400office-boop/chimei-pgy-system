FROM python:3.12-slim

WORKDIR /app

# 安裝相依
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製所有檔案
COPY . .

# 第一次啟動執行 seed.py 寫入種子資料 (若 chimei.db 已存在則略過)
RUN python -c "import os; os.path.exists('chimei.db') or __import__('seed').seed()"

# Railway / Render / Fly 會自動帶入 PORT 環境變數
EXPOSE 8000

CMD ["sh", "-c", "python -c 'import os; not os.path.exists(\"chimei.db\") and __import__(\"seed\").seed()' && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
