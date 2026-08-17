from datetime import date

from app.models.schemas import NormalizedAd


def _first_or_none(values: list[str] | None) -> str | None:
    if not values:
        return None
    for value in values:
        if value:
            return value
    return None


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def normalize_ad(raw: dict) -> NormalizedAd:
    """Maps one raw ArchivedAd object (as returned by the ads_archive
    endpoint) into our internal NormalizedAd shape. Only maps fields that
    Meta actually documents — never fabricates landing_url or creative_url,
    since the ArchivedAd object does not expose them."""

    ad_id = raw["id"]
    end_date = _parse_date(raw.get("ad_delivery_stop_time"))

    return NormalizedAd(
        ad_id=ad_id,
        page_id=raw.get("page_id"),
        page_name=raw.get("page_name"),
        body=_first_or_none(raw.get("ad_creative_bodies")),
        headline=_first_or_none(raw.get("ad_creative_link_titles")),
        description=_first_or_none(raw.get("ad_creative_link_descriptions")),
        start_date=_parse_date(raw.get("ad_delivery_start_time")),
        end_date=end_date,
        # ArchivedAd has no explicit status field. Per Meta's own field
        # description, ad_delivery_stop_time is blank while the ad is still
        # running, so its absence is the documented signal for "active".
        status="ACTIVE" if end_date is None else "INACTIVE",
        platforms=raw.get("publisher_platforms") or [],
        creative_url=None,
        landing_url=None,
        ad_library_url=raw.get("ad_snapshot_url") or f"https://www.facebook.com/ads/library/?id={ad_id}",
        raw_data=raw,
    )
