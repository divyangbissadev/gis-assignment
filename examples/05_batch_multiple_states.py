"""
Example 5: Batch Processing - Analyze Multiple States

This example demonstrates how to analyze compliance for multiple
states in a batch process and compare results.

Run:
    python examples/05_batch_multiple_states.py
    python examples/05_batch_multiple_states.py --json
    python examples/05_batch_multiple_states.py --output=multi_state_report.json
"""

import sys
import os
import time
import json
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.arcgis_client import ArcGISClient
from src.compliance_checker import analyze_oil_gas_lease_compliance


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Batch analysis of multiple states'
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
        '--states',
        type=str,
        help='Comma-separated list of states (default: TX,OK,LA,NM,WY)'
    )
    return parser.parse_args()


def analyze_state(client, state_name, min_area, quiet=False):
    """Analyze compliance for a single state."""
    if not quiet:
        print(f"\nProcessing {state_name}...")

    try:
        start_time = time.time()

        # Query state counties
        state_counties = client.query(
            where=f"STATE_NAME = '{state_name}'",
            page_size=500
        )

        feature_count = len(state_counties['features'])
        if not quiet:
            print(f"  ✓ Retrieved {feature_count} counties")

        # Analyze compliance
        report = analyze_oil_gas_lease_compliance(
            state_counties['features'],
            min_area_sq_miles=min_area
        )

        elapsed = time.time() - start_time
        if not quiet:
            print(f"  ✓ Analysis completed in {elapsed:.2f}s")

        return report

    except Exception as e:
        if not quiet:
            print(f"  ✗ Error: {e}")
        return None


def print_state_comparison(state_reports):
    """Print comparison table of all analyzed states."""
    print()
    print("=" * 120)
    print("STATE COMPARISON TABLE")
    print("=" * 120)

    # Header
    print(f"{'State':<15} {'Total':<8} {'Compliant':<12} {'Non-Comp':<12} "
          f"{'Rate %':<10} {'Total Shortfall':<18} {'Avg Shortfall':<15}")
    print("-" * 120)

    # Data rows
    for state_name, report in sorted(state_reports.items()):
        if report:
            summary = report['summary']
            print(f"{state_name:<15} "
                  f"{summary['total_counties_analyzed']:<8} "
                  f"{summary['compliant_count']:<12} "
                  f"{summary['non_compliant_count']:<12} "
                  f"{summary['compliance_rate_percentage']:<10.2f} "
                  f"{summary['total_shortfall_sq_miles']:<18,.2f} "
                  f"{summary['average_shortfall_sq_miles']:<15,.2f}")


def print_worst_counties_across_states(state_reports, top_n=10):
    """Find and print worst counties across all states."""
    print()
    print("=" * 100)
    print(f"TOP {top_n} WORST COUNTIES ACROSS ALL STATES (Ranked by Shortfall)")
    print("=" * 100)

    # Combine all non-compliant counties from all states
    all_non_compliant = []
    for state_name, report in state_reports.items():
        if report:
            for county in report['non_compliant_counties']:
                county['state_analyzed'] = state_name
                all_non_compliant.append(county)

    # Sort by shortfall
    all_non_compliant.sort(key=lambda x: x['shortfall_sq_miles'], reverse=True)

    # Print top N
    for i, county in enumerate(all_non_compliant[:top_n], 1):
        print(f"\n{i}. {county['county_name']}, {county['state']}")
        print(f"   Area:        {county['area_sq_miles']:>10.2f} sq mi")
        print(f"   Shortfall:   {county['shortfall_sq_miles']:>10.2f} sq mi")
        print(f"   Compliance:  {county['compliance_percentage']:>10.2f}%")
        print(f"   Population:  {county['population']:>10,}")


