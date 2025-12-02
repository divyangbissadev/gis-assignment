"""
Tests for oil & gas lease compliance analysis.
"""

import unittest
from src.compliance_checker import analyze_oil_gas_lease_compliance, _generate_lease_recommendation
from src.errors import ComplianceError


class TestOilGasLeaseCompliance(unittest.TestCase):
    """Test cases for oil & gas lease compliance analysis."""

    def setUp(self):
        """Set up test fixtures."""
        # Sample features in GeoJSON format (like ArcGISClient returns)
        self.sample_features = [
            {
                "type": "Feature",
                "properties": {
                    "NAME": "Large County",
                    "STATE_NAME": "Texas",
                    "SQMI": 3000.0,
                    "POPULATION": 50000
                },
                "geometry": {"type": "Point", "coordinates": [-97.0, 30.0]}
            },
            {
                "type": "Feature",
                "properties": {
                    "NAME": "Medium County",
                    "STATE_NAME": "Texas",
                    "SQMI": 2000.0,
                    "POPULATION": 25000
                },
                "geometry": {"type": "Point", "coordinates": [-98.0, 31.0]}
            },
            {
                "type": "Feature",
                "properties": {
                    "NAME": "Small County",
                    "STATE_NAME": "Texas",
                    "SQMI": 500.0,
                    "POPULATION": 5000
                },
                "geometry": {"type": "Point", "coordinates": [-99.0, 32.0]}
            },
            {
                "type": "Feature",
                "properties": {
                    "NAME": "Tiny County",
                    "STATE_NAME": "Texas",
                    "SQMI": 100.0,
                    "POPULATION": 1000
                },
                "geometry": {"type": "Point", "coordinates": [-100.0, 33.0]}
            },
        ]

    def test_basic_analysis(self):
        """Test basic compliance analysis with 2500 sq mi requirement."""
        report = analyze_oil_gas_lease_compliance(
            self.sample_features,
            min_area_sq_miles=2500.0
        )

        # Check report structure
        self.assertIn('summary', report)
        self.assertIn('non_compliant_counties', report)
        self.assertIn('compliant_counties', report)
        self.assertIn('metadata', report)

        # Check summary statistics
        summary = report['summary']
        self.assertEqual(summary['total_counties_analyzed'], 4)
        self.assertEqual(summary['compliant_count'], 1)  # Only Large County
        self.assertEqual(summary['non_compliant_count'], 3)  # Medium, Small, Tiny

    def test_shortfall_ranking(self):
        """Test that counties are ranked by shortfall (largest gap first)."""
        report = analyze_oil_gas_lease_compliance(
            self.sample_features,
            min_area_sq_miles=2500.0
        )

        non_compliant = report['non_compliant_counties']

        # Should be 3 non-compliant counties
        self.assertEqual(len(non_compliant), 3)

        # Check they're sorted by shortfall (descending)
        # Tiny County: 2500 - 100 = 2400
        # Small County: 2500 - 500 = 2000
        # Medium County: 2500 - 2000 = 500
        self.assertEqual(non_compliant[0]['county_name'], 'Tiny County')
        self.assertEqual(non_compliant[0]['shortfall_sq_miles'], 2400.0)

        self.assertEqual(non_compliant[1]['county_name'], 'Small County')
        self.assertEqual(non_compliant[1]['shortfall_sq_miles'], 2000.0)

        self.assertEqual(non_compliant[2]['county_name'], 'Medium County')
        self.assertEqual(non_compliant[2]['shortfall_sq_miles'], 500.0)

    def test_compliance_percentage(self):
        """Test that compliance percentage is calculated correctly."""
        report = analyze_oil_gas_lease_compliance(
            self.sample_features,
            min_area_sq_miles=2500.0
        )

        non_compliant = report['non_compliant_counties']

        # Medium County: 2000/2500 = 80%
        medium = [c for c in non_compliant if c['county_name'] == 'Medium County'][0]
        self.assertEqual(medium['compliance_percentage'], 80.0)

        # Small County: 500/2500 = 20%
        small = [c for c in non_compliant if c['county_name'] == 'Small County'][0]
        self.assertEqual(small['compliance_percentage'], 20.0)

    def test_recommendations(self):
        """Test that appropriate recommendations are generated."""
        report = analyze_oil_gas_lease_compliance(
            self.sample_features,
            min_area_sq_miles=2500.0
        )

        non_compliant = report['non_compliant_counties']

        # Medium County at 80% should get adjacent tracts recommendation
        medium = [c for c in non_compliant if c['county_name'] == 'Medium County'][0]
        self.assertIn('adjacent tracts', medium['recommendation'].lower())

        # Tiny County at 4% should get alternative structure recommendation
        tiny = [c for c in non_compliant if c['county_name'] == 'Tiny County'][0]
        self.assertIn('alternative lease structure', tiny['recommendation'].lower())

    def test_include_geojson(self):
        """Test that geometry is included when requested."""
        # Without geometry
        report_no_geo = analyze_oil_gas_lease_compliance(
            self.sample_features,
            min_area_sq_miles=2500.0,
            include_geojson=False
        )

        non_compliant = report_no_geo['non_compliant_counties'][0]
        self.assertNotIn('geometry', non_compliant)

        # With geometry
        report_with_geo = analyze_oil_gas_lease_compliance(
            self.sample_features,
            min_area_sq_miles=2500.0,
            include_geojson=True
        )

        non_compliant_geo = report_with_geo['non_compliant_counties'][0]
        self.assertIn('geometry', non_compliant_geo)

    def test_invalid_features_parameter(self):
        """Test that invalid features parameter raises error."""
        with self.assertRaises(ComplianceError):
            analyze_oil_gas_lease_compliance("not a list", 2500.0)

        with self.assertRaises(ComplianceError):
            analyze_oil_gas_lease_compliance(None, 2500.0)

    def test_invalid_min_area_parameter(self):
        """Test that invalid min_area parameter raises error."""
        with self.assertRaises(ComplianceError):
            analyze_oil_gas_lease_compliance(self.sample_features, 0)

        with self.assertRaises(ComplianceError):
            analyze_oil_gas_lease_compliance(self.sample_features, -1000)

    def test_empty_features_list(self):
        """Test handling of empty features list."""
        report = analyze_oil_gas_lease_compliance([], 2500.0)

        self.assertEqual(report['summary']['total_counties_analyzed'], 0)
        self.assertEqual(report['summary']['compliant_count'], 0)
        self.assertEqual(report['summary']['non_compliant_count'], 0)

    def test_all_compliant(self):
        """Test case where all counties are compliant."""
        large_counties = [
            {
                "properties": {
                    "NAME": f"Large County {i}",
                    "STATE_NAME": "Texas",
                    "SQMI": 3000.0 + (i * 100),
                    "POPULATION": 50000
                }
            }
            for i in range(5)
        ]

        report = analyze_oil_gas_lease_compliance(large_counties, 2500.0)

        self.assertEqual(report['summary']['compliant_count'], 5)
        self.assertEqual(report['summary']['non_compliant_count'], 0)
        self.assertEqual(report['summary']['compliance_rate_percentage'], 100.0)
        self.assertEqual(report['summary']['total_shortfall_sq_miles'], 0.0)

    def test_invalid_area_data(self):
        """Test handling of features with invalid area data."""
        features_with_invalid = [
            {
                "properties": {
                    "NAME": "Valid County",
                    "STATE_NAME": "Texas",
                    "SQMI": 2000.0,
                    "POPULATION": 25000
                }
            },
            {
                "properties": {
                    "NAME": "Invalid County 1",
                    "STATE_NAME": "Texas",
                    "SQMI": "not a number",
                    "POPULATION": 10000
                }
            },
            {
                "properties": {
                    "NAME": "Invalid County 2",
                    "STATE_NAME": "Texas",
                    # Missing SQMI field - defaults to 0
                    "POPULATION": 5000
                }
            },
        ]

        report = analyze_oil_gas_lease_compliance(features_with_invalid, 2500.0)

        # Valid County and Invalid County 2 (with 0 area) should be analyzed
        # Invalid County 1 ("not a number") should be skipped
        self.assertEqual(report['summary']['total_counties_analyzed'], 2)
        self.assertEqual(report['summary']['invalid_count'], 1)

    def test_metadata(self):
        """Test that metadata is included in report."""
        report = analyze_oil_gas_lease_compliance(
            self.sample_features,
            min_area_sq_miles=2500.0
        )

        metadata = report['metadata']
        self.assertIn('policy', metadata)
        self.assertEqual(metadata['minimum_area_requirement_sq_miles'], 2500.0)
        self.assertIn('analysis_timestamp', metadata)
        self.assertIn('include_geometry', metadata)

    def test_total_shortfall_calculation(self):
        """Test that total shortfall is calculated correctly."""
        report = analyze_oil_gas_lease_compliance(
            self.sample_features,
            min_area_sq_miles=2500.0
        )

        # Expected shortfalls:
        # Medium: 500, Small: 2000, Tiny: 2400
        # Total: 4900
        expected_total = 500.0 + 2000.0 + 2400.0
        self.assertEqual(report['summary']['total_shortfall_sq_miles'], expected_total)

    def test_average_shortfall_calculation(self):
        """Test that average shortfall is calculated correctly."""
        report = analyze_oil_gas_lease_compliance(
            self.sample_features,
            min_area_sq_miles=2500.0
        )

        # Average of 500, 2000, 2400 = 4900 / 3 = 1633.33
        expected_avg = 4900.0 / 3
        self.assertAlmostEqual(
            report['summary']['average_shortfall_sq_miles'],
            expected_avg,
            places=2
        )

    def test_custom_min_area(self):
        """Test with custom minimum area requirement."""
        report = analyze_oil_gas_lease_compliance(
            self.sample_features,
            min_area_sq_miles=1000.0
        )

        # With 1000 sq mi requirement:
        # Compliant: Large (3000), Medium (2000)
        # Non-compliant: Small (500), Tiny (100)
        self.assertEqual(report['summary']['compliant_count'], 2)
        self.assertEqual(report['summary']['non_compliant_count'], 2)


class TestLeaseRecommendations(unittest.TestCase):
    """Test lease recommendation generation."""

    def test_minor_shortfall_recommendation(self):
        """Test recommendation for minor shortfall (>= 90%)."""
        rec = _generate_lease_recommendation(2300.0, 2500.0)  # 92%
        self.assertIn('special terms', rec.lower())

    def test_moderate_shortfall_recommendation(self):
        """Test recommendation for moderate shortfall (75-90%)."""
        rec = _generate_lease_recommendation(2000.0, 2500.0)  # 80%
        self.assertIn('adjacent tracts', rec.lower())

    def test_significant_shortfall_recommendation(self):
        """Test recommendation for significant shortfall (50-75%)."""
        rec = _generate_lease_recommendation(1500.0, 2500.0)  # 60%
        self.assertIn('pooling', rec.lower())

    def test_major_shortfall_recommendation(self):
        """Test recommendation for major shortfall (< 50%)."""
        rec = _generate_lease_recommendation(500.0, 2500.0)  # 20%
        self.assertIn('alternative lease structure', rec.lower())


if __name__ == '__main__':
    unittest.main()
