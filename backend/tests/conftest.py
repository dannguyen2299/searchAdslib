import pytest

from app.config import Settings


@pytest.fixture
def settings() -> Settings:
    """Settings tuned for fast tests: short retries/backoff, fake token."""
    return Settings(
        meta_access_token="test-token",
        meta_graph_api_base_url="https://graph.facebook.com",
        meta_graph_api_version="v21.0",
        meta_ad_library_max_results=10,
        meta_ad_library_max_retries=1,
        meta_ad_library_request_timeout_seconds=1.0,
        meta_ad_library_cache_ttl=0,
        database_url="sqlite:///:memory:",
    )
