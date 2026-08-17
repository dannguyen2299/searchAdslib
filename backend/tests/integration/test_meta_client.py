"""Integration tests for MetaAdLibraryClient against a MOCKED HTTP transport
(via respx). These verify our request/response/error handling logic only —
they are NOT proof that the real Meta Ad Library API behaves this way in
production. See README.md for how to run a real-API smoke test separately.
"""

import httpx
import pytest
import respx

from app.clients.meta_ad_library_client import MetaAdLibraryClient
from app.core.logging import configure_logging
from app.core.errors import (
    MetaApiUnavailableError,
    MetaAuthenticationError,
    MetaPermissionError,
    MetaRateLimitError,
    MetaTimeoutError,
)

ADS_ARCHIVE_URL = "https://graph.facebook.com/v21.0/ads_archive"


@pytest.fixture(autouse=True)
def fast_backoff(monkeypatch):
    async def _no_sleep(self, attempt):
        return None

    monkeypatch.setattr(MetaAdLibraryClient, "_backoff", _no_sleep)


@respx.mock
async def test_search_ads_page_returns_parsed_json(settings):
    respx.get(ADS_ARCHIVE_URL).mock(
        return_value=httpx.Response(200, json={"data": [{"id": "1"}], "paging": {}})
    )

    async with httpx.AsyncClient() as http_client:
        client = MetaAdLibraryClient(settings, http_client)
        result = await client.search_ads_page(
            keyword="xe ha noi", country="VN", ad_active_status="ACTIVE", ad_type="ALL", limit=25
        )

    assert result["data"] == [{"id": "1"}]


@respx.mock
async def test_authentication_error_raises_typed_exception(settings):
    respx.get(ADS_ARCHIVE_URL).mock(
        return_value=httpx.Response(
            400, json={"error": {"message": "Invalid OAuth access token", "type": "OAuthException", "code": 190}}
        )
    )

    async with httpx.AsyncClient() as http_client:
        client = MetaAdLibraryClient(settings, http_client)
        with pytest.raises(MetaAuthenticationError):
            await client.search_ads_page(
                keyword="xe ha noi", country="VN", ad_active_status="ACTIVE", ad_type="ALL", limit=25
            )


@respx.mock
async def test_permission_error_raises_typed_exception(settings):
    respx.get(ADS_ARCHIVE_URL).mock(
        return_value=httpx.Response(
            403, json={"error": {"message": "Permission denied", "type": "OAuthException", "code": 10}}
        )
    )

    async with httpx.AsyncClient() as http_client:
        client = MetaAdLibraryClient(settings, http_client)
        with pytest.raises(MetaPermissionError):
            await client.search_ads_page(
                keyword="xe ha noi", country="VN", ad_active_status="ACTIVE", ad_type="ALL", limit=25
            )


@respx.mock
async def test_rate_limit_retries_then_raises(settings):
    route = respx.get(ADS_ARCHIVE_URL).mock(
        return_value=httpx.Response(
            400, json={"error": {"message": "Rate limit exceeded", "type": "OAuthException", "code": 613}}
        )
    )

    async with httpx.AsyncClient() as http_client:
        client = MetaAdLibraryClient(settings, http_client)
        with pytest.raises(MetaRateLimitError):
            await client.search_ads_page(
                keyword="xe ha noi", country="VN", ad_active_status="ACTIVE", ad_type="ALL", limit=25
            )

    # 1 initial attempt + meta_ad_library_max_retries retries (settings fixture uses 1)
    assert route.call_count == settings.meta_ad_library_max_retries + 1


@respx.mock
async def test_server_error_raises_unavailable_after_retries(settings):
    respx.get(ADS_ARCHIVE_URL).mock(return_value=httpx.Response(503, json={}))

    async with httpx.AsyncClient() as http_client:
        client = MetaAdLibraryClient(settings, http_client)
        with pytest.raises(MetaApiUnavailableError):
            await client.search_ads_page(
                keyword="xe ha noi", country="VN", ad_active_status="ACTIVE", ad_type="ALL", limit=25
            )


@respx.mock
async def test_timeout_raises_typed_exception(settings):
    respx.get(ADS_ARCHIVE_URL).mock(side_effect=httpx.TimeoutException("timed out"))

    async with httpx.AsyncClient() as http_client:
        client = MetaAdLibraryClient(settings, http_client)
        with pytest.raises(MetaTimeoutError):
            await client.search_ads_page(
                keyword="xe ha noi", country="VN", ad_active_status="ACTIVE", ad_type="ALL", limit=25
            )


@respx.mock
async def test_never_logs_access_token(settings, caplog):
    configure_logging()
    respx.get(ADS_ARCHIVE_URL).mock(
        return_value=httpx.Response(
            400, json={"error": {"message": "Invalid OAuth access token", "type": "OAuthException", "code": 190}}
        )
    )

    async with httpx.AsyncClient() as http_client:
        client = MetaAdLibraryClient(settings, http_client)
        with caplog.at_level("DEBUG"):
            with pytest.raises(MetaAuthenticationError):
                await client.search_ads_page(
                    keyword="xe ha noi", country="VN", ad_active_status="ACTIVE", ad_type="ALL", limit=25
                )

    assert settings.meta_access_token not in caplog.text
