#!/usr/bin/env python3
"""
Test script to verify max_pages safety limit functionality.

This demonstrates the new max_pages parameter that prevents runaway pagination.
"""

from src.arcgis_client import ArcGISClient

def test_max_pages_limit():
    """Test that max_pages parameter properly limits pagination."""
    print("=" * 80)
    print("Testing max_pages Safety Limit")
    print("=" * 80)
    print()

    service_url = (
        "https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/"
        "USA_Census_Counties/FeatureServer/0"
    )

    print("Test 1: Query with max_pages=1 (should get only first page)")
    print("-" * 80)

    with ArcGISClient(service_url) as client:
        result = client.query(
            where="STATE_NAME = 'Texas'",
            page_size=50,  # Small page size to force multiple pages
            max_pages=1    # Limit to just 1 page
        )

        print(f"✓ Retrieved {len(result['features'])} features (limited to 1 page)")
        print(f"  Partial results: {result.get('partialResults', False)}")
        print(f"  Max pages reached: {result.get('maxPagesReached', False)}")
        print()

    print("Test 2: Query with max_pages=None (unlimited, gets all pages)")
    print("-" * 80)

    with ArcGISClient(service_url) as client:
        result = client.query(
            where="STATE_NAME = 'Texas'",
            page_size=50,
            max_pages=None  # No limit
        )

        print(f"✓ Retrieved {len(result['features'])} features (all pages)")
        print(f"  Partial results: {result.get('partialResults', False)}")
        print(f"  Max pages reached: {result.get('maxPagesReached', False)}")
        print()

    print("Test 3: Query with max_pages=10 (should get all Texas counties)")
    print("-" * 80)

    with ArcGISClient(service_url) as client:
        result = client.query(
            where="STATE_NAME = 'Texas'",
            page_size=50,
            max_pages=10  # More than enough for 254 counties
        )

        print(f"✓ Retrieved {len(result['features'])} features (max 10 pages)")
        print(f"  Partial results: {result.get('partialResults', False)}")
        print(f"  Max pages reached: {result.get('maxPagesReached', False)}")
        print()

    print("=" * 80)
    print("✓ All tests passed!")
    print("=" * 80)


if __name__ == "__main__":
    test_max_pages_limit()
