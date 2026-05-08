#!/bin/sh
set -e

echo "==========================================="
echo "  Chimei PGY Demo - Starting up..."
echo "==========================================="
echo "  PORT       = ${PORT:-8000}"
echo "  AUTH       = $([ -n "$DEMO_USER" ] && [ -n "$DEMO_PASSWORD" ] && echo 'enabled' || echo 'disabled')"
echo "==========================================="

# 第一次啟動時 seed 資料 (容器內 chimei.db 不存在的話)
if [ ! -f chimei.db ]; then
    echo "📦 chimei.db not found, seeding..."
    python seed.py
fi

# 啟動 uvicorn (exec 讓訊號正確傳遞)
echo "🚀 Starting uvicorn on 0.0.0.0:${PORT:-8000}"
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}" --log-level info
