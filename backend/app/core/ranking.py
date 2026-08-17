import re
from datetime import date
from typing import Protocol

from app.models.schemas import NormalizedAd

EXACT_PHRASE_SCORE = 100.0
ALL_WORDS_SCORE = 75.0
PARTIAL_WORD_SCORE = 50.0
PAGE_NAME_SCORE = 25.0
NO_MATCH_SCORE = 0.0


class RankingStrategy(Protocol):
    """Swappable relevance scoring strategy. The MVP ships a plain keyword
    matcher (`KeywordRankingStrategy`); a future AI/NLP ranker just needs to
    implement this same `score` method and can be dropped in without
    touching the service layer."""

    def score(self, ad: NormalizedAd, keyword: str) -> float: ...


def _tokenize(text: str) -> list[str]:
    return [t for t in re.split(r"\s+", text.strip().lower()) if t]


class KeywordRankingStrategy:
    """Tiered relevance: exact phrase > all keyword words present > partial
    word overlap > page name match only > no match. Never used to drop
    results — only to order them — since Meta's search_terms filter already
    determined the candidate set."""

    def score(self, ad: NormalizedAd, keyword: str) -> float:
        keyword_norm = keyword.strip().lower()
        keyword_words = set(_tokenize(keyword))
        if not keyword_norm or not keyword_words:
            return NO_MATCH_SCORE

        content_fields = [ad.body, ad.headline, ad.description]
        content_text = " ".join(f for f in content_fields if f).lower()
        content_words = set(_tokenize(content_text))

        if keyword_norm in content_text:
            return EXACT_PHRASE_SCORE

        if keyword_words and keyword_words.issubset(content_words):
            return ALL_WORDS_SCORE

        if keyword_words & content_words:
            return PARTIAL_WORD_SCORE

        page_name = (ad.page_name or "").lower()
        page_name_words = set(_tokenize(page_name))
        if keyword_norm in page_name or (keyword_words & page_name_words):
            return PAGE_NAME_SCORE

        return NO_MATCH_SCORE


def rank_ads(ads: list[NormalizedAd], keyword: str, strategy: RankingStrategy | None = None) -> list[NormalizedAd]:
    strategy = strategy or KeywordRankingStrategy()
    for ad in ads:
        ad.relevance_score = strategy.score(ad, keyword)

    return sorted(ads, key=lambda a: (a.relevance_score, a.start_date or date.min), reverse=True)
