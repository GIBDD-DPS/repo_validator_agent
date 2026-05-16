#!/usr/bin/env python3
"""
Точка входа для запуска сервера (локально или в облаке).
Исправлено: импортируем app из main.py напрямую.
"""

import uvicorn
import sys
import os

# Добавляем текущую директорию в путь, чтобы гарантировать импорт main
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        reload=False  # В production reload выключен
    )
