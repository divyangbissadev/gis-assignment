"""
Example 3: Export Compliance Results to Multiple Formats

This example demonstrates how to export compliance analysis results
to JSON and CSV formats for further processing or reporting.

Run:
    python examples/03_export_results.py
    python examples/03_export_results.py --state=California
    python examples/03_export_results.py --state=Texas --min-area=3000.0
    python examples/03_export_results.py --output-dir=my_reports
    python examples/03_export_results.py --formats=json,csv
    python examples/03_export_results.py --json  # Also export to stdout
"""

import sys
import os
import json
import csv
import argparse
from datetime import datetime
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
        description='Export compliance results to multiple formats'
    )
    parser.add_argument(
        '--state',
        type=str,
        default='Texas',
        help='State to analyze (default: Texas)'
    )
    parser.add_argument(
        '--min-area',
        type=float,
        default=2500.0,
        help='Minimum area requirement in square miles (default: 2500.0)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='examples/output',
        help='Output directory for exported files (default: examples/output)'
    )
    parser.add_argument(
        '--formats',
        type=str,
        default='json,csv,txt',
        help='Comma-separated list of formats to export (json,csv,txt) (default: all)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Also output JSON to stdout'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress progress messages'
    )
    parser.add_argument(
        '--no-timestamp',
        action='store_true',
        help='Do not add timestamp to filenames'
    )
    return parser.parse_args()


def export_to_json(report, filename, quiet=False):
    """Export full report to JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    if not quiet:
        print(f"✓ Exported full report to: {filename}")


def export_to_csv(counties, filename, quiet=False):
    """Export county list to CSV file."""
    if not counties:
        if not quiet:
            print(f"✗ No data to export to {filename}")
        return

    fieldnames = [
        'county_name',
        'state',
        'area_sq_miles',
        'required_sq_miles',
        'shortfall_sq_miles',
        'compliance_percentage',
        'population',
        'recommendation'
    ]

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(counties)

    if not quiet:
        print(f"✓ Exported {len(counties)} counties to: {filename}")


def export_summary_report(report, filename, quiet=False):
    """Export a text summary report."""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("OIL & GAS LEASE COMPLIANCE REPORT\n")
        f.write("=" * 80 + "\n\n")

        # Metadata
        metadata = report['metadata']
        f.write(f"Report Generated: {metadata['analysis_timestamp']}\n")
        f.write(f"Policy: {metadata['policy']}\n")
        f.write(f"Minimum Requirement: {metadata['minimum_area_requirement_sq_miles']} sq mi\n\n")

        # Summary
        summary = report['summary']
        f.write("SUMMARY\n")
        f.write("-" * 80 + "\n")
        f.write(f"Total Counties Analyzed:    {summary['total_counties_analyzed']}\n")
        f.write(f"Compliant Counties:         {summary['compliant_count']} ({summary['compliance_rate_percentage']}%)\n")
        f.write(f"Non-Compliant Counties:     {summary['non_compliant_count']}\n")
        f.write(f"Total Area Shortfall:       {summary['total_shortfall_sq_miles']:,.2f} sq mi\n")
        f.write(f"Average Shortfall:          {summary['average_shortfall_sq_miles']:,.2f} sq mi\n\n")

        # Top 10 non-compliant
        f.write("TOP 10 NON-COMPLIANT COUNTIES (Ranked by Shortfall)\n")
        f.write("-" * 80 + "\n\n")

        for i, county in enumerate(report['non_compliant_counties'][:10], 1):
            f.write(f"{i}. {county['county_name']}, {county['state']}\n")
            f.write(f"   Area:         {county['area_sq_miles']:>10.2f} sq mi\n")
            f.write(f"   Shortfall:    {county['shortfall_sq_miles']:>10.2f} sq mi\n")
            f.write(f"   Compliance:   {county['compliance_percentage']:>10.2f}%\n")
            f.write(f"   Population:   {county['population']:>10,}\n")
            f.write(f"   Action:       {county['recommendation']}\n\n")

    if not quiet:
        print(f"✓ Exported summary report to: {filename}")


def main():
    args = parse_arguments()

    if not args.quiet:
        print("=" * 80)
        print("Export Compliance Results to Multiple Formats")
        print("=" * 80)
        print(f"State: {args.state}")
        print(f"Minimum Area: {args.min_area} sq mi")
        print()

    # ArcGIS Feature Service URL
    service_url = os.getenv(
        'ARCGIS_SERVICE_URL',
        "https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/"
        "USA_Census_Counties/FeatureServer/0"
    )

    if not args.quiet:
        print(f"Step 1: Querying {args.state} counties...")

    with ArcGISClient(service_url) as client:
        state_counties = client.query(
            where=f"STATE_NAME = '{args.state}'",
            page_size=500
        )
        if not args.quiet:
            print(f"✓ Retrieved {len(state_counties['features'])} counties")

    if not args.quiet:
        print("\nStep 2: Running compliance analysis...")

    report = analyze_oil_gas_lease_compliance(
        state_counties['features'],
        min_area_sq_miles=args.min_area
    )

    if not args.quiet:
        print(f"✓ Analysis complete")

    # Parse requested formats
    requested_formats = [fmt.strip().lower() for fmt in args.formats.split(',')]

    # Create output directory
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    if not args.quiet:
        print(f"\nStep 3: Exporting results to {output_dir}/...")
        print()

    # Generate timestamp for filenames
    timestamp = "" if args.no_timestamp else f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    exported_files = []

    # Export to different formats based on flags
    if 'json' in requested_formats:
        json_file = f"{output_dir}/full_report{timestamp}.json"
        export_to_json(report, json_file, args.quiet)
        exported_files.append(("Full JSON Report", json_file))

    if 'csv' in requested_formats:
        non_compliant_csv = f"{output_dir}/non_compliant_counties{timestamp}.csv"
        compliant_csv = f"{output_dir}/compliant_counties{timestamp}.csv"
        export_to_csv(report['non_compliant_counties'], non_compliant_csv, args.quiet)
        export_to_csv(report['compliant_counties'], compliant_csv, args.quiet)
        exported_files.append(("Non-Compliant CSV", non_compliant_csv))
        exported_files.append(("Compliant CSV", compliant_csv))

    if 'txt' in requested_formats:
        summary_file = f"{output_dir}/summary_report{timestamp}.txt"
        export_summary_report(report, summary_file, args.quiet)
        exported_files.append(("Summary Text Report", summary_file))

    # Output JSON to stdout if requested
    if args.json:
        print(json.dumps(report, indent=2))

    # Display summary
    if not args.quiet:
        print()
        print("=" * 80)
        print("EXPORT SUMMARY")
        print("=" * 80)

        summary = report['summary']
        print(f"Total Counties:       {summary['total_counties_analyzed']}")
        print(f"Non-Compliant:        {summary['non_compliant_count']}")
        print(f"Compliant:            {summary['compliant_count']}")
        print()
        print("Exported Files:")
        for i, (desc, filepath) in enumerate(exported_files, 1):
            print(f"  {i}. {desc:30} {os.path.basename(filepath)}")

        print()
        print("=" * 80)
        print(f"✓ All exports complete! Check the '{output_dir}/' directory.")
        print("=" * 80)


if __name__ == "__main__":
    main()
