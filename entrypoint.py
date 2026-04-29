# entrypoint.py – точка входа для Yandex Cloud Functions
from mangum import Mangum
from main import app  # импортируем наше FastAPI-приложение

# Mangum оборачивает ASGI-приложение в функцию handler
handler = Mangum(app, lifespan="off")
