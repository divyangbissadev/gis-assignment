import os
import tempfile
import unittest

from src.discrepancy_detector import detect_area_discrepancies, seed_reference_database
from src.errors import DiscrepancyError


class TestDiscrepancyDetector(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        seed_reference_database(
            self.db_path,
            [
                {"name": "Sample County", "state": "TX", "sqmi": 1450},
                {"name": "Matching County", "state": "TX", "sqmi": 1500},
            ],
        )
        self.features = [
            {"attributes": {"NAME": "Sample County", "STATE_NAME": "TX", "SQMI": 1500}},
            {"attributes": {"NAME": "Matching County", "STATE_NAME": "TX", "SQMI": 1500}},
            {"attributes": {"NAME": "Missing County", "STATE_NAME": "TX", "SQMI": 1200}},
        ]

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_detects_discrepancies_against_reference_db(self):
        report = detect_area_discrepancies(self.features, self.db_path, tolerance_percent=1.0)

        self.assertEqual(report["flagged_count"], 1)
        self.assertEqual(report["discrepancies"][0]["name"], "Sample County")
        self.assertAlmostEqual(report["discrepancies"][0]["percent_difference"], 3.45, places=2)
        self.assertEqual(report["matching_count"], 1)
        self.assertIn("Missing County", report["missing_in_db"])

    def test_validation_errors_are_raised(self):
        with self.assertRaises(DiscrepancyError):
            detect_area_discrepancies("not-a-list", self.db_path)
        with self.assertRaises(DiscrepancyError):
            seed_reference_database(self.db_path, [])


if __name__ == "__main__":
    unittest.main()
