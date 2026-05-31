"""
test_lru_cache.py
Complete pytest test suite for LRUCache.
 
Run all tests:    pytest test_lru_cache.py -v
Run one class:    pytest test_lru_cache.py::TestEviction -v
Run one test:     pytest test_lru_cache.py::TestBasic::test_put_and_get -v
Show output:      pytest test_lru_cache.py -v -s
"""
 
import time
import threading
import pytest
from lru_cache import LRUCache
 
 
# ─────────────────────────────────────────────────────────────────────────
# CLASS 1: BASIC OPERATIONS
# ─────────────────────────────────────────────────────────────────────────
 
class TestBasic:
    """Tests for fundamental get/put/delete/clear behaviour."""
 
    def test_put_and_get(self):
        c = LRUCache(3)
        c.put("a", 1)
        assert c.get("a") == 1
 
    def test_missing_key_returns_none(self):
        c = LRUCache(3)
        assert c.get("ghost") is None
 
    def test_overwrite_updates_value(self):
        c = LRUCache(3)
        c.put("x", 10)
        c.put("x", 99)
        assert c.get("x") == 99
 
    def test_delete_existing_key(self):
        c = LRUCache(3)
        c.put("k", "hello")
        assert c.delete("k") is True
        assert c.get("k") is None
 
    def test_delete_missing_key(self):
        assert LRUCache(3).delete("nope") is False
 
    def test_clear_removes_all(self):
        c = LRUCache(3)
        c.put("a", 1)
        c.put("b", 2)
        c.clear()
        assert c.get("a") is None
        assert c.get("b") is None
        assert len(c) == 0
 
    def test_len(self):
        c = LRUCache(5)
        c.put("a", 1)
        c.put("b", 2)
        assert len(c) == 2
 
    def test_contains_operator(self):
        c = LRUCache(3)
        c.put("k", "v")
        assert "k" in c
        assert "x" not in c
 
    def test_store_various_value_types(self):
        c = LRUCache(10)
        c.put("int",    42)
        c.put("float",  3.14)
        c.put("string", "hello")
        c.put("list",   [1, 2, 3])
        c.put("dict",   {"nested": True})
        c.put("none",   None)
        assert c.get("int")    == 42
        assert c.get("list")   == [1, 2, 3]
        assert c.get("dict")   == {"nested": True}
 
 
# ─────────────────────────────────────────────────────────────────────────
# CLASS 2: EVICTION
# ─────────────────────────────────────────────────────────────────────────
 
class TestEviction:
    """Tests that the LRU eviction policy works correctly."""
 
    def test_evicts_lru_when_full(self):
        """
        Access order: a, b, c → c is MRU, a is LRU
        Add d → a should be evicted
        """
        c = LRUCache(3)
        c.put("a", 1)   # LRU
        c.put("b", 2)
        c.put("c", 3)   # MRU
        c.put("d", 4)   # evicts "a"
        assert c.get("a") is None, "a should have been evicted"
        assert c.get("b") == 2
        assert c.get("c") == 3
        assert c.get("d") == 4
 
    def test_get_refreshes_lru_order(self):
        """
        Access a after b was inserted → a is now MRU, b is LRU
        Insert c → b should be evicted, not a
        """
        c = LRUCache(2)
        c.put("a", 1)
        c.put("b", 2)
        c.get("a")       # makes a MRU, b is now LRU
        c.put("c", 3)    # evicts b (LRU)
        assert c.get("a") == 1,    "a should still be there"
        assert c.get("b") is None, "b should have been evicted"
        assert c.get("c") == 3
 
    def test_put_update_refreshes_order(self):
        """Updating an existing key should make it MRU."""
        c = LRUCache(2)
        c.put("a", 1)
        c.put("b", 2)
        c.put("a", 99)   # update a → a becomes MRU
        c.put("c", 3)    # should evict b (LRU)
        assert c.get("a") == 99
        assert c.get("b") is None
 
    def test_eviction_counter_increments(self):
        c = LRUCache(2)
        c.put("a", 1)
        c.put("b", 2)
        c.put("c", 3)    # 1 eviction
        c.put("d", 4)    # 2 evictions
        assert c.stats()["evictions"] == 2
 
    def test_capacity_one(self):
        """Extreme case: capacity of 1."""
        c = LRUCache(1)
        c.put("a", 1)
        c.put("b", 2)    # evicts a
        assert c.get("a") is None
        assert c.get("b") == 2
 
 
