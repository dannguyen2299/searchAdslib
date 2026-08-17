from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.clients.meta_ad_library_client import MetaAdLibraryClient
from app.config import Settings, get_settings
from app.core.cache import TTLCache
from app.db.base import get_db
from app.repositories.ad_repository import AdRepository
from app.services.meta_ad_library_service import MetaAdLibraryService


def get_client(request: Request) -> MetaAdLibraryClient:
    return request.app.state.meta_client


def get_cache(request: Request) -> TTLCache:
    return request.app.state.cache


def get_service(
    settings: Settings = Depends(get_settings),
    client: MetaAdLibraryClient = Depends(get_client),
    cache: TTLCache = Depends(get_cache),
    db: Session = Depends(get_db),
) -> MetaAdLibraryService:
    return MetaAdLibraryService(settings, client, cache, AdRepository(db))
