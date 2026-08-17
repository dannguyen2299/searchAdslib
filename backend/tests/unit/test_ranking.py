from app.core.ranking import (
    ALL_WORDS_SCORE,
    EXACT_PHRASE_SCORE,
    NO_MATCH_SCORE,
    PAGE_NAME_SCORE,
    PARTIAL_WORD_SCORE,
    KeywordRankingStrategy,
    rank_ads,
)
from app.models.schemas import NormalizedAd


def _ad(**overrides) -> NormalizedAd:
    base = dict(ad_id="1", body=None, headline=None, description=None, page_name=None)
    base.update(overrides)
    return NormalizedAd(**base)


def test_exact_phrase_scores_highest():
    ad = _ad(body="Xe Ha Noi Sai Gon chat luong cao")
    score = KeywordRankingStrategy().score(ad, "xe ha noi sai gon")
    assert score == EXACT_PHRASE_SCORE


def test_all_words_present_unordered_scores_second_tier():
    ad = _ad(body="Sai Gon di Ha Noi bang xe khach")
    score = KeywordRankingStrategy().score(ad, "xe ha noi sai gon")
    assert score == ALL_WORDS_SCORE


def test_partial_word_overlap_scores_third_tier():
    ad = _ad(body="Ve xe Da Lat gia re")
    score = KeywordRankingStrategy().score(ad, "xe ha noi sai gon")
    assert score == PARTIAL_WORD_SCORE


def test_page_name_only_match_scores_lowest_nonzero_tier():
    ad = _ad(body="Khuyen mai mua he", page_name="Xe Ha Noi Sai Gon Express")
    score = KeywordRankingStrategy().score(ad, "xe ha noi sai gon")
    assert score == PAGE_NAME_SCORE


def test_no_match_scores_zero():
    ad = _ad(body="Ban dien thoai gia re", page_name="Shop ABC")
    score = KeywordRankingStrategy().score(ad, "xe ha noi sai gon")
    assert score == NO_MATCH_SCORE


def test_rank_ads_orders_by_score_descending_without_dropping_any():
    low = _ad(ad_id="low", body="khong lien quan")
    high = _ad(ad_id="high", body="xe ha noi sai gon chat luong cao")
    mid = _ad(ad_id="mid", body="xe di Ha Noi")

    ranked = rank_ads([low, high, mid], "xe ha noi sai gon")

    assert [ad.ad_id for ad in ranked] == ["high", "mid", "low"]
    assert len(ranked) == 3
