from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Meta Ad Library API
    meta_access_token: str = ""
    meta_app_id: str = ""
    meta_app_secret: str = ""
    meta_graph_api_version: str = "v21.0"
    meta_graph_api_base_url: str = "https://graph.facebook.com"

    meta_ad_library_country: str = "VN"
    meta_ad_library_max_results: int = 100
    meta_ad_library_cache_ttl: int = 3600
    meta_ad_library_request_timeout_seconds: float = 15.0
    meta_ad_library_max_retries: int = 3

    # Database
    database_url: str = "postgresql+psycopg2://adslib:adslib@localhost:5432/adslib"

    # App
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
