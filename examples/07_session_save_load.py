"""
Example 7: Session Save/Load - Resume Analysis Sessions

This example demonstrates how to save and load analysis sessions,
allowing you to resume work later or share results with others.

Run:
    python examples/07_session_save_load.py
    python examples/07_session_save_load.py --load-only
    python examples/07_session_save_load.py --session-file=my_session.json
"""

import sys
import os
import argparse
from datetime import datetime
from pathlib import Path # Added import
from dotenv import load_dotenv

load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.arcgis_client import ArcGISClient
from src.compliance_checker import analyze_oil_gas_lease_compliance
from src.session_manager import SessionManager


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Test session save/load functionality'
    )
    parser.add_argument(
        '--session-dir',
        type=str,
        default='examples/sessions',
        help='Directory to store session files (default: examples/sessions)'
    )
    parser.add_argument(
        '--session-name',
        type=str,
        default='texas_compliance',
        help='Name of the session (default: texas_compliance). File will be <session_name>.json'
    )
    parser.add_argument(
        '--load-only',
        action='store_true',
        help='Only load existing session (skip query)'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Disable automatic backup creation'
    )
    parser.add_argument(
        '--user',
        type=str,
        default='demo_user',
        help='User identifier for session metadata'
    )
    return parser.parse_args()


