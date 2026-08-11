"""VeriMind AI - FastAPI Application Entry Point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database.connection import connect_db, close_db
from app.api.chat import router as chat_router
from app.api.history import router as history_router
from app.api.files import router as files_router

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown events."""
    await connect_db()
    yield
    await close_db()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Intent-Aligned, Evidence-Grounded AI Assistant",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(history_router)
app.include_router(files_router)

@app.get("/api")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "description": "Intent-Aligned, Evidence-Grounded AI Assistant",
    }

@app.get("/api/health")
async def health():
    return {"status": "healthy"}

# Serve Frontend statically if it exists (for Docker / Production deployment)
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")

if os.path.exists(frontend_dist):
    # Serve static files (js, css, assets)
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    
    # Catch-all for SPA routing to serve index.html
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        path_to_file = os.path.join(frontend_dist, full_path)
        if os.path.isfile(path_to_file):
            return FileResponse(path_to_file)
        return FileResponse(os.path.join(frontend_dist, "index.html"))

