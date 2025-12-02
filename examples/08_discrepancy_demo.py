"""
Offline demo: detect mismatches between GIS features and a SQLite reference table.

Simulates a scenario where GIS reports 1,500 sq mi for a county while the
database of record shows 1,450 sq mi (3.3% difference). Discrepancies above the
configured tolerance are flagged.
"""

import tempfile
from pathlib import Path

import os
import sys

# Make project root importable when running from repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.discrepancy_detector import detect_area_discrepancies, seed_reference_database


def build_sample_features():
    """Return synthetic GIS features for comparison."""
    return [
        {"attributes": {"NAME": "Sample County", "STATE_NAME": "TX", "SQMI": 1500}},
        {"attributes": {"NAME": "Matching County", "STATE_NAME": "TX", "SQMI": 1500}},
        {"attributes": {"NAME": "Untracked County", "STATE_NAME": "TX", "SQMI": 1200}},
    ]


def main():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = Path(tmp.name)

    # Seed reference data where Sample County is smaller in the system of record.
    seed_reference_database(
        str(db_path),
        [
            {"name": "Sample County", "state": "TX", "sqmi": 1450},
            {"name": "Matching County", "state": "TX", "sqmi": 1500},
        ],
    )

    report = detect_area_discrepancies(
        build_sample_features(),
        str(db_path),
        tolerance_percent=1.0,  # Flag anything over 1% difference
    )

    print("\n=== GIS vs Database Discrepancy Demo ===")
    print(f"Tolerance: +/-{report['tolerance_percent']}%")
    print(f"Records compared: {report['compared']}")

    if report["discrepancies"]:
        print("\nFlagged discrepancies:")
        for item in report["discrepancies"]:
            print(
                f"- {item['name']} ({item['state'] or 'N/A'}): "
                f"GIS {item['gis_sq_miles']} sq mi vs DB {item['db_sq_miles']} sq mi "
                f"({item['percent_difference']}% difference, {item['status']})"
            )
    else:
        print("\nNo discrepancies detected.")

    if report["missing_in_db"]:
        missing = ', '.join(report["missing_in_db"])
        print(f"\nMissing from database: {missing}")

    db_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
