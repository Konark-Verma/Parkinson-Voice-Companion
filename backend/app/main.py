import os
import json
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.core.config import CLINICAL_SAFETY_DISCLAIMER, UPLOAD_DIR
from backend.app.core.database import init_db, AsyncSessionLocal
from backend.app.seed.seed_data import seed_database
from backend.app.ml.classifier import ParkinsonVoiceClassifier
from backend.app.websocket.ws_manager import ws_manager

from backend.app.api.auth import router as auth_router
from backend.app.api.patients import router as patients_router
from backend.app.api.voice_samples import router as voice_samples_router
from backend.app.api.medications import router as medications_router
from backend.app.api.therapy import router as therapy_router
from backend.app.api.alerts import router as alerts_router
from backend.app.api.dashboard import router as dashboard_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("main")

FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("[STARTUP] Initializing database schema...")
    await init_db()

    logger.info("[STARTUP] Initializing ML classifier model...")
    ParkinsonVoiceClassifier.get_instance()

    logger.info("[STARTUP] Initializing clinical seed data...")
    async with AsyncSessionLocal() as session:
        await seed_database(session)

    logger.info("[STARTUP] Parkinson's Voice Companion system is fully ready.")
    yield
    logger.info("[SHUTDOWN] Terminating services.")

app = FastAPI(
    title="Parkinson's Voice Companion API",
    description="A voice-based screening, monitoring, and therapy companion backend for Parkinson's Disease.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if UPLOAD_DIR.exists():
    app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

@app.websocket("/ws/{user_id}/{role}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, role: str):
    await ws_manager.connect(websocket, user_id=user_id, role=role.upper())
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("action") == "PING":
                    await websocket.send_text(json.dumps({"action": "PONG"}))
            except Exception:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user_id=user_id, role=role.upper())

app.include_router(auth_router, prefix="/api")
app.include_router(patients_router, prefix="/api")
app.include_router(voice_samples_router, prefix="/api")
app.include_router(medications_router, prefix="/api")
app.include_router(therapy_router, prefix="/api")
app.include_router(alerts_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")

@app.get("/health")
@app.get("/api/health")
async def health_check():
    return {
        "status": "HEALTHY",
        "ml_classifier": "READY",
        "disclaimer": CLINICAL_SAFETY_DISCLAIMER
    }

# Mount frontend production dist if built
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="static_assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/") or full_path.startswith("uploads/") or full_path.startswith("ws/"):
            return None
        file_target = FRONTEND_DIST / full_path
        if file_target.exists() and file_target.is_file():
            return FileResponse(file_target)
        return FileResponse(FRONTEND_DIST / "index.html")
else:
    @app.get("/")
    async def root():
        return {
            "service": "Parkinson's Voice Companion API",
            "status": "ONLINE",
            "version": "1.0.0",
            "disclaimer": CLINICAL_SAFETY_DISCLAIMER
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
