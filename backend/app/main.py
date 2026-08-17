from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.error_handlers import register_error_handlers
from app.api.routes.ads import router as ads_router
from app.clients.meta_ad_library_client import MetaAdLibraryClient
from app.config import get_settings
from app.core.cache import TTLCache
from app.core.logging import configure_logging, get_logger
from app.db.base import Base, engine

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    settings = get_settings()

    # MVP: create tables directly from models instead of a migration tool.
    # Revisit with Alembic once the schema needs to evolve across environments.
    Base.metadata.create_all(bind=engine)

    app.state.meta_client = MetaAdLibraryClient(settings, httpx.AsyncClient(timeout=settings.meta_ad_library_request_timeout_seconds))
    app.state.cache = TTLCache()

    logger.info("Application startup complete")
    yield

    await app.state.meta_client.aclose()
    logger.info("Application shutdown complete")


app = FastAPI(title="Facebook Ads Library Research Tool", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

register_error_handlers(app)
app.include_router(ads_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