# ─────────────────────────────────────────────────────────────────────────
# CLASS 3: TTL (TIME TO LIVE)
# ─────────────────────────────────────────────────────────────────────────
 
class TestTTL:
    """Tests for time-based expiry."""
 
    def test_entry_accessible_before_expiry(self):
        c = LRUCache(5)
        c.put("temp", "value", ttl=5.0)
        assert c.get("temp") == "value"
 
    def test_entry_gone_after_expiry(self):
        c = LRUCache(5)
        c.put("temp", "value", ttl=0.1)
        time.sleep(0.15)           # wait for TTL to expire
        assert c.get("temp") is None
 
    def test_no_ttl_does_not_expire(self):
        c = LRUCache(5)
        c.put("perm", "stays")
        time.sleep(0.05)
        assert c.get("perm") == "stays"
 
    def test_expired_key_not_in_keys_list(self):
        c = LRUCache(5)
        c.put("live", 1)
        c.put("dead", 2, ttl=0.05)
        time.sleep(0.1)
        live_keys = c.keys()
        assert "live" in live_keys
        assert "dead" not in live_keys
 
 
# ─────────────────────────────────────────────────────────────────────────
# CLASS 4: STATS
# ─────────────────────────────────────────────────────────────────────────
 
class TestStats:
    """Tests for hit/miss/eviction counting."""
 
    def test_hit_and_miss_counting(self):
        c = LRUCache(5)
        c.put("k", "v")
        c.get("k")          # hit
        c.get("k")          # hit
        c.get("missing")    # miss
        s = c.stats()
        assert s["hits"]   == 2
        assert s["misses"] == 1
 
    def test_hit_rate_calculation(self):
        c = LRUCache(5)
        c.put("k", "v")
        c.get("k")          # hit  → hit_rate = 1/1 = 1.0
        c.get("missing")    # miss → hit_rate = 1/2 = 0.5
        assert c.stats()["hit_rate"] == pytest.approx(0.5, rel=1e-3)
 
    def test_zero_hit_rate_on_empty(self):
        c = LRUCache(5)
        assert c.stats()["hit_rate"] == 0.0
 
    def test_size_reflects_entries(self):
        c = LRUCache(10)
        c.put("a", 1)
        c.put("b", 2)
        assert c.stats()["size"] == 2
 
 
# ─────────────────────────────────────────────────────────────────────────
# CLASS 5: EDGE CASES & THREAD SAFETY
# ─────────────────────────────────────────────────────────────────────────
 
class TestEdgeCasesAndThreadSafety:
 
    def test_invalid_capacity_raises_value_error(self):
        with pytest.raises(ValueError):
            LRUCache(0)
 
    def test_resize_shrinks_evicting_lru(self):
        c = LRUCache(3)
        c.put("a", 1)
        c.put("b", 2)
        c.put("c", 3)    # c is MRU
        c.resize(1)      # keep only 1 entry (MRU = c)
        assert len(c) == 1
        assert c.get("c") == 3
 
    def test_peek_does_not_update_recency(self):
        c = LRUCache(2)
        c.put("a", 1)
        c.put("b", 2)
        c.peek("a")      # peek should NOT make a MRU
        c.put("c", 3)    # should evict a (still LRU)
        assert c.get("a") is None
        assert c.get("c") == 3
 
    def test_keys_mru_to_lru_order(self):
        c = LRUCache(5)
        c.put("a", 1)
        c.put("b", 2)
        c.put("c", 3)
        c.get("a")       # a becomes MRU: order now [a, c, b]
        keys = c.keys()
        assert keys[0] == "a"
        assert keys[-1] == "b"
 
    def test_concurrent_puts_no_crash_no_data_race(self):
        """
        Run 10 threads each doing 200 puts and gets.
        If there is a data race, this will crash or corrupt state.
        """
        c = LRUCache(50)
        errors = []
 
        def worker(thread_id):
            try:
                for i in range(200):
                    c.put(f"t{thread_id}_k{i}", i)
                    c.get(f"t{thread_id}_k{i}")
            except Exception as e:
                errors.append(str(e))
 
        threads = [threading.Thread(target=worker, args=(t,)) for t in range(10)]
        for t in threads: t.start()
        for t in threads: t.join()
 
        assert errors == [], f"Thread safety errors: {errors}"
        assert len(c) <= c.capacity
