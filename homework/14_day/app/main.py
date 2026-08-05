from fastapi import FastAPI

from app.api import router
from app.errors import register_error_handlers

app = FastAPI(title="ML Churn Service")
register_error_handlers(app)
app.include_router(router)
