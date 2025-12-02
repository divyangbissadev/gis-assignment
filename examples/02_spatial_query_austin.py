"""
Example 2: Spatial Query - Counties Near Austin, TX

This example demonstrates spatial queries to find counties within
50 miles of Austin, TX and check their compliance.

Run:
    python examples/02_spatial_query_austin.py
    python examples/02_spatial_query_austin.py --json
    python examples/02_spatial_query_austin.py --format=json
    python examples/02_spatial_query_austin.py --output=austin_report.json
"""

import sys
import os
import json
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.arcgis_client import ArcGISClient
from src.compliance_checker import analyze_oil_gas_lease_compliance


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Spatial query: Find counties near Austin, TX and analyze compliance'
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
    parser.add_argument(
        '--distance',
        type=int,
        default=50,
        help='Search radius in miles (default: 50)'
    )
    return parser.parse_args()


def print_text_output(report, austin_coords, distance_miles, args):
    """Print human-readable output."""
    if args.quiet:
        return

    print("=" * 80)
    print("AUSTIN AREA COMPLIANCE SUMMARY")
    print("=" * 80)

    summary = report['summary']
    print(f"Counties in Search Area:    {summary['total_counties_analyzed']}")
    print(f"Compliant:                  {summary['compliant_count']}")
    print(f"Non-Compliant:              {summary['non_compliant_count']}")
    print(f"Compliance Rate:            {summary['compliance_rate_percentage']}%")

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


def output_json(report, austin_coords, distance_miles, args):
    """Output JSON data."""
    # Enhance report with query metadata
    enhanced_report = {
        **report,
        'query_metadata': {
            'location': 'Austin, TX',
            'coordinates': {
                'longitude': austin_coords[0],
                'latitude': austin_coords[1]
            },
            'search_radius_miles': distance_miles
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
        print(f"Spatial Query: Counties Within {args.distance} Miles of Austin, TX")
        print("=" * 80)
        print()

    # ArcGIS Feature Service URL
    service_url = (
        "https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/"
        "USA_Census_Counties/FeatureServer/0"
    )

    # Austin, TX coordinates (longitude, latitude)
    austin_coords = (-97.7431, 30.2672)
    distance_miles = args.distance

    if not args.quiet:
        print(f"Location: Austin, TX")
        print(f"Coordinates: {austin_coords[1]}°N, {austin_coords[0]}°W")
        print(f"Search Radius: {distance_miles} miles")
        print()

    with ArcGISClient(service_url) as client:
        if not args.quiet:
            print("Executing spatial query...")

        nearby_counties = client.query_nearby(
            point=austin_coords,
            distance_miles=distance_miles,
            where="1=1"
        )

        feature_count = len(nearby_counties['features'])
        if not args.quiet:
            print(f"✓ Found {feature_count} counties within {distance_miles} miles of Austin")
            print()
            print("Analyzing compliance...")

        report = analyze_oil_gas_lease_compliance(
            nearby_counties['features'],
            min_area_sq_miles=2500.0
        )

        # Output based on format
        if args.format in ['text', 'both'] or (not args.json and not args.output):
            print()
            print_text_output(report, austin_coords, distance_miles, args)

        if args.format in ['json', 'both'] or args.json or args.output:
            output_json(report, austin_coords, distance_miles, args)


if __name__ == "__main__":
    main()
