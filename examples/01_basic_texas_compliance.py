"""
Example 1: Basic Texas Counties Compliance Check

This example demonstrates the simplest usage of the oil & gas lease
compliance checker for all Texas counties.

Run:
    python examples/01_basic_texas_compliance.py
    python examples/01_basic_texas_compliance.py --json
    python examples/01_basic_texas_compliance.py --format=json
    python examples/01_basic_texas_compliance.py --output=report.json
"""

import sys
import os
import json
import argparse

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.arcgis_client import ArcGISClient
from src.compliance_checker import analyze_oil_gas_lease_compliance


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Analyze Texas counties for oil & gas lease compliance'
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
        '--top',
        type=int,
        default=5,
        help='Number of top non-compliant counties to show (default: 5)'
    )
    return parser.parse_args()


def print_text_output(report, args):
    """Print human-readable output."""
    if args.quiet:
        return

    print("=" * 80)
    print("COMPLIANCE SUMMARY")
    print("=" * 80)

    summary = report['summary']
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


def output_json(report, args):
    """Output JSON data."""
    if args.format == 'json' or args.json:
        # Print to stdout
        print(json.dumps(report, indent=2))

    if args.output:
        # Save to file
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        if not args.quiet:
            print(f"\n✓ JSON output saved to: {args.output}")


def main():
    args = parse_arguments()

    if not args.quiet:
        print("=" * 80)
        print("Oil & Gas Lease Compliance Check - Texas Counties")
        print("=" * 80)
        print()

    # ArcGIS Feature Service URL for USA Counties
    service_url = (
        "https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/"
        "USA_Census_Counties/FeatureServer/0"
    )

    if not args.quiet:
        print("Step 1: Connecting to ArcGIS Feature Service...")
        print(f"URL: {service_url}")
        print()

    # Query Texas counties
    with ArcGISClient(service_url) as client:
        if not args.quiet:
            print("Step 2: Querying Texas counties...")

        texas_counties = client.query(
            where="STATE_NAME = 'California'",
            page_size=500
        )

        feature_count = len(texas_counties['features'])
        if not args.quiet:
            print(f"✓ Retrieved {feature_count} Texas counties")
            print()
            print("Step 3: Analyzing compliance with 2,500 sq mi requirement...")

        report = analyze_oil_gas_lease_compliance(
            texas_counties['features'],
            min_area_sq_miles=2500.0
        )

        # Output based on format
        if args.format in ['text', 'both'] or (not args.json and not args.output):
            print_text_output(report, args)

        if args.format in ['json', 'both'] or args.json or args.output:
            output_json(report, args)


if __name__ == "__main__":
    main()
