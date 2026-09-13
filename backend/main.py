import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config.settings import settings
from backend.api.routes import router as api_router
from backend.database.mongo import db_manager
from backend.services.live_tracking_service import live_tracking_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing SAHYOG Cryptocurrency Attribution Workstation backend...")
    await db_manager.initialize()
    live_tracking_service.start_scheduler()
    yield
    # Shutdown
    logger.info("Shutting down background tasks...")
    live_tracking_service.stop_scheduler()


app = FastAPI(
    title="TraceACT - Cryptocurrency Forensic Intelligence Platform",
    description="Cryptocurrency Wallet Multi-Hop Forensic Intelligence Platform",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {
        "service": "TraceACT Cryptocurrency Wallet Attribution & Forensics Engine",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/api/health",
        "database": db_manager.get_status(),
        "ollamaHost": settings.OLLAMA_HOST,
        "endpoints": {
            "detect_chain": "POST /api/wallet/detect",
            "analyze_wallet": "POST /api/wallet/analyze",
            "trace_wallet": "POST /api/wallet/trace",
            "attribute_vasp": "POST /api/wallet/attribution",
            "expand_node": "POST /api/investigation/expand-node",
            "live_tracking": "POST /api/tracking/enable",
            "generate_report": "POST /api/report/generate",
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8001, reload=True)
