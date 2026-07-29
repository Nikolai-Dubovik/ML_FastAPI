"""Сборка приложения. Точка входа: uvicorn app.main:app"""

from fastapi import FastAPI

from app.api import router
from app.config import APP_TITLE
from app.errors import register_error_handlers

app = FastAPI(title=APP_TITLE)
register_error_handlers(app)
app.include_router(router)
