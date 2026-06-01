# LRU Cache REST API
 
> In-memory LRU Cache built from scratch in Python, exposed as a production-style
> REST API using FastAPI. Built as a portfolio project for backend SDE interviews.
 
## What It Does
 
An **LRU (Least Recently Used) Cache** automatically evicts the least recently accessed
item when storage is full. This implementation:
 
- Achieves **O(1) get and put** using a doubly linked list + hash map
- Supports **TTL (time-to-live)** per key for automatic expiry
- Is **thread-safe** using Python threading.Lock()
- Exposes **8 REST endpoints** via FastAPI with auto-generated /docs UI
- Benchmarks at **~60,000 ops/sec** locally
 
## Architecture
 
```
Hash Map (dict)       key ──► Node reference      O(1) lookup
Doubly Linked List    HEAD ◄──► [MRU] ◄──► ... ◄──► [LRU] ◄──► TAIL
                                                     evict this
```
 
## Run It
 
```bash
pip install -r requirements.txt
uvicorn api:app --reload
```
 
Visit **http://localhost:8000/docs** for the interactive API UI.
 
## API Endpoints
 
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Liveness check |
| GET | /stats | Hit rate, evictions, size |
| GET | /cache | List all keys (MRU order) |
| GET | /cache/{key} | Get a value |
| POST | /cache | Set a value (+ optional TTL) |
| DELETE | /cache/{key} | Remove a key |
| DELETE | /cache | Clear all |
| PATCH | /cache/resize | Change capacity |
 
## Quick Test
 
```bash
# Set a value
curl -X POST http://localhost:8000/cache \
  -H "Content-Type: application/json" \
  -d '{"key": "user:42", "value": {"name": "Rahul"}, "ttl": 60}'
 
# Get it back
curl http://localhost:8000/cache/user:42
 
# Check performance stats
curl http://localhost:8000/stats
```
 
## Run Tests
 
```bash
pytest test_lru_cache.py -v
# 25 tests — all passing
```
 
## Tech Stack
 
- **Python 3.11** — core language
- **FastAPI** — REST framework
- **pytest** — testing
- **threading.Lock** — thread safety
 
## Key Design Decisions
 
- **Why doubly linked list?** — O(1) remove from any position (need prev pointer)
- **Why sentinel nodes?** — Eliminates null checks for empty list edge cases
- **Why lazy TTL eviction?** — Simpler than background sweeper; cleans on access
- **Why threading.Lock?** — Prevents data races with concurrent HTTP requests
