"""Integration tests for MetaAdLibraryService pagination control, using a
fake MetaAdLibraryClient (no real network / no respx) so we can assert on
exactly how many pages were requested and that max_results is enforced.
"""

import pytest

from app.core.cache import TTLCache
from app.services.meta_ad_library_service import MetaAdLibraryService


class FakeClient:
    def __init__(self, pages: list[dict]):
        self._pages = pages
        self.calls: list[dict] = []

    async def search_ads_page(self, **kwargs):
        self.calls.append(kwargs)
        index = len(self.calls) - 1
        if index >= len(self._pages):
            return {"data": [], "paging": {}}
        return self._pages[index]


def _raw(ad_id: str) -> dict:
    return {
        "id": ad_id,
        "page_id": "1",
        "page_name": "Page",
        "ad_creative_bodies": ["body"],
        "ad_creative_link_titles": [],
        "ad_creative_link_descriptions": [],
        "ad_delivery_start_time": "2026-08-01",
        "ad_delivery_stop_time": None,
        "ad_snapshot_url": f"https://www.facebook.com/ads/library/?id={ad_id}",
        "publisher_platforms": ["facebook"],
    }


async def test_follows_pagination_cursor_across_pages(settings):
    pages = [
        {"data": [_raw("1"), _raw("2")], "paging": {"cursors": {"after": "CURSOR1"}, "next": "https://x/next"}},
        {"data": [_raw("3")], "paging": {}},
    ]
    client = FakeClient(pages)
    service = MetaAdLibraryService(settings, client, TTLCache())

    result = await service.search(keyword="xe", country="VN", status="ACTIVE")

    assert {ad.ad_id for ad in result.ads} == {"1", "2", "3"}
    assert len(client.calls) == 2
    assert client.calls[1]["after"] == "CURSOR1"


async def test_stops_when_no_next_cursor(settings):
    pages = [{"data": [_raw("1")], "paging": {}}]
    client = FakeClient(pages)
    service = MetaAdLibraryService(settings, client, TTLCache())

    result = await service.search(keyword="xe", country="VN", status="ACTIVE")

    assert len(result.ads) == 1
    assert len(client.calls) == 1


async def test_never_exceeds_configured_max_results(settings):
    settings.meta_ad_library_max_results = 5
    pages = [
        {"data": [_raw(str(i)) for i in range(25)], "paging": {"cursors": {"after": "C1"}, "next": "https://x"}},
        {"data": [_raw(str(i)) for i in range(25, 50)], "paging": {"cursors": {"after": "C2"}, "next": "https://x"}},
    ]
    client = FakeClient(pages)
    service = MetaAdLibraryService(settings, client, TTLCache())

    result = await service.search(keyword="xe", country="VN", status="ACTIVE")

    assert len(result.ads) <= 5


async def test_limitation_notice_present_for_non_eu_uk_country(settings):
    client = FakeClient([{"data": [_raw("1")], "paging": {}}])
    service = MetaAdLibraryService(settings, client, TTLCache())

    result = await service.search(keyword="xe", country="VN", status="ACTIVE")

    assert result.limitation_notice is not None
    assert "VN" in result.limitation_notice


async def test_no_limitation_notice_for_eu_country(settings):
    client = FakeClient([{"data": [_raw("1")], "paging": {}}])
    service = MetaAdLibraryService(settings, client, TTLCache())

    result = await service.search(keyword="xe", country="DE", status="ACTIVE")

    assert result.limitation_notice is None
