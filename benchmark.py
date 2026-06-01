"""
benchmark.py
Measure LRU Cache performance (ops/sec).
 
Run:  python benchmark.py
 
What to do with results:
  Copy the ops/sec number into your resume bullet points.
  Example: "Benchmarked at ~60,000 ops/sec locally"
"""
 
import time
import random
from lru_cache import LRUCache
 
 
def run_benchmark(capacity: int, n_ops: int, read_ratio: float, label: str):
    """
    Run a mixed read/write benchmark.
 
    Args:
        capacity   : cache size
        n_ops      : total number of operations
        read_ratio : fraction of ops that are GET (0.7 = 70% reads)
        label      : description printed in output
    """
    cache = LRUCache(capacity=capacity)
 
    # Use more unique keys than capacity to force some evictions
    keys = [str(i) for i in range(capacity * 2)]
 
    # Warm up: fill cache to capacity first
    for i in range(capacity):
        cache.put(str(i), i * 10)
 
    # Benchmark
    start = time.perf_counter()
    for _ in range(n_ops):
        k = random.choice(keys)
        if random.random() < read_ratio:
            cache.get(k)
        else:
            cache.put(k, random.random())
    elapsed = time.perf_counter() - start
 
    ops_per_sec = int(n_ops / elapsed)
    s = cache.stats()
 
    print(f"\n{label}")
    print(f"  Ops:       {n_ops:>10,}")
    print(f"  Time:      {elapsed:>10.3f} s")
    print(f"  Ops/sec:   {ops_per_sec:>10,}")
    print(f"  Hit rate:  {s['hit_rate']:>10.2%}")
    print(f"  Evictions: {s['evictions']:>10,}")
    return ops_per_sec
 
 
if __name__ == "__main__":
    print("=" * 50)
    print("  LRU Cache Benchmark")
    print("=" * 50)
 
    run_benchmark(
        capacity=1000, n_ops=200_000, read_ratio=0.7,
        label="Standard: capacity=1000, 200k ops, 70% reads"
    )
    run_benchmark(
        capacity=100, n_ops=200_000, read_ratio=0.9,
        label="High read: capacity=100, 200k ops, 90% reads"
    )
    run_benchmark(
        capacity=5000, n_ops=500_000, read_ratio=0.5,
        label="Heavy:    capacity=5000, 500k ops, 50% reads"
    )
 
    print("\n" + "=" * 50)
    print("  Copy the ops/sec number into your resume!")
    print("=" * 50)
