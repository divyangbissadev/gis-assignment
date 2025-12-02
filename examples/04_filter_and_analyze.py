"""
Example 4: Filter and Analyze Specific County Subsets

This example demonstrates how to filter compliance results and
perform targeted analysis on specific subsets of counties.

Run:
    python examples/04_filter_and_analyze.py
    python examples/04_filter_and_analyze.py --json
    python examples/04_filter_and_analyze.py --output=filtered_results.json
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
        description='Filter and analyze compliance results by categories'
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
        help='Suppress human-readable output'
    )
    return parser.parse_args()


def filter_by_compliance_percentage(counties, min_percent, max_percent):
    """Filter counties by compliance percentage range."""
    return [
        c for c in counties
        if min_percent <= c['compliance_percentage'] < max_percent
    ]


def filter_by_population(counties, min_population):
    """Filter counties by minimum population."""
    return [
        c for c in counties
        if c['population'] >= min_population
    ]


def filter_by_shortfall(counties, min_shortfall):
    """Filter counties by minimum shortfall."""
    return [
        c for c in counties
        if c.get('shortfall_sq_miles', 0) >= min_shortfall
    ]


def print_text_output(filtered_results, args):
    """Print human-readable output."""
    if args.quiet:
        return

    near_compliant = filtered_results['near_compliant']
    moderate = filtered_results['moderate']
    far_non_compliant = filtered_results['far_non_compliant']
    high_pop = filtered_results['high_population']
    large_shortfall = filtered_results['large_shortfall']

    # Filter 1: Counties close to compliant (90-99%)
    print()
    print("=" * 80)
    print("FILTER 1: Counties Close to Compliant (90-99%)")
    print("=" * 80)
    print(f"\nFound {len(near_compliant)} counties that are 90-99% compliant:")
    print("These counties have minor shortfalls and may qualify for special terms.\n")

    for county in near_compliant:
        print(f"{county['county_name']:30} - "
              f"{county['compliance_percentage']:5.1f}% - "
              f"Short by {county['shortfall_sq_miles']:6.1f} sq mi")

    # Filter 2: Counties moderately compliant (50-89%)
    print()
    print("=" * 80)
    print("FILTER 2: Counties Moderately Compliant (50-89%)")
    print("=" * 80)
    print(f"\nFound {len(moderate)} counties that are 50-89% compliant:")
    print("These counties may benefit from pooling agreements or tract consolidation.\n")

    for county in moderate[:10]:
        print(f"{county['county_name']:30} - "
              f"{county['compliance_percentage']:5.1f}% - "
              f"Short by {county['shortfall_sq_miles']:6.1f} sq mi")

    if len(moderate) > 10:
        print(f"... and {len(moderate) - 10} more counties")

    # Filter 3: Counties far from compliant (<50%)
    print()
    print("=" * 80)
    print("FILTER 3: Counties Far from Compliant (<50%)")
    print("=" * 80)
    print(f"\nFound {len(far_non_compliant)} counties that are <50% compliant:")
    print("These counties likely need alternative lease structures.\n")

    for county in far_non_compliant[:10]:
        print(f"{county['county_name']:30} - "
              f"{county['compliance_percentage']:5.1f}% - "
              f"Short by {county['shortfall_sq_miles']:6.1f} sq mi")

    if len(far_non_compliant) > 10:
        print(f"... and {len(far_non_compliant) - 10} more counties")

    # Filter 4: High-population non-compliant counties
    print()
    print("=" * 80)
    print("FILTER 4: High-Population Non-Compliant Counties (>100,000)")
    print("=" * 80)
    print(f"\nFound {len(high_pop)} non-compliant counties with population >100,000:")
    print("These may be priority areas for policy review.\n")

    for county in sorted(high_pop, key=lambda x: x['population'], reverse=True):
        print(f"{county['county_name']:30} - "
              f"Pop: {county['population']:>8,} - "
              f"{county['compliance_percentage']:5.1f}% - "
              f"Short by {county['shortfall_sq_miles']:6.1f} sq mi")

    # Filter 5: Large shortfalls (>1500 sq mi)
    print()
    print("=" * 80)
    print("FILTER 5: Counties with Large Shortfalls (>1,500 sq mi)")
    print("=" * 80)
    print(f"\nFound {len(large_shortfall)} counties with shortfall >1,500 sq mi:")
    print("These counties are significantly below requirements.\n")

    for county in large_shortfall:
        print(f"{county['county_name']:30} - "
              f"Area: {county['area_sq_miles']:7.1f} sq mi - "
              f"Short by {county['shortfall_sq_miles']:6.1f} sq mi")

    # Summary statistics by category
    print()
    print("=" * 80)
    print("SUMMARY STATISTICS BY CATEGORY")
    print("=" * 80)
    print(f"\nNear Compliant (90-99%):          {len(near_compliant):>3} counties")
    print(f"Moderately Compliant (50-89%):    {len(moderate):>3} counties")
    print(f"Far from Compliant (<50%):        {len(far_non_compliant):>3} counties")
    print(f"High Population (>100k):          {len(high_pop):>3} counties")
    print(f"Large Shortfall (>1,500 sq mi):   {len(large_shortfall):>3} counties")

    total_near_shortfall = sum(c['shortfall_sq_miles'] for c in near_compliant)
    print(f"\nTotal shortfall (Near Compliant): {total_near_shortfall:>10,.2f} sq mi")
    print(f"Avg shortfall (Near Compliant):   {total_near_shortfall/len(near_compliant) if near_compliant else 0:>10,.2f} sq mi")

    print()
    print("=" * 80)
    print("✓ Analysis Complete!")
    print("=" * 80)


def output_json(filtered_results, args):
    """Output JSON data."""
    if args.format == 'json' or args.json:
        print(json.dumps(filtered_results, indent=2))

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(filtered_results, f, indent=2)
        if not args.quiet:
            print(f"\n✓ JSON output saved to: {args.output}")


def main():
    args = parse_arguments()

    if not args.quiet:
        print("=" * 80)
        print("Filter and Analyze Compliance Results")
        print("=" * 80)
        print()

    # ArcGIS Feature Service URL
    service_url = (
        "https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/"
        "USA_Census_Counties/FeatureServer/0"
    )

    if not args.quiet:
        print("Querying Texas counties...")

    with ArcGISClient(service_url) as client:
        texas_counties = client.query(
            where="STATE_NAME = 'Texas'",
            page_size=500
        )

    if not args.quiet:
        print("Running compliance analysis...")

    report = analyze_oil_gas_lease_compliance(
        texas_counties['features'],
        min_area_sq_miles=2500.0
    )

    non_compliant = report['non_compliant_counties']

    # Apply all filters
    near_compliant = filter_by_compliance_percentage(non_compliant, 90, 100)
    moderate = filter_by_compliance_percentage(non_compliant, 50, 90)
    far_non_compliant = filter_by_compliance_percentage(non_compliant, 0, 50)
    high_pop = filter_by_population(non_compliant, 100000)
    large_shortfall = filter_by_shortfall(non_compliant, 1500)

    # Build filtered results structure
    total_near_shortfall = sum(c['shortfall_sq_miles'] for c in near_compliant)
    filtered_results = {
        'base_report': report,
        'near_compliant': near_compliant,
        'moderate': moderate,
        'far_non_compliant': far_non_compliant,
        'high_population': high_pop,
        'large_shortfall': large_shortfall,
        'summary_stats': {
            'near_compliant_count': len(near_compliant),
            'moderate_count': len(moderate),
            'far_non_compliant_count': len(far_non_compliant),
            'high_population_count': len(high_pop),
            'large_shortfall_count': len(large_shortfall),
            'total_near_shortfall_sq_miles': round(total_near_shortfall, 2),
            'avg_near_shortfall_sq_miles': round(
                total_near_shortfall / len(near_compliant) if near_compliant else 0, 2
            )
        }
    }

    # Output based on format
    if args.format in ['text', 'both'] or (not args.json and not args.output):
        print_text_output(filtered_results, args)

    if args.format in ['json', 'both'] or args.json or args.output:
        output_json(filtered_results, args)


if __name__ == "__main__":
    main()
