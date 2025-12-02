"""
Example 2: Spatial Query - Counties Near a City

This example demonstrates spatial queries to find counties within
a specified radius of any city and check their compliance.

Run:
    python examples/02_spatial_query_city.py
    python examples/02_spatial_query_city.py --city="San Francisco" --lat=37.7749 --lon=-122.4194
    python examples/02_spatial_query_city.py --city="Houston" --lat=29.7604 --lon=-95.3698 --distance=100
    python examples/02_spatial_query_city.py --json
    python examples/02_spatial_query_city.py --format=json --output=city_report.json
"""

import sys
import os
import json
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.arcgis_client import ArcGISClient
from src.compliance_checker import analyze_oil_gas_lease_compliance


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Spatial query: Find counties near a city and analyze compliance'
    )
    parser.add_argument(
        '--city',
        type=str,
        default='Austin, TX',
        help='City name (default: Austin, TX)'
    )
    parser.add_argument(
        '--lat',
        type=float,
        default=30.2672,
        help='Latitude in decimal degrees (default: 30.2672 for Austin)'
    )
    parser.add_argument(
        '--lon',
        type=float,
        default=-97.7431,
        help='Longitude in decimal degrees (default: -97.7431 for Austin)'
    )
    parser.add_argument(
        '--distance',
        type=int,
        default=50,
        help='Search radius in miles (default: 50)'
    )
    parser.add_argument(
        '--min-area',
        type=float,
        default=2500.0,
        help='Minimum area requirement in square miles (default: 2500.0)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON to stdout'
    )
    parser.add_argument(
        '--format',
        choices=['text', 'json', 'both'],
        default='text',
        help='Output format (default: text)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Save JSON output to file'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress human-readable output (useful with --output)'
    )
    return parser.parse_args()


def print_text_output(report, city_name, coords, distance_miles, min_area, args):
    """Print human-readable output."""
    if args.quiet:
        return

    print("=" * 80)
    print(f"{city_name.upper()} AREA COMPLIANCE SUMMARY")
    print("=" * 80)

    summary = report['summary']
    print(f"Counties in Search Area:    {summary['total_counties_analyzed']}")
    print(f"Compliant:                  {summary['compliant_count']}")
    print(f"Non-Compliant:              {summary['non_compliant_count']}")
    print(f"Compliance Rate:            {summary['compliance_rate_percentage']}%")
    print(f"Minimum Area Requirement:   {min_area:,.2f} sq mi")

    # List all counties in the area
    print()
    print("=" * 80)
    print("ALL COUNTIES IN SEARCH AREA")
    print("=" * 80)

    # Combine and sort all counties by area
    all_counties = (
        report['non_compliant_counties'] +
        report['compliant_counties']
    )
    all_counties.sort(key=lambda x: x.get('area_sq_miles', 0), reverse=True)

    for county in all_counties:
        status = "✓ COMPLIANT" if county['compliant'] else "✗ NON-COMPLIANT"
        shortfall = county.get('shortfall_sq_miles', 0)

        print(f"\n{county['county_name']}, {county['state']}")
        print(f"  Area:        {county['area_sq_miles']:>10.2f} sq mi")
        print(f"  Status:      {status}")
        if not county['compliant']:
            print(f"  Shortfall:   {shortfall:>10.2f} sq mi ({county['compliance_percentage']}%)")
            print(f"  Action:      {county['recommendation']}")

    print()
    print("=" * 80)
    print("✓ Analysis Complete!")
    print("=" * 80)


def output_json(report, city_name, coords, distance_miles, min_area, args):
    """Output JSON data."""
    # Enhance report with query metadata
    enhanced_report = {
        **report,
        'query_metadata': {
            'location': city_name,
            'coordinates': {
                'longitude': coords[0],
                'latitude': coords[1]
            },
            'search_radius_miles': distance_miles,
            'min_area_sq_miles': min_area
        }
    }

    if args.format == 'json' or args.json:
        # Print to stdout
        print(json.dumps(enhanced_report, indent=2))

    if args.output:
        # Save to file
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(enhanced_report, f, indent=2)
        if not args.quiet:
            print(f"\n✓ JSON output saved to: {args.output}")


def main():
    args = parse_arguments()

    if not args.quiet:
        print("=" * 80)
        print(f"Spatial Query: Counties Within {args.distance} Miles of {args.city}")
        print("=" * 80)
        print()

    # ArcGIS Feature Service URL
    service_url = os.getenv(
        'ARCGIS_SERVICE_URL',
        "https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/"
        "USA_Census_Counties/FeatureServer/0"
    )

    # City coordinates (longitude, latitude)
    coords = (args.lon, args.lat)
    distance_miles = args.distance

    if not args.quiet:
        print(f"Location: {args.city}")
        print(f"Coordinates: {coords[1]}°{'N' if coords[1] >= 0 else 'S'}, "
              f"{abs(coords[0])}°{'W' if coords[0] < 0 else 'E'}")
        print(f"Search Radius: {distance_miles} miles")
        print()

    with ArcGISClient(service_url) as client:
        if not args.quiet:
            print("Executing spatial query...")

        nearby_counties = client.query_nearby(
            point=coords,
            distance_miles=distance_miles,
            where="1=1"
        )

        feature_count = len(nearby_counties['features'])
        if not args.quiet:
            print(f"✓ Found {feature_count} counties within {distance_miles} miles of {args.city}")
            print()
            print("Analyzing compliance...")

        report = analyze_oil_gas_lease_compliance(
            nearby_counties['features'],
            min_area_sq_miles=args.min_area
        )

        # Output based on format
        if args.format in ['text', 'both'] or (not args.json and not args.output):
            print()
            print_text_output(report, args.city, coords, distance_miles, args.min_area, args)

        if args.format in ['json', 'both'] or args.json or args.output:
            output_json(report, args.city, coords, distance_miles, args.min_area, args)


if __name__ == "__main__":
    main()
