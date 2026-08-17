from datetime import date

from app.core.normalize import normalize_ad


def _raw_ad(**overrides) -> dict:
    base = {
        "id": "123456789",
        "page_id": "999",
        "page_name": "Nha Xe ABC",
        "ad_creative_bodies": ["Xe Ha Noi Sai Gon chat luong cao"],
        "ad_creative_link_titles": ["Xe Ha Noi Sai Gon"],
        "ad_creative_link_descriptions": ["Dat ve ngay"],
        "ad_delivery_start_time": "2026-08-12",
        "ad_delivery_stop_time": None,
        "ad_snapshot_url": "https://www.facebook.com/ads/library/?id=123456789&access_token=abc",
        "publisher_platforms": ["facebook", "instagram"],
    }
    base.update(overrides)
    return base


def test_normalize_maps_documented_fields():
    ad = normalize_ad(_raw_ad())

    assert ad.ad_id == "123456789"
    assert ad.page_id == "999"
    assert ad.page_name == "Nha Xe ABC"
    assert ad.body == "Xe Ha Noi Sai Gon chat luong cao"
    assert ad.headline == "Xe Ha Noi Sai Gon"
    assert ad.description == "Dat ve ngay"
    assert ad.start_date == date(2026, 8, 12)
    assert ad.platforms == ["facebook", "instagram"]


def test_normalize_prefers_official_ad_snapshot_url():
    ad = normalize_ad(_raw_ad())
    assert ad.ad_library_url == "https://www.facebook.com/ads/library/?id=123456789&access_token=abc"


def test_normalize_falls_back_to_constructed_url_when_snapshot_missing():
    ad = normalize_ad(_raw_ad(ad_snapshot_url=None))
    assert ad.ad_library_url == "https://www.facebook.com/ads/library/?id=123456789"


def test_normalize_never_fabricates_landing_or_creative_url():
    ad = normalize_ad(_raw_ad())
    assert ad.landing_url is None
    assert ad.creative_url is None


def test_normalize_status_active_when_no_stop_time():
    ad = normalize_ad(_raw_ad(ad_delivery_stop_time=None))
    assert ad.status == "ACTIVE"
    assert ad.end_date is None


def test_normalize_status_inactive_when_stop_time_present():
    ad = normalize_ad(_raw_ad(ad_delivery_stop_time="2026-08-15"))
    assert ad.status == "INACTIVE"
    assert ad.end_date == date(2026, 8, 15)


def test_normalize_handles_empty_creative_lists():
    ad = normalize_ad(_raw_ad(ad_creative_bodies=[], ad_creative_link_titles=[], ad_creative_link_descriptions=[]))
    assert ad.body is None
    assert ad.headline is None
    assert ad.description is None
