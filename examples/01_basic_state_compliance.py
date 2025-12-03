"""
Example 1: Basic State Counties Compliance Check

This example demonstrates the simplest usage of the oil & gas lease
compliance checker for counties in any state.

Run:
    python examples/01_basic_state_compliance.py
    python examples/01_basic_state_compliance.py --state="California"
    python examples/01_basic_state_compliance.py --state="Texas" --min-area=2500
    python examples/01_basic_state_compliance.py --json
    python examples/01_basic_state_compliance.py --format=json --output=report.json
"""

import sys
import os
import json
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.arcgis_client import ArcGISClient, SimpleArcGISClient
from src.compliance_checker import analyze_oil_gas_lease_compliance


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Analyze state counties for oil & gas lease compliance'
    )
    parser.add_argument(
        '--state',
        type=str,
        default='Texas',
        help='State name to analyze (default: Texas)'
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
        choices=['text', 'json', 'geojson', 'both'],
        default='text',
        help='Output format: text, json, geojson, or both (default: text)'
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
        '--top',
        type=int,
        default=5,
        help='Number of top non-compliant counties to show (default: 5)'
    )
    return parser.parse_args()


def print_text_output(report, state_name, min_area, args):
    """Print human-readable output."""
    if args.quiet:
        return

    print("=" * 80)
    print("COMPLIANCE SUMMARY")
    print("=" * 80)

    summary = report['summary']
    print(f"State:                      {state_name}")
    print(f"Minimum Area Requirement:   {min_area:,.2f} sq mi")
    print(f"Total Counties Analyzed:    {summary['total_counties_analyzed']}")
    print(f"Compliant Counties:         {summary['compliant_count']} ({summary['compliance_rate_percentage']}%)")
    print(f"Non-Compliant Counties:     {summary['non_compliant_count']}")
    print()
    print(f"Total Area Shortfall:       {summary['total_shortfall_sq_miles']:,.2f} sq mi")
    print(f"Average Shortfall:          {summary['average_shortfall_sq_miles']:,.2f} sq mi")

    # Display top N non-compliant counties
    print()
    print("=" * 80)
    print(f"TOP {args.top} NON-COMPLIANT COUNTIES (Ranked by Shortfall)")
    print("=" * 80)

    for i, county in enumerate(report['non_compliant_counties'][:args.top], 1):
        print(f"\n{i}. {county['county_name']}")
        print(f"   Current Area:    {county['area_sq_miles']:>10.2f} sq mi")
        print(f"   Shortfall:       {county['shortfall_sq_miles']:>10.2f} sq mi")
        print(f"   Compliance:      {county['compliance_percentage']:>10.2f}%")
        print(f"   Recommendation:  {county['recommendation']}")

    total_non_compliant = len(report['non_compliant_counties'])
    if total_non_compliant > args.top:
        print(f"\n... and {total_non_compliant - args.top} more non-compliant counties")

    print()
    print("=" * 80)
    print("✓ Analysis Complete!")
    print("=" * 80)


