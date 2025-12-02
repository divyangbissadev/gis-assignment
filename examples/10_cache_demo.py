#!/usr/bin/env python3
"""
ArcGIS Client Cache Demo

Demonstrates the caching capabilities of the ArcGIS client:
- Automatic caching of query results
- Cache hit/miss logging
- Performance improvements
- Cache statistics

Usage:
    python3 cache_demo.py
"""

import time
from dotenv import load_dotenv
load_dotenv()

from src.arcgis_client import ArcGISClient

# USA Census Counties Feature Service
SERVICE_URL = (
    "https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/"
    "USA_Census_Counties/FeatureServer/0"
)


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def demo_basic_caching():
    """Demonstrate basic cache hit/miss."""
    print_section("Demo 1: Basic Caching (Hit/Miss)")

    # Initialize client with caching enabled (default)
    client = ArcGISClient(SERVICE_URL, enable_cache=True, cache_ttl=300)
    print("✓ Client initialized with caching enabled (TTL: 300 seconds)")

    query = "STATE_NAME = 'Texas'"

    # First query - CACHE MISS
    print(f"\nQuery 1 (First time): {query}")
    print("Expected: Cache MISS")
    print("-" * 60)

    start = time.time()
    result1 = client.query(where=query)
    time1 = (time.time() - start) * 1000

    print(f"✓ Completed in {time1:.0f}ms")
    print(f"  Features: {len(result1['features'])}")

    # Second query - CACHE HIT
    print(f"\nQuery 2 (Same query): {query}")
    print("Expected: Cache HIT")
    print("-" * 60)

    start = time.time()
    result2 = client.query(where=query)
    time2 = (time.time() - start) * 1000

    print(f"✓ Completed in {time2:.0f}ms")
    print(f"  Features: {len(result2['features'])}")

    # Show performance improvement
    print(f"\nPerformance Comparison:")
    print(f"  First query (MISS):  {time1:.0f}ms")
    print(f"  Second query (HIT):  {time2:.0f}ms")
    if time2 > 0:
        speedup = time1 / time2
        print(f"  Speedup: {speedup:.0f}x faster! 🚀")

    # Show cache stats
    stats = client.get_cache_stats()
    print(f"\nCache Statistics:")
    print(f"  Total requests: {stats['total_requests']}")
    print(f"  Cache hits: {stats['cache_hits']}")
    print(f"  Cache misses: {stats['cache_misses']}")
    print(f"  Hit rate: {stats['hit_rate']:.1%}")


def demo_multiple_queries():
    """Demonstrate caching with multiple different queries."""
    print_section("Demo 2: Multiple Queries")

    client = ArcGISClient(SERVICE_URL, enable_cache=True, cache_ttl=300)

    queries = [
        "STATE_NAME = 'California'",
        "STATE_NAME = 'Texas'",
        "STATE_NAME = 'California'",  # Repeat
        "STATE_NAME = 'New York'",
        "STATE_NAME = 'Texas'",  # Repeat
    ]

    print("Running 5 queries (some repeated)...")
    print("-" * 60)

    for i, query in enumerate(queries, 1):
        print(f"\nQuery {i}: {query}")

        start = time.time()
        result = client.query(where=query)
        elapsed = (time.time() - start) * 1000

        print(f"  Time: {elapsed:.0f}ms | Features: {len(result['features'])}")

    # Show cache stats
    print("\n" + "-" * 60)
    stats = client.get_cache_stats()
    print(f"\nCache Statistics:")
    print(f"  Total requests: {stats['total_requests']}")
    print(f"  Cache hits: {stats['cache_hits']} (queries 3 and 5 were cached)")
    print(f"  Cache misses: {stats['cache_misses']}")
    print(f"  Hit rate: {stats['hit_rate']:.1%}")
    print(f"  Cache entries: {stats['valid_entries']}")


def demo_cache_management():
    """Demonstrate cache management operations."""
    print_section("Demo 3: Cache Management")

    client = ArcGISClient(SERVICE_URL, enable_cache=True, cache_ttl=300)

    # Run some queries
    print("Populating cache with 3 queries...")
    queries = [
        "STATE_NAME = 'Texas'",
        "STATE_NAME = 'California'",
        "STATE_NAME = 'Florida'"
    ]

    for query in queries:
        client.query(where=query)
        print(f"  ✓ Cached: {query}")

    # Show cache stats
    stats = client.get_cache_stats()
    print(f"\nCache entries: {stats['valid_entries']}")

    # Clear cache
    print("\nClearing cache...")
    client.clear_cache()

    # Show stats after clear
    stats = client.get_cache_stats()
    print(f"✓ Cache cleared")
    print(f"  Cache entries: {stats['valid_entries']}")
    print(f"  Total hits (before clear): {stats['cache_hits']}")
    print(f"  Total misses (before clear): {stats['cache_misses']}")