def main():
    args = parse_arguments()

    if not args.quiet:
        print("=" * 80)
        print("Batch Processing: Multi-State Compliance Analysis")
        print("=" * 80)

    # States to analyze
    if args.states:
        # Parse custom states from command line
        state_mapping = {
            'TX': 'Texas', 'OK': 'Oklahoma', 'LA': 'Louisiana',
            'NM': 'New Mexico', 'WY': 'Wyoming', 'CO': 'Colorado',
            'ND': 'North Dakota', 'MT': 'Montana', 'KS': 'Kansas'
        }
        state_codes = [s.strip().upper() for s in args.states.split(',')]
        states_to_analyze = [state_mapping.get(code, code) for code in state_codes]
    else:
        # Default states (oil & gas producing states)
        states_to_analyze = ['Texas', 'Oklahoma', 'Louisiana', 'New Mexico', 'Wyoming']

    # ArcGIS Feature Service URL
    service_url = (
        "https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/"
        "USA_Census_Counties/FeatureServer/0"
    )

    min_area_requirement = 2500.0

    if not args.quiet:
        print(f"\nAnalyzing {len(states_to_analyze)} states:")
        for state in states_to_analyze:
            print(f"  - {state}")
        print(f"\nMinimum area requirement: {min_area_requirement} sq mi")
        print("\nStarting batch analysis...")

    state_reports = {}
    total_start_time = time.time()

    with ArcGISClient(service_url) as client:
        for state_name in states_to_analyze:
            report = analyze_state(client, state_name, min_area_requirement, args.quiet)
            if report:
                state_reports[state_name] = report

    total_elapsed = time.time() - total_start_time

    if not args.quiet:
        print()
        print("=" * 80)
        print("BATCH PROCESSING COMPLETE")
        print("=" * 80)
        print(f"States analyzed: {len(state_reports)}/{len(states_to_analyze)}")
        print(f"Total time: {total_elapsed:.2f} seconds")

    # Calculate overall statistics for JSON output
    if state_reports:
        total_counties = sum(r['summary']['total_counties_analyzed'] for r in state_reports.values())
        total_compliant = sum(r['summary']['compliant_count'] for r in state_reports.values())
        total_non_compliant = sum(r['summary']['non_compliant_count'] for r in state_reports.values())
        total_shortfall = sum(r['summary']['total_shortfall_sq_miles'] for r in state_reports.values())

        best_state = max(state_reports.items(),
                        key=lambda x: x[1]['summary']['compliance_rate_percentage'])
        worst_state = min(state_reports.items(),
                         key=lambda x: x[1]['summary']['compliance_rate_percentage'])

        # Build structured result
        all_non_compliant = []
        for state_name, report in state_reports.items():
            for county in report['non_compliant_counties']:
                county_copy = county.copy()
                county_copy['state_analyzed'] = state_name
                all_non_compliant.append(county_copy)
        all_non_compliant.sort(key=lambda x: x['shortfall_sq_miles'], reverse=True)

        results = {
            'state_reports': state_reports,
            'overall_statistics': {
                'states_analyzed': len(state_reports),
                'total_counties': total_counties,
                'total_compliant': total_compliant,
                'total_non_compliant': total_non_compliant,
                'overall_compliance_rate': round(total_compliant / total_counties * 100, 2) if total_counties > 0 else 0,
                'total_shortfall_sq_miles': round(total_shortfall, 2),
                'average_shortfall_per_county': round(
                    total_shortfall / total_non_compliant if total_non_compliant > 0 else 0, 2
                ),
                'best_performing_state': {
                    'name': best_state[0],
                    'compliance_rate': best_state[1]['summary']['compliance_rate_percentage']
                },
                'worst_performing_state': {
                    'name': worst_state[0],
                    'compliance_rate': worst_state[1]['summary']['compliance_rate_percentage']
                }
            },
            'worst_counties_across_states': all_non_compliant[:10],
            'processing_time_seconds': round(total_elapsed, 2)
        }

        # Text output
        if args.format in ['text', 'both'] or (not args.json and not args.output):
            print_state_comparison(state_reports)
            print_worst_counties_across_states(state_reports, top_n=10)

            # Overall statistics
            print()
            print("=" * 80)
            print("OVERALL STATISTICS ACROSS ALL STATES")
            print("=" * 80)
            print(f"\nTotal Counties Analyzed:      {total_counties}")
            print(f"Total Compliant:              {total_compliant} ({total_compliant/total_counties*100:.2f}%)")
            print(f"Total Non-Compliant:          {total_non_compliant}")
            print(f"Combined Area Shortfall:      {total_shortfall:,.2f} sq mi")
            print(f"Average Shortfall per County: {total_shortfall/total_non_compliant if total_non_compliant > 0 else 0:,.2f} sq mi")
            print(f"\nBest Performing State:        {best_state[0]} "
                  f"({best_state[1]['summary']['compliance_rate_percentage']:.2f}% compliant)")
            print(f"Worst Performing State:       {worst_state[0]} "
                  f"({worst_state[1]['summary']['compliance_rate_percentage']:.2f}% compliant)")

            print()
            print("=" * 80)
            print("✓ All analyses complete!")
            print("=" * 80)

        # JSON output
        if args.format in ['json', 'both'] or args.json or args.output:
            if args.format == 'json' or args.json:
                print(json.dumps(results, indent=2))
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2)
                if not args.quiet:
                    print(f"\n✓ JSON output saved to: {args.output}")


if __name__ == "__main__":
    main()
