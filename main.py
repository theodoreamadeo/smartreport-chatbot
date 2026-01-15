# app/main.py
from fastapi import FastAPI
from app.api.webhook import router as webhook_router
from app.api.health import router as health_router
from app.services.vector_db import vector_db
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    print("🚀 Starting up...")
    vector_db.load_excel_to_vectordb()
    print("Vector database loaded")
    yield
    # Shutdown code (if needed)
    print("Shutting down...")

def create_app() -> FastAPI:
    app = FastAPI(
        title="Telegram OpenAI Bot",
        lifespan=lifespan
    )

    app.include_router(health_router, prefix="/health", tags=["health"])
    app.include_router(webhook_router, prefix="/telegram", tags=["telegram"])

    return app

app = create_app()