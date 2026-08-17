from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_service
from app.models.schemas import AdOut, SearchMeta, SearchResponse
from app.services.meta_ad_library_service import MetaAdLibraryService

router = APIRouter(prefix="/api/ads", tags=["ads"])

VALID_STATUSES = {"ACTIVE", "INACTIVE", "ALL"}
VALID_AD_TYPES = {"ALL", "POLITICAL_AND_ISSUE_ADS", "HOUSING_ADS", "EMPLOYMENT_ADS", "FINANCIAL_PRODUCTS_AND_SERVICES_ADS"}


@router.get("/search", response_model=SearchResponse)
async def search_ads(
    keyword: str = Query(..., min_length=1, description="Required search keyword"),
    country: str = Query("VN", min_length=2, max_length=2, description="ISO 3166-1 alpha-2 country code"),
    status: str = Query("ACTIVE"),
    ad_type: str = Query("ALL"),
    service: MetaAdLibraryService = Depends(get_service),
) -> SearchResponse:
    keyword = keyword.strip()
    if not keyword:
        raise HTTPException(status_code=400, detail="keyword is required")

    status = status.upper()
    if status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"status must be one of {sorted(VALID_STATUSES)}")

    ad_type = ad_type.upper()
    if ad_type not in VALID_AD_TYPES:
        raise HTTPException(status_code=400, detail=f"ad_type must be one of {sorted(VALID_AD_TYPES)}")

    result = await service.search(keyword=keyword, country=country.upper(), status=status, ad_type=ad_type)

    data = [
        AdOut(
            ad_id=ad.ad_id,
            page_id=ad.page_id,
            page_name=ad.page_name,
            body=ad.body,
            headline=ad.headline,
            description=ad.description,
            status=ad.status,
            start_date=ad.start_date,
            end_date=ad.end_date,
            platforms=ad.platforms,
            creative_url=ad.creative_url,
            landing_url=ad.landing_url,
            ad_library_url=ad.ad_library_url,
        )
        for ad in result.ads
    ]

    return SearchResponse(
        data=data,
        meta=SearchMeta(
            total=len(data),
            keyword=keyword,
            country=country.upper(),
            status=status,
            ad_type=ad_type,
            limitation_notice=result.limitation_notice,
        ),
    )
