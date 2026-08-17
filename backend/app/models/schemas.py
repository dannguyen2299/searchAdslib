from datetime import date

from pydantic import BaseModel, Field


class NormalizedAd(BaseModel):
    """Internal representation of one Meta Ad Library ad, independent of the
    raw Graph API shape so the rest of the app never touches raw field names."""

    ad_id: str
    page_id: str | None = None
    page_name: str | None = None
    body: str | None = None
    headline: str | None = None
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: str | None = None
    platforms: list[str] = Field(default_factory=list)
    creative_url: str | None = None
    landing_url: str | None = None
    ad_library_url: str | None = None
    raw_data: dict = Field(default_factory=dict)
    relevance_score: float = 0.0


class AdOut(BaseModel):
    ad_id: str
    page_id: str | None
    page_name: str | None
    body: str | None
    headline: str | None
    description: str | None
    status: str | None
    start_date: date | None
    end_date: date | None
    platforms: list[str]
    creative_url: str | None
    landing_url: str | None
    ad_library_url: str | None


class SearchMeta(BaseModel):
    total: int
    keyword: str
    country: str
    status: str
    ad_type: str
    limitation_notice: str | None = None


class SearchResponse(BaseModel):
    data: list[AdOut]
    meta: SearchMeta
