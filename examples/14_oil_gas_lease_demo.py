"""
Oil & Gas Lease Compliance Demonstration

This script demonstrates the analysis of Texas counties for oil & gas lease
compliance based on the policy: "All oil & gas leases must be at least 2,500
square miles to qualify for standard terms."

Requirements demonstrated:
1. Query Texas counties from ArcGIS Feature Service
2. Query counties within 50 miles of Austin, TX
3. Identify counties BELOW 2,500 square miles
4. Calculate shortfall for each non-compliant county
5. Rank counties by largest gap first
6. Generate comprehensive compliance report
"""

import sys
import json
from typing import Dict, Any

from src.arcgis_client import ArcGISClient
from src.compliance_checker import analyze_oil_gas_lease_compliance
from errors import ArcGISError, ComplianceError
from logger import get_logger

logger = get_logger(__name__)


def print_section_header(title: str) -> None:
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_county_details(county: Dict[str, Any], rank: int) -> None:
    """Print formatted county compliance details."""
    print(f"\nRank #{rank}: {county['county_name']}, {county['state']}")
    print(f"  Current Area:     {county['area_sq_miles']:>10.2f} sq mi")
    print(f"  Required Area:    {county['required_sq_miles']:>10.2f} sq mi")
    print(f"  Shortfall:        {county['shortfall_sq_miles']:>10.2f} sq mi")
    print(f"  Compliance:       {county['compliance_percentage']:>10.2f}%")
    print(f"  Population:       {county['population']:>10,}")
    print(f"  Recommendation:   {county['recommendation']}")


def save_report_to_file(report: Dict[str, Any], filename: str) -> None:
    """Save compliance report to JSON file."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Report saved to {filename}")
        print(f"\n✓ Full report saved to: {filename}")
    except Exception as e:
        logger.error(f"Failed to save report: {e}")
        print(f"\n✗ Failed to save report: {e}")


def demonstrate_texas_counties_analysis() -> int:
    """
    Demonstrate oil & gas lease compliance analysis for all Texas counties.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    print_section_header("Oil & Gas Lease Compliance Analysis - Texas Counties")

    # ArcGIS Service URL for USA Counties
    service_url = (
        "https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/"
        "USA_Census_Counties/FeatureServer/0"
    )

    logger.info("Starting Texas counties analysis")

    try:
        # Initialize ArcGIS client with context manager for automatic cleanup
        with ArcGISClient(service_url) as client:
            print("Querying Texas counties from ArcGIS Feature Service...")
            print(f"Service URL: {service_url}")

            # Query all Texas counties
            texas_counties = client.query(
                where="STATE_NAME = 'Texas'",
                page_size=500,
                paginate=True
            )

            feature_count = len(texas_counties.get('features', []))
            print(f"✓ Retrieved {feature_count} Texas counties\n")

            # Analyze compliance with 2,500 sq mi requirement
            print("Analyzing compliance with oil & gas lease policy...")
            print("Policy: All leases must be at least 2,500 square miles for standard terms")

            report = analyze_oil_gas_lease_compliance(
                texas_counties['features'],
                min_area_sq_miles=2500.0,
                include_geojson=False
            )

            # Display summary
            print_section_header("Compliance Summary")
            summary = report['summary']
            print(f"Total Counties Analyzed:      {summary['total_counties_analyzed']}")
            print(f"Compliant Counties:           {summary['compliant_count']} ({summary['compliance_rate_percentage']}%)")
            print(f"Non-Compliant Counties:       {summary['non_compliant_count']}")
            print(f"Invalid/Missing Data:         {summary['invalid_count']}")
            print(f"\nTotal Area Shortfall:         {summary['total_shortfall_sq_miles']:,.2f} sq mi")
            print(f"Average Shortfall:            {summary['average_shortfall_sq_miles']:,.2f} sq mi")

            # Display top 10 non-compliant counties by shortfall
            print_section_header("Top 10 Non-Compliant Counties (Ranked by Shortfall)")
            non_compliant = report['non_compliant_counties']

            if non_compliant:
                for i, county in enumerate(non_compliant[:10], 1):
                    print_county_details(county, i)

                # Show total count if more than 10
                if len(non_compliant) > 10:
                    print(f"\n... and {len(non_compliant) - 10} more non-compliant counties")
            else:
                print("✓ All counties meet the minimum area requirement!")

            # Save full report
            save_report_to_file(report, "texas_counties_compliance_report.json")

            logger.info("Texas counties analysis completed successfully")
            return 0

    except ArcGISError as e:
        logger.error(f"ArcGIS query failed: {e}", exc_info=True)
        print(f"\n✗ Error querying ArcGIS service: {e}")
        return 1

    except ComplianceError as e:
        logger.error(f"Compliance analysis failed: {e}", exc_info=True)
        print(f"\n✗ Error analyzing compliance: {e}")
        return 1

    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        print(f"\n✗ Unexpected error: {e}")
        return 1


