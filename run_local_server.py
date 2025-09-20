#!/usr/bin/env python3
"""
Локальный запуск FastAPI сервера без webhook
Для разработки и тестирования API
"""

import uvicorn
import os
from dotenv import load_dotenv

# Загружаем локальные переменные
load_dotenv('.env.local')

if __name__ == "__main__":
    print("🚀 Запуск локального сервера...")
    print("📡 API будет доступно по адресу: http://127.0.0.1:8000")
    print("📖 Документация: http://127.0.0.1:8000/docs")
    print("🔍 Health check: http://127.0.0.1:8000/health")
    print("⏹️  Остановка: Ctrl+C")
    print()
    
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,      # Автоперезагрузка при изменениях
        log_level="info",
        access_log=True
    )
