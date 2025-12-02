#!/usr/bin/env python3
"""
Advanced NLP Query Parser Demo

Demonstrates advanced features:
- ORDER BY and LIMIT (top N queries)
- Aggregations (count, sum, average)
- Spatial queries (near location)
- Query caching

Usage:
    python3 advanced_query_demo.py
"""

import os
from dotenv import load_dotenv
load_dotenv()

from src.nlp_query_parser import NLPQueryParser
from src.arcgis_client import ArcGISClient
from src.query_executor import execute_query

# USA Census Counties Feature Service
SERVICE_URL = os.getenv(
    'ARCGIS_SERVICE_URL',
    "https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/"
    "USA_Census_Counties/FeatureServer/0"
)


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def demo_top_n_query(parser, client):
    """Demonstrate top N queries with ORDER BY and LIMIT."""
    print_section("Demo 1: Top N Queries (ORDER BY + LIMIT)")

    queries = [
        "top 5 largest counties in Texas",
        "smallest 3 counties in California",
        "10 most populous counties in Texas"
    ]

    for query in queries:
        print(f"Query: \"{query}\"")
        print("-" * 60)

        result = parser.parse(query)

        print(f"✓ WHERE: {result.where_clause}")
        if result.order_by:
            print(f"  ORDER BY: {result.order_by}")
        if result.limit:
            print(f"  LIMIT: {result.limit}")
        print(f"  Confidence: {result.confidence:.2%}")
        print(f"  Explanation: {result.explanation}")

        # Execute the query
        results = execute_query(client, result)

        print(f"\n  Results ({results['count']} counties):")
        for i, feature in enumerate(results['features'][:5], 1):
            props = feature['properties']
            print(f"    {i}. {props.get('NAME', 'N/A')}: "
                  f"{props.get('SQMI', 'N/A')} sq mi, "
                  f"{props.get('POPULATION', 'N/A'):,} people")

        print()


def demo_aggregation_query(parser, client):
    """Demonstrate aggregation queries (COUNT)."""
    print_section("Demo 2: Aggregation Queries (COUNT)")

    queries = [
        "how many counties are in Texas",
        "count counties in California with population over 500000"
    ]

    for query in queries:
        print(f"Query: \"{query}\"")
        print("-" * 60)

        result = parser.parse(query)

        print(f"✓ WHERE: {result.where_clause}")
        if result.aggregation:
            print(f"  AGGREGATION: {result.aggregation}")
        print(f"  Confidence: {result.confidence:.2%}")
        print(f"  Explanation: {result.explanation}")

        # Execute the query
        results = execute_query(client, result)

        if results['type'] == 'Aggregation':
            print(f"\n  Result: {results['result']} counties")
        else:
            print(f"\n  Result: {results['count']} counties")

        print()


def demo_spatial_query(parser, client):
    """Demonstrate spatial proximity queries."""
    print_section("Demo 3: Spatial Queries (NEAR location)")

    queries = [
        "counties near Austin Texas within 50 miles",
        "find counties within 100 miles of Houston Texas"
    ]

    for query in queries:
        print(f"Query: \"{query}\"")
        print("-" * 60)

        result = parser.parse(query)

        print(f"✓ WHERE: {result.where_clause}")
        if result.spatial_filter:
            print(f"  SPATIAL FILTER:")
            print(f"    Location: {result.spatial_filter.get('location')}")
            print(f"    Distance: {result.spatial_filter.get('distance_miles')} miles")
        print(f"  Confidence: {result.confidence:.2%}")
        print(f"  Explanation: {result.explanation}")

        # Execute the query
        results = execute_query(client, result)

        print(f"\n  Results ({results['count']} counties):")
        for i, feature in enumerate(results['features'][:5], 1):
            props = feature['properties']
            print(f"    {i}. {props.get('NAME', 'N/A')}, {props.get('STATE_NAME', 'N/A')}")

        print()


def demo_caching(parser):
    """Demonstrate query caching."""
    print_section("Demo 4: Query Caching")

    query = "top 5 largest counties in Texas"

    # First query (cache miss)
    print(f"Query (1st time): \"{query}\"")
    print("-" * 60)

    import time
    start = time.time()
    result1 = parser.parse(query)
    time1 = (time.time() - start) * 1000

    print(f"✓ Parsed in {time1:.0f}ms")
    print(f"  WHERE: {result1.where_clause}")

    # Second query (cache hit)
    print(f"\nQuery (2nd time - cached): \"{query}\"")
    print("-" * 60)

    start = time.time()
    result2 = parser.parse(query)
    time2 = (time.time() - start) * 1000

    print(f"✓ Parsed in {time2:.0f}ms (from cache)")
    print(f"  Speedup: {time1/time2:.1f}x faster")

    # Cache stats
    print("\nCache Statistics:")
    stats = parser.get_cache_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print()


def demo_complex_queries(parser, client):
    """Demonstrate complex queries combining multiple features."""
    print_section("Demo 5: Complex Queries")

    queries = [
        "top 5 largest counties in Texas under 3000 square miles",
        "smallest 3 counties in California with population over 100000"
    ]

    for query in queries:
        print(f"Query: \"{query}\"")
        print("-" * 60)

        result = parser.parse(query)

        print(f"✓ WHERE: {result.where_clause}")
        if result.order_by:
            print(f"  ORDER BY: {result.order_by}")
        if result.limit:
            print(f"  LIMIT: {result.limit}")
        print(f"  Confidence: {result.confidence:.2%}")

        # Execute the query
        results = execute_query(client, result)

        print(f"\n  Results ({results['count']} counties):")
        for i, feature in enumerate(results['features'][:5], 1):
            props = feature['properties']
            print(f"    {i}. {props.get('NAME', 'N/A')}: "
                  f"{props.get('SQMI', 'N/A')} sq mi, "
                  f"{props.get('POPULATION', 'N/A'):,} people")

        print()


def main():
    """Main demo function."""
    print_section("Advanced NLP Query Parser Demo")

    # Initialize parser and client
    print("Initializing...")
    parser = NLPQueryParser(provider="gemini")  # Change to your preferred provider
    client = ArcGISClient(SERVICE_URL)
    print(f"✓ Parser initialized with {parser.provider.provider_name}")
    print(f"✓ ArcGIS client connected")

    # Run demos
    demo_top_n_query(parser, client)
    demo_aggregation_query(parser, client)
    demo_spatial_query(parser, client)
    demo_caching(parser)
    demo_complex_queries(parser, client)

    print_section("Demo Complete!")
    print("\nAdvanced Features Demonstrated:")
    print("  ✓ ORDER BY - Sort results (largest, smallest)")
    print("  ✓ LIMIT - Top N queries")
    print("  ✓ Aggregations - COUNT queries")
    print("  ✓ Spatial filters - Near location queries")
    print("  ✓ Query caching - Fast repeated queries")
    print("\nAll features are working! 🎉")


if __name__ == "__main__":
    main()
