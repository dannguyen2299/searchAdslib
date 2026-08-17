import time

from app.clients.meta_ad_library_client import MetaAdLibraryClient
from app.config import Settings
from app.core.cache import TTLCache
from app.core.logging import get_logger
from app.core.normalize import normalize_ad
from app.core.ranking import rank_ads
from app.models.schemas import NormalizedAd
from app.repositories.ad_repository import AdRepository

logger = get_logger(__name__)

PAGE_SIZE = 25

# ISO 3166-1 alpha-2 codes for the EU + UK. Per Meta's own ads_archive docs,
# ads that never reached one of these only come back from the API if they
# are about social issues, elections or politics — everything else (i.e.
# ordinary commercial ads) is invisible to the API outside this set.
EU_UK_COUNTRIES = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR",
    "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK",
    "SI", "ES", "SE", "GB",
}

NON_EU_UK_COMMERCIAL_NOTICE = (
    "'{country}' is outside the EU/UK, so per Meta's Ad Library API scope only "
    "ads about social issues, elections or politics reaching '{country}' can be "
    "returned — ordinary commercial ads are not available through this API for "
    "this country. Select ad_type=POLITICAL_AND_ISSUE_ADS for real results here, "
    "or pick an EU/UK country to search commercial ads."
)


class SearchResult:
    def __init__(self, ads: list[NormalizedAd], limitation_notice: str | None):
        self.ads = ads
        self.limitation_notice = limitation_notice


class MetaAdLibraryService:
    def __init__(
        self,
        settings: Settings,
        client: MetaAdLibraryClient,
        cache: TTLCache,
        repository: AdRepository | None = None,
    ):
        self._settings = settings
        self._client = client
        self._cache = cache
        self._repository = repository

    async def search(
        self,
        *,
        keyword: str,
        country: str,
        status: str,
        ad_type: str = "ALL",
    ) -> SearchResult:
        cache_key = TTLCache.build_key(keyword, country, status, ad_type)
        cached = self._cache.get(cache_key)
        if cached is not None:
            logger.info("Cache hit keyword=%s country=%s status=%s", keyword, country, status)
            return cached

        started_at = time.monotonic()
        logger.info("Ad Library search started keyword=%s country=%s status=%s ad_type=%s", keyword, country, status, ad_type)

        raw_ads = await self._fetch_all_pages(keyword=keyword, country=country, status=status, ad_type=ad_type)

        normalized = self._deduplicate([normalize_ad(raw) for raw in raw_ads])
        ranked = rank_ads(normalized, keyword)

        if self._repository is not None:
            self._repository.upsert_many(ranked, keyword=keyword)

        limitation_notice = None
        if country.upper() not in EU_UK_COUNTRIES:
            limitation_notice = NON_EU_UK_COMMERCIAL_NOTICE.format(country=country.upper())

        result = SearchResult(ads=ranked, limitation_notice=limitation_notice)
        self._cache.set(cache_key, result, self._settings.meta_ad_library_cache_ttl)

        elapsed = time.monotonic() - started_at
        logger.info(
            "Ad Library search finished keyword=%s results=%s elapsed_seconds=%.2f",
            keyword,
            len(ranked),
            elapsed,
        )
        return result

    async def _fetch_all_pages(self, *, keyword: str, country: str, status: str, ad_type: str) -> list[dict]:
        max_results = self._settings.meta_ad_library_max_results
        collected: list[dict] = []
        after: str | None = None
        page_number = 0

        while len(collected) < max_results:
            page_number += 1
            remaining = max_results - len(collected)
            page_limit = min(PAGE_SIZE, remaining)

            logger.info("Fetching page=%s after=%s limit=%s", page_number, bool(after), page_limit)
            response = await self._client.search_ads_page(
                keyword=keyword,
                country=country,
                ad_active_status=status,
                ad_type=ad_type,
                limit=page_limit,
                after=after,
            )

            data = response.get("data", [])
            if not data:
                break
            collected.extend(data)

            paging = response.get("paging", {})
            after = paging.get("cursors", {}).get("after")
            if not paging.get("next") or not after:
                break

        return collected[:max_results]

    @staticmethod
    def _deduplicate(ads: list[NormalizedAd]) -> list[NormalizedAd]:
        seen: set[str] = set()
        unique: list[NormalizedAd] = []
        for ad in ads:
            if ad.ad_id in seen:
                continue
            seen.add(ad.ad_id)
            unique.append(ad)
        return unique