def output_json(report, state_name, min_area, args):
    """Output JSON data."""
    # Enhance report with query metadata
    enhanced_report = {
        **report,
        'query_metadata': {
            'state': state_name,
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


def output_geojson(report, state_name, min_area, args):
    """Output GeoJSON data."""
    # Combine all counties
    all_counties = report['non_compliant_counties'] + report['compliant_counties']

    # Filter counties that have geometry
    features_with_geometry = [county for county in all_counties if county.get('geometry')]

    if not features_with_geometry:
        if not args.quiet:
            print("\n⚠ No geometries available for GeoJSON output")
        return

    # Create GeoJSON FeatureCollection
    geojson = {
        "type": "FeatureCollection",
        "metadata": {
            "state": state_name,
            "min_area_sq_miles": min_area,
            "total_features": len(features_with_geometry),
            "compliant_count": report['summary']['compliant_count'],
            "non_compliant_count": report['summary']['non_compliant_count']
        },
        "features": []
    }

    for county in features_with_geometry:
        feature = {
            "type": "Feature",
            "geometry": county.get('geometry'),
            "properties": {
                "county_name": county.get('county_name'),
                "state": county.get('state'),
                "area_sq_miles": county.get('area_sq_miles'),
                "required_sq_miles": county.get('required_sq_miles'),
                "compliant": county.get('compliant'),
                "population": county.get('population')
            }
        }

        # Add compliance-specific properties
        if county.get('compliant'):
            feature["properties"]["excess_area"] = county.get('excess_area')
        else:
            feature["properties"]["shortfall_sq_miles"] = county.get('shortfall_sq_miles')
            feature["properties"]["compliance_percentage"] = county.get('compliance_percentage')
            feature["properties"]["recommendation"] = county.get('recommendation')

        geojson["features"].append(feature)

    if args.format == 'geojson' and not args.output:
        # Print to stdout only if no output file is specified
        print(json.dumps(geojson, indent=2))

    if args.output:
        # Save to file (use .geojson extension if not specified)
        output_file = args.output
        if args.format == 'geojson' and not output_file.endswith('.geojson'):
            output_file = output_file.rsplit('.', 1)[0] + '.geojson'

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(geojson, f, indent=2)
        if not args.quiet:
            print(f"\n✓ GeoJSON output saved to: {output_file}")
            print(f"  Features: {len(geojson['features'])}")
            print(f"  Compliant: {report['summary']['compliant_count']}")
            print(f"  Non-Compliant: {report['summary']['non_compliant_count']}")


def main():
    args = parse_arguments()

    # Check if GeoJSON format is requested
    needs_geometry = args.format == 'geojson'

    if not args.quiet:
        print("=" * 80)
        print(f"Oil & Gas Lease Compliance Check - {args.state} Counties")
        print("=" * 80)
        print()

    # ArcGIS Feature Service URL for USA Counties
    service_url = os.getenv(
        'ARCGIS_SERVICE_URL',
        "https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/"
        "USA_Census_Counties/FeatureServer/0"
    )

    if not args.quiet:
        print("Step 1: Connecting to ArcGIS Feature Service...")
        print(f"URL: {service_url}")
        print()

    # Query state counties - use SimpleArcGISClient for GeoJSON to preserve geometry
    if needs_geometry:
        with SimpleArcGISClient(service_url) as client:
            if not args.quiet:
                print(f"Step 2: Querying {args.state} counties with geometry...")

            counties = client.query_features(
                where_clause=f"STATE_NAME = '{args.state}'",
                max_records=1000,
                return_geometry=True,
                paginate=True
            )

            feature_count = len(counties['features'])
            if not args.quiet:
                print(f"✓ Retrieved {feature_count} {args.state} counties (with geometry)")
                print()
                print(f"Step 3: Analyzing compliance with {args.min_area:,.2f} sq mi requirement...")

            report = analyze_oil_gas_lease_compliance(
                counties['features'],
                min_area_sq_miles=args.min_area,
                include_geojson=True
            )
    else:
        with ArcGISClient(service_url) as client:
            if not args.quiet:
                print(f"Step 2: Querying {args.state} counties...")

            counties = client.query(
                where=f"STATE_NAME = '{args.state}'",
                page_size=1000
            )

            feature_count = len(counties['features'])
            if not args.quiet:
                print(f"✓ Retrieved {feature_count} {args.state} counties")
                print()
                print(f"Step 3: Analyzing compliance with {args.min_area:,.2f} sq mi requirement...")

            report = analyze_oil_gas_lease_compliance(
                counties['features'],
                min_area_sq_miles=args.min_area
            )

    # Output based on format
    if args.format in ['text', 'both'] or (not args.json and not args.output and args.format != 'geojson'):
        print_text_output(report, args.state, args.min_area, args)

    if args.format == 'geojson':
        output_geojson(report, args.state, args.min_area, args)
    elif args.format in ['json', 'both'] or args.json or args.output:
        output_json(report, args.state, args.min_area, args)


if __name__ == "__main__":
    main()
