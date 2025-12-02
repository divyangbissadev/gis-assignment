"""
Example 6: Custom Thresholds and Scenarios

This example demonstrates how to use different area thresholds
to model various lease policy scenarios.

Run:
    python examples/06_custom_thresholds.py
    python examples/06_custom_thresholds.py --json
    python examples/06_custom_thresholds.py --output=threshold_comparison.json
"""

import argparse
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.arcgis_client import ArcGISClient
from src.compliance_checker import analyze_oil_gas_lease_compliance


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Model different policy scenarios with custom thresholds'
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
    parser.add_argument(
        '--thresholds',
        type=str,
        help='Comma-separated list of thresholds in sq mi (default: 1000,1500,2000,2500,3000,3500)'
    )
    return parser.parse_args()


def compare_thresholds(features, thresholds, quiet=False):
    """Compare compliance across different area thresholds."""
    results = {}

    for threshold in thresholds:
        if not quiet:
            print(f"  Analyzing with {threshold} sq mi threshold...")
        report = analyze_oil_gas_lease_compliance(
            features,
            min_area_sq_miles=threshold
        )
        results[threshold] = report

    return results


def print_threshold_comparison(threshold_results, args):
    """Print comparison table for different thresholds."""
    if args.quiet:
        return

    print()
    print("=" * 100)
    print("THRESHOLD COMPARISON TABLE")
    print("=" * 100)

    print(f"{'Threshold':<15} {'Total':<8} {'Compliant':<12} {'Non-Comp':<12} "
          f"{'Rate %':<10} {'Total Shortfall':<18}")
    print("-" * 100)

    for threshold in sorted(threshold_results.keys()):
        summary = threshold_results[threshold]['summary']
        print(f"{threshold:<15.0f} "
              f"{summary['total_counties_analyzed']:<8} "
              f"{summary['compliant_count']:<12} "
              f"{summary['non_compliant_count']:<12} "
              f"{summary['compliance_rate_percentage']:<10.2f} "
              f"{summary['total_shortfall_sq_miles']:<18,.2f}")


def main():
    args = parse_arguments()

    if not args.quiet:
        print("=" * 80)
        print("Custom Thresholds and Policy Scenarios")
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

    feature_count = len(texas_counties['features'])
    if not args.quiet:
        print(f"✓ Retrieved {feature_count} Texas counties\n")

    # Define different policy scenarios
    if args.thresholds:
        # Parse custom thresholds from command line
        thresholds = [float(t.strip()) for t in args.thresholds.split(',')]
        scenarios = {t: f"Custom Threshold - {t} sq mi" for t in thresholds}
    else:
        # Default scenarios
        scenarios = {
            1000: "Relaxed Policy - Small Leases",
            1500: "Moderate Policy",
            2000: "Standard Policy - Medium Leases",
            2500: "Current Policy - Standard Terms",
            3000: "Strict Policy - Large Leases Only",
            3500: "Very Strict Policy"
        }

    if not args.quiet:
        print("=" * 80)
        print("POLICY SCENARIOS")
        print("=" * 80)
        for threshold, description in scenarios.items():
            print(f"{threshold:>6} sq mi - {description}")
        print("\n" + "=" * 80)
        print("RUNNING ANALYSIS FOR ALL SCENARIOS")
        print("=" * 80)

    threshold_results = compare_thresholds(
        texas_counties['features'],
        list(scenarios.keys()),
        args.quiet
    )

    # Display comparison
    print_threshold_comparison(threshold_results, args)

    # Detailed analysis for current policy (2500 sq mi)
    print()
    print("=" * 80)
    print("DETAILED ANALYSIS: CURRENT POLICY (2,500 sq mi)")
    print("=" * 80)

    current_report = threshold_results[2500]
    summary = current_report['summary']

    print(f"\nCompliance Rate:          {summary['compliance_rate_percentage']:.2f}%")
    print(f"Compliant Counties:       {summary['compliant_count']}")
    print(f"Non-Compliant Counties:   {summary['non_compliant_count']}")
    print(f"Total Area Shortfall:     {summary['total_shortfall_sq_miles']:,.2f} sq mi")

    print("\nTop 5 Non-Compliant Counties:")
    for i, county in enumerate(current_report['non_compliant_counties'][:5], 1):
        print(f"{i}. {county['county_name']:30} - "
              f"Short by {county['shortfall_sq_miles']:>7.2f} sq mi "
              f"({county['compliance_percentage']:.1f}%)")

    # Impact analysis: What if we lowered the threshold?
    print()
    print("=" * 80)
    print("IMPACT ANALYSIS: Lowering Threshold from 2,500 to 2,000 sq mi")
    print("=" * 80)

    current = threshold_results[2500]['summary']
    lower = threshold_results[2000]['summary']

    change_compliant = lower['compliant_count'] - current['compliant_count']
    change_percentage = lower['compliance_rate_percentage'] - current['compliance_rate_percentage']
    change_shortfall = current['total_shortfall_sq_miles'] - lower['total_shortfall_sq_miles']

    print(f"\nAdditional Compliant Counties:    {change_compliant}")
    print(f"Compliance Rate Increase:         {change_percentage:.2f} percentage points")
    print(f"Reduction in Total Shortfall:     {change_shortfall:,.2f} sq mi")

    # Find counties that would become compliant
    current_non_compliant_names = {c['county_name'] for c in current_report['non_compliant_counties']}
    lower_compliant_names = {c['county_name'] for c in threshold_results[2000]['compliant_counties']}

    newly_compliant = current_non_compliant_names & lower_compliant_names

    if newly_compliant:
        print(f"\nCounties that would become compliant ({len(newly_compliant)}):")
        for name in sorted(newly_compliant)[:10]:
            print(f"  - {name}")
        if len(newly_compliant) > 10:
            print(f"  ... and {len(newly_compliant) - 10} more")

    # Recommendation based on analysis
    print()
    print("=" * 80)
    print("POLICY RECOMMENDATION")
    print("=" * 80)

    if current['compliance_rate_percentage'] < 20:
        print("\n⚠ Current policy (2,500 sq mi) results in very low compliance (<20%).")
        print("  Consider lowering the threshold or implementing tiered policies.")
    elif current['compliance_rate_percentage'] < 50:
        print("\n⚠ Current policy (2,500 sq mi) results in moderate compliance (<50%).")
        print("  Review threshold and consider special provisions for smaller counties.")
    else:
        print("\n✓ Current policy (2,500 sq mi) achieves good compliance (>50%).")
        print("  Policy appears reasonable for this region.")

    print()
    print("=" * 80)
    print("✓ Analysis Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
