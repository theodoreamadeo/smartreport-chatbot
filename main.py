# app/main.py
from fastapi import FastAPI
from app.api.webhook import router as webhook_router
from app.api.health import router as health_router

def create_app() -> FastAPI:
    app = FastAPI(title="Telegram OpenAI Bot")

    app.include_router(health_router, prefix="/health", tags=["health"])
    app.include_router(webhook_router, prefix="/telegram", tags=["telegram"])

    return app

app = create_app()