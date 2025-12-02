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

from src.arcgis_client import ArcGISClient
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


def main():
    args = parse_arguments()

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

    # Query state counties
    with ArcGISClient(service_url) as client:
        if not args.quiet:
            print(f"Step 2: Querying {args.state} counties...")

        counties = client.query(
            where=f"STATE_NAME = '{args.state}'",
            page_size=500
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
        if args.format in ['text', 'both'] or (not args.json and not args.output):
            print_text_output(report, args.state, args.min_area, args)

        if args.format in ['json', 'both'] or args.json or args.output:
            output_json(report, args.state, args.min_area, args)


if __name__ == "__main__":
    main()
