"""
api.py
FastAPI REST API wrapping the LRUCache.
 
Run:  uvicorn api:app --reload
Docs: http://localhost:8000/docs   (auto-generated interactive UI)
 
Endpoints:
  GET    /health               check if server is running
  GET    /stats                hit rate, evictions, size
  GET    /cache                list all keys (MRU order)
  GET    /cache/{key}          get a value
  POST   /cache                insert/update key
  DELETE /cache/{key}          remove one key
  DELETE /cache                clear all entries
  PATCH  /cache/resize         change capacity at runtime
"""
 
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Optional
from lru_cache import LRUCache
 
app = FastAPI(
    title="LRU Cache API",
    description="Thread-safe in-memory LRU Cache with TTL support.",
    version="1.0.0",
)
 
# One global cache instance shared across all HTTP requests
cache = LRUCache(capacity=100)
 
 
# ─── REQUEST / RESPONSE MODELS ───────────────────────────────────────────
# Pydantic models define the shape of JSON request/response bodies.
# FastAPI validates them automatically — no manual validation needed.
 
class PutRequest(BaseModel):
    key:   str         = Field(..., description="Cache key")
    value: Any         = Field(..., description="Any JSON value: string, number, list, dict")
    ttl:   Optional[float] = Field(None, description="Time-to-live in seconds. Omit for no expiry.")
 
class ResizeRequest(BaseModel):
    capacity: int = Field(..., ge=1, description="New capacity (must be >= 1)")
 
 
# ─── ENDPOINTS ───────────────────────────────────────────────────────────
 
@app.get("/health", tags=["Meta"])
def health():
    """
    Liveness probe — use this to check if the server is running.
    Returns 200 OK if up.
    """
    return {"status": "ok", "cache": repr(cache)}
 
 
@app.get("/stats", tags=["Meta"])
def get_stats():
    """
    Return cache performance metrics.
    hit_rate: fraction of requests that found a value (higher = better)
    evictions: how many entries were removed due to capacity limits
    """
    return cache.stats()
 
 
@app.get("/cache", tags=["Cache"])
def list_keys():
    """
    List all live (non-expired) keys in MRU order.
    First key = most recently used. Last key = least recently used.
    """
    return {"keys": cache.keys(), "size": len(cache)}
 
 
@app.get("/cache/{key}", tags=["Cache"])
def get_value(key: str):
    """
    Fetch a value by key.
    found: true  → value contains the cached data
    found: false → key not in cache or expired
    NOTE: This moves the key to MRU position (counts as a "use").
    """
    value = cache.get(key)
    return {"key": key, "found": value is not None, "value": value}
 
 
@app.post("/cache", status_code=201, tags=["Cache"])
def put_value(body: PutRequest):
    """
    Insert or update a key-value pair.
    If cache is full, the least recently used key is evicted automatically.
    Set ttl (seconds) for auto-expiry.
    """
    cache.put(body.key, body.value, body.ttl)
    return {"key": body.key, "status": "stored", "ttl_seconds": body.ttl}
 
 
@app.delete("/cache/{key}", tags=["Cache"])
def delete_key(key: str):
    """Remove a specific key. Returns 404 if key not found."""
    deleted = cache.delete(key)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Key '{key}' not found")
    return {"key": key, "status": "deleted"}
 
 
@app.delete("/cache", tags=["Cache"])
def clear_cache():
    """Flush all entries from the cache."""
    cache.clear()
    return {"status": "cleared"}
 
 
@app.patch("/cache/resize", tags=["Cache"])
def resize_cache(body: ResizeRequest):
    """
    Change cache capacity at runtime.
    If new capacity < current size, LRU entries are evicted.
    """
    old = cache.capacity
    cache.resize(body.capacity)
    return {
        "old_capacity":  old,
        "new_capacity":  cache.capacity,
        "current_size":  len(cache),
    }
 
 
@app.get("/benchmark", tags=["Meta"])
def run_benchmark(n: int = 10000):
    """
    Run N random get/put operations and report ops/sec.
    Use this to get real numbers for your resume.
    """
    import time, random
    keys = [str(i) for i in range(200)]
    start = time.perf_counter()
    for _ in range(n):
        k = random.choice(keys)
        if random.random() < 0.6:
            cache.get(k)
        else:
            cache.put(k, random.random())
    elapsed = time.perf_counter() - start
    return {
        "ops":           n,
        "elapsed_ms":    round(elapsed * 1000, 2),
        "ops_per_sec":   round(n / elapsed),
    }
