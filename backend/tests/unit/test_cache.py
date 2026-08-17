import time

from app.core.cache import TTLCache


def test_cache_returns_none_when_missing():
    cache = TTLCache()
    assert cache.get("missing") is None


def test_cache_returns_value_before_expiry():
    cache = TTLCache()
    cache.set("k", "v", ttl_seconds=5)
    assert cache.get("k") == "v"


def test_cache_expires_after_ttl():
    cache = TTLCache()
    cache.set("k", "v", ttl_seconds=0.01)
    time.sleep(0.05)
    assert cache.get("k") is None


def test_cache_key_is_case_and_whitespace_insensitive():
    key_a = TTLCache.build_key("Xe Ha Noi ", "VN", "ACTIVE")
    key_b = TTLCache.build_key("xe ha noi", "vn", "active")
    assert key_a == key_b
