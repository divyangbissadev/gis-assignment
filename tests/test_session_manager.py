import os
import json
import shutil
from pathlib import Path
from src.session_manager import SessionManager

def test_session_save_load():
    """Test basic save and load functionality."""
    print("=" * 80)
    print("Testing SessionManager Save/Load")
    print("=" * 80)
    print()

    # Test data
    query_params = {
        "where": "STATE_NAME = 'Texas'",
        "page_size": 500,
        "min_area_sq_miles": 2500.0
    }

    query_results = {
        "features": [
            {"attributes": {"NAME": "Harris", "SQMI": 1700.5}},
            {"attributes": {"NAME": "Dallas", "SQMI": 880.3}},
            {"attributes": {"NAME": "Brewster", "SQMI": 6193.0}}
        ]
    }

    compliance_report = {
        "summary": {
            "total_counties_analyzed": 3,
            "compliant_count": 1,
            "non_compliant_count": 2,
            "compliance_rate_percentage": 33.33
        },
        "non_compliant_counties": [
            {"county_name": "Harris", "area_sq_miles": 1700.5, "shortfall_sq_miles": 799.5},
            {"county_name": "Dallas", "area_sq_miles": 880.3, "shortfall_sq_miles": 1619.7}
        ]
    }

    session_name = "TestSession1"
    session_dir = "test_sessions"
    session_filepath = Path(session_dir) / f"{session_name}.json"

    # Ensure a clean slate before starting the test
    if Path(session_dir).exists():
        shutil.rmtree(session_dir)

    try:
        # Test 1: Save session
        print("Test 1: Save Session")
        print("-" * 80)

        session_mgr = SessionManager(session_dir=session_dir, auto_backup=False)
        saved_path = session_mgr.save(
            name=session_name,
            query_params=query_params,
            results=query_results,
            compliance_report=compliance_report,
            user="test_user"
        )

        print(f"✓ Session saved to: {saved_path}")
        print(f"  File exists: {session_filepath.exists()}")
        assert session_filepath.exists()
        print(f"  File size: {session_filepath.stat().st_size} bytes")
        assert session_filepath.stat().st_size > 0
        print()

        # Test 2: Load session
        print("Test 2: Load Session")
        print("-" * 80)

        loaded_data = session_mgr.load(name=session_name)
        print(f"✓ Session loaded from: {session_filepath}")
        print()

        # Test 3: Verify data integrity
        print("Test 3: Verify Data Integrity")
        print("-" * 80)

        checks = [
            ("User matches", loaded_data['meta']['user'] == "test_user"),
            ("Session name in meta matches", loaded_data['meta']['session_name'] == session_name),
            ("Query params match", loaded_data['query_params'] == query_params),
            ("Feature count matches", len(loaded_data['results']['features']) == 3),
            ("Summary matches", loaded_data['report']['summary']['total_counties_analyzed'] == 3),
            ("Metadata has timestamp", 'timestamp' in loaded_data['meta']),
            ("Metadata has version", loaded_data['meta']['version'] == "1.0"),
        ]

        all_passed = True
        for check_name, passed in checks:
            status = "✓" if passed else "✗"
            print(f"{status} {check_name}")
            if not passed:
                all_passed = False
                assert False, f"{check_name} failed." # Fail immediately for visibility

        print()

        # Test 4: Test backup creation
        print("Test 4: Test Backup Creation")
        print("-" * 80)

        session_mgr_with_backup = SessionManager(session_dir=session_dir, auto_backup=True)

        # Modify and save again to trigger backup
        query_params["where"] = "STATE_NAME = 'California'"
        session_mgr_with_backup.save(
            name=session_name,
            query_params=query_params,
            results=query_results,
            compliance_report=compliance_report,
            user="test_user_2"
        )

        # Check for backup files
        directory_path = Path(session_dir)
        backups = [f for f in os.listdir(directory_path)
                   if f.startswith(f"{session_name}.json.") and f.endswith(".bak")]

        print(f"✓ Backup files created: {len(backups)}")
        assert len(backups) > 0 # At least one backup should exist
        for backup in backups:
            print(f"  - {backup}")
        print()

        # Test 5: Verify updated data
        print("Test 5: Verify Updated Data")
        print("-" * 80)

        reloaded_data = session_mgr_with_backup.load(name=session_name)
        updated_user = reloaded_data['meta']['user']
        updated_where = reloaded_data['query_params']['where']

        print(f"✓ Updated user: {updated_user}")
        assert updated_user == "test_user_2"
        print(f"✓ Updated where clause: {updated_where}")
        assert updated_where == "STATE_NAME = 'California'"
        print()

        # Final results
        print("=" * 80)
        if all_passed:
            print("✅ ALL TESTS PASSED!")
        else:
            print("⚠️  SOME TESTS FAILED")
        print("=" * 80)

        assert all_passed # Final assertion to ensure all checks passed

    finally:
        # Cleanup
        if Path(session_dir).exists():
            shutil.rmtree(session_dir)
            print()
            print(f"✓ Cleanup complete (removed {session_dir} directory)")


if __name__ == "__main__":
    test_session_save_load()
