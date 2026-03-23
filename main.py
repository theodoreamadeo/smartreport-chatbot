# app/main.py
from fastapi import FastAPI
from app.api.webhook import router as webhook_router
from app.api.health import router as health_router
from contextlib import asynccontextmanager
from app.services.vector_db import VectorDBService
from app.services.pdf_knowledge_management import KnowledgeBaseManager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    print("Starting up the codebase")
    
    # Initialize vector DB
    vector_db_service = VectorDBService()
    
    # Initialize knowledge base manager
    kb_manager = KnowledgeBaseManager(pdf_directory="src")
    
    # Update knowledge base if needed
    chunks_processed = kb_manager.update_knowledge_base(vector_db_service)
    
    # Store in app state for access in other modules
    app.state.vector_db = vector_db_service
    app.state.kb_manager = kb_manager
    
    print(f"Application started successfully! Processed {chunks_processed} chunks.")
    
    yield
    
    # Shutdown code (optional)
    print("Shutting down the codebase")

def create_app() -> FastAPI:
    app = FastAPI(
        title="Telegram OpenAI Bot",
        lifespan=lifespan
    )

    app.include_router(health_router, prefix="/health", tags=["health"])
    app.include_router(webhook_router, prefix="/telegram", tags=["telegram"])

    return app

app = create_app()