def demo_cache_disabled():
    """Demonstrate behavior with caching disabled."""
    print_section("Demo 4: Cache Disabled")

    # Initialize client with caching disabled
    client = ArcGISClient(SERVICE_URL, enable_cache=False)
    print("✓ Client initialized with caching DISABLED")

    query = "STATE_NAME = 'Texas'"

    # Run same query twice
    print(f"\nQuery 1: {query}")
    start = time.time()
    result1 = client.query(where=query)
    time1 = (time.time() - start) * 1000
    print(f"  Time: {time1:.0f}ms")

    print(f"\nQuery 2 (Same query): {query}")
    start = time.time()
    result2 = client.query(where=query)
    time2 = (time.time() - start) * 1000
    print(f"  Time: {time2:.0f}ms")

    print(f"\n⚠️  Both queries took similar time (no caching)")
    print(f"  Query 1: {time1:.0f}ms")
    print(f"  Query 2: {time2:.0f}ms")

    # Show cache stats (should be all zeros)
    stats = client.get_cache_stats()
    print(f"\nCache Statistics:")
    print(f"  Enabled: {stats['enabled']}")
    print(f"  Total requests: {stats['total_requests']}")
    print(f"  Cache hits: {stats['cache_hits']}")


def demo_cache_expiration():
    """Demonstrate cache expiration."""
    print_section("Demo 5: Cache Expiration")

    # Initialize client with short TTL for demo
    client = ArcGISClient(SERVICE_URL, enable_cache=True, cache_ttl=3)  # 3 seconds
    print("✓ Client initialized with TTL: 3 seconds")

    query = "STATE_NAME = 'Texas'"

    # First query
    print(f"\nQuery 1: {query}")
    result1 = client.query(where=query)
    print("✓ Result cached")

    # Second query (should hit cache)
    print(f"\nQuery 2 (immediately after): {query}")
    result2 = client.query(where=query)
    stats = client.get_cache_stats()
    print(f"✓ Cache HIT (hits: {stats['cache_hits']}, misses: {stats['cache_misses']})")

    # Wait for cache to expire
    print("\n⏳ Waiting 4 seconds for cache to expire...")
    time.sleep(4)

    # Third query (should miss cache - expired)
    print(f"\nQuery 3 (after expiration): {query}")
    result3 = client.query(where=query)
    stats = client.get_cache_stats()
    print(f"✓ Cache MISS - entry expired (hits: {stats['cache_hits']}, misses: {stats['cache_misses']})")


def demo_performance_comparison():
    """Compare performance with and without caching."""
    print_section("Demo 6: Performance Comparison")

    queries = [
        "STATE_NAME = 'Texas'",
        "STATE_NAME = 'California'",
        "STATE_NAME = 'Texas'",
        "STATE_NAME = 'California'",
        "STATE_NAME = 'Texas'",
    ]

    # Test WITH caching
    print("Test 1: WITH CACHING")
    print("-" * 60)
    client_cached = ArcGISClient(SERVICE_URL, enable_cache=True, cache_ttl=300)

    start_total = time.time()
    for i, query in enumerate(queries, 1):
        start = time.time()
        client_cached.query(where=query)
        elapsed = (time.time() - start) * 1000
        print(f"  Query {i}: {elapsed:6.0f}ms - {query}")

    total_cached = (time.time() - start_total) * 1000
    stats_cached = client_cached.get_cache_stats()

    print(f"\nTotal time: {total_cached:.0f}ms")
    print(f"Hit rate: {stats_cached['hit_rate']:.1%}")

    # Test WITHOUT caching
    print(f"\nTest 2: WITHOUT CACHING")
    print("-" * 60)
    client_uncached = ArcGISClient(SERVICE_URL, enable_cache=False)

    start_total = time.time()
    for i, query in enumerate(queries, 1):
        start = time.time()
        client_uncached.query(where=query)
        elapsed = (time.time() - start) * 1000
        print(f"  Query {i}: {elapsed:6.0f}ms - {query}")

    total_uncached = (time.time() - start_total) * 1000

    print(f"\nTotal time: {total_uncached:.0f}ms")

    # Show comparison
    print("\n" + "=" * 60)
    print("PERFORMANCE COMPARISON")
    print("=" * 60)
    print(f"With caching:    {total_cached:.0f}ms")
    print(f"Without caching: {total_uncached:.0f}ms")
    if total_cached > 0:
        speedup = total_uncached / total_cached
        print(f"Speedup:         {speedup:.1f}x faster! 🚀")
    print(f"Time saved:      {total_uncached - total_cached:.0f}ms")


def main():
    """Run all cache demos."""
    print_section("ArcGIS Client Cache Demo")

    print("This demo shows:")
    print("  1. Basic caching (hit/miss)")
    print("  2. Multiple queries")
    print("  3. Cache management")
    print("  4. Cache disabled")
    print("  5. Cache expiration")
    print("  6. Performance comparison")

    try:
        demo_basic_caching()
        demo_multiple_queries()
        demo_cache_management()
        demo_cache_disabled()
        demo_cache_expiration()
        demo_performance_comparison()

        print_section("Demo Complete! 🎉")
        print("\nKey Takeaways:")
        print("  ✓ Caching provides significant performance improvements")
        print("  ✓ Cache hits are logged with hit/miss statistics")
        print("  ✓ Cache can be enabled/disabled per client")
        print("  ✓ Cache entries expire based on TTL")
        print("  ✓ Cache can be cleared programmatically")
        print("\nUse caching in production for:")
        print("  • Repeated queries (dashboards, reports)")
        print("  • Read-heavy applications")
        print("  • Reducing API load")
        print("  • Improving response times")

    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n\n✗ Error: {e}")


if __name__ == "__main__":
    main()
