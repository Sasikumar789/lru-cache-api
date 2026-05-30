"""
lru_cache.py
LRU (Least Recently Used) Cache
 
Data structures used:
  - Hash Map (Python dict): O(1) lookup by key
  - Doubly Linked List:     O(1) move-to-front, O(1) remove
 
Time complexity:  O(1) for get, put, delete
Space complexity: O(capacity)
"""
 
import time
from threading import Lock
 
 
# ─────────────────────────────────────────────────────────────────────────
# NODE CLASS
# Each node holds one key-value pair and lives in the doubly linked list.
# ─────────────────────────────────────────────────────────────────────────
 
class Node:
    """
    One node in the doubly linked list.
 
    Attributes:
        key        : the cache key (also stored so we can delete from map on eviction)
        value      : the cached value
        expires_at : Unix timestamp after which this entry is invalid (None = no expiry)
        prev       : pointer to previous node
        next       : pointer to next node
    """
 
    def __init__(self, key=None, value=None, ttl: float = None):
        self.key   = key
        self.value = value
        # If ttl given: store (current time + ttl) as the expiry timestamp
        self.expires_at = (time.time() + ttl) if ttl else None
        self.prev: "Node" = None
        self.next: "Node" = None
 
    def is_expired(self) -> bool:
        """Return True if this entry has passed its TTL."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
 
 
# ─────────────────────────────────────────────────────────────────────────
# LRU CACHE CLASS
# ─────────────────────────────────────────────────────────────────────────
 
class LRUCache:
    """
    Thread-safe LRU Cache with optional per-key TTL.
 
    How it works internally:
    ┌─────────────────────────────────────────────────────────┐
    │  self.map (dict):  key ──► Node (O(1) lookup)          │
    │                                                         │
    │  Linked List:                                           │
    │  HEAD ◄──► [MRU node] ◄──► ... ◄──► [LRU node] ◄──► TAIL │
    │  (dummy)                              evict this (dummy) │
    └─────────────────────────────────────────────────────────┘
 
    HEAD.next  = most recently used
    TAIL.prev  = least recently used  ← evicted first when full
 
    Operations:
      get(key)  → look up in map → move node to front → return value
      put(k, v) → create node → insert at front → evict tail if full
    """
 
    def __init__(self, capacity: int = 128):
        if capacity < 1:
            raise ValueError("Capacity must be >= 1")
 
        self.capacity = capacity
        self.map: dict = {}          # key → Node
        self.lock = Lock()           # ensures thread safety
 
        # Sentinel nodes — always exist, never hold real data
        # They eliminate null/edge-case checks on empty list or single node
        self.head = Node()           # HEAD: always at MRU side
        self.tail = Node()           # TAIL: always at LRU side
        self.head.next = self.tail
        self.tail.prev = self.head
 
        # Stats counters
        self._hits      = 0
        self._misses    = 0
        self._evictions = 0
 
 
    # ─── PRIVATE HELPERS ────────────────────────────────────────────────
 
    def _remove(self, node: Node) -> None:
        """
        Unlink a node from the doubly linked list.
        Works for any position — no special cases needed because of sentinels.
 
        Before:  A ◄──► node ◄──► B
        After:   A ◄──► B          (node is detached)
        """
        node.prev.next = node.next   # left neighbor skips node
        node.next.prev = node.prev   # right neighbor skips node
 
    def _insert_front(self, node: Node) -> None:
        """
        Insert node just after HEAD — makes it the Most Recently Used.
 
        Before:  HEAD ◄──► old_first
        After:   HEAD ◄──► node ◄──► old_first
        """
        node.next          = self.head.next   # node → old first
        node.prev          = self.head         # node ← HEAD
        self.head.next.prev = node             # old first ← node
        self.head.next     = node              # HEAD → node
 
 
    # ─── PUBLIC API ─────────────────────────────────────────────────────
 
    def get(self, key) -> object:
        """
        Retrieve a value by key.
        Returns None if key is missing or expired.
        Side effect: moves the key to MRU position.
        """
        with self.lock:
            node = self.map.get(key)     # O(1) hash map lookup
 
            if node is None:             # key not in cache
                self._misses += 1
                return None
 
            if node.is_expired():        # key expired via TTL
                self._remove(node)
                del self.map[key]
                self._misses += 1
                return None
 
            # Key found and valid — refresh its recency
            self._remove(node)           # detach from current position
            self._insert_front(node)     # put at MRU position
            self._hits += 1
            return node.value
 
    def put(self, key, value, ttl: float = None) -> None:
        """
        Insert or update a key-value pair.
        Optional ttl (seconds): entry auto-expires after this duration.
        If cache is full after insert, the LRU entry is evicted.
        """
        with self.lock:
            if key in self.map:
                # Key already exists: remove old node (position refresh)
                self._remove(self.map[key])
 
            node = Node(key, value, ttl)  # create new node
            self.map[key] = node           # add to map
            self._insert_front(node)       # place at MRU front
 
            if len(self.map) > self.capacity:
                # Over capacity: evict the Least Recently Used node
                lru_node = self.tail.prev      # node just before TAIL
                self._remove(lru_node)
                del self.map[lru_node.key]
                self._evictions += 1
 
    def delete(self, key) -> bool:
        """
        Explicitly remove a key.
        Returns True if key existed, False if not found.
        """
        with self.lock:
            node = self.map.get(key)
            if node is None:
                return False
            self._remove(node)
            del self.map[key]
            return True
 
    def clear(self) -> None:
        """Remove all entries and reset the linked list."""
        with self.lock:
            self.map.clear()
            self.head.next = self.tail
            self.tail.prev = self.head
 
    def resize(self, new_capacity: int) -> None:
        """
        Change the cache capacity at runtime.
        If new capacity is smaller, evicts from LRU end until within limit.
        """
        if new_capacity < 1:
            raise ValueError("Capacity must be >= 1")
        with self.lock:
            self.capacity = new_capacity
            while len(self.map) > self.capacity:
                lru = self.tail.prev
                self._remove(lru)
                del self.map[lru.key]
                self._evictions += 1
 
    def peek(self, key) -> object:
        """
        Get value WITHOUT updating recency (does not move to MRU).
        Useful for inspection/testing without side effects.
        """
        with self.lock:
            node = self.map.get(key)
            if node is None or node.is_expired():
                return None
            return node.value
 
    def stats(self) -> dict:
        """Return cache performance metrics."""
        with self.lock:
            total = self._hits + self._misses
            return {
                "capacity":  self.capacity,
                "size":      len(self.map),
                "hits":      self._hits,
                "misses":    self._misses,
                "hit_rate":  round(self._hits / total, 4) if total else 0.0,
                "evictions": self._evictions,
            }
 
    def keys(self) -> list:
        """Return all live (non-expired) keys in MRU to LRU order."""
        with self.lock:
            result = []
            node = self.head.next
            while node != self.tail:
                if not node.is_expired():
                    result.append(node.key)
                node = node.next
            return result
 
    # ─── DUNDER METHODS ─────────────────────────────────────────────────
 
    def __len__(self) -> int:
        return len(self.map)
 
    def __contains__(self, key) -> bool:
        """Supports:  if "key" in cache"""
        return key in self.map
 
    def __repr__(self) -> str:
        return f"LRUCache(capacity={self.capacity}, size={len(self.map)})"
