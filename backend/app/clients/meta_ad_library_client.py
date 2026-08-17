import asyncio
import json

import httpx

from app.config import Settings
from app.core.errors import (
    MetaApiError,
    MetaApiUnavailableError,
    MetaAuthenticationError,
    MetaBadRequestError,
    MetaPermissionError,
    MetaRateLimitError,
    MetaTimeoutError,
)
from app.core.logging import get_logger, redact_params

logger = get_logger(__name__)

# Fields we actually use, from the official ArchivedAd reference:
# https://developers.facebook.com/docs/marketing-api/reference/archived-ad/
FIELDS = [
    "id",
    "ad_creation_time",
    "ad_creative_bodies",
    "ad_creative_link_captions",
    "ad_creative_link_descriptions",
    "ad_creative_link_titles",
    "ad_delivery_start_time",
    "ad_delivery_stop_time",
    "ad_snapshot_url",
    "languages",
    "page_id",
    "page_name",
    "publisher_platforms",
]

# error codes documented/observed for the Graph API — see
# https://developers.facebook.com/docs/graph-api/guides/error-handling/
_AUTH_ERROR_CODES = {190}
_RATE_LIMIT_ERROR_CODES = {4, 17, 32, 613}
_PERMISSION_ERROR_CODES = {10, 200, 299}


class MetaAdLibraryClient:
    """Thin wrapper around the Graph API `ads_archive` endpoint.

    Scope note: per Meta's own documentation, ads that did not reach any
    location in the EU only come back if they are about social issues,
    elections or politics. For non-EU/UK countries this endpoint will NOT
    return ordinary commercial ads — that limitation lives here, not in the
    caller, so every consumer of this client inherits it automatically.
    """

    def __init__(self, settings: Settings, http_client: httpx.AsyncClient | None = None):
        self._settings = settings
        self._owns_client = http_client is None
        self._client = http_client or httpx.AsyncClient(
            timeout=settings.meta_ad_library_request_timeout_seconds
        )

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    def _base_url(self) -> str:
        return f"{self._settings.meta_graph_api_base_url}/{self._settings.meta_graph_api_version}/ads_archive"

    async def search_ads_page(
        self,
        *,
        keyword: str,
        country: str,
        ad_active_status: str,
        ad_type: str,
        limit: int,
        after: str | None = None,
    ) -> dict:
        """Fetches one page of results. Raises a typed MetaApiError subclass
        on failure; never returns partial/garbage data silently."""

        params = {
            "access_token": self._settings.meta_access_token,
            "search_terms": keyword,
            "ad_reached_countries": json.dumps([country]),
            "ad_active_status": ad_active_status,
            "ad_type": ad_type,
            "fields": ",".join(FIELDS),
            "limit": limit,
        }
        if after:
            params["after"] = after

        return await self._request_with_retry(params)

    async def _request_with_retry(self, params: dict) -> dict:
        max_retries = self._settings.meta_ad_library_max_retries
        attempt = 0

        while True:
            attempt += 1
            try:
                response = await self._client.get(self._base_url(), params=params)
            except httpx.TimeoutException as exc:
                raise MetaTimeoutError("Meta Ad Library API request timed out.") from exc
            except httpx.HTTPError as exc:
                if attempt <= max_retries:
                    await self._backoff(attempt)
                    continue
                raise MetaApiUnavailableError(f"Network error calling Meta Ad Library API: {exc}") from exc

            if response.status_code == 200:
                return response.json()

            error = self._classify_error(response)

            if isinstance(error, (MetaRateLimitError, MetaApiUnavailableError)) and attempt <= max_retries:
                logger.warning(
                    "Retrying Meta Ad Library API call (attempt %s/%s) after %s",
                    attempt,
                    max_retries,
                    type(error).__name__,
                )
                await self._backoff(attempt)
                continue

            raise error

    async def _backoff(self, attempt: int) -> None:
        await asyncio.sleep(min(2 ** attempt, 30))

    def _classify_error(self, response: httpx.Response) -> MetaApiError:
        status_code = response.status_code
        try:
            body = response.json()
            error_body = body.get("error", {})
        except ValueError:
            error_body = {}

        message = error_body.get("message") or f"Meta API returned HTTP {status_code}"
        code = error_body.get("code")

        logger.error(
            "Meta Ad Library API error: status=%s code=%s params=%s",
            status_code,
            code,
            redact_params(dict(response.request.url.params)) if response.request else {},
        )

        if code in _AUTH_ERROR_CODES or status_code == 401:
            return MetaAuthenticationError(
                "Meta API authentication failed. Please check META_ACCESS_TOKEN.",
                status_code=status_code,
                meta_code=code,
            )
        if code in _PERMISSION_ERROR_CODES or status_code == 403:
            return MetaPermissionError(
                "The Meta access token does not have permission for the Ad Library API "
                "(identity confirmation at facebook.com/ID may be required). "
                f"Meta message: {message}",
                status_code=status_code,
                meta_code=code,
            )
        if code in _RATE_LIMIT_ERROR_CODES or status_code == 429:
            return MetaRateLimitError(
                "Meta Ad Library API rate limit exceeded. Please retry later.",
                status_code=status_code,
                meta_code=code,
            )
        if status_code >= 500:
            return MetaApiUnavailableError(
                f"Meta Ad Library API is currently unavailable ({status_code}).",
                status_code=status_code,
                meta_code=code,
            )
        return MetaBadRequestError(message, status_code=status_code, meta_code=code)
