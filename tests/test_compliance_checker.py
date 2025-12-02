import unittest
from src.compliance_checker import check_area_compliance, generate_shortfall_report
from src.errors import ComplianceError

class TestComplianceChecker(unittest.TestCase):

    def setUp(self):
        self.sample_features = [
            {"attributes": {"NAME": "County A", "SQMI": 500}},
            {"attributes": {"NAME": "County B", "SQMI": 1500}}
        ]

    # Test 3: Compliance checking works
    def test_compliance_check(self):
        # We need area >= 1000. County A (500) fail, County B (1500) pass.
        min_area = 1000
        report = check_area_compliance(self.sample_features, min_area)

        self.assertEqual(report["total_checked"], 2)
        self.assertEqual(report["compliant_count"], 1)
        self.assertEqual(report["non_compliant_count"], 1)
        self.assertEqual(report["invalid_features"], 0)
        
        details = report["details"]
        self.assertFalse(details[0]["compliant"]) # County A
        self.assertGreater(details[0]["shortfall"], 0)
        self.assertTrue(details[1]["compliant"])  # County B
        self.assertEqual(details[1]["shortfall"], 0)

    def test_invalid_features_are_counted(self):
        features = [{"attributes": {"NAME": "Bad", "SQMI": "not-a-number"}}]
        report = check_area_compliance(features, 1)
        self.assertEqual(report["invalid_features"], 1)
        self.assertEqual(report["total_checked"], 0)
        self.assertEqual(report["non_compliant_count"], 0)

    def test_validation_errors(self):
        with self.assertRaises(ComplianceError):
            check_area_compliance("not-a-list", 1)
        with self.assertRaises(ComplianceError):
            check_area_compliance([], 0)

    def test_generate_shortfall_report_orders_results(self):
        report = generate_shortfall_report(self.sample_features, 1000)
        non_compliant = report["non_compliant_details"]
        self.assertEqual(non_compliant[0]["name"], "County A")
        self.assertGreater(non_compliant[0]["shortfall_sq_miles"], 0)

if __name__ == "__main__":
    unittest.main()