def demonstrate_austin_spatial_query() -> int:
    """
    Demonstrate spatial query for counties within 50 miles of Austin, TX.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    print_section_header("Spatial Query - Counties Within 50 Miles of Austin, TX")

    service_url = (
        "https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/"
        "USA_Census_Counties/FeatureServer/0"
    )

    austin_coords = (-97.7431, 30.2672)  # Austin, TX (longitude, latitude)
    distance_miles = 50

    logger.info("Starting Austin spatial query")

    try:
        with ArcGISClient(service_url) as client:
            print(f"Querying counties within {distance_miles} miles of Austin, TX")
            print(f"Austin coordinates: {austin_coords[1]}, {austin_coords[0]}")

            # Spatial query
            nearby_counties = client.query_nearby(
                point=austin_coords,
                distance_miles=distance_miles,
                where="1=1",
                page_size=500
            )

            feature_count = len(nearby_counties.get('features', []))
            print(f"✓ Retrieved {feature_count} counties near Austin\n")

            # Analyze compliance
            print("Analyzing compliance for counties near Austin...")

            report = analyze_oil_gas_lease_compliance(
                nearby_counties['features'],
                min_area_sq_miles=2500.0,
                include_geojson=False
            )

            # Display summary
            print_section_header("Austin Area Compliance Summary")
            summary = report['summary']
            print(f"Counties Within {distance_miles} Miles:  {summary['total_counties_analyzed']}")
            print(f"Compliant:                    {summary['compliant_count']}")
            print(f"Non-Compliant:                {summary['non_compliant_count']}")
            print(f"Compliance Rate:              {summary['compliance_rate_percentage']}%")

            # Display all non-compliant counties in the area
            print_section_header("Non-Compliant Counties Near Austin")
            non_compliant = report['non_compliant_counties']

            if non_compliant:
                for i, county in enumerate(non_compliant, 1):
                    print_county_details(county, i)
            else:
                print("✓ All counties near Austin meet the minimum area requirement!")

            # Save report
            save_report_to_file(report, "austin_area_compliance_report.json")

            logger.info("Austin spatial query completed successfully")
            return 0

    except ArcGISError as e:
        logger.error(f"Spatial query failed: {e}", exc_info=True)
        print(f"\n✗ Error executing spatial query: {e}")
        return 1

    except ComplianceError as e:
        logger.error(f"Compliance analysis failed: {e}", exc_info=True)
        print(f"\n✗ Error analyzing compliance: {e}")
        return 1

    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        print(f"\n✗ Unexpected error: {e}")
        return 1


def demonstrate_api_usage() -> None:
    """Demonstrate basic API usage with code examples."""
    print_section_header("API Usage Examples")

    example_code = '''
# Example 1: Basic compliance analysis
from src.arcgis_client import ArcGISClient
from src.compliance_checker import analyze_oil_gas_lease_compliance

service_url = "https://services.arcgis.com/.../FeatureServer/0"

# Query Texas counties
with ArcGISClient(service_url) as client:
    texas_data = client.query(where="STATE_NAME = 'Texas'")

# Analyze compliance
report = analyze_oil_gas_lease_compliance(
    texas_data['features'],
    min_area_sq_miles=2500.0
)

# Access results
print(f"Non-compliant: {report['summary']['non_compliant_count']}")
for county in report['non_compliant_counties'][:5]:
    print(f"{county['county_name']}: {county['shortfall_sq_miles']} sq mi short")

# Example 2: Spatial query near a location
austin_coords = (-97.7431, 30.2672)
nearby = client.query_nearby(
    point=austin_coords,
    distance_miles=50
)

# Analyze nearby counties
report = analyze_oil_gas_lease_compliance(nearby['features'])

# Example 3: Include GeoJSON geometry in results
report = analyze_oil_gas_lease_compliance(
    texas_data['features'],
    min_area_sq_miles=2500.0,
    include_geojson=True  # Includes geometry for mapping
)

# Example 4: Access specific report sections
summary = report['summary']
non_compliant = report['non_compliant_counties']
metadata = report['metadata']

# Save to file
import json
with open('compliance_report.json', 'w') as f:
    json.dump(report, f, indent=2)
'''

    print(example_code)


def main() -> int:
    """
    Main entry point for oil & gas lease compliance demonstration.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    logger.info("Oil & Gas Lease Compliance Demo starting")

    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  Oil & Gas Lease Compliance Analysis - Demonstration".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("║" + "  Policy: All oil & gas leases must be at least 2,500 square miles".center(78) + "║")
    print("║" + "          to qualify for standard terms".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "═" * 78 + "╝")

    # Run demonstrations
    try:
        # 1. Analyze all Texas counties
        result = demonstrate_texas_counties_analysis()
        if result != 0:
            return result

        # 2. Spatial query near Austin
        result = demonstrate_austin_spatial_query()
        if result != 0:
            return result

        # 3. Show API usage examples
        demonstrate_api_usage()

        print_section_header("Demonstration Complete")
        print("✓ All analyses completed successfully")
        print("\nGenerated Reports:")
        print("  - texas_counties_compliance_report.json")
        print("  - austin_area_compliance_report.json")
        print("\nCheck the logs/ directory for detailed execution logs.")

        logger.info("Demo completed successfully")
        return 0

    except KeyboardInterrupt:
        print("\n\n✗ Demo interrupted by user")
        logger.warning("Demo interrupted by user")
        return 130

    except Exception as e:
        print(f"\n✗ Demo failed: {e}")
        logger.critical(f"Demo failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