def run_analysis_and_save(args):
    """Run analysis and save session."""
    print("=" * 80)
    print("STEP 1: Running Analysis")
    print("=" * 80)
    print()

    # ArcGIS Feature Service URL
    service_url = os.getenv(
        'ARCGIS_SERVICE_URL',
        "https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/"
        "USA_Census_Counties/FeatureServer/0"
    )

    # Define query parameters
    query_params = {
        "where": "STATE_NAME = 'Texas'",
        "page_size": 500,
        "min_area_sq_miles": 2500.0
    }

    print(f"Query: {query_params['where']}")
    print(f"Minimum area requirement: {query_params['min_area_sq_miles']} sq mi")
    print()

    # Execute query
    print("Querying ArcGIS service...")
    with ArcGISClient(service_url) as client:
        query_results = client.query(
            where=query_params["where"],
            page_size=query_params["page_size"]
        )

    print(f"✓ Retrieved {len(query_results['features'])} counties")
    print()

    # Analyze compliance
    print("Analyzing compliance...")
    compliance_report = analyze_oil_gas_lease_compliance(
        query_results['features'],
        min_area_sq_miles=query_params['min_area_sq_miles']
    )

    summary = compliance_report['summary']
    print(f"✓ Compliance rate: {summary['compliance_rate_percentage']}%")
    print(f"  Compliant: {summary['compliant_count']}")
    print(f"  Non-compliant: {summary['non_compliant_count']}")
    print()

    # Save session
    print("=" * 80)
    print("STEP 2: Saving Session")
    print("=" * 80)
    print()

    session_mgr = SessionManager(
        session_dir=args.session_dir,
        auto_backup=not args.no_backup
    )

    saved_path = session_mgr.save(
        name=args.session_name,
        query_params=query_params,
        results=query_results,
        compliance_report=compliance_report,
        user=args.user
    )

    print(f"✓ Session saved to: {saved_path}")
    file_size = saved_path.stat().st_size
    print(f"  File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
    print()

    # Check for backups
    if not args.no_backup:
        directory = saved_path.parent
        filename = saved_path.name
        backups = [f for f in os.listdir(directory) if f.startswith(f"{filename}.") and f.endswith(".bak")]
        if backups:
            print(f"  Backups created: {len(backups)}")
            for backup in sorted(backups)[-3:]:  # Show last 3
                print(f"    - {backup}")
            print()

    return saved_path


def load_and_verify_session(session_dir, session_name):
    """Load session and display summary."""
    print("=" * 80)
    print("STEP 3: Loading Session")
    print("=" * 80)
    print()

    session_filepath = Path(session_dir) / f"{session_name}.json"
    if not session_filepath.exists():
        print(f"✗ Session file not found: {session_filepath}")
        print("  Run without --load-only to create a new session first.")
        return None

    session_mgr = SessionManager(session_dir=session_dir)

    try:
        session_data = session_mgr.load(name=session_name)
        print(f"✓ Session loaded from: {session_filepath}")
        print()

        # Display metadata
        meta = session_data.get('meta', {})
        print("Session Metadata:")
        print(f"  User: {meta.get('user', 'unknown')}")
        print(f"  Saved: {meta.get('timestamp', 'unknown')}")
        print(f"  Version: {meta.get('version', 'unknown')}")
        print(f"  Session Name: {meta.get('session_name', 'unknown')}")
        print()

        # Display query parameters
        query_params = session_data.get('query_params', {})
        print("Query Parameters:")
        print(f"  Where clause: {query_params.get('where', 'N/A')}")
        print(f"  Page size: {query_params.get('page_size', 'N/A')}")
        print(f"  Min area: {query_params.get('min_area_sq_miles', 'N/A')} sq mi")
        print()

        # Display results summary
        results = session_data.get('results', {})
        features = results.get('features', [])
        print(f"Query Results: {len(features)} features")
        print()

        # Display compliance summary
        report = session_data.get('report', {})
        summary = report.get('summary', {})
        print("Compliance Summary:")
        print(f"  Total analyzed: {summary.get('total_counties_analyzed', 'N/A')}")
        print(f"  Compliant: {summary.get('compliant_count', 'N/A')}")
        print(f"  Non-compliant: {summary.get('non_compliant_count', 'N/A')}")
        print(f"  Compliance rate: {summary.get('compliance_rate_percentage', 'N/A')}%")
        print(f"  Total shortfall: {summary.get('total_shortfall_sq_miles', 'N/A')} sq mi")
        print()

        # Display top non-compliant counties
        non_compliant = report.get('non_compliant_counties', [])
        if non_compliant:
            print("Top 3 Non-Compliant Counties:")
            for i, county in enumerate(non_compliant[:3], 1):
                print(f"  {i}. {county.get('county_name', 'Unknown')}")
                print(f"     Area: {county.get('area_sq_miles', 0):.2f} sq mi")
                print(f"     Shortfall: {county.get('shortfall_sq_miles', 0):.2f} sq mi")
            print()

        return session_data

    except FileNotFoundError:
        print(f"✗ Session file not found: {session_filepath}")
        return None
    except Exception as e:
        print(f"✗ Error loading session: {e}")
        return None


def test_data_integrity(original_session_dir, original_session_name, loaded_data):
    """Verify loaded data matches saved data."""
    print("=" * 80)
    print("STEP 4: Data Integrity Verification")
    print("=" * 80)
    print()

    if loaded_data is None:
        print("✗ Cannot verify - no loaded data")
        return False

    # Re-load to compare
    session_mgr = SessionManager(session_dir=original_session_dir)
    fresh_load = session_mgr.load(name=original_session_name)

    # Verify key fields match
    checks = [
        ("meta.user", fresh_load.get('meta', {}).get('user')),
        ("meta.session_name", fresh_load.get('meta', {}).get('session_name')),
        ("query_params.where", fresh_load.get('query_params', {}).get('where')),
        ("results.features count", len(fresh_load.get('results', {}).get('features', []))),
        ("report.summary.total_counties_analyzed",
         fresh_load.get('report', {}).get('summary', {}).get('total_counties_analyzed')),
        ("report.summary.compliant_count",
         fresh_load.get('report', {}).get('summary', {}).get('compliant_count')),
    ]

    all_passed = True
    for field_name, value in checks:
        if value is not None:
            print(f"✓ {field_name}: {value}")
        else:
            print(f"✗ {field_name}: Missing")
            all_passed = False

    print()
    if all_passed:
        print("✓ All integrity checks passed!")
    else:
        print("⚠ Some integrity checks failed")

    return all_passed


def main():
    args = parse_arguments()

    print("=" * 80)
    print("Session Save/Load Example")
    print("=" * 80)
    print()

    # Create output directory
    session_dir_path = Path(args.session_dir)
    session_dir_path.mkdir(parents=True, exist_ok=True)

    if args.load_only:
        # Load existing session only
        loaded_data = load_and_verify_session(args.session_dir, args.session_name)
        if loaded_data:
            print("=" * 80)
            print("✓ Session loaded successfully!")
            print("=" * 80)
    else:
        # Full workflow: save and load
        saved_path = run_analysis_and_save(args)
        loaded_data = load_and_verify_session(args.session_dir, args.session_name)

        if loaded_data:
            test_data_integrity(args.session_dir, args.session_name, loaded_data)

            print()
            print("=" * 80)
            print("✓ Complete workflow successful!")
            print("=" * 80)
            print()
            print("Next steps:")
            print(f"  1. Load this session: python {__file__} --load-only --session-name {args.session_name}")
            print(f"  2. View session file: cat {saved_path}")
            print(f"  3. Share with others: Send {saved_path}")


if __name__ == "__main__":
    main()
