from app.models.schemas import NormalizedAd
from app.services.meta_ad_library_service import MetaAdLibraryService


def _ad(ad_id: str) -> NormalizedAd:
    return NormalizedAd(ad_id=ad_id)


def test_deduplicate_keeps_first_occurrence_only():
    ads = [_ad("1"), _ad("2"), _ad("1"), _ad("3"), _ad("2")]

    unique = MetaAdLibraryService._deduplicate(ads)

    assert [ad.ad_id for ad in unique] == ["1", "2", "3"]


def test_deduplicate_handles_empty_list():
    assert MetaAdLibraryService._deduplicate([]) == []
