from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ad import Ad
from app.models.schemas import NormalizedAd


class AdRepository:
    """Persists normalized ads. Upserts on the unique ad_id so re-running the
    same search never creates duplicate rows."""

    def __init__(self, db: Session):
        self.db = db

    def upsert_many(self, ads: list[NormalizedAd], keyword: str) -> None:
        if not ads:
            return

        ad_ids = [ad.ad_id for ad in ads]
        existing = {
            row.ad_id: row
            for row in self.db.execute(select(Ad).where(Ad.ad_id.in_(ad_ids))).scalars()
        }
        now = datetime.now(timezone.utc)

        for ad in ads:
            row = existing.get(ad.ad_id)
            if row is None:
                row = Ad(ad_id=ad.ad_id)
                self.db.add(row)

            row.page_id = ad.page_id
            row.page_name = ad.page_name
            row.body = ad.body
            row.headline = ad.headline
            row.description = ad.description
            row.start_date = ad.start_date
            row.end_date = ad.end_date
            row.status = ad.status
            row.platforms = ad.platforms
            row.creative_url = ad.creative_url
            row.landing_url = ad.landing_url
            row.ad_library_url = ad.ad_library_url
            row.raw_data = ad.raw_data
            row.keyword = keyword
            row.fetched_at = now

        self.db.commit()